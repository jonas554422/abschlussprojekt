import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
import pandas as pd
from backend import UserDatabase
from refresh_mci import aktualisiere_mci_daten
import os
import time


# Stellen Sie sicher, dass die Locale korrekt für die Datumsformatierung gesetzt ist
# Achtung: Diese Zeile könnte auf nicht-englischen Systemen oder in bestimmten Umgebungen angepasst werden müssen
#locale.setlocale(locale.LC_TIME, 'en_US.utf8' or 'English_United States.1252')

# Pfad zur Datenbank für verfügbare Räume
DB_PATH = 'verfuegbare_raeume_db.json'
user_db = UserDatabase('reservation.json', 'verfuegbare_raeume_db.json')


# Initialisierung des Session State für den Anmeldestatus, falls noch nicht vorhanden
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None
if 'confirm_cancel' not in st.session_state:
    st.session_state['confirm_cancel'] = False


# UserDatabase-Instanz erstellen
user_db = UserDatabase('reservation.json', 'verfuegbare_raeume_db.json')

def display_login():
    login_email = st.sidebar.text_input("Email einloggen", key="login_email")

    if st.sidebar.button("Einloggen", key="login_button"):
        if user_db.authenticate(login_email):
            st.session_state['logged_in_user'] = login_email
            st.sidebar.success('Anmeldung erfolgreich!')
            # Aufruf von display_storno_notifications() mit der E-Mail des angemeldeten Benutzers
            display_storno_notifications(login_email)  # Zeige Stornierungsnachrichten, falls vorhanden
            st.experimental_rerun()
        else:
            st.sidebar.error('Ungültige E-Mail-Adresse oder nicht registriert.')


def display_registration():
    reg_email = st.sidebar.text_input("Email registrieren", key="reg_email")
    if st.sidebar.button("Registrieren", key="register_button"):
        registration_result = user_db.register_user(reg_email)
        if registration_result is True:
            st.sidebar.success('Registrierung erfolgreich!')
        else:
            st.sidebar.error(registration_result)


def display_available_rooms():
    if 'logged_in_user' in st.session_state and st.session_state['logged_in_user']:
        db = TinyDB(DB_PATH)
        rooms = db.all()
        if rooms:
            room_numbers = list(set(room['Raumnummer'] for room in rooms))
            selected_room = st.selectbox('Wählen Sie einen Raum', room_numbers)

            available_times_list = [room for room in rooms if room['Raumnummer'] == selected_room]
            reservations = user_db.get_reservations_for_room(selected_room)
            available_times = user_db.calculate_availability(available_times_list, reservations)

            if available_times:
                available_times_df = pd.DataFrame(available_times)
                available_times_df['Datum'] = pd.to_datetime(available_times_df['Datum'], dayfirst=True).dt.strftime('%A, %d.%m.%Y')
                available_times_df.sort_values(by=['Datum', 'Verfuegbar von'], inplace=True)
                table_placeholder = st.empty()
                table_placeholder.dataframe(available_times_df[['Datum', 'Verfuegbar von', 'Verfuegbar bis']], height=200)

            date = st.date_input("Datum wählen", min_value=datetime.today())
            start_time = st.time_input("Startzeit wählen", value=datetime.now())
            end_time = st.time_input("Endzeit wählen", value=(datetime.now() + timedelta(hours=1)))

            if start_time >= end_time:
                st.error("Die Startzeit muss vor der Endzeit liegen.")
                return

            formatted_date = date.strftime('%A, %d.%m.%Y')
            formatted_start_time = start_time.strftime('%H:%M')
            formatted_end_time = end_time.strftime('%H:%M')

            user_email = st.session_state.get('logged_in_user', 'admin')

            if st.button("Raum buchen"):
                # Prüfen, ob der Raum zum gewählten Zeitpunkt verfügbar ist
                success, message = user_db.add_reservation(user_email, selected_room, formatted_date, formatted_start_time, formatted_end_time)
                if success:
                    st.success("Raum erfolgreich gebucht.")
                else:
                    st.error(f"Buchung fehlgeschlagen: {message}")
        else:
            st.write("Keine verfügbaren Räume gefunden.")
    else:
        st.error("Bitte einloggen, um das Buchungssystem zu nutzen.")







def display_user_reservations():
    if 'logged_in_user' in st.session_state and st.session_state['logged_in_user']:
        user_email = st.session_state['logged_in_user']
        user_reservations = user_db.get_user_reservations(user_email)
    
        if user_reservations:
            for reservation in user_reservations:
                doc_id = reservation.doc_id  # Zugriff auf die doc_id des aktuellen Dokuments
                st.write(f"Reservierung für Raum {reservation['room_number']} am {reservation['date']} von {reservation['start_time']} bis {reservation['end_time']}")
                if st.button(f"Stornieren {doc_id}", key=f"cancel-{doc_id}"):
                    if 'confirm_cancel' not in st.session_state:
                        st.session_state['confirm_cancel'] = False
                    st.session_state['confirm_cancel'] = doc_id  # Speichere die doc_id für die Bestätigung

            # Bestätigungsdialog für Stornierung anzeigen, wenn notwendig
            if st.session_state['confirm_cancel']:
                if st.button("Ja, stornieren", key=f"confirm-cancel-{st.session_state['confirm_cancel']}"):
                    user_db.cancel_reservation(st.session_state['confirm_cancel'])
                    st.success("Reservierung wurde erfolgreich storniert.")
                    del st.session_state['confirm_cancel']  # Zurücksetzen
                    st.experimental_rerun()
                elif st.button("Nein", key=f"deny-cancel-{st.session_state['confirm_cancel']}"):
                    del st.session_state['confirm_cancel']  # Zurücksetzen
        else:
            st.write("Sie haben keine aktiven Reservierungen.")
    

def display_mci_daten_aktualisierung():
    st.sidebar.title("MCI-Datenaktualisierung")
    
    # Hinweis für den Benutzer hinzufügen
    st.sidebar.warning("Hinweis: Die Funktion zur Datenaktualisierung kann nur im Offline-Betrieb verwendet werden, da aktuell auf dem Webserver kein Browser installiert ist, welcher benötigt wird, um die Daten zu downloaden.")
    
    if st.sidebar.button("Daten aktualisieren"):
        with st.spinner("Bitte warten Sie, die Daten werden aktualisiert..."):
            erfolg, nachricht = aktualisiere_mci_daten()
            if erfolg:
                st.success(nachricht)
                # Aufruf der Verifizierungsmethode, um die Reservierungen zu überprüfen
                if 'logged_in_user' in st.session_state:
                    user_db.verify_reservations(st.session_state['logged_in_user'])
            else:
                st.error(nachricht)


def display_storno_entries():
    user_db = UserDatabase()
    if 'logged_in_user' in st.session_state and st.session_state['logged_in_user']:
        user_email = st.session_state['logged_in_user']
        storno_entries = user_db.storno_table.search(Query().email == user_email)

        if storno_entries:
            st.write("Stornierte Reservierungen:")
            for entry in storno_entries:
                st.write(f"Raum {entry['room_number']} am {entry['date']} von {entry['start_time']} bis {entry['end_time']} wurde am {entry['storno_time']} storniert.")

            # Wenn der Button gedrückt wird, setzen Sie eine Zustandsvariable für die Bestätigung
            if st.button("Storno-Meldungen löschen"):
                st.session_state['confirm_delete'] = True

            # Zeige die Bestätigungsanfrage an, wenn die Zustandsvariable gesetzt ist
            if st.session_state.get('confirm_delete', False):
                if st.button("Bestätige die Löschung aller Storno-Meldungen"):
                    user_db.delete_all_user_storno_entries(user_email)  # Nutzung der Methode aus UserDatabase
                    st.success("Alle stornierten Reservierungen wurden erfolgreich gelöscht.")
                    st.experimental_rerun()  # Seite neu laden, um Änderungen anzuzeigen
                elif st.button("Abbrechen"):
                    del st.session_state['confirm_delete']  # Entferne die Bestätigungszustandsvariable, um den Vorgang abzubrechen
        else:
            st.write("Keine stornierten Reservierungen vorhanden.")


# Funktion zum Setzen des Anmeldezeitpunkts
def user_logged_in():
    # Speichere den aktuellen Zeitpunkt als letzten Anmeldezeitpunkt
    st.session_state['last_login_time'] = datetime.datetime.now()

# Funktion zum Anzeigen von Stornierungsnachrichten, zeigt Nachrichten nur einmal nach der Anmeldung an
def display_storno_notifications(user_db, user_email):
    # Prüfe, ob seit der letzten Anmeldung genügend Zeit vergangen ist und ob Stornierungsnachrichten bereits angezeigt wurden
    if 'last_login_time' in st.session_state and not st.session_state.get('storno_shown', False):
        time_since_login = datetime.datetime.now() - st.session_state['last_login_time']
        if time_since_login.total_seconds() <= 10:
            storno_entries = user_db.storno_table.search(Query().email == user_email)
            if storno_entries:
                for entry in storno_entries:
                    message = entry.get('message', 'Keine zusätzliche Nachricht vorhanden.')
                    st.warning(f"Stornierte Buchung: Raum {entry['room_number']} am {entry['date']} von {entry['start_time']} bis {entry['end_time']} wurde storniert. {message}")
                # Markiere, dass Stornierungsnachrichten angezeigt wurden
                st.session_state['storno_shown'] = True





def display_room_review_form(user_db):
    st.header("Raum bewerten")
    room_numbers = user_db.get_unique_room_numbers()
    room_number = st.selectbox("Raumnummer wählen", options=room_numbers)
    
    # Bewertungsformular nur anzeigen, wenn nicht im Bearbeitungsmodus
    if 'editing_review_id' not in st.session_state:
        rating = st.slider("Bewertung", 1, 5)
        feedback = st.text_area("Feedback")
        photo_upload = st.file_uploader("Foto hochladen", type=["png", "jpg", "jpeg"])

        if photo_upload is not None:
            os.makedirs("uploads", exist_ok=True)
            file_path = f"uploads/{photo_upload.name}"
            with open(file_path, "wb") as f:
                f.write(photo_upload.getvalue())
        else:
            file_path = None

        if st.button("Bewertung abgeben"):
            user_email = st.session_state.get('logged_in_user', 'anonymous')
            photo_path = file_path
            user_db.add_room_review(room_number, user_email, rating, feedback, photo_path=photo_path)
            st.success("Bewertung erfolgreich abgegeben.")
    
    # Bearbeitungsformular
    if 'editing_review_id' in st.session_state:
        # Laden der zu bearbeitenden Bewertungsdetails
        editing_review = user_db.get_review_by_id(st.session_state['editing_review_id'])
        with st.form("edit_review"):
            new_rating = st.slider("Bewertung anpassen", 1, 5, editing_review['rating'])
            new_feedback = st.text_area("Feedback anpassen", editing_review['feedback'])
            # Implementieren Sie Logik für Foto-Uploads im Bearbeitungsmodus nach Bedarf
            submitted = st.form_submit_button("Änderungen speichern")
            if submitted:
                user_db.edit_room_review(st.session_state['editing_review_id'], new_rating, new_feedback)
                st.success("Bewertung erfolgreich aktualisiert.")
                del st.session_state['editing_review_id']  # Bearbeitungsmodus beenden
                st.experimental_rerun()

    # Anzeigen bestehender Bewertungen
    st.write("Bisherige Bewertungen für Raum:", room_number)
    reviews = user_db.get_room_reviews(room_number)
    if reviews:
        for review in reviews:
            with st.expander(f"Bewertung von {review['email']} am {review['timestamp']}"):
                st.write(f"Rating: {review['rating']}/5")
                st.text(f"Feedback: {review['feedback']}")
                if review.get('photo_path'):
                    st.image(review['photo_path'], caption="Bewertungsfoto")
                if review['email'] == st.session_state.get('logged_in_user'):
                    delete_key = f"delete-{review['doc_id']}"
                    if st.button("Stornieren", key=delete_key):
                        user_db.cancel_room_review(review['doc_id'])
                        st.experimental_rerun()
                    edit_key = f"edit-{review['doc_id']}"
                    if st.button("Bearbeiten", key=edit_key):
                        st.session_state['editing_review_id'] = review['doc_id']
                        st.experimental_rerun()
    else:
        st.write("Noch keine Bewertungen für diesen Raum vorhanden.")


def display_all_reviews(user_db):
    st.header("Alle Bewertungen")
    all_reviews = user_db.get_all_reviews()
    
    if all_reviews:
        for i, review in enumerate(all_reviews):
            with st.expander(f"Bewertung {i+1} von {review['email']}"):
                st.write(f"Bewertung von {review['email']}: {review['rating']}/5")
                st.text(f"Feedback: {review['feedback']}")
                st.text(f"Raumnummer: {review['room_number']}") 
                if review.get('photo_path'):
                    st.image(review['photo_path'], caption="Bewertungsfoto")
                if st.button("Bewertung stornieren", key=f"cancel-{review['doc_id']}-{i+1}"):
                    user_db.cancel_room_review(review['doc_id'])
                    st.experimental_rerun()
    else:
        st.write("Keine Bewertungen vorhanden.")


def display_user_reviews(user_db):
    st.header("Meine Bewertungen")
    user_email = st.session_state.get('logged_in_user', 'anonymous')
    user_reviews = user_db.get_user_reviews(user_email)
    
    if user_reviews:
        for i, review in enumerate(user_reviews):
            with st.expander(f"Bewertung {i+1}"):
                st.write(f"Bewertung für Raum {review['room_number']}: {review['rating']}/5")
                st.text(f"Feedback: {review['feedback']}")
                if review.get('photo_path'):
                    st.image(review['photo_path'], caption="Bewertungsfoto")
    else:
        st.write("Keine Bewertungen vorhanden.")













ADMIN_SECRET_CODE = "123"  # Das spezielle Kennwort für den Admin-Zugang

def check_for_admin_code(input_code):
    if input_code == ADMIN_SECRET_CODE:
        st.session_state['is_admin'] = True
        st.experimental_rerun()
    else:
        st.session_state['is_admin'] = False

def display_admin_input():
    # Überprüfen, ob der Benutzer bereits als Admin angemeldet ist
    if st.session_state.get('is_admin'):
        if st.sidebar.button("Ausloggen"):
            # Setze den Admin-Status zurück
            st.session_state['is_admin'] = False
            st.sidebar.success("Sie wurden erfolgreich als Admin ausgeloggt.")
            st.experimental_rerun()
    else:
        with st.sidebar.expander("Admin-Zugang"):
            admin_code = st.text_input("Admin Code eingeben", key="admin_code", type="password")
            if st.button("Admin-Zugang bestätigen"):
                # Hier wird die bereits existierende Funktion aufgerufen, die den Admin-Code überprüft
                check_for_admin_code(admin_code)



def display_login_and_registration():
    login_email = st.sidebar.text_input("Email einloggen", key="login_email")
    if st.sidebar.button("Einloggen", key="login_button"):
        if user_db.authenticate(login_email):
            st.session_state['logged_in_user'] = login_email
            # Wenn die Authentifizierung erfolgreich ist, nehmen wir an, dass der Benutzer registriert ist.
            st.session_state['is_registered'] = True
            st.sidebar.success('Anmeldung erfolgreich!')
            st.experimental_rerun()
        else:
            st.sidebar.error('Ungültige E-Mail-Adresse oder nicht registriert.')

    # Überprüfen, ob der Benutzer nicht als Admin angemeldet ist und ob der Anmeldestatus nicht auf 'True' gesetzt ist,
    # was darauf hindeutet, dass der Benutzer bereits registriert ist.
    if not st.session_state.get('is_admin') and not st.session_state.get('logged_in_user'):
        reg_email = st.sidebar.text_input("Email registrieren", key="reg_email")
        if st.sidebar.button("Registrieren", key="register_button"):
            registration_result = user_db.register_user(reg_email)
            if registration_result == True:
                st.session_state['is_registered'] = True
                st.sidebar.success('Registrierung erfolgreich!')
            else:
                st.sidebar.error(registration_result)

# Stellen Sie sicher, dass diese Zeile am Anfang des main()-Funktionskörpers steht, 
# um den initialen Status von 'is_registered' festzulegen.
if 'is_registered' not in st.session_state:
    st.session_state['is_registered'] = False


def display_admin_interface():
    st.write("Admin-Bereich: Verwaltung der Buchungen")
    reservations = user_db.get_all_reservations()

    if reservations:
        # Konvertieren Sie die Reservierungen in ein DataFrame
        df_reservations = pd.DataFrame(reservations)

        # Überprüfen Sie, ob die 'doc_id' vorhanden ist
        if 'doc_id' not in df_reservations.columns:
            st.error("Fehler: Keine doc_id in den Reservierungsdaten gefunden.")
            return

        # Nach Datum sortieren
        df_reservations['date'] = pd.to_datetime(df_reservations['date'], format='%A, %d.%m.%Y')
        df_reservations_sorted = df_reservations.sort_values(by='date')

        # Zeige das DataFrame an
        st.dataframe(df_reservations_sorted[['email', 'room_number', 'date', 'start_time', 'end_time']], height=600)

        # Für jede Reservierung, generiere einen Stornieren-Button basierend auf der 'doc_id'
        for index, row in df_reservations.iterrows():
            if st.button(f"Stornieren {row['doc_id']}", key=f"cancel-{row['doc_id']}"):
                # Führe die Stornierung durch und zeige eine Bestätigungsnachricht an
                user_db.cancel_reservation(row['doc_id'])
                st.success(f"Reservierung {row['doc_id']} storniert.")
                # Optional: Nachricht an den Benutzer senden, dass seine Reservierung storniert wurde
                user_db.notify_user_of_cancellation(row['email'], row['room_number'], row['date'])
                st.experimental_rerun()  # Seite neu laden, um die Änderungen zu reflektieren
    else:
        st.write("Keine Reservierungen vorhanden.")

def display_stats():
    if len(user_db.get_all_reservations()) == 0:
        st.write("Statistik")
        st.write("Räume und deren Reservierungszeiten:")
        st.write("Aktuell gibt es keine Reservierungen")
    else:
        st.write("Statistik")
        st.write("Räume und deren Reservierungszeiten:")
        st.write("In den folgenden Bar-Charts werden zum jeweiligen Datum die Räume mit den größten Reservierungszeiten dargestellt")
        user_db.plot_reservierte_räume()
        
        ## Eine Toast-Nachricht anzeigen
        #st.toast("Ihre Zeit läuft bald ab...")
        #time.sleep(5)
    



def main():
    st.title('Raumbuchung MCI-IV')

    if 'is_registered' not in st.session_state:
        st.session_state['is_registered'] = False

    display_admin_input()  # Überprüft den Admin-Code und setzt den Admin-Status

    display_login_and_registration()  # Zeigt Anmelde- und Registrierungsfelder an, abhängig vom Admin-Status

    user_email = st.session_state.get('logged_in_user')

    display_storno_notifications(user_db, user_email)   # Zeige Stornierungsnachrichten an, falls vorhanden

    # Definiere die Menüoptionen abhängig vom Anmeldestatus des Benutzers oder ob es sich um einen Admin handelt
    menu_options = ["Bitte wählen"]
    if st.session_state.get('logged_in_user') or st.session_state.get('is_admin'):
        menu_options += ["Buchungssystem", "Meine Reservierungen", "MCI-Datenaktualisierung", "Stornierte Reservierungen", "Raum bewerten", "Meine Bewertungen", "Statistik"]
        
    #Aktuelle Zeit erstellen
    # Lasse den Benutzer das Menü auswählen
    selected_option = st.sidebar.selectbox("Menü", menu_options, index=0)

    # Führe Funktionen basierend auf dem ausgewählten Menüpunkt und dem Anmeldestatus aus
    if selected_option == "Buchungssystem":
        display_available_rooms()
    elif selected_option == "Meine Reservierungen":
        display_user_reservations()
    elif selected_option == "MCI-Datenaktualisierung":
        display_mci_daten_aktualisierung()
    elif selected_option == "Stornierte Reservierungen":
        display_storno_entries()
    elif selected_option == "Raum bewerten":  # Neuer Menüpunkt
        display_room_review_form(user_db)  # Aufruf mit der UserDatabase-Instanz
    elif selected_option == "Meine Bewertungen":
        display_user_reviews(user_db)
    elif selected_option =="Statistik":
        display_stats()
    
    #Ist die Zeit für eine Reservierung gekommen?
    #Eine Toast-Nachricht anzeigen
    #st.toast('''You can change text color 
        #:red[Red] :blue[Blue] :green[Green] :orange[Orange]  :violet[Violet]
        #''')

    # Zeige die Admin-Oberfläche, wenn der Benutzer als Admin authentifiziert ist
    if st.session_state.get('is_admin'):
        display_admin_interface()
        display_all_reviews(user_db)  # Die neue Funktion zum Anzeigen aller Bewertungen


if __name__ == "__main__":
    main()
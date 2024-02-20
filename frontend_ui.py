import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
import pandas as pd
from backend import UserDatabase
from refresh_mci import aktualisiere_mci_daten


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

            # Erstelle eine Liste für die verfügbaren Zeiten des ausgewählten Raums
            available_times_list = [room for room in rooms if room['Raumnummer'] == selected_room]

            # Hole alle Reservierungen für den ausgewählten Raum
            reservations = user_db.get_reservations_for_room(selected_room)

            # Berechne die verfügbaren Zeitslots basierend auf den Reservierungen
            available_times = user_db.calculate_availability(available_times_list, reservations)

            # Erstelle ein DataFrame für die berechneten verfügbaren Zeiten
            if available_times:
                available_times_df = pd.DataFrame(available_times)
                available_times_df['Datum'] = pd.to_datetime(available_times_df['Datum'], dayfirst=True).dt.strftime('%A, %d.%m.%Y')
                available_times_df.sort_values(by=['Datum', 'Verfuegbar von'], inplace=True)

                # Zeige die Verfügbarkeit als Tabelle an
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

            # Korrigiere den Aufruf von admin_book_room über die user_db Instanz
            if st.button("Raum buchen"):
                success, message = user_db.admin_book_room(selected_room, formatted_date, formatted_start_time, formatted_end_time)
                if success:
                    # Aktualisiere die verfügbaren Zeiten nach erfolgreicher Buchung
                    updated_reservations = user_db.get_reservations_for_room(selected_room)
                    updated_available_times = user_db.calculate_availability(available_times_list, updated_reservations)

                    # Aktualisiere das DataFrame für die neuen verfügbaren Zeiten
                    if updated_available_times:
                        updated_available_times_df = pd.DataFrame(updated_available_times)
                        updated_available_times_df['Datum'] = pd.to_datetime(updated_available_times_df['Datum'], dayfirst=True).dt.strftime('%A, %d.%m.%Y')
                        updated_available_times_df.sort_values(by=['Datum', 'Verfuegbar von'], inplace=True)

                        # Aktualisiere die vorhandene Tabelle mit den neuen verfügbaren Zeiten
                        table_placeholder.dataframe(updated_available_times_df[['Datum', 'Verfuegbar von', 'Verfuegbar bis']], height=200)
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
        else:
            st.write("Keine stornierten Reservierungen vorhanden.")


# Angenommen, diese Funktion wird aufgerufen, wenn sich der Benutzer erfolgreich anmeldet
def user_logged_in():
    st.session_state['last_login_time'] = datetime.datetime.now()


# Funktion zum Anzeigen von Stornierungsnachrichten, begrenzt auf 15 Sekunden nach der Anmeldung
def display_storno_notifications(user_email):
    # Prüfen, ob 'last_login_time' im session_state existiert und berechnen, wie viel Zeit seitdem vergangen ist
    if 'last_login_time' in st.session_state:
        elapsed_time = datetime.datetime.now() - st.session_state['last_login_time']
        if elapsed_time.total_seconds() > 10:
            return  # Wenn mehr als 15 Sekunden vergangen sind, zeige keine Stornierungsnachrichten

    storno_entries = user_db.storno_table.search(Query().email == user_email)
    for entry in storno_entries:
        message = entry.get('message', 'Keine zusätzliche Nachricht vorhanden.')
        st.warning(f"Stornierte Buchung: Raum {entry['room_number']} am {entry['date']} von {entry['start_time']} bis {entry['end_time']} wurde storniert. {message}")
        # Beachte: Die Nachrichten werden nicht automatisch nach 15 Sekunden entfernt,
        # sie werden nur nicht mehr angezeigt, wenn diese Funktion mehr als 15 Sekunden nach der Anmeldung aufgerufen wird.



ADMIN_SECRET_CODE = "123"  # Das spezielle Kennwort für den Admin-Zugang

def check_for_admin_code(input_code):
    if input_code == ADMIN_SECRET_CODE:
        st.session_state['is_admin'] = True
        st.experimental_rerun()
    else:
        st.session_state['is_admin'] = False

def display_admin_input():
    with st.expander("Admin-Zugang"):
        admin_code = st.text_input("Admin Code eingeben", key="admin_code", type="password")
        if st.button("Admin-Zugang bestätigen"):
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

        # Erstelle eine Spalte für Stornierungsbuttons
        df_reservations['Aktion'] = df_reservations.apply(lambda row: f"Stornieren {row['doc_id']}", axis=1)

        # Zeige das DataFrame an, ohne die 'Aktion'-Spalte, da Streamlit keine Buttons direkt in DataFrames unterstützt
        st.dataframe(df_reservations[['email', 'room_number', 'date', 'start_time', 'end_time']], height=600)

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


def main():
    st.title('Raumbuchungssystem')

    # Initialisiere den Zustand 'is_registered', falls noch nicht geschehen.
    if 'is_registered' not in st.session_state:
        st.session_state['is_registered'] = False

    display_admin_input()  # Überprüft den Admin-Code und setzt den Admin-Status

    display_login_and_registration()  # Zeigt Anmelde- und Registrierungsfelder an, abhängig vom Admin-Status

    user_email = st.session_state.get('logged_in_user')

    display_storno_notifications(user_email)  # Zeige Stornierungsnachrichten an, falls vorhanden

    # Definiere die Menüoptionen abhängig vom Anmeldestatus des Benutzers oder ob es sich um einen Admin handelt
    menu_options = ["Bitte wählen"]
    if st.session_state.get('logged_in_user') or st.session_state.get('is_admin'):
        menu_options += ["Buchungssystem", "Meine Reservierungen", "MCI-Datenaktualisierung", "Stornierte Reservierungen"]

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

    # Zeige die Admin-Oberfläche, wenn der Benutzer als Admin authentifiziert ist
    if st.session_state.get('is_admin'):
        display_admin_interface()

if __name__ == "__main__":
    main()

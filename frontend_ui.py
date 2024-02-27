import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
import pandas as pd
from backend import UserDatabase
from refresh_mci import aktualisiere_mci_daten
import matplotlib.pyplot as plt

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

            # Ermitteln Sie die Email des aktuellen Benutzers oder verwenden 'admin' als Fallback
            user_email = st.session_state.get('logged_in_user', 'admin')

            if st.button("Raum buchen"):
                # Pass user_email to the admin_book_room function
                success, message = user_db.admin_book_room(selected_room, formatted_date, formatted_start_time, formatted_end_time, user_email)
                if success:
                    updated_reservations = user_db.get_reservations_for_room(selected_room)
                    updated_available_times = user_db.calculate_availability(available_times_list, updated_reservations)
                    if updated_available_times:
                        updated_available_times_df = pd.DataFrame(updated_available_times)
                        updated_available_times_df['Datum'] = pd.to_datetime(updated_available_times_df['Datum'], dayfirst=True).dt.strftime('%A, %d.%m.%Y')
                        updated_available_times_df.sort_values(by=['Datum', 'Verfuegbar von'], inplace=True)
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
    
def display_stats():
    st.write("Statistik")
    st.write("Räume und deren Reservierungszeiten:")
    st.write("In den folgenden Bar-Charts werden zum jeweiligen Datum die Räume mit den größten Reservierungszeiten dargestellt")
    user_db.plot_reservierte_räume()
    ##Was soll umgesetzt werden?
    ##1. Was sind die beliebtesten räume?
    #l1 =[]
    #l1:list =  user_db.get_all_reservations() #Liste aller aktuell reservierten Räume(Wer hat reserviert, Wie lang, Welchen Raum)
#
#
    ##Welcher raum ist am belibtesten?
    ##Raum wurde mehrmals gebucht oder der TimeSlot ist am längsten
    ##plot(bar chart) von raumnummer und gebuchten Stunden
#
    ##neue Liste die Nur noch Raumnummer und die gebuchten Stunden enthält
    #dict_1 = {}
    #l2 = []
#
    #for item in l1:
    #    date = item['date']
    #    room_number = item['room_number']
    #    start_time = datetime.strptime(item['start_time'], '%H:%M')
    #    end_time = datetime.strptime(item['end_time'], '%H:%M')
    #    duration_hours = (end_time - start_time).total_seconds() / 3600  # Differenz in Stunden berechnen
#
    #    if room_number in dict_1 and date == dict_1[room_number]['date']:
    #        dict_1[room_number]['total_time'] += duration_hours  # Gesamtzeit für diesen Raum aktualisieren
    #    else:
    #        if room_number in dict_1:
    #            # Raumnummer vorhanden, aber Datum unterscheidet sich, daher neuen Eintrag hinzufügen
    #            l2.append({'date': dict_1[room_number]['date'], 'room_number': room_number, 'total_time': round(dict_1[room_number]['total_time'], 2)})
    #        dict_1[room_number] = {'date': date, 'total_time': duration_hours}  # Raum hinzufügen oder aktualisieren
#
    ## Füge die letzten Einträge aus dict_1 zu l2 hinzu
    #for room_number, entry in dict_1.items():
    #    l2.append({'date': entry['date'], 'room_number': room_number, 'total_time': round(entry['total_time'], 2)})
#
    ##Plot:
    ## Sortiere die Daten nach Datum
    #l2.sort(key=lambda x: datetime.strptime(x['date'], '%A, %d.%m.%Y'))
    #dates = sorted(set(item['date'] for item in l2), key=lambda x: datetime.strptime(x, '%A, %d.%m.%Y'))
    #print(l2)
    ## Daten vorbereiten
    ##dates = set(item['date'] for item in l2)
#
    ## Größe der Figure basierend auf der Anzahl der Subplots anpassen
    #fig_height = max(6, len(dates) * 3)  # Mindesthöhe von 6 Zoll festlegen
#
    ## Erstellen von Subplots für jedes Datum
    #fig, axs = plt.subplots(len(dates), figsize=(10, fig_height))
#
    ## Schleife über jedes Datum und Erstellung des Barcharts für jeden Raum
    #for i, date in enumerate(dates):
    #    # Filtern der Einträge für das aktuelle Datum
    #    filtered_entries = [item for item in l2 if item['date'] == date]
    #    filtered_room_numbers = [entry['room_number'] for entry in filtered_entries]
    #    filtered_total_times = [entry['total_time'] for entry in filtered_entries]
#
    #    # Erstellen von Barcharts für die Gesamtzeit jedes Raums an diesem Datum
    #    ax = axs[i] if len(dates) > 1 else axs
    #    bars = ax.bar(filtered_room_numbers, filtered_total_times)
#
    #    # Achsenbeschriftungen und Titel hinzufügen
    #    ax.set_xlabel('Raumnummer')
    #    ax.set_ylabel('Gesamtzeit (Stunden)')
    #    ax.set_title(f'Folgende Räume wurden am {date} Reserviert')
#
    #    # Raumnummern als x-Achsenbeschriftungen festlegen
    #    ax.set_xticks(range(len(filtered_room_numbers)))
    #    ax.set_xticklabels(filtered_room_numbers, rotation=45)  # Rotation der Beschriftungen für bessere Lesbarkeit
#
    #    # Beschriftungen für jeden Balken hinzufügen
    #    for bar, time in zip(bars, filtered_total_times):
    #        ax.text(bar.get_x() + bar.get_width() / 2, time / 2, f'{time}', ha='center', va='center')
#
    ## Layout anpassen und Plot anzeigen
    #plt.tight_layout()
    #st.pyplot(fig)
    # Layout anpassen und Plot anzeigen
def main():
    st.title('Raumbuchungssystem')

    # Initialisiere den Zustand 'is_registered', falls noch nicht geschehen.
    if 'is_registered' not in st.session_state:
        st.session_state['is_registered'] = False

    display_admin_input()  # Überprüft den Admin-Code und setzt den Admin-Status

    display_login_and_registration()  # Zeigt Anmelde- und Registrierungsfelder an, abhängig vom Admin-Status

    user_email = st.session_state.get('logged_in_user')

    display_storno_notifications(user_db, user_email)   # Zeige Stornierungsnachrichten an, falls vorhanden

    # Definiere die Menüoptionen abhängig vom Anmeldestatus des Benutzers oder ob es sich um einen Admin handelt
    menu_options = ["Bitte wählen"]
    if st.session_state.get('logged_in_user') or st.session_state.get('is_admin'):
        menu_options += ["Buchungssystem", "Meine Reservierungen", "MCI-Datenaktualisierung", "Stornierte Reservierungen", "Statistik"]

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
    elif selected_option =="Statistik":
        display_stats()
    # Zeige die Admin-Oberfläche, wenn der Benutzer als Admin authentifiziert ist
    if st.session_state.get('is_admin'):
        display_admin_interface()

if __name__ == "__main__":
    main()
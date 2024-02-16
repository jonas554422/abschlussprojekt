import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
from backend import UserDatabase
from refresh_mci import aktualisiere_mci_daten

# Stellen Sie sicher, dass die Locale korrekt für die Datumsformatierung gesetzt ist
# Achtung: Diese Zeile könnte auf nicht-englischen Systemen oder in bestimmten Umgebungen angepasst werden müssen
locale.setlocale(locale.LC_TIME, 'en_US.utf8' or 'English_United States.1252')

# Pfad zur Datenbank für verfügbare Räume
DB_PATH = 'verfuegbare_raeume_db.json'

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

            # Anzeigen der verfügbaren Daten für den ausgewählten Raum
            available_times = [room for room in rooms if room['Raumnummer'] == selected_room]
            if available_times:
                for room in available_times:
                    st.write(f"Raum {room['Raumnummer']} ist verfügbar am {room['Datum']} von {room['Verfuegbar von']} bis {room['Verfuegbar bis']}.")

            date = st.date_input("Datum wählen", min_value=datetime.today())
            start_time = st.time_input("Startzeit wählen", value=datetime.now())
            end_time = st.time_input("Endzeit wählen", value=(datetime.now() + timedelta(hours=1)))

            if start_time >= end_time:
                st.error("Die Startzeit muss vor der Endzeit liegen.")
            else:
                formatted_date = date.strftime('%A, %d.%m.%Y')
                formatted_start_time = start_time.strftime('%H:%M')
                formatted_end_time = end_time.strftime('%H:%M')

                if st.button("Raum buchen"):
                    success, message = user_db.add_reservation(st.session_state['logged_in_user'], selected_room, formatted_date, formatted_start_time, formatted_end_time)
                    if success:
                        st.success("Reservierung erfolgreich hinzugefügt.")
                    else:
                        st.error(message)
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



def main():
    st.title('Raumbuchungssystem')
    display_login()
    display_registration()

    # Füge den neuen Menüpunkt hinzu
    menu_options = ["Bitte wählen"]
    if st.session_state.get('logged_in_user'):
        menu_options += ["Buchungssystem", "Meine Reservierungen", "MCI-Datenaktualisierung", "Stornierte Reservierungen"]

    selected_option = st.sidebar.selectbox("Menü", menu_options)

    if selected_option == "Buchungssystem":
        display_available_rooms()
    elif selected_option == "Meine Reservierungen":
        display_user_reservations()
    elif selected_option == "MCI-Datenaktualisierung":
        display_mci_daten_aktualisierung()
    elif selected_option == "Stornierte Reservierungen":
        display_storno_entries()

if __name__ == "__main__":
    main()
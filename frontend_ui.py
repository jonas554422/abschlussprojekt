import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
from backend import UserDatabase

# Stellen Sie sicher, dass die Locale korrekt für die Datumsformatierung gesetzt ist
# Achtung: Diese Zeile könnte auf nicht-englischen Systemen oder in bestimmten Umgebungen angepasst werden müssen
locale.setlocale(locale.LC_TIME, 'en_US.utf8' or 'English_United States.1252')

# Pfad zur Datenbank für verfügbare Räume
DB_PATH = 'verfuegbare_raeume_db.json'

# Initialisierung des Session State für den Anmeldestatus, falls noch nicht vorhanden
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

# UserDatabase-Instanz erstellen
user_db = UserDatabase('reservation.json', 'verfuegbare_raeume_db.json')

def display_login():
    """Zeigt das Login-System an."""
    with st.sidebar:
        login_email = st.text_input("Email einloggen", key="login_email")
        if st.button("Einloggen", key="login_button"):
            if user_db.authenticate(login_email):
                st.session_state['logged_in_user'] = login_email
                st.sidebar.success('Anmeldung erfolgreich!')
            else:
                st.sidebar.error('Ungültige E-Mail-Adresse oder nicht registriert.')

def display_registration():
    """Zeigt das Registrierungs-System an."""
    with st.sidebar:
        reg_email = st.text_input("Email registrieren", key="reg_email")
        if st.button("Registrieren", key="register_button"):
            registration_result = user_db.register_user(reg_email)
            if registration_result is True:
                st.sidebar.success('Registrierung erfolgreich!')
            else:
                st.sidebar.error(registration_result)

def display_available_rooms():
    db = TinyDB(DB_PATH)
    rooms = db.all()
    if rooms:
        room_numbers = [room['Raumnummer'] for room in rooms]
        selected_room = st.selectbox('Wählen Sie einen Raum', room_numbers)

        # Anzeigen der verfügbaren Daten für den ausgewählten Raum
        available_times = [room for room in rooms if room['Raumnummer'] == selected_room]
        if available_times:
            for room in available_times:
                st.write(f"Raum {room['Raumnummer']} ist verfügbar am {room['Datum']} von {room['Verfuegbar von']} bis {room['Verfuegbar bis']}.")

            date = st.date_input("Datum wählen", min_value=datetime.today())
            start_time = st.time_input("Startzeit wählen")
            end_time = st.time_input("Endzeit wählen")

            formatted_date = date.strftime('%A, %d.%m.%Y')
            formatted_start_time = start_time.strftime('%H:%M')
            formatted_end_time = end_time.strftime('%H:%M')

            if st.button("Raum buchen"):
                if st.session_state.logged_in_user:
                    # Verfügbarkeit prüfen und bei Erfolg Reservierung hinzufügen
                    if user_db.is_room_available(selected_room, formatted_date, formatted_start_time, formatted_end_time):
                        if user_db.add_reservation(st.session_state.logged_in_user, selected_room, formatted_date, formatted_start_time, formatted_end_time):
                            st.success(f"Raum {selected_room} erfolgreich gebucht für {formatted_date} von {formatted_start_time} bis {formatted_end_time}.")
                        else:
                            st.error("Es gab ein Problem bei der Buchung des Raums.")
                    else:
                        st.error("Der Raum ist zu diesem Zeitpunkt nicht verfügbar.")
                else:
                    st.error("Sie müssen eingeloggt sein, um einen Raum zu buchen.")
        else:
            st.write("Für den ausgewählten Raum sind keine Verfügbarkeitsdaten vorhanden.")
    else:
        st.write("Keine verfügbaren Räume gefunden.")




def main():
    st.title('Raumbuchungssystem')

    # Anzeigen von Login- und Registrierungsoptionen im Seitenmenü
    display_login()
    display_registration()

    # Anzeigen der Buchungsoption nur, wenn der Benutzer eingeloggt ist
    if st.session_state['logged_in_user']:
        display_available_rooms()

if __name__ == "__main__":
    main()

import streamlit as st
from backend import lade_verfuegbare_raeume, speichere_registrierung, ist_registriert
import datetime
import re

class RaumBuchungApp:
    MCI_EMAIL_REGEX = r'^[a-zA-Z]{2}\d{4}@mci4me\.at$'

    def __init__(self):
        self.init_session_state()
        verfuegbare_raeume = lade_verfuegbare_raeume()
        self.gesamtraeume = sorted(set(raum['Raumnummer'] for raum in verfuegbare_raeume))

    @staticmethod
    def init_session_state():
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        if 'view' not in st.session_state:
            st.session_state['view'] = 'Verfügbare Räume'
        if 'auth_message' not in st.session_state:
            st.session_state['auth_message'] = ''

    @staticmethod
    def check_mci_email(email):
        return re.match(RaumBuchungApp.MCI_EMAIL_REGEX, email) is not None

    def authenticate(self, email):
        if self.check_mci_email(email) and ist_registriert(email):
            st.session_state['authenticated'] = True
            st.session_state['auth_message'] = 'Anmeldung erfolgreich!'
            st.session_state['view'] = 'Verfügbare Räume'
        elif not ist_registriert(email):
            st.session_state['authenticated'] = False
            st.sidebar.error('E-Mail-Adresse nicht registriert.')
        else:
            st.session_state['authenticated'] = False
            st.sidebar.error('Ungültige MCI-E-Mail-Adresse.')

    def login_form(self):
        with st.sidebar:
            email = st.text_input("MCI-E-Mail-Adresse")
            if st.button("Anmelden"):
                self.authenticate(email)

    def registrierungs_formular(self):
        name = st.text_input("Name")
        email = st.text_input("E-Mail-Adresse")
        if st.button("Registrieren"):
            if self.check_mci_email(email):
                erfolg = speichere_registrierung(name, email)
                if erfolg:
                    st.success(f"{name} wurde erfolgreich registriert!")
                else:
                    st.error("Diese E-Mail-Adresse ist bereits vergeben.")
            else:
                st.error("Ungültige MCI-E-Mail-Adresse.")

    def suche_nach_raum(self):
        ausgewaehlter_raum = st.selectbox("Wählen Sie einen Raum:", self.gesamtraeume)
        self.raeume_anzeigen(ausgewaehlter_raum)

    def raeume_anzeigen(self, ausgewaehlter_raum):
        verfuegbare_raeume = lade_verfuegbare_raeume()
        gefilterte_raeume = [raum for raum in verfuegbare_raeume if raum['Raumnummer'] == ausgewaehlter_raum]
        
        for raum in gefilterte_raeume:
            st.write(f"{raum['Datum']}: Verfügbar von {raum['Verfuegbar von']} bis {raum['Verfuegbar bis']}.")

    def abmelden(self):
        if st.session_state['authenticated']:
            if st.session_state['auth_message']:
                if st.sidebar.button("Abmelden"):
                    st.session_state['authenticated'] = False
                    st.session_state['auth_message'] = ''
                    st.session_state['view'] = 'Verfügbare Räume'

    def handle_view(self):
        option = "Verfügbare Räume"

        if not st.session_state['authenticated']:
            option = st.sidebar.radio("Navigation", ["Anmelden", "Registrieren"])
        elif st.session_state['view'] == 'Verfügbare Räume':
            option = st.sidebar.radio("Navigation", ["Suche nach Raum", "Abmelden"])

        if option == "Anmelden":
            self.login_form()
            if st.session_state['auth_message']:
                if st.button("Hier klicken, um zum Buchungssystem zu gelangen"):
                    st.session_state['auth_message'] = ''
        elif option == "Registrieren":
            self.registrierungs_formular()
        elif option == "Suche nach Raum":
            self.suche_nach_raum()
            self.abmelden()
        elif option == "Abmelden":
            self.abmelden()

    def start(self):
        self.handle_view()

if __name__ == '__main__':
    app = RaumBuchungApp()
    app.start()

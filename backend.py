import re
from tinydb import TinyDB, Query

class UserDatabase:
    def __init__(self, db_path='reservation.json', available_rooms_path='verfuegbare_raeume_db.json'):
        self.db = TinyDB(db_path)
        self.reservation_table = self.db.table('reservations')
        self.available_rooms_db = TinyDB(available_rooms_path)
        self.MCI_EMAIL_REGEX = r'^[a-zA-Z]{2}\d{4}@mci4me\.at$'

    def check_mci_email(self, email):
        """Überprüft, ob die E-Mail-Adresse dem MCI-Format entspricht."""
        return re.match(self.MCI_EMAIL_REGEX, email) is not None

    def register_user(self, email):
        """Registriert einen Benutzer in der Datenbank, wenn er noch nicht existiert."""
        if self.db.contains(Query().email == email):
            return "Benutzer existiert bereits."
        elif not self.check_mci_email(email):
            return "Ungültige E-Mail-Adresse."
        else:
            self.db.insert({'email': email})
            return True

    def authenticate(self, email):
        """Versucht, den Benutzer zu authentifizieren, basierend auf der E-Mail-Adresse."""
        return self.db.contains(Query().email == email)
    
    def is_room_available(self, room_number, date, start_time, end_time):
        """Überprüft, ob der Raum zum gewünschten Zeitpunkt verfügbar ist."""
        reservations = self.reservation_table.search((Query().room_number == room_number) & (Query().date == date))
        for reservation in reservations:
            if (start_time < reservation['end_time'] and end_time > reservation['start_time']):
                return False  # Zeitkonflikt gefunden
    
        available_rooms = self.available_rooms_db.search(Query().room_number == room_number)
        for available in available_rooms:
            if date == available['Datum'] and start_time >= available['Verfuegbar von'] and end_time <= available['Verfuegbar bis']:
                return True  # Der Raum ist verfügbar

        return False  # Standardmäßig nicht verfügbar, wenn keine Übereinstimmung gefunden wurde


    

    def add_reservation(self, email, room_number, date, start_time, end_time):
        """Fügt eine neue Reservierung hinzu, wenn der Raum verfügbar ist."""
        if self.is_room_available(room_number, date, start_time, end_time):
            reservation = {
                'email': email,
                'room_number': room_number,
                'date': date,
                'start_time': start_time,
                'end_time': end_time
            }
            self.reservations_table.insert(reservation)
            return True
        else:
            return False

def main():
    db = UserDatabase()  # Erstellen Sie eine Instanz der UserDatabase-Klasse
    email = "test@example.com"  # Falsche E-Mail-Adresse zum Testen

    # Beispiel für die Verwendung des Backend-Codes
    registration_result = db.register_user(email)
    if registration_result is True:
        print("Benutzer erfolgreich registriert.")
    else:
        print(f"Fehler bei der Registrierung: {registration_result}")

    if db.authenticate(email):
        print("Benutzer erfolgreich authentifiziert.")
        
        # Hier fügen Sie die Reservierung hinzu
        room_number = "Raum 101"
        date = "2024-02-15"
        start_time = "08:00"
        end_time = "10:00"
        
        # Rufen Sie die add_reservation-Methode von der db-Instanz ab, nicht von db.reservations_table
        add_reservation_result = db.add_reservation(email, room_number, date, start_time, end_time)
        if add_reservation_result:
            print(f"Reservierung für Raum {room_number} erfolgreich hinzugefügt.")
        else:
            print("Fehler beim Hinzufügen der Reservierung.")
            
    else:
        print("Benutzer nicht gefunden oder nicht authentifiziert.")

if __name__ == "__main__":
    main()

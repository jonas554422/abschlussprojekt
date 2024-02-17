import re
from tinydb import TinyDB, Query
from datetime import datetime

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
        print(f"Überprüfung für Raum {room_number} am {date}, von {start_time} bis {end_time}")
        
        # Konvertiere die Eingabe in datetime Objekte für genaue Vergleiche
        date_format = "%A, %d.%m.%Y"
        time_format = "%H:%M"
        
        # Konvertiere Datum und Zeit in das erforderliche Format
        date_obj = datetime.strptime(date, date_format)
        start_time_obj = datetime.strptime(start_time, time_format).time()
        end_time_obj = datetime.strptime(end_time, time_format).time()
        
        # Hole alle Verfügbarkeiten für den gegebenen Raum
        availabilities = self.available_rooms_db.search(Query().Raumnummer == room_number)
        print(f"Gefundene Verfügbarkeiten für {room_number}: {availabilities}")
        
        # Überprüfe, ob das Datum und die Zeit innerhalb der verfügbaren Zeiten liegen
        for available in availabilities:
            avail_date_obj = datetime.strptime(available['Datum'], date_format)
            avail_start_time_obj = datetime.strptime(available['Verfuegbar von'], time_format).time()
            avail_end_time_obj = datetime.strptime(available['Verfuegbar bis'], time_format).time()

            # Vergleiche Datum und Zeit
            if date_obj == avail_date_obj and start_time_obj >= avail_start_time_obj and end_time_obj <= avail_end_time_obj:
                print("Raum ist laut Verfügbarkeitsdatenbank verfügbar.")
                return True
        
        print("Raum ist standardmäßig nicht verfügbar.")
        return False


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
            self.reservation_table.insert(reservation)
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
    db = UserDatabase()  # Erstelle eine Instanz deiner Klasse
    # Beispielhafter Aufruf der is_room_available Methode
    verfügbar = db.is_room_available("4B-001", "Thursday, 15.02.2024", "09:00", "11:00")
    print(f"Raum verfügbar: {verfügbar}")
    


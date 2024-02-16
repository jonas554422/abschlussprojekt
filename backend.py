import re
from tinydb import TinyDB, Query
from datetime import datetime
from refresh_mci import aktualisiere_mci_daten

class UserDatabase:
    def __init__(self, db_path='reservation.json', available_rooms_path='verfuegbare_raeume_db.json'):
        self.db = TinyDB(db_path)
        self.reservation_table = self.db.table('reservations')
        self.available_rooms_db = TinyDB(available_rooms_path)
        self.storno_table = self.db.table('storno')  # Füge das storno_table Attribut hinzu
        self.MCI_EMAIL_REGEX = r'^[a-zA-Z]{2}\d{4}@mci4me\.at$'

    def check_mci_email(self, email):
        return re.match(self.MCI_EMAIL_REGEX, email) is not None

    def register_user(self, email):
        if self.db.contains(Query().email == email):
            return "Benutzer existiert bereits."
        elif not self.check_mci_email(email):
            return "Ungültige E-Mail-Adresse."
        else:
            self.db.insert({'email': email})
            return True

    def authenticate(self, email):
        return self.db.contains(Query().email == email)

    def is_room_available(self, room_number, date, start_time, end_time):
        date_format = "%A, %d.%m.%Y"
        time_format = "%H:%M"
        date_obj = datetime.strptime(date, date_format)
        start_time_obj = datetime.strptime(start_time, time_format).time()
        end_time_obj = datetime.strptime(end_time, time_format).time()
        availabilities = self.available_rooms_db.search(Query().Raumnummer == room_number)

        for available in availabilities:
            avail_date_obj = datetime.strptime(available['Datum'], date_format)
            avail_start_time_obj = datetime.strptime(available['Verfuegbar von'], time_format).time()
            avail_end_time_obj = datetime.strptime(available['Verfuegbar bis'], time_format).time()

            if date_obj == avail_date_obj and start_time_obj >= avail_start_time_obj and end_time_obj <= avail_end_time_obj:
                return True
        return False

    def add_reservation(self, email, room_number, date, start_time, end_time):
        if not self.is_room_available(room_number, date, start_time, end_time):
            return False, "Raum ist zu diesem Zeitpunkt nicht verfügbar."
        # Überprüfe, ob die Reservierung bereits existiert
        existing_reservations = self.reservation_table.search((Query().room_number == room_number) & 
                                                           (Query().date == date) & 
                                                           ((Query().start_time < end_time) & (Query().end_time > start_time)))
        if existing_reservations:
            return False, "Raum ist zu diesem Zeitpunkt bereits reserviert."

        

        self.reservation_table.insert({
            'email': email,
            'room_number': room_number,
            'date': date,
            'start_time': start_time,
            'end_time': end_time
        })
        return True, "Reservierung erfolgreich hinzugefügt."

    def get_user_reservations(self, email):
        return self.reservation_table.search(Query().email == email)
    
    def cancel_reservation(self, reservation_id):
        # Finde die Reservierung anhand ihrer ID
        reservation = self.reservation_table.get(doc_id=reservation_id)
        if reservation:
            # Erstelle einen Storno-Eintrag vor dem Löschen
            self.storno_table.insert({
                'email': reservation['email'],
                'room_number': reservation['room_number'],
                'date': reservation['date'],
                'start_time': reservation['start_time'],
                'end_time': reservation['end_time'],
                'storno_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            # Lösche die Reservierung
            self.reservation_table.remove(doc_ids=[reservation_id])


    def verify_reservations(self, email):
        user_reservations = self.get_user_reservations(email)
        for reservation in user_reservations:
            if not self.is_reservation_still_valid(reservation):
                self.cancel_reservation(reservation.doc_id)

    def is_reservation_still_valid(self, reservation):
        available_rooms = self.available_rooms_db.search(Query().Raumnummer == reservation['room_number'])
        for available_room in available_rooms:
            if available_room['Datum'] == reservation['date']:
                if available_room['Verfuegbar von'] <= reservation['start_time'] and available_room['Verfuegbar bis'] >= reservation['end_time']:
                    return True
        return False

if __name__ == "__main__":
    db = UserDatabase()
    #  Test
    email = "mj5804@mci4me.at"
    db.verify_reservations(email)

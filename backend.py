import re
from tinydb import TinyDB, Query
from datetime import datetime
from refresh_mci import aktualisiere_mci_daten
import locale


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
    
    def get_reservations_for_room(self, room_number):
        """Gibt alle Reservierungen für einen bestimmten Raum zurück."""
        reservations = self.reservation_table.search(Query().room_number == room_number)
        return reservations

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
    
    def get_all_reservations(self):
        """Holt alle Reservierungen aus der Datenbank und fügt die doc_id hinzu."""
        reservations = self.reservation_table.all()
        # Aktualisiere jede Reservierung, um die doc_id einzuschließen
        for reservation in reservations:
            reservation['doc_id'] = reservation.doc_id  # Zugriff auf die interne doc_id von TinyDB
        return reservations  # Gib die aktualisierten Reservierungen zurück
    

    def admin_book_room(self, room_number, date, start_time, end_time, user_email):
        existing_reservations = self.get_reservations_for_room(room_number)
    
        # Überprüfen, ob bereits eine Reservierung für den angegebenen Zeitpunkt vorliegt
        for reservation in existing_reservations:
            if reservation['date'] == date and reservation['start_time'] == start_time:
                # Storniere die vorhandene Buchung, kennzeichne die Stornierung als vom Administrator
                self.cancel_reservation(reservation.doc_id, cancelled_by_admin=True)
                success, message = self.add_reservation(user_email, room_number, date, start_time, end_time)  # Verwende user_email statt 'admin'
                if success:
                    return True, "Die Buchung wurde erfolgreich aktualisiert."
                else:
                    return False, f"Fehler beim Aktualisieren der Buchung: {message}"

        # Falls keine vorhandene Buchung gefunden wurde, füge einfach eine neue Buchung hinzu
        success, message = self.add_reservation(user_email, room_number, date, start_time, end_time)  # Verwende user_email statt 'admin'
        if success:
            return True, "Buchung erfolgreich hinzugefügt."
        else:
            return False, f"Fehler beim Hinzufügen der Buchung: {message}"
        
        
    def set_supported_locale():
        locales_to_try = ['en_US.UTF-8', 'en_US.utf8', 'English_United States.1252', 'en_US']
        for loc in locales_to_try:
            try:
                locale.setlocale(locale.LC_TIME, loc)
                print(f"Locale erfolgreich auf {loc} gesetzt.")
                return  # Erfolg, breche die Schleife ab
            except locale.Error:
                continue  # Bei Misserfolg, versuche die nächste Locale
        print("Warnung: Keine der Locales konnte gesetzt werden.")

    set_supported_locale()

    def get_user_reservations(self, email):
        return self.reservation_table.search(Query().email == email)
    
    def check_existing_reservation(self, room_number, date, start_time):
        reservations = self.get_reservations_for_room(room_number)
        for reservation in reservations:
            if (reservation['date'] == date and
                reservation['start_time'] <= start_time <= reservation['end_time']):
                return True
        return False
    

    def notify_user_of_cancellation(self, email, room_number, date):
        # Hier können Sie den Code einfügen, der die Benachrichtigung an den Benutzer sendet,
        # z. B. per E-Mail, über ein internes Nachrichtensystem usw.
        # In diesem Beispiel drucken wir einfach eine Nachricht aus.
        print(f"Benachrichtigung: Ihre Reservierung für Raum {room_number} am {date} wurde storniert.")

    def cancel_reservation(self, reservation_id, cancelled_by_admin=False):
        # Finde die Reservierung anhand ihrer ID
        reservation = self.reservation_table.get(doc_id=reservation_id)
        if reservation:
            # Benutzer über die Stornierung benachrichtigen
            print("Stornierung erfolgt, Benutzer wird benachrichtigt...")
            self.notify_user_of_cancellation(reservation['email'], reservation['room_number'], reservation['date'])

            cancellation_message = "Ihre Buchung wurde storniert."
            if cancelled_by_admin:
                cancellation_message += " (Stornierung durch Administrator)"

            self.storno_table.insert({
                'email': reservation['email'],
                'room_number': reservation['room_number'],
                'date': reservation['date'],
                'start_time': reservation['start_time'],
                'end_time': reservation['end_time'],
                'storno_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'message': 'Ihre Buchung wurde storniert.'  # Nachricht über die Stornierung
            })
            # Lösche die Reservierung
            self.reservation_table.remove(doc_ids=[reservation_id])

    def calculate_availability(self, available_times, reservations):
        new_availability = []

        for slot in available_times:
            slot_start = datetime.strptime(f"{slot['Datum']} {slot['Verfuegbar von']}", '%A, %d.%m.%Y %H:%M')
            slot_end = datetime.strptime(f"{slot['Datum']} {slot['Verfuegbar bis']}", '%A, %d.%m.%Y %H:%M')

            daily_reservations = [r for r in reservations if r['date'] == slot['Datum']]
            daily_reservations.sort(key=lambda r: r['start_time'])

            time_points = [slot_start]
            for reservation in daily_reservations:
                res_start = datetime.strptime(f"{reservation['date']} {reservation['start_time']}", '%A, %d.%m.%Y %H:%M')
                res_end = datetime.strptime(f"{reservation['date']} {reservation['end_time']}", '%A, %d.%m.%Y %H:%M')

                if res_start >= slot_start and res_end <= slot_end:
                    time_points.append(res_start)
                    time_points.append(res_end)

            time_points.append(slot_end)

            for i in range(0, len(time_points), 2):
                if i+1 < len(time_points):
                    start = time_points[i]
                    end = time_points[i+1]
                    if start != end:
                        new_availability.append({
                            'Datum': start.strftime('%A, %d.%m.%Y'),
                            'Verfuegbar von': start.strftime('%H:%M'),
                            'Verfuegbar bis': end.strftime('%H:%M')
                        })

        return new_availability



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
    # Test
    email = "mj5804@mci4me.at"
    db.verify_reservations(email)

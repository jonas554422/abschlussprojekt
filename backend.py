import re
from tinydb import TinyDB, Query
from datetime import datetime
from refresh_mci import aktualisiere_mci_daten
import locale
import matplotlib.pyplot as plt
import streamlit as st


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
                # Storniere die vorhandene Buchung
                self.cancel_reservation(reservation.doc_id)
                # Füge die neue Buchung hinzu
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

    def cancel_reservation(self, reservation_id):
        # Finde die Reservierung anhand ihrer ID
        reservation = self.reservation_table.get(doc_id=reservation_id)
        if reservation:
            # Benutzer über die Stornierung benachrichtigen
            self.notify_user_of_cancellation(reservation['email'], reservation['room_number'], reservation['date'])
            # Erstelle einen Storno-Eintrag vor dem Löschen
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
    
    def convert_to_decimal_time(time_str):
        hours, minutes = map(int, time_str.split(':'))
        decimal_minutes = minutes / 60
        decimal_time = hours + decimal_minutes
        return decimal_time
    
    def plot_reservierte_räume(self):
        l1 =[]
        l1:list =  self.get_all_reservations() #Liste aller aktuell reservierten Räume(Wer hat reserviert, Wie lang, Welchen Raum)


        #Welcher raum ist am belibtesten?
        #Raum wurde mehrmals gebucht oder der TimeSlot ist am längsten
        #plot(bar chart) von raumnummer und gebuchten Stunden

        #neue Liste die Nur noch Raumnummer und die gebuchten Stunden enthält
        dict_1 = {}
        l2 = []

        for item in l1:
            date = item['date']
            room_number = item['room_number']
            start_time = datetime.strptime(item['start_time'], '%H:%M')
            end_time = datetime.strptime(item['end_time'], '%H:%M')
            duration_hours = (end_time - start_time).total_seconds() / 3600  # Differenz in Stunden berechnen

            if room_number in dict_1 and date == dict_1[room_number]['date']:
                dict_1[room_number]['total_time'] += duration_hours  # Gesamtzeit für diesen Raum aktualisieren
            else:
                if room_number in dict_1:
                    # Raumnummer vorhanden, aber Datum unterscheidet sich, daher neuen Eintrag hinzufügen
                    l2.append({'date': dict_1[room_number]['date'], 'room_number': room_number, 'total_time': round(dict_1[room_number]['total_time'], 2)})
                dict_1[room_number] = {'date': date, 'total_time': duration_hours}  # Raum hinzufügen oder aktualisieren

        # Füge die letzten Einträge aus dict_1 zu l2 hinzu
        for room_number, entry in dict_1.items():
            l2.append({'date': entry['date'], 'room_number': room_number, 'total_time': round(entry['total_time'], 2)})

        #Plot:
        # Nur maxmimal 10 plots Pro Subplot, sortiert nach den Stunden!!!
        # Noch zu implementieren!!!
        # Sortiere die Daten nach Datum
        # Daten vorbereiten
        # Daten vorbereiten
        dates = sorted(set(item['date'] for item in l2), key=lambda x: datetime.strptime(x, '%A, %d.%m.%Y'))

        # Farbpalette basierend auf der Anzahl der einzigartigen Daten generieren
        num_unique_dates = len(dates)
        color_palette = plt.cm.get_cmap('tab10', num_unique_dates)

        # Größe für jeden Subplot definieren
        subplot_width = 10  # Breite jedes Subplots
        subplot_height = 4  # Höhe jedes Subplots

        # Gesamtanzahl der Subplots berechnen
        num_subplots = len(dates)

        # Größe der gesamten Figur basierend auf der Anzahl der Subplots anpassen
        fig_width = subplot_width
        fig_height = num_subplots * subplot_height

        # Figure erstellen
        if num_subplots > 1:
            fig, axs = plt.subplots(num_subplots, figsize=(fig_width, fig_height))
        else:
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Schleife über jedes Datum und Erstellung des Barcharts für jeden Raum
        for i, date in enumerate(dates):
            # Filtern der Einträge für das aktuelle Datum
            filtered_entries = [item for item in l2 if item['date'] == date]
            filtered_entries.sort(key=lambda x: x['total_time'], reverse=True)  # Sortieren nach höchsten Stunden
            filtered_entries = filtered_entries[:5]  # Begrenzung auf die 5 Einträge mit den höchsten Zeiten
            filtered_room_numbers = [entry['room_number'] for entry in filtered_entries] 
            filtered_total_times = [entry['total_time'] for entry in filtered_entries]

            # Farben für die Balken aus der Farbpalette auswählen
            color = color_palette(i)

            # Erstellen von Barcharts für die Gesamtzeit jedes Raums an diesem Datum
            if num_subplots > 1:
                ax = axs[i]
            else:
                ax = axs
            bars = ax.bar(filtered_room_numbers, filtered_total_times, color=color)

            # Achsenbeschriftungen und Titel hinzufügen
            ax.set_xlabel('Raumnummer')
            ax.set_ylabel('Reservierte Zeit/h')
            ax.set_title(f'Folgende Räume wurden am {date} Reserviert')

            # Raumnummern als x-Achsenbeschriftungen festlegen
            ax.set_xticks(range(len(filtered_room_numbers)))
            ax.set_xticklabels(filtered_room_numbers, rotation=45)  # Rotation der Beschriftungen für bessere Lesbarkeit

            # Beschriftungen für jeden Balken hinzufügen
            for bar, time in zip(bars, filtered_total_times):
                ax.text(bar.get_x() + bar.get_width() / 2, time / 2, f'{time}h', ha='center', va='center')

        # Layout anpassen und Plot anzeigen
        plt.tight_layout()
        st.pyplot(fig)


if __name__ == "__main__":
    db = UserDatabase()
    #  Test
    email = "mj5804@mci4me.at"
    db.verify_reservations(email)
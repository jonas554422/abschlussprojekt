import re
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
from refresh_mci import aktualisiere_mci_daten
import locale
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd


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
        date_format = "%A, %d.%m.%Y"  # Aktualisiert, um den Wochentag zu berücksichtigen
        time_format = "%H:%M"
        try:
            date_obj = datetime.strptime(date, date_format).date()
            start_time_obj = datetime.strptime(start_time, time_format).time()
            end_time_obj = datetime.strptime(end_time, time_format).time()
        except ValueError as e:
            print(f"Fehler beim Parsen des Datums oder der Uhrzeit: {e}")
            return False  # oder entsprechende Fehlerbehandlung

        availabilities = self.available_rooms_db.search(Query().Raumnummer == room_number)

        for available in availabilities:
            try:
                avail_date_obj = datetime.strptime(available['Datum'], date_format).date()
                avail_start_time_obj = datetime.strptime(available['Verfuegbar von'], time_format).time()
                avail_end_time_obj = datetime.strptime(available['Verfuegbar bis'], time_format).time()
            except ValueError as e:
                print(f"Fehler beim Parsen des Datums oder der Uhrzeit in Verfügbarkeiten: {e}")
                continue  # oder entsprechende Fehlerbehandlung

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
    





    def get_unique_room_numbers(self):
        rooms = self.available_rooms_db.all()
        unique_room_numbers = list(set(room['Raumnummer'] for room in rooms))
        return unique_room_numbers
    
    def add_room_review(self, room_number, email, rating, feedback, photo_path=None):
        review = {
            'room_number': room_number,
            'email': email,
            'rating': rating,
            'feedback': feedback,
            'photo_path': photo_path,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.table('reviews').insert(review)

    def edit_room_review(self, review_id, new_rating=None, new_feedback=None, new_photo_path=None):
        updates = {}
        if new_rating is not None:
            updates['rating'] = new_rating
        if new_feedback is not None:
            updates['feedback'] = new_feedback
        if new_photo_path is not None:
            updates['photo_path'] = new_photo_path
    
        self.db.table('reviews').update(updates, doc_ids=[review_id])


    def get_room_reviews(self, room_number):
        reviews = self.db.table('reviews').search(Query().room_number == room_number)
        # Füge die doc_id zu jedem Bewertungsobjekt hinzu
        for review in reviews:
            review['doc_id'] = review.doc_id  # TinyDB fügt jedem Dokument eine doc_id-Eigenschaft hinzu
        return reviews

    def get_review_by_id(self, review_id):
        # Suchen der Bewertung anhand ihrer doc_id
        review = self.db.table('reviews').get(doc_id=review_id)
        if review:
            # Füge die doc_id zum Review-Objekt hinzu, falls nicht schon vorhanden
            review['doc_id'] = review_id
            return review
        else:
            return None
        
    def get_all_reviews(self):
        reviews = self.db.table('reviews').all()
        for review in reviews:
            review['doc_id'] = review.doc_id
        return reviews
    
    def get_user_reviews(self, user_email):
        # Suchen Sie alle Bewertungen für den angegebenen Benutzer
        reviews = self.db.table('reviews').search(Query().email == user_email)
        for review in reviews:
            review['doc_id'] = review.doc_id
        return reviews


    def report_damage(self, room_number, email, description, photo_path):
        # Implementierung des Schadensberichts
        damage_report = {
            'room_number': room_number,
            'reported_by': email,
            'description': description,
            'photo_path': photo_path,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.table('damages').insert(damage_report)
        
    def cancel_room_review(self, review_id):
        self.db.table('reviews').remove(doc_ids=[review_id])

        
        
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
    
    def plot_reservierte_räume(self):
        #Alle reservierungen aus der Datenbank Holen
        l1 = self.get_all_reservations()
        #Leeres Dict und Leere liste erstellen:
        dict_1 = {}             #Wir benötigt um die totale Buchungszeit eines Raumes zu bestimmen 
        l2 = []                 #Liste die nur noch Datum, Raumnummer und Bunchungszeit enthält

        for item in l1:                 #Daten extrahieren
            date = item['date']
            room_number = item['room_number']
            start_time = datetime.strptime(item['start_time'], '%H:%M')
            end_time = datetime.strptime(item['end_time'], '%H:%M')
            duration_hours = (end_time - start_time).total_seconds() / 3600  

            if room_number in dict_1 and date == dict_1[room_number]['date']:       #Wenn Raum schon existiert -> Bunchungszeit vergrößern
                dict_1[room_number]['total_time'] += duration_hours  
            else:
                if room_number in dict_1:                                           
                    l2.append({'date': dict_1[room_number]['date'], 'room_number': room_number, 'total_time': round(dict_1[room_number]['total_time'], 2)})
                dict_1[room_number] = {'date': date, 'total_time': duration_hours}  #dict_1 füttern

        for room_number, entry in dict_1.items():
            l2.append({'date': entry['date'], 'room_number': room_number, 'total_time': round(entry['total_time'], 2)})

        if len(l2) == 0:
            st.write("Keine Daten zum Plotten verfügbar.")
        else:
            #Daten Plotten:
    
            dates = sorted(set(item['date'] for item in l2), key=lambda x: datetime.strptime(x, '%A, %d.%m.%Y')) #Daten Sortieren

            num_unique_dates = len(dates)
            color_palette = plt.cm.get_cmap('tab10', num_unique_dates)      #Farben

            subplot_width = 10                                              #Plott größen                                            
            subplot_height = 4                                                                   

            num_subplots = len(dates)                                       # Anzahl der Subplotts soll abhängig von den Verschiedenen Daten sein

            fig_width = subplot_width                                       #Größe und Breite des Plots festlegen
            fig_height = num_subplots * subplot_height
            #Falls fall eintritt -> nur ein subplot
            if num_subplots > 1:
                fig, axs = plt.subplots(num_subplots, figsize=(fig_width, fig_height))
            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                axs = [ax]
            
            #Für jedes Datum ein subplot
            for i, date in enumerate(dates):                                            #Daten Filtern und sortieren
                filtered_entries = [item for item in l2 if item['date'] == date] 
                filtered_entries.sort(key=lambda x: x['total_time'], reverse=True)
                filtered_entries = filtered_entries[:5]                                 #Zeigt die 5 Räume mit den Größten Buchungszeiten an
                filtered_room_numbers = [entry['room_number'] for entry in filtered_entries] 
                filtered_total_times = [entry['total_time'] for entry in filtered_entries]

                color = color_palette(i)

                ax = axs[i] if num_subplots > 1 else axs[0]                             # Subplot anwählen

                bars = ax.bar(filtered_room_numbers, filtered_total_times, color=color) #Barchart

                ax.set_xlabel('Raumnummer')                                             #Achsenbeschriftung
                ax.set_ylabel('Reservierte Zeit/h')
                ax.set_title(f'Folgende Räume wurden am {date} Reserviert')

                ax.set_xticks(range(len(filtered_room_numbers)))
                ax.set_xticklabels(filtered_room_numbers, rotation=45)  

                for bar, time in zip(bars, filtered_total_times):                      #Zeit in der Mitte des Charts anzeigen lassen
                    ax.text(bar.get_x() + bar.get_width() / 2, time / 2, f'{time}h', ha='center', va='center')

            plt.tight_layout()
            st.pyplot(fig)
        
    def reminder_reservation(self, user_email):
        # Get Datum and Time
        #Aktuelles Datum 
        current_date = datetime.now().date()        #Aktuelles Datum     
        #Aktuelle Zeit
        current_time = datetime.now() # Zeit im format 'datetime.datetime'
        #Differenz -> wird für einen vergelcih benötigt
        diff_dauer = timedelta(minutes=5)   #Diff von 5 min
        #liste mit allen reservierungen des users
        l1 = self.get_user_reservations(user_email)
        #rausfiltern Wann die nächste reservierung Vorliegt
        for i, item in enumerate(l1):
            #für jedes item einen eigenen session_state anlegen:
            if f'item_state{i}' not in st.session_state:
                st.session_state[f'item_state{i}'] = 0
            print(f"Wert im State {i}: {st.session_state[f'item_state{i}']}")
            datum_item = item['date']
            datum_user_reservation = datetime.strptime(datum_item, '%A, %d.%m.%Y').date()
            #Zeit mit datum Kombinieren und in format 'datetime.datetime' bringen
            start_time = datetime.combine(datum_user_reservation, datetime.strptime(item['start_time'],"%H:%M").time()) 
            end_time = datetime.combine(datum_user_reservation, datetime.strptime(item['end_time'],"%H:%M").time())

            if datum_user_reservation == current_date:
                if st.session_state[f'item_state{i}'] < 2 and current_time < start_time:
                    #Beginnt meine Reservierung in den nächsten 5 minuten?
                    if start_time - current_time <= diff_dauer:
                        st.toast(f''':green[Ihre Reservierung für den raum {item['room_number']} beginnt inerhalb der nächsten 5 min]''')
                        #Counter Session State 'func_call um 1 erhöhen 
                        st.session_state[f'item_state{i}'] +=1
                        #print(f"Wert im State {i}: {st.session_state[f'item_state{i}']}")

                elif st.session_state[f'item_state{i}']>=2 and st.session_state[f'item_state{i}']<4:         
                    #Endet meine Reservierung in den nächsten 5 minuten?
                    if end_time > current_time:
                        if end_time - current_time <= diff_dauer:
                            st.toast(f''':red[Ihre Reservierung für den raum {item['room_number']} endet inerhalb der nächsten 5 min]''')
                            st.session_state[f'item_state{i}']+=1
                            #print(f"Wert im State {i}: {st.session_state[f'item_state{i}']}")
                #Counter reseten wenn 4 und end_time überschritten ist:
                elif st.session_state[f'item_state{i}'] == 4 and current_time >= end_time:
                    st.session_state[f'item_state{i}'] = 0
                    #print(f"Reset -> Wert im State{i} : {st.session_state[f'item_state{i}']}")
                #Spezialfälle
                # Wenn die Seite neu geladen wurde und die Reservierung bald endet
                elif st.session_state[f'item_state{i}'] == 0 and current_time < end_time and current_time > start_time:
                    st.session_state[f'item_state{i}'] =2
                    #print(f"Quereinstieg -> Wert im State{i} : {st.session_state[f'item_state{i}']}")


if __name__ == "__main__":
    db = UserDatabase()
    #  Test
    email = "mj5804@mci4me.at"
    db.verify_reservations(email)
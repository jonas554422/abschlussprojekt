from datetime import datetime
from tinydb import TinyDB, Query
import json


def leichen_beseitigung():
        
        """Alle nicht mehr aktuellen einträge in verfuegbare_raeum_db.json löschen"""
        #Daten generieren:
        db = TinyDB('verfuegbare_raeume_db.json')       
        daten = db.all()
        #Aktuelles Datum erzeuge
        current_date = datetime.now().date()
        #Aktuelle zeit erzeugen
        current_time = datetime.now().time().strftime('%H:%M') # Zeit als string

        # Leere Liste erstellen; hier kommen die neuen Daten rein
        angepasste_daten = []
        
        for item in daten:
            datum_item = item['Datum']
            #Datum in gewünschtes format bringen:
            datum_item = datetime.strptime(datum_item, '%A, %d.%m.%Y').date()       

            #Alle Daten die älter als das aktuelle Datum sind werden nicht in die Aktuelle liste übernommen!!
            #Zeit 'Verfuegbar bis' sollte vor der aktuellen zeit liegen, ansonsten ebenfalls rausschmeißen!!
            if datum_item == current_date:
                if current_time<item['Verfuegbar bis']:
                    angepasste_daten.append(item)
            elif datum_item > current_date:
                 angepasste_daten.append(item)
                
        # Die angepassten Daten in die Datenbank speichern
        if angepasste_daten:
            db.truncate()  # Alte Daten in der Datenbank löschen
            db.insert_multiple(angepasste_daten)  # Neue Daten in die Datenbank einfügen
            print('Angepasste Daten wurden erfolgreich in die Datenbank gespeichert.')
        else:
            print('Keine Daten zur Anpassung gefunden!')

leichen_beseitigung()
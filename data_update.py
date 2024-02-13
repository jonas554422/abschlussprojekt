from datetime import datetime
import json
from tinydb import TinyDB, Query

def parse_uhrzeit(uhrzeit_str):
    try:
        uhrzeit_str = uhrzeit_str.replace(" ", "")
        if '-' in uhrzeit_str:
            startzeit_str, endzeit_str = uhrzeit_str.split('-')
        else:
            startzeit_str = uhrzeit_str[:5]
            endzeit_str = uhrzeit_str[5:]
        startzeit = datetime.strptime(startzeit_str, "%H:%M").time()
        endzeit = datetime.strptime(endzeit_str, "%H:%M").time()
        return startzeit, endzeit
    except ValueError as e:
        print(f"Fehler beim Parsen der Uhrzeit '{uhrzeit_str}': {e}")
        return None, None

def trenne_gebaeude_und_raum(raum_str):
    gebaeude_namen = ["MCI I", "MCI II", "MCI III", "MCI IV", "MCI VI", "MCI VII"]
    for gebaeude_name in reversed(gebaeude_namen):
        if gebaeude_name in raum_str:
            teile = raum_str.split(gebaeude_name)
            raum = teile[0].strip()
            gebaeude = gebaeude_name + (teile[1].strip() if len(teile) > 1 else "")
            return raum, gebaeude
    return "", ""  # Gebe leere Strings zurück, wenn keine Übereinstimmung gefunden wurde

def anpassen_und_speichern():
    db = TinyDB('kalenderdaten.json')
    daten = db.all()
    angepasste_daten = []

    for eintrag in daten:
        uhrzeit = eintrag.get('Uhrzeit', '')
        startzeit, endzeit = parse_uhrzeit(uhrzeit)
        if startzeit and endzeit:
            eintrag['Startzeit'] = startzeit.strftime("%H:%M")
            eintrag['Endzeit'] = endzeit.strftime("%H:%M")
            raum = eintrag.get('Raum', '')
            if raum:
                raum, gebaeude = trenne_gebaeude_und_raum(raum)
                if gebaeude:
                    eintrag['Raumnummer'] = raum
                    eintrag['Gebaeude'] = gebaeude
                    angepasste_daten.append(eintrag)
                else:
                    print(f"Überspringe Eintrag wegen fehlendem oder ungültigem Gebäude: {raum}")
            else:
                print(f"Überspringe Eintrag wegen fehlender Raumangabe: {eintrag}")
        else:
            print(f"Überspringe Eintrag wegen Fehler beim Parsen der Uhrzeit: {uhrzeit}")

    if angepasste_daten:
        with open('angepasste_kalenderdaten.json', 'w') as f:
            json.dump(angepasste_daten, f, indent=4, default=str)
        print('Angepasste Daten wurden erfolgreich gespeichert.')
    else:
        print('Keine Daten zur Anpassung gefunden.')

anpassen_und_speichern()

from datetime import datetime, time
import json

def lese_angepasste_daten():
    with open('angepasste_kalenderdaten.json', 'r') as f:
        return json.load(f)

def zeit_im_bereich(start, ende, pruefzeit):
    """Prüft, ob eine Zeit innerhalb eines Zeitbereichs liegt."""
    if start <= pruefzeit < ende:
        return True
    return False

def generiere_verfuegbare_raeume(daten):
    verfuegbare_raeume = []
    # Definiere das Zeitfenster für die Verfügbarkeit
    tagesbeginn = time(7, 0)
    tagesende = time(18, 0)

    for eintrag in daten:
        datum = eintrag.get('Datum', '')
        gebaeude = eintrag.get('Gebaeude', '')
        raumnummer = eintrag.get('Raumnummer', '')
        startzeit = datetime.strptime(eintrag.get('Startzeit', ''), "%H:%M").time()
        endzeit = datetime.strptime(eintrag.get('Endzeit', ''), "%H:%M").time()

        # Verfügbarkeit vor der Buchung, wenn Startzeit nach 7:00 Uhr
        if zeit_im_bereich(tagesbeginn, tagesende, startzeit):
            verfuegbare_raeume.append({
                'Datum': datum,
                'Gebaeude': gebaeude,
                'Raumnummer': raumnummer,
                'Verfuegbar von': tagesbeginn.strftime("%H:%M"),
                'Verfuegbar bis': startzeit.strftime("%H:%M")
            })
        
        # Verfügbarkeit nach der Buchung, wenn Endzeit vor 18:00 Uhr
        if zeit_im_bereich(tagesbeginn, tagesende, endzeit) and endzeit < tagesende:
            verfuegbare_raeume.append({
                'Datum': datum,
                'Gebaeude': gebaeude,
                'Raumnummer': raumnummer,
                'Verfuegbar von': endzeit.strftime("%H:%M"),
                'Verfuegbar bis': tagesende.strftime("%H:%M")
            })
    
    return verfuegbare_raeume

def speichere_verfuegbare_raeume(verfuegbare_raeume):
    with open('verfuegbare_raeume.json', 'w') as f:
        json.dump(verfuegbare_raeume, f, indent=4, default=str)
    print('Verfügbare Räume wurden erfolgreich in verfuegbare_raeume.json gespeichert.')

angepasste_daten = lese_angepasste_daten()
verfuegbare_raeume = generiere_verfuegbare_raeume(angepasste_daten)
speichere_verfuegbare_raeume(verfuegbare_raeume)

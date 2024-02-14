from datetime import datetime, time
import json
import re

class RaumVerwaltung:
    def __init__(self, gesamtraeume, daten_pfad):
        self.gesamtraeume = gesamtraeume
        self.daten_pfad = daten_pfad
        self.angepasste_daten = self.lese_angepasste_daten()

    def lese_angepasste_daten(self):
        with open(self.daten_pfad, 'r') as f:
            return json.load(f)

    @staticmethod
    def parse_datum(datum):
        datum_teil = datum.split(',')[0].strip()
        wochentag, tag, monat, jahr = re.match(r'([a-zA-Z]+)(\d{2})\.(\d{2})\.(\d{4})', datum_teil).groups()
        monat_num = datetime.strptime(monat, '%m').month
        return datetime.strptime(f'{jahr}-{monat_num}-{tag}', '%Y-%m-%d').date()

    def generiere_verfuegbare_raeume(self):
        verfuegbare_raeume = []
        tagesbeginn = time(7, 0)
        tagesende = time(18, 0)
        einzigartige_datum = set(eintrag['Datum'] for eintrag in self.angepasste_daten)

        for datum in einzigartige_datum:
            buchungen_pro_datum = [eintrag for eintrag in self.angepasste_daten if eintrag['Datum'] == datum]
            verfuegbare_raeume_pro_datum = self.verfuegbare_raeume_pro_datum(buchungen_pro_datum, tagesbeginn, tagesende, datum)
            verfuegbare_raeume.extend(verfuegbare_raeume_pro_datum)

        verfuegbare_raeume.sort(key=lambda x: datetime.strptime(x['Datum'], '%A, %d.%m.%Y'))
        return verfuegbare_raeume

    def verfuegbare_raeume_pro_datum(self, buchungen_pro_datum, tagesbeginn, tagesende, datum):
        verfuegbare_raeume_pro_datum = []
        for raum in self.gesamtraeume:
            buchungen_fuer_raum = [buchung for buchung in buchungen_pro_datum if buchung['Raumnummer'] == raum]
            verfuegbarkeiten = [(tagesbeginn, tagesende)]
            for buchung in buchungen_fuer_raum:
                verfuegbarkeiten = self.aktualisiere_verfuegbarkeiten(verfuegbarkeiten, buchung)
            for start, ende in verfuegbarkeiten:
                verfuegbare_raeume_pro_datum.append({
                    "Datum": f"{self.parse_datum(datum).strftime('%A, %d.%m.%Y')}",
                    "Gebaeude": "MCI IV" if not buchungen_fuer_raum else buchungen_fuer_raum[0].get('Gebaeude', 'MCI IV'),
                    "Raumnummer": raum,
                    "Verfuegbar von": start.strftime('%H:%M'),
                    "Verfuegbar bis": ende.strftime('%H:%M')
                })
        return verfuegbare_raeume_pro_datum

    @staticmethod
    def aktualisiere_verfuegbarkeiten(verfuegbarkeiten, buchung):
        neue_verfuegbarkeiten = []
        buchung_start = datetime.strptime(buchung['Startzeit'], '%H:%M').time()
        buchung_ende = datetime.strptime(buchung['Endzeit'], '%H:%M').time()
        for start, ende in verfuegbarkeiten:
            if buchung_start <= start and buchung_ende >= ende:
                continue
            if buchung_start > start:
                neue_verfuegbarkeiten.append((start, min(ende, buchung_start)))
            if buchung_ende < ende:
                neue_verfuegbarkeiten.append((max(start, buchung_ende), ende))
        return neue_verfuegbarkeiten

    def speichere_verfuegbare_raeume(self, verfuegbare_raeume):
        with open('verfuegbare_raeume.json', 'w') as f:
            json.dump(verfuegbare_raeume, f, indent=4)
        print('Verfügbare Räume wurden erfolgreich in verfuegbare_raeume.json gespeichert.')

# Beispiel für die Verwendung der Klasse
gesamtraeume = [
    "4B-001", "4B-003", "4B-005", "4B-006", "4B-007", "4B-117",
    "4C-501", "4C-502", "4C-503", "4C-504", "4C-505",
    "4A-020", "4A-024", "4A-027", "4A-135", "4A-393",
    "4A-412", "4A-434", "4A-438", "4A-439"
]

verwaltung = RaumVerwaltung(gesamtraeume, 'angepasste_kalenderdaten.json')
verfuegbare_raeume = verwaltung.generiere_verfuegbare_raeume()
verwaltung.speichere_verfuegbare_raeume(verfuegbare_raeume)

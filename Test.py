import matplotlib.pyplot as plt
from collections import defaultdict


l1 = [
    {'email': 'bj5954@mci4me.at', 'room_number': '4B-117', 'date': 'Thursday, 22.02.2024', 'start_time': '08:00', 'end_time': '09:00', 'doc_id': 1},
    {'email': 'bj5954@mci4me.at', 'room_number': '4B-117', 'date': 'Thursday, 22.02.2024', 'start_time': '09:15', 'end_time': '18:00', 'doc_id': 2}
]

l2 = [{'date': 'Friday, 23.02.2024', 'room_number': '4A-027', 'total_time': 1.75},
      {'date': 'Friday, 23.02.2024', 'room_number': '4C-501', 'total_time': 6.75},
      {'date': 'Friday, 23.02.2024', 'room_number': '4B-101', 'total_time': 4.5},
      {'date': 'Friday, 23.02.2024', 'room_number': '4D-301', 'total_time': 3.25},
      {'date': 'Friday, 23.02.2024', 'room_number': '4E-201', 'total_time': 2.0},
      {'date': 'Friday, 23.02.2024', 'room_number': '4F-401', 'total_time': 5.0},
      {'date': 'Friday, 23.02.2024', 'room_number': '4G-501', 'total_time': 2.75},
      {'date': 'Friday, 23.02.2024', 'room_number': '4H-601', 'total_time': 1.5},
      {'date': 'Friday, 23.02.2024', 'room_number': '4I-701', 'total_time': 4.0},
      {'date': 'Friday, 23.02.2024', 'room_number': '4J-801', 'total_time': 3.0},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4A-027', 'total_time': 1.0},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4B-101', 'total_time': 2.5},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4C-501', 'total_time': 3.75},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4D-301', 'total_time': 2.25},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4E-201', 'total_time': 1.75},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4F-401', 'total_time': 4.0},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4G-501', 'total_time': 3.25},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4H-601', 'total_time': 2.5},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4I-701', 'total_time': 1.0},
      {'date': 'Saturday, 24.02.2024', 'room_number': '4J-801', 'total_time': 5.5},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4A-027', 'total_time': 3.0},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4B-101', 'total_time': 2.25},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4C-501', 'total_time': 4.75},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4D-301', 'total_time': 1.5},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4E-201', 'total_time': 2.5},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4F-401', 'total_time': 3.25},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4G-501', 'total_time': 2.0},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4H-601', 'total_time': 1.75},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4I-701', 'total_time': 3.75},
      {'date': 'Sunday, 25.02.2024', 'room_number': '4J-801', 'total_time': 4.5},
      {'date': 'Monday, 26.02.2024', 'room_number': '4A-027', 'total_time': 2.0},
      {'date': 'Monday, 26.02.2024', 'room_number': '4B-101', 'total_time': 3.5},
      {'date': 'Monday, 26.02.2024', 'room_number': '4C-501', 'total_time': 2.25},
      {'date': 'Monday, 26.02.2024', 'room_number': '4D-301', 'total_time': 1.75},
      {'date': 'Monday, 26.02.2024', 'room_number': '4E-201', 'total_time': 4.0},
      {'date': 'Monday, 26.02.2024', 'room_number': '4F-401', 'total_time': 3.25},
      {'date': 'Monday, 26.02.2024', 'room_number': '4G-501', 'total_time': 2.5},
      {'date': 'Monday, 26.02.2024', 'room_number': '4H-601', 'total_time': 1.0},
      {'date': 'Monday, 26.02.2024', 'room_number': '4I-701', 'total_time': 3.75},
      {'date': 'Monday, 26.02.2024', 'room_number': '4J-801', 'total_time': 2.25},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4A-027', 'total_time': 1.5},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4B-101', 'total_time': 2.0},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4C-501', 'total_time': 3.0},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4D-301', 'total_time': 2.75},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4E-201', 'total_time': 1.25},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4F-401', 'total_time': 4.5},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4G-501', 'total_time': 3.25},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4H-601', 'total_time': 2.0},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4I-701', 'total_time': 1.75},
      {'date': 'Tuesday, 27.02.2024', 'room_number': '4J-801', 'total_time': 5.0}]

# Daten vorbereiten
dates = sorted(set(item['date'] for item in l2))

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
    colors = [color_palette(i)] * len(filtered_room_numbers)

    # Erstellen von Barcharts für die Gesamtzeit jedes Raums an diesem Datum
    if num_subplots > 1:
        ax = axs[i]
    else:
        ax = axs
    bars = ax.bar(filtered_room_numbers, filtered_total_times, color=colors)

    # Achsenbeschriftungen und Titel hinzufügen
    ax.set_xlabel('Raumnummer')
    ax.set_ylabel('Gesamtzeit (Stunden)')
    ax.set_title(f'Folgende Räume wurden am {date} Reserviert')

    # Raumnummern als x-Achsenbeschriftungen festlegen
    ax.set_xticks(range(len(filtered_room_numbers)))
    ax.set_xticklabels(filtered_room_numbers, rotation=45)  # Rotation der Beschriftungen für bessere Lesbarkeit

    # Beschriftungen für jeden Balken hinzufügen
    for bar, time in zip(bars, filtered_total_times):
        ax.text(bar.get_x() + bar.get_width() / 2, time / 2, f'{time}h', ha='center', va='center')

# Layout anpassen und Plot anzeigen
plt.tight_layout()
plt.show()
#l2 = [{'date': 'Friday, 23.02.2024', 'room_number': '4A-027', 'total_time': 1.75},
#      {'date': 'Friday, 23.02.2024', 'room_number': '4C-501', 'total_time': 6.75},
#      {'date': 'Saturday, 24.02.2024', 'room_number': '4A-027', 'total_time': 1.0}]

## Daten vorbereiten
#dates = sorted(set(item['date'] for item in l2))
#
## Erstellen von Subplots für jedes Datum
#fig, axs = plt.subplots(len(dates), figsize=(10, 6))
#
## Farbpalette für die Balken
#color_palette = plt.get_cmap('tab10')
#
## Schleife über jedes Datum und Erstellung des Barcharts für jeden Raum
#for i, date in enumerate(dates):
#    # Filtern der Einträge für das aktuelle Datum
#    filtered_entries = [item for item in l2 if item['date'] == date]
#    filtered_room_numbers = [entry['room_number'] for entry in filtered_entries]
#    filtered_total_times = [entry['total_time'] for entry in filtered_entries]
#
#    # Farbe für die Balken dieses Datums auswählen
#    color = color_palette(i)
#
#    # Erstellen von Barcharts für die Gesamtzeit jedes Raums an diesem Datum
#    ax = axs[i] if len(dates) > 1 else axs
#    bars = ax.bar(filtered_room_numbers, filtered_total_times, color=color)
#
#    # Achsenbeschriftungen und Titel hinzufügen
#    ax.set_xlabel('Raumnummer')
#    ax.set_ylabel('Gesamtzeit (Stunden)')
#    ax.set_title(f'Folgende Räume wurden am {date} Reserviert')
#
#    # Raumnummern als x-Achsenbeschriftungen festlegen
#    ax.set_xticks(range(len(filtered_room_numbers)))
#    ax.set_xticklabels(filtered_room_numbers, rotation=45)  # Rotation der Beschriftungen für bessere Lesbarkeit
#
#    # Beschriftungen für jeden Balken hinzufügen
#    for bar, time in zip(bars, filtered_total_times):
#        ax.text(bar.get_x() + bar.get_width() / 2, time / 2, f'{time}h', ha='center', va='center')
#
## Layout anpassen und Plot anzeigen
#plt.tight_layout()
#plt.show()
##print(room_numbers)
#
### Erstellen von Subplots für jedes Datum
##fig, axs = plt.subplots(len(dates), figsize=(10, 6), sharex=True)
##
### Schleife über jedes Datum und Erstellung des Barcharts für die gebuchten Räume
#for i, date in enumerate(dates):
#    # Daten für das aktuelle Datum extrahieren
#    room_nums=[]
#    
#    # Subplot für das aktuelle Datum erstellen
#    ax = axs[i] if len(dates) > 1 else axs
#    ax.bar(room_numbers, total_times)
#    
#    # Achsenbeschriftungen und Titel hinzufügen
#    ax.set_xlabel(f'Raumnummer {room_numbers[i]}')
#    ax.set_ylabel('Gesamtzeit (Stunden)')
#    ax.set_title(f'Gebuchte Räume am {date}')
#    
#    # Raumnummern als x-Achsenbeschriftungen festlegen
#    ax.set_xticks(range(len(room_numbers)))
#    ax.set_xticklabels(room_numbers, rotation=45)  # Rotation der Beschriftungen für bessere Lesbarkeit
#
## Layout anpassen und Plot anzeigen
#plt.tight_layout()
#plt.show()
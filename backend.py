import json

def lade_verfuegbare_raeume():
    try:
        with open('verfuegbare_raeume.json', 'r') as file:
            verfuegbare_raeume = json.load(file)
        return verfuegbare_raeume
    except FileNotFoundError:
        return []

def speichere_registrierung(name, email):
    try:
        with open('reservation.json', 'r') as file:
            try:
                reservierungen = json.load(file)
            except json.JSONDecodeError:
                reservierungen = []
    except FileNotFoundError:
        reservierungen = []

    if ist_registriert(email):
        return False
    
    reservierungen.append({"name": name, "email": email})
    
    with open('reservation.json', 'w') as file:
        json.dump(reservierungen, file, indent=4)
    
    return True

def ist_registriert(email):
    try:
        with open('reservation.json', 'r') as file:
            reservierungen = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        reservierungen = []

    for reservierung in reservierungen:
        if reservierung['email'] == email:
            return True
    return False

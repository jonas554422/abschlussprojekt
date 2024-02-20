import json

def func_1():
    """Funktion extrahiert die reservierten Räume aus der DB"""

    data = json.load(open('reservation.json'))

    l1:list = []

    for elem, elm in data.get("reservations", {}).items():
        date = elm.get("date")
        room_num = elm.get("room_number")
        l1.append({"date": date, "room_number": room_num})

    return(l1)
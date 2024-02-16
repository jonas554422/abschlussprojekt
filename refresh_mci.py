import subprocess
import sys

def aktualisiere_mci_daten():
    try:
        # Ermittle den Pfad zum aktuell ausgeführten Python-Interpreter
        python_path = sys.executable

        # Führe data_mci.py aus und warte auf seine Fertigstellung
        subprocess.run([python_path, 'data_mci.py'], check=True)

        # Führe data_update.py aus und warte auf seine Fertigstellung
        subprocess.run([python_path, 'data_update.py'], check=True)

        # Führe free_rooms.py aus und warte auf seine Fertigstellung
        subprocess.run([python_path, 'free_rooms.py'], check=True)

        return True, "Die MCI-Daten wurden erfolgreich aktualisiert."
    except subprocess.CalledProcessError as e:
        return False, f"Fehler bei der Ausführung der Skripte: {e}"

if __name__ == "__main__":
    erfolg, nachricht = aktualisiere_mci_daten()
    

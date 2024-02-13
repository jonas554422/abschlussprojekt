from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select  # Korrigierte Zeile
import time
from bs4 import BeautifulSoup
from tinydb import TinyDB


# Initialisiere den WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL der Anmeldeseite
login_url = 'https://my.mci4me.at/?request=timetable&mode=mci&ts=1707513332100'
driver.get(login_url)
time.sleep(2)

# Anmeldung
username_input = driver.find_element(By.NAME, 'username')
password_input = driver.find_element(By.NAME, 'password')
username_input.send_keys('mj5804@mci4me.at')
password_input.send_keys('SvWerder1899')
password_input.send_keys(Keys.RETURN)
time.sleep(5)

# Auswahl im Dropdown-Menü
select_element = driver.find_element(By.CSS_SELECTOR, 'select')
select = Select(select_element)
select.select_by_value('-1')
time.sleep(5)

# Datenextraktion
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')
kalenderdaten = []
tabellenzeilen = soup.find('table', {'id': 'scheduletable'}).find('tbody').find_all('tr')

for zeile in tabellenzeilen:
    zellen = zeile.find_all('td')
    if len(zellen) > 5:
        datum = zellen[0].text.strip()
        uhrzeit = zellen[1].text.strip()
        veranstaltung = zellen[2].text.strip()
        gruppe = zellen[3].text.strip()
        raum = zellen[5].text.strip()
        kalenderdaten.append({'Datum': datum, 'Uhrzeit': uhrzeit, 'Veranstaltung': veranstaltung, 'Gruppe': gruppe, 'Raum': raum})

db = TinyDB('kalenderdaten.json')
db.insert_multiple(kalenderdaten)

driver.quit()

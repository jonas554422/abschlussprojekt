import streamlit as st
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
import locale
import pandas as pd
from backend import UserDatabase
from refresh_mci import aktualisiere_mci_daten
import os
import time

#Testen wie der Scheiß funktioniert:

user_db = UserDatabase('reservation.json', 'verfuegbare_raeume_db.json')

user_db.reminder_1()
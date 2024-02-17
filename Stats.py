# Soll eine Plott der belibtesten Räume machen

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Daten für die Grafik generieren
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Matplotlib Grafik erstellen
fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_xlabel('x')
ax.set_ylabel('sin(x)')
ax.set_title('Sinusfunktion')

# Streamlit-Grafik anzeigen
st.pyplot(fig)
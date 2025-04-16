
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

st.title("Calculateur de salaire avec majorations")

def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin):
    fmt = "%H:%M"
    h_debut = datetime.strptime(heure_debut, fmt)
    h_fin = datetime.strptime(heure_fin, fmt)
    if h_fin <= h_debut:
        h_fin += timedelta(days=1)

    total_heures = (h_fin - h_debut).total_seconds() / 3600

    heure = h_debut
    heures_nuit = 0
    while heure < h_fin:
        if heure.time() >= datetime.strptime("23:00", fmt).time() or heure.time() < datetime.strptime("06:00", fmt).time():
            heures_nuit += 1
        heure += timedelta(hours=1)

    heures_sup = max(0, total_heures - 9.5)

    salaire_base = round(total_heures * tarif_horaire, 2)
    jour_semaine = pd.Timestamp(date).day_name().lower()
    maj_dimanche = 4.80 * total_heures if jour_semaine == "sunday" else 0
    maj_samedi = 2.40 * total_heures if jour_semaine == "saturday" else 0
    maj_nuit = round(heures_nuit * 8.4, 2)
    maj_sup = round(heures_sup * tarif_horaire * 0.25, 2)
    total_brut = round(salaire_base + maj_dimanche + maj_samedi + maj_nuit + maj_sup, 2)

    return {
        "Nom": nom,
        "Date": date,
        "Jour": jour_semaine,
        "Heures totales": round(total_heures, 2),
        "Heures de nuit": heures_nuit,
        "Heures sup (>9h30)": round(heures_sup, 2),
        "Majoration dimanche": round(maj_dimanche, 2),
        "Majoration samedi": round(maj_samedi, 2),
        "Majoration nuit": maj_nuit,
        "Majoration heures sup": maj_sup,
        "Salaire de base": salaire_base,
        "Salaire total brut": total_brut
    }

with st.form("salaire_form"):
    nom = st.text_input("Nom du collaborateur")
    date = st.date_input("Date")
    tarif = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05)
    heure_debut = st.time_input("Heure de début")
    heure_fin = st.time_input("Heure de fin")
    submitted = st.form_submit_button("Calculer")

    if submitted:
        result = calcul_salaire(nom, date, tarif, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"))
        st.subheader("Résultat")
        st.dataframe(pd.DataFrame([result]))

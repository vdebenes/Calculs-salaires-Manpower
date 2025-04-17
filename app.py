import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date as date_class
import io

st.set_page_config(page_title="Calculateur de salaire Manpower", layout="wide")

st.markdown("""
    <style>
    .stTextInput, .stNumberInput, .stDateInput, .stTimeInput {
        max-width: 300px;
    }
    .recap-box {
        background-color: #ffe6f0;
        border-radius: 10px;
        padding: 10px 20px;
        margin: 10px 0;
        font-size: 16px;
    }
    .form-box {
        padding: 10px;
    }
    .small-table .stDataFrame {
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def init_data():
    return []

if "missions" not in st.session_state:
    st.session_state.missions = []

if "tarifs_par_nom" not in st.session_state:
    st.session_state.tarifs_par_nom = {}

def convert_pause_to_decimal(pause_str):
    try:
        if ":" in pause_str:
            h, m = map(int, pause_str.split(":"))
            return h + m / 60
        elif "." in pause_str:
            h, d = map(int, pause_str.split("."))
            return h + d / 60 if d >= 6 else h + d * 0.1
        return float(pause_str)
    except:
        return 0.0

def format_minutes(decimal_hours):
    heures = int(decimal_hours)
    minutes = int(round((decimal_hours - heures) * 60))
    return f"{heures}:{minutes:02d}"

def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin, pause, numero_mission):
    heure_debut = datetime.strptime(heure_debut, "%H:%M")
    heure_fin = datetime.strptime(heure_fin, "%H:%M")
    if heure_fin <= heure_debut:
        heure_fin += timedelta(days=1)

    heures_brutes = (heure_fin - heure_debut).total_seconds() / 3600
    total_heures = heures_brutes - pause

    jour_en = pd.Timestamp(date).day_name().lower()
    jours_fr = {
        "monday": "Lundi", "tuesday": "Mardi", "wednesday": "Mercredi",
        "thursday": "Jeudi", "friday": "Vendredi", "saturday": "Samedi", "sunday": "Dimanche"
    }
    jour_semaine = jours_fr.get(jour_en, jour_en.capitalize())

    jours_feries = {
        date_class(2025, 1, 1), date_class(2025, 4, 18), date_class(2025, 4, 21),
        date_class(2025, 5, 29), date_class(2025, 6, 9), date_class(2025, 8, 1),
        date_class(2025, 9, 22), date_class(2025, 12, 25)
    }
    is_jour_ferie = date in jours_feries

    heures_nuit = heures_dimanche = heures_samedi = heures_normales = heures_sup = 0.0
    current = heure_debut
    pause_minutes = int(pause * 60)
    total_minutes = int((heure_fin - heure_debut).total_seconds() / 60)
    worked_minutes = total_minutes - pause_minutes
    minute_count = 0

    while minute_count < worked_minutes:
        h = current.time()
        is_nuit = h >= time(23, 0) or h < time(6, 0)
        is_dimanche = jour_semaine == "Dimanche" or is_jour_ferie
        is_samedi = jour_semaine == "Samedi"
        minute_in_hour = minute_count / 60

        if is_nuit:
            heures_nuit += 1 / 60
        elif is_dimanche:
            heures_dimanche += 1 / 60
        elif is_samedi:
            heures_samedi += 1 / 60
        elif minute_in_hour >= 9.5:
            heures_sup += 1 / 60
        else:
            heures_normales += 1 / 60

        current += timedelta(minutes=1)
        minute_count += 1

    maj_25_taux = round(tarif_horaire * 0.25, 2)
    maj_sup = maj_nuit = maj_dimanche = maj_samedi = 0.0

    if heures_dimanche > 0 or heures_nuit > 0 or heures_samedi > 0:
        maj_sup = 0.0
    else:
        maj_sup = round(heures_sup * maj_25_taux, 2)

    salaire_base = round((heures_normales + heures_sup) * tarif_horaire, 2)
    maj_nuit = round(8.40 * heures_nuit, 2)
    maj_dimanche = round(4.80 * heures_dimanche, 2)
    maj_samedi = round(2.40 * heures_samedi, 2)
    total_brut = round(salaire_base + maj_sup + maj_nuit + maj_dimanche + maj_samedi, 2)

    return {
        "Mission": numero_mission,
        "Nom": nom,
        "Date": date.strftime("%Y-%m-%d"),
        "Heure de début": heure_debut.strftime("%H:%M"),
        "Heure de fin": heure_fin.strftime("%H:%M"),
        "Tarif horaire": tarif_horaire,
        "Pause (h)": f"{int(pause)}:{int((pause - int(pause)) * 60):02d}",
        "Heures totales": round(total_heures, 2),
        "Heures totales (hh:mm)": format_minutes(total_heures),
        "Salaire de base": salaire_base,
        "Majoration 25% (heure sup)": maj_25_taux,
        "Heures sup (hh:mm)": format_minutes(heures_sup),
        "Heures samedi (hh:mm)": format_minutes(heures_samedi),
        "Heures dimanche (hh:mm)": format_minutes(heures_dimanche),
        "Heures de nuit (hh:mm)": format_minutes(heures_nuit),
        "Majoration heures sup": maj_sup,
        "Majoration samedi": maj_samedi,
        "Majoration dimanche": maj_dimanche,
        "Majoration nuit": maj_nuit,
        "Salaire total brut": total_brut
    }

# Interface utilisateur ici
col1, col2 = st.columns(2)

with col1:
    st.subheader("Informations de la mission")
    numero_mission = st.text_input("Numéro de mission", "")
    nom = st.text_input("Nom", "")
    tarif_horaire = st.number_input("Tarif horaire", min_value=0.0, format="%.2f")
    date = st.date_input("Date")
    heure_debut = st.time_input("Heure de début", value=time(8, 0))
    heure_fin = st.time_input("Heure de fin", value=time(17, 0))
    pause_str = st.text_input("Pause (hh:mm ou décimal)", value="0:00")
    if st.button("Vider le formulaire"):
        st.experimental_rerun()

with col2:
    st.subheader("Résumé de la dernière mission")
    if st.session_state.missions:
        last = st.session_state.missions[-1]
        with st.container():
            st.markdown("<div class='recap-box'>" +
                f"<b>Mission :</b> {last['Mission']} — <b>Date :</b> {last['Date']} — <b>Heure de début :</b> {last['Heure de début']} — <b>Heure de fin :</b> {last['Heure de fin']}<br>" +
                f"<b>Nom :</b> {last['Nom']} — <b>Tarif horaire :</b> CHF {last['Tarif horaire']} — <b>Pause :</b> {last['Pause (h)']}<br>" +
                f"<b>Heures totales :</b> {last['Heures totales (hh:mm)']} (soit {last['Heures totales']} h)<br>" +
                f"<b>Salaire de base :</b> CHF {last['Salaire de base']}<br>" +
                f"<b>Majoration 25% (heure sup) :</b> CHF {last['Majoration 25% (heure sup)']} — <b>Heures sup :</b> {last['Heures sup (hh:mm)']}<br>" +
                f"<b>Heures samedi :</b> {last['Heures samedi (hh:mm)']} — <b>Majoration samedi :</b> CHF {last['Majoration samedi']}<br>" +
                f"<b>Heures dimanche :</b> {last['Heures dimanche (hh:mm)']} — <b>Majoration dimanche :</b> CHF {last['Majoration dimanche']}<br>" +
                f"<b>Heures de nuit :</b> {last['Heures de nuit (hh:mm)']} — <b>Majoration nuit :</b> CHF {last['Majoration nuit']}<br>" +
                f"<b>Salaire total brut :</b> <b>CHF {last['Salaire total brut']}</b>" +
                "</div>", unsafe_allow_html=True)

if st.button("Calculer salaire"):
    pause_decimal = convert_pause_to_decimal(pause_str)
    resultat = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause_decimal, numero_mission)
    st.session_state.missions.append(resultat)
    st.session_state.tarifs_par_nom[nom] = tarif_horaire
    st.experimental_rerun()

# Tableau des missions
if st.session_state.missions:
    st.subheader("Historique des missions")
    df = pd.DataFrame(st.session_state.missions)
    st.dataframe(df, use_container_width=True, height=350)
    index_to_delete = st.number_input("Supprimer la ligne n° (index commençant à 0)", min_value=0, max_value=len(df)-1, step=1)
    if st.button("Supprimer cette ligne"):
        st.session_state.missions.pop(index_to_delete)
        st.experimental_rerun()

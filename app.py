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

# Interface utilisateur
st.title("Calculateur de salaire Manpower")
col1, col2 = st.columns(2)

with col1:
    nom = st.text_input("Nom")
    tarif_horaire = st.number_input("Tarif horaire", value=st.session_state.tarifs_par_nom.get(nom, 0.0), step=0.01)
    date = st.date_input("Date")
    heure_debut = st.time_input("Heure de début", value=time(8, 0))
    heure_fin = st.time_input("Heure de fin", value=time(17, 0))
    pause = st.text_input("Pause (hh:mm ou décimale)", value="0:00")
    numero_mission = st.text_input("Numéro de mission")

with col2:
    st.markdown("### Résumé de la dernière mission", unsafe_allow_html=True)
    if st.session_state.missions:
        dernier = st.session_state.missions[-1]
        recap_html = f"""
        <div class='recap-box'>
        <b>Mission :</b> {dernier['Mission']}<br>
        <b>Date :</b> {dernier['Date']}<br>
        <b>Heure de début :</b> {dernier['Heure de début']} — <b>Heure de fin :</b> {dernier['Heure de fin']}<br>
        <b>Nom :</b> {dernier['Nom']}<br>
        <b>Tarif horaire :</b> CHF {dernier['Tarif horaire']}<br>
        <b>Heures brutes :</b> {dernier['Heures totales (hh:mm)']}<br>
        <b>Pause :</b> {dernier['Pause (h)']}<br>
        <b>Salaire de base :</b> CHF {dernier['Salaire de base']}<br>
        <b>Majoration 25% (heure sup) :</b> CHF {dernier['Majoration 25% (heure sup)']} — Heures sup : {dernier['Heures sup (hh:mm)']}<br>
        <b>Heures samedi :</b> {dernier['Heures samedi (hh:mm)']} — Majoration : CHF {dernier['Majoration samedi']}<br>
        <b>Heures dimanche :</b> {dernier['Heures dimanche (hh:mm)']} — Majoration : CHF {dernier['Majoration dimanche']}<br>
        <b>Heures de nuit :</b> {dernier['Heures de nuit (hh:mm)']} — Majoration : CHF {dernier['Majoration nuit']}<br>
        Salaire total brut : <b>{dernier['Salaire total brut']} CHF</b>
        </div>
        """
        st.markdown(recap_html, unsafe_allow_html=True)

col_reset, col_submit = st.columns([1, 2])

with col_submit:
    if st.button("Calculer salaire"):
        pause_decimal = convert_pause_to_decimal(pause)
        result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause_decimal, numero_mission)
        st.session_state.missions.append(result)
        st.session_state.tarifs_par_nom[nom] = tarif_horaire

with col_reset:
    if st.button("Vider le formulaire"):
        st.experimental_rerun()

st.markdown("---")

if st.session_state.missions:
    df_result = pd.DataFrame(st.session_state.missions)
    st.dataframe(df_result, use_container_width=True, height=300)

    for i in range(len(df_result)):
        if st.button(f"🗑️ Supprimer ligne {i+1}", key=f"delete_{i}"):
            st.session_state.missions.pop(i)
            st.experimental_rerun()

    if st.button("🧹 Vider toutes les lignes du tableau"):
        st.session_state.missions = []
        st.experimental_rerun()

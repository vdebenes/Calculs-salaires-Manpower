import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date as date_class
import io

# Fonction d'export Excel
def generate_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Missions')
        workbook = writer.book
        worksheet = writer.sheets['Missions']

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'align': 'center',
            'bg_color': '#FFB6C1',
            'border': 1
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            column_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, column_len)

        worksheet.freeze_panes(1, 0)
    output.seek(0)
    return output

# Fonction de conversion d'une pause (hh:mm ou h.mm) en décimal
def convert_pause_to_decimal(pause_str):
    try:
        if ":" in pause_str:
            h, m = map(int, pause_str.split(":"))
            return h + m / 60
        else:
            return float(pause_str)
    except Exception:
        return 0.0

st.set_page_config(page_title="Calculateur de salaire Manpower", layout="wide")

# Initialisation des états
if "missions" not in st.session_state:
    st.session_state.missions = []
if "tarifs_par_nom" not in st.session_state:
    st.session_state.tarifs_par_nom = {}

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

# Interface utilisateur
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Calculateur de salaire")
    numero_mission = st.text_input("Numéro de mission", key="mission")
    nom = st.text_input("Nom du collaborateur", key="nom")
    tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05, key="tarif")
    date = st.date_input("Date de la mission", key="date")
    heure_debut = st.time_input("Heure de début", key="debut")
    heure_fin = st.time_input("Heure de fin", key="fin")
    pause_str = st.text_input("Durée de la pause (hh:mm ou h.mm)", value="0:00", key="pause")

    if nom in st.session_state.tarifs_par_nom and not tarif_horaire:
        tarif_horaire = st.session_state.tarifs_par_nom[nom]

    if st.button("Ajouter la mission"):
        pause_decimal = convert_pause_to_decimal(pause_str)
        result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause_decimal, numero_mission)
        st.session_state.missions.append(result)
        st.session_state.tarifs_par_nom[nom] = tarif_horaire
        st.experimental_rerun()

    if st.button("Vider le formulaire"):
        st.session_state.mission = ""
        st.session_state.nom = ""
        st.session_state.tarif = 0.0
        st.session_state.pause = "0:00"
        st.experimental_rerun()

if st.session_state.missions:
    last = st.session_state.missions[-1]
    with col2:
        try:
            st.markdown("""
                <div class='recap-box'>
                <strong>Résumé :</strong><br>
                - Mission : {Mission}<br>
                - Date : {Date}<br>
                - Heure de début : {Heure de début} — Heure de fin : {Heure de fin}<br>
                - Nom : {Nom}<br>
                - Tarif horaire : CHF {Tarif horaire}<br>
                - Heures brutes : {Heures totales} h<br>
                - Pause : {Pause (h)}<br>
                - Heures totales : {Heures totales (hh:mm)}<br>
                - Salaire de base : CHF {Salaire de base}<br>
                - Majoration 25% (heure sup) : CHF {Majoration 25% (heure sup)}<br>
                - Heures sup : {Heures sup (hh:mm)}<br>
                - Heures samedi : {Heures samedi (hh:mm)}<br>
                - Heures dimanche : {Heures dimanche (hh:mm)}<br>
                - Heures de nuit : {Heures de nuit (hh:mm)}<br>
                - Majoration heures sup : CHF {Majoration heures sup}<br>
                - Majoration samedi : CHF {Majoration samedi}<br>
                - Majoration dimanche : CHF {Majoration dimanche}<br>
                - Majoration nuit : CHF {Majoration nuit}<br>
                - <strong>Salaire brut : CHF {Salaire total brut}</strong>
                </div>
            """.format(**last), unsafe_allow_html=True)
        except KeyError as e:
            st.error(f"Clé manquante dans les données du résumé : {e}")

    st.subheader("Tableau des missions")
    df_result = pd.DataFrame(st.session_state.missions)
    st.dataframe(df_result, use_container_width=True, height=250)

    excel_data = generate_excel(df_result)
    st.download_button("📥 Télécharger en Excel", data=excel_data, file_name="missions_manpower.xlsx")

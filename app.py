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

    if heures_dimanche > 0 or heures_nuit > 0 or heures_samedi > 0:
        heures_sup = 0

    salaire_base = round(total_heures * tarif_horaire, 2)
    maj_sup = round(heures_sup * maj_25_taux, 2)
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

st.title("Calculateur de salaire Manpower")

col_form, col_recap = st.columns([1, 1])

with col_form:
    with st.form("salaire_form"):
        nom = st.text_input("Nom du collaborateur", key="nom")
        numero_mission = st.text_input("Numéro de mission", key="mission")
        date = st.date_input("Date de la mission", key="date")
        tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05,
            value=st.session_state.tarifs_par_nom.get(nom, 0.0), key="tarif")
        heure_debut = st.time_input("Heure de début", time(8, 0), key="debut")
        heure_fin = st.time_input("Heure de fin", time(17, 0), key="fin")
        pause_str = st.text_input("Pause (hh:mm ou décimal)", value="0:00", key="pause")
        col_submit, col_reset = st.columns([1, 1])
        with col_submit:
            submit = st.form_submit_button("Ajouter")
        with col_reset:
            reset = st.form_submit_button("Vider le formulaire")

if reset:
    for key in ["nom", "mission", "date", "tarif", "debut", "fin", "pause"]:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

if submit:
    pause = convert_pause_to_decimal(st.session_state.pause)
    result = calcul_salaire(
        st.session_state.nom, st.session_state.date, st.session_state.tarif,
        st.session_state.debut.strftime("%H:%M"), st.session_state.fin.strftime("%H:%M"),
        pause, st.session_state.mission
    )
    st.session_state.missions.append(result)
    st.session_state.tarifs_par_nom[st.session_state.nom] = st.session_state.tarif

if st.session_state.missions:
    df_all = pd.DataFrame(st.session_state.missions)

    with col_recap:
        dernier = st.session_state.missions[-1]
        recap_html = f"""
        <div class='recap-box'>
        <b>Résumé :</b><br>
        Mission : {dernier['Mission']} — Date : {dernier['Date']} — Heure de début : {dernier['Heure de début']} — Heure de fin : {dernier['Heure de fin']}<br>
        Nom : {dernier['Nom']} — Tarif horaire : {dernier['Tarif horaire']} CHF — Pause : {dernier['Pause (h)']} h<br>
        Heures totales : {dernier['Heures totales (hh:mm)']} (soit {dernier['Heures totales']} h)<br>
        Salaire de base : {dernier['Salaire de base']} CHF<br>
        Majoration 25% (heure sup) : {dernier['Majoration 25% (heure sup)']} CHF — Heures sup : {dernier['Heures sup (hh:mm)']}<br>
        Heures samedi : {dernier['Heures samedi (hh:mm)']} — Majoration samedi : {dernier['Majoration samedi']} CHF<br>
        Heures dimanche : {dernier['Heures dimanche (hh:mm)']} — Majoration dimanche : {dernier['Majoration dimanche']} CHF<br>
        Heures de nuit : {dernier['Heures de nuit (hh:mm)']} — Majoration nuit : {dernier['Majoration nuit']} CHF<br>
        <b>Salaire total brut : {dernier['Salaire total brut']} CHF</b>
        </div>
        """
        st.markdown(recap_html, unsafe_allow_html=True)

    st.dataframe(df_all, use_container_width=False, height=300, width=800)

    for i in range(len(st.session_state.missions)):
        col1, col2 = st.columns([10, 1])
        with col1:
            st.write(f"Ligne {i+1} – {st.session_state.missions[i]['Nom']} – {st.session_state.missions[i]['Date']}")
        with col2:
            if st.button("❌", key=f"suppr_{i}"):
                st.session_state.missions.pop(i)
                st.experimental_rerun()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_all.to_excel(writer, index=False, sheet_name="Salaires")
        worksheet = writer.sheets["Salaires"]
        for idx, col in enumerate(df_all.columns):
            worksheet.set_column(idx, idx, max(15, len(col) + 2))

    st.download_button(
        label="📥 Télécharger toutes les missions en Excel",
        data=buffer.getvalue(),
        file_name="toutes_les_missions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

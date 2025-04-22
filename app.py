import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date as date_class
import io

st.set_page_config(page_title="Calculateur de salaire Manpower", layout="wide")

@st.cache_data
def init_data():
    return []

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

    heures_nuit = heures_dimanche = heures_samedi = heures_sup = heures_normales = 0.0
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

    if heures_nuit > 0 or heures_samedi > 0 or heures_dimanche > 0:
        heures_sup = 0.0

    salaire_base = round(total_heures * tarif_horaire, 2)
    maj_sup = round(heures_sup * tarif_horaire * 0.25, 2)
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
        "Pause (h)": round(pause, 2),
        "Heures totales": round(total_heures, 2),
        "Heures totales (hh:mm)": format_minutes(total_heures),
        "Salaire de base": salaire_base,
        "Majoration 25% (heure sup)": round(tarif_horaire * 0.25, 2),
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

if 'historique' not in st.session_state:
    st.session_state.historique = []

with st.form("salaire_form"):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nom du collaborateur")
        numero_mission = st.text_input("Numéro de mission")
        date = st.date_input("Date de la mission")
        tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05)
    with col2:
        heure_debut = st.time_input("Heure de début", time(8, 0))
        heure_fin = st.time_input("Heure de fin", time(17, 0))
        pause_str = st.text_input("Pause (hh:mm ou décimal)", value="0:00")
    submit = st.form_submit_button("Calculer")

if submit:
    pause = convert_pause_to_decimal(pause_str)
    result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause, numero_mission)
    st.session_state.historique.append(result)

    st.markdown(
        f"""
        <div style='background-color:#ffe6e6; padding:10px; border-radius:10px; font-size:16px;'>
        <b>Résumé :</b><br>
        Mission : {result['Mission']} — Date : {result['Date']} — Heure de début : {result['Heure de début']} — Heure de fin : {result['Heure de fin']}<br>
        Nom : {result['Nom']} — Tarif horaire : {result['Tarif horaire']} CHF — Pause : {result['Pause (h)']} h<br>
        Heures totales : {result['Heures totales (hh:mm)']} (soit {result['Heures totales']:.2f} h)<br>
        Salaire de base : {result['Salaire de base']:.2f} CHF<br>
        Majoration 25% (heure sup) : {result['Majoration 25% (heure sup)']:.2f} CHF — Heures sup : {result['Heures sup (hh:mm)']}<br>
        Heures samedi : {result['Heures samedi (hh:mm)']} — Majoration samedi : {result['Majoration samedi']:.2f} CHF<br>
        Heures dimanche : {result['Heures dimanche (hh:mm)']} — Majoration dimanche : {result['Majoration dimanche']:.2f} CHF<br>
        Heures de nuit : {result['Heures de nuit (hh:mm)']} — Majoration nuit : {result['Majoration nuit']:.2f} CHF<br>
        <b>Total brut : {result['Salaire total brut']:.2f} CHF</b>
        </div>
        """,
        unsafe_allow_html=True
    )

if st.session_state.historique:
    st.subheader("Historique des missions")
    df_historique = pd.DataFrame(st.session_state.historique)
    lignes_a_supprimer = st.multiselect("Sélectionner les lignes à supprimer", df_historique.index.tolist())

    if st.button("Supprimer les lignes sélectionnées"):
        st.session_state.historique = [ligne for idx, ligne in enumerate(st.session_state.historique) if idx not in lignes_a_supprimer]
        st.experimental_rerun()

    st.dataframe(df_historique, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_historique.to_excel(writer, index=False, sheet_name="Historique")
        worksheet = writer.sheets["Historique"]
        for idx, col in enumerate(df_historique.columns):
            worksheet.set_column(idx, idx, max(15, len(col) + 2))

    st.download_button(
        label="📥 Télécharger l'historique en Excel",
        data=buffer.getvalue(),
        file_name="historique_salaire.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

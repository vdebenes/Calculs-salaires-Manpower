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

        taux_majorations = {
            "nuit": 8.40 if is_nuit else 0,
            "dimanche": 4.80 if is_dimanche else 0,
            "samedi": 2.40 if is_samedi else 0,
            "sup": tarif_horaire * 0.25 if minute_in_hour >= 9.5 else 0
        }

        max_cat = max(taux_majorations, key=taux_majorations.get)

        if taux_majorations[max_cat] == 0:
            heures_normales += 1 / 60
        elif max_cat == "nuit":
            heures_nuit += 1 / 60
        elif max_cat == "dimanche":
            heures_dimanche += 1 / 60
        elif max_cat == "samedi":
            heures_samedi += 1 / 60
        elif max_cat == "sup":
            heures_sup += 1 / 60

        current += timedelta(minutes=1)
        minute_count += 1

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

# Interface utilisateur
st.title("Calculateur de salaire Manpower")

if "data" not in st.session_state:
    st.session_state.data = []

col1, col2 = st.columns([2, 3])

with col1:
    with st.form("formulaire"):
        numero_mission = st.text_input("Numéro de mission")
        nom = st.text_input("Nom")
        tarif_horaire = st.number_input("Tarif horaire", min_value=0.0, step=0.05)
        date = st.date_input("Date")
        heure_debut = st.time_input("Heure de début", value=time(8, 0))
        heure_fin = st.time_input("Heure de fin", value=time(17, 0))
        pause_str = st.text_input("Pause (hh:mm ou décimal)", value="0:00")

        col_gauche, col_droite = st.columns([1, 1])
        with col_gauche:
            submit = st.form_submit_button("Calculer salaire")
        with col_droite:
            if st.form_submit_button("Vider le formulaire"):
                st.experimental_rerun()

with col2:
    if st.session_state.data:
        dernier = st.session_state.data[-1]
        st.markdown(
            f"""
            <div style='background-color:#ffe6e6; padding:10px; border-radius:10px; font-size:16px;'>
            <b>Mission :</b> {dernier['Mission']} — <b>Date :</b> {dernier['Date']} — <b>Heure de début :</b> {dernier['Heure de début']} — <b>Heure de fin :</b> {dernier['Heure de fin']}<br>
            <b>Nom :</b> {dernier['Nom']} — <b>Tarif horaire :</b> CHF {dernier['Tarif horaire']} — <b>Pause :</b> {dernier['Pause (h)']} h<br>
            <b>Heures totales :</b> {dernier['Heures totales (hh:mm)']} (soit {dernier['Heures totales']:.2f} h)<br>
            <b>Salaire de base :</b> CHF {dernier['Salaire de base']:.2f}<br>
            <b>Majoration 25% (heure sup) :</b> CHF {dernier['Majoration heures sup']:.2f} — <b>Heures sup :</b> {dernier['Heures sup (hh:mm)']}<br>
            <b>Heures samedi :</b> {dernier['Heures samedi (hh:mm)']} — <b>Majoration samedi :</b> CHF {dernier['Majoration samedi']:.2f}<br>
            <b>Heures dimanche :</b> {dernier['Heures dimanche (hh:mm)']} — <b>Majoration dimanche :</b> CHF {dernier['Majoration dimanche']:.2f}<br>
            <b>Heures de nuit :</b> {dernier['Heures de nuit (hh:mm)']} — <b>Majoration nuit :</b> CHF {dernier['Majoration nuit']:.2f}<br>
            <b>Total brut :</b> <b>CHF {dernier['Salaire total brut']:.2f}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

if submit:
    pause = convert_pause_to_decimal(pause_str)
    result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause, numero_mission)
    st.session_state.data.append(result)

if st.session_state.data:
    df_result = pd.DataFrame(st.session_state.data)
    for i, row in df_result.iterrows():
        delete = st.button(f"Supprimer la ligne {i+1}", key=f"delete_{i}")
        if delete:
            st.session_state.data.pop(i)
            st.experimental_rerun()

    st.dataframe(df_result, use_container_width=True, height=250)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name="Salaire")
        worksheet = writer.sheets["Salaire"]
        for idx, col in enumerate(df_result.columns):
            worksheet.set_column(idx, idx, max(15, len(col) + 2))

    st.download_button(
        label="📅 Télécharger le tableau Excel",
        data=buffer.getvalue(),
        file_name="salaire_calculé.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

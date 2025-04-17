import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
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

    heures_sup = max(0, total_heures - 9.5)
    heures_sup_minutes = round(heures_sup * 60)
    heures_sup_format = f"{heures_sup_minutes // 60}:{heures_sup_minutes % 60:02d}"

    heures_nuit = 0.0
    current = heure_debut
    while current < heure_fin:
        h = current.time()
        if h >= time(23, 0) or h < time(6, 0):
            heures_nuit += 1 / 60
        current += timedelta(minutes=1)

    jour_en = pd.Timestamp(date).day_name().lower()
    jours_fr = {
        "monday": "Lundi",
        "tuesday": "Mardi",
        "wednesday": "Mercredi",
        "thursday": "Jeudi",
        "friday": "Vendredi",
        "saturday": "Samedi",
        "sunday": "Dimanche"
    }
    jour_semaine = jours_fr.get(jour_en, jour_en.capitalize())

    salaire_base = round(total_heures * tarif_horaire, 2)
    maj_25_taux = round(tarif_horaire * 0.25, 2)
    maj_sup = round((heures_sup_minutes / 60) * maj_25_taux, 2)
    heures_dimanche = total_heures if jour_semaine == "Dimanche" else 0.0
    heures_samedi = total_heures if jour_semaine == "Samedi" else 0.0
    maj_dimanche = round(4.80 * heures_dimanche, 2)
    maj_samedi = round(2.40 * heures_samedi, 2)
    maj_nuit = round(8.40 * heures_nuit, 2)
    total_brut = round(salaire_base + maj_sup + maj_dimanche + maj_samedi + maj_nuit, 2)

    return {
        "Mission": numero_mission,
        "Nom": nom,
        "Date": date,
        "Heure de début": heure_debut.strftime("%H:%M"),
        "Heure de fin": heure_fin.strftime("%H:%M"),
        "Tarif horaire": tarif_horaire,
        "Pause (h)": round(pause, 2),
        "Heures totales": round(total_heures, 2),
        "Heures totales (hh:mm)": format_minutes(total_heures),
        "Salaire de base": salaire_base,
        "Majoration 25% (heure sup)": maj_25_taux,
        "Heures sup (hh:mm)": heures_sup_format,
        "Heures samedi (hh:mm)": format_minutes(heures_samedi),
        "Heures dimanche (hh:mm)": format_minutes(heures_dimanche),
        "Heures de nuit (hh:mm)": format_minutes(heures_nuit),
        "Majoration heures sup": maj_sup,
        "Majoration samedi": maj_samedi,
        "Majoration dimanche": maj_dimanche,
        "Majoration nuit": maj_nuit,
        "Salaire total brut": total_brut
    }

st.title("🗞 Calculateur de salaire Manpower")
data = st.session_state.get("data", init_data())

with st.form("formulaire"):
    col1, col2, col3 = st.columns(3)
    with col1:
        numero_mission = st.text_input("Numéro de mission")
        nom = st.text_input("Nom")
        date = st.date_input("Date")
    with col2:
        tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.01)
        pause_str = st.text_input("Pause (hh:mm ou h)", value="0:00")
    with col3:
        heure_debut = st.time_input("Heure de début")
        heure_fin = st.time_input("Heure de fin")

    submitted = st.form_submit_button("Ajouter")
    if submitted:
        pause = convert_pause_to_decimal(pause_str)
        result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause, numero_mission)
        data.append(result)
        st.session_state["data"] = data

        st.markdown(f"""
            <div style='background-color:#ffe6e6;padding:10px;border-radius:5px;'>
            <strong>Résumé :</strong><br>
            - Mission : <strong>{result['Mission']}</strong><br>
            - Date : <strong>{result['Date']}</strong><br>
            - Heure de début : <strong>{result['Heure de début']}</strong> — Heure de fin : <strong>{result['Heure de fin']}</strong><br>
            - Nom : <strong>{result['Nom']}</strong><br>
            - Tarif horaire : <strong>CHF {result['Tarif horaire']:.2f}</strong><br>
            - Heures brutes : <strong>{result['Heures totales'] + result['Pause (h)']:.2f} h</strong><br>
            - Pause : <strong>{result['Pause (h)']:.2f} h</strong><br>
            - Heures totales : <strong>{result['Heures totales (hh:mm)']} (soit {result['Heures totales']:.2f} h)</strong><br>
            - Salaire de base : <strong>CHF {result['Salaire de base']:.2f}</strong><br>
            - Majoration 25% (heure sup) : <strong>CHF {result['Majoration 25% (heure sup)']:.2f} / h</strong><br>
            - Heures sup : <strong>{result['Heures sup (hh:mm)']}</strong><br>
            - Heures samedi : <strong>{result['Heures samedi (hh:mm)']}</strong><br>
            - Heures dimanche : <strong>{result['Heures dimanche (hh:mm)']}</strong><br>
            - Heures de nuit : <strong>{result['Heures de nuit (hh:mm)']}</strong><br>
            - Majoration heures sup : <strong>CHF {result['Majoration heures sup']:.2f}</strong><br>
            - Majoration samedi : <strong>CHF {result['Majoration samedi']:.2f}</strong><br>
            - Majoration dimanche : <strong>CHF {result['Majoration dimanche']:.2f}</strong><br>
            - Majoration nuit : <strong>CHF {result['Majoration nuit']:.2f}</strong><br>
            - Salaire brut : <strong>CHF {result['Salaire total brut']:.2f}</strong>
            </div>
        """, unsafe_allow_html=True)

if data:
    df_result = pd.DataFrame(data)[[
        "Mission", "Nom", "Date", "Heure de début", "Heure de fin", "Tarif horaire",
        "Pause (h)", "Heures totales", "Heures totales (hh:mm)", "Salaire de base",
        "Majoration 25% (heure sup)", "Heures sup (hh:mm)", "Heures samedi (hh:mm)",
        "Heures dimanche (hh:mm)", "Heures de nuit (hh:mm)", "Majoration heures sup",
        "Majoration samedi", "Majoration dimanche", "Majoration nuit", "Salaire total brut"
    ]]
    st.dataframe(df_result, use_container_width=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name='Salaires')
        workbook = writer.book
        worksheet = writer.sheets['Salaires']
        for i, col in enumerate(df_result.columns):
            column_len = max(df_result[col].astype(str).map(len).max(), len(col)) + 1
            worksheet.set_column(i, i, column_len)
        worksheet.freeze_panes(1, 0)

    st.download_button(
        label="📅 Télécharger le tableau en Excel",
        data=output.getvalue(),
        file_name='salaires_manpower.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.info("Aucune donnée enregistrée.")

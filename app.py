import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import io
from fpdf import FPDF

st.set_page_config(page_title="Calculateur de salaire Manpower", layout="wide")

@st.cache_data
def init_data():
    return []

def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin, pause):
    heure_debut = datetime.strptime(heure_debut, "%H:%M")
    heure_fin = datetime.strptime(heure_fin, "%H:%M")
    if heure_fin <= heure_debut:
        heure_fin += timedelta(days=1)
    heures_brutes = (heure_fin - heure_debut).total_seconds() / 3600
    total_heures = heures_brutes - pause
    heures_sup = max(0, total_heures - 9.5)
    minutes_sup = round(heures_sup * 60)

    heures_nuit = 0.0
    current = heure_debut
    while current < heure_fin:
        if current.time() >= time(23, 0) or current.time() < time(6, 0):
            next_point = min(heure_fin, datetime.combine(current.date(), time(6, 0)) if current.time() < time(6, 0) else current + timedelta(minutes=1))
            heures_nuit += (min(next_point, heure_fin) - current).total_seconds() / 3600
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
    maj_sup = round(heures_sup * tarif_horaire * 0.25, 2)
    maj_dimanche = round(4.80 * total_heures, 2) if jour_semaine == "Dimanche" else 0
    maj_samedi = round(2.40 * total_heures, 2) if jour_semaine == "Samedi" else 0
    maj_nuit = round(8.40 * heures_nuit, 2) if heures_nuit > 0 else 0
    total_brut = round(salaire_base + maj_sup + maj_dimanche + maj_samedi + maj_nuit, 2)

    heures_arrondies = int(total_heures)
    minutes = int((total_heures - heures_arrondies) * 60)
    if minutes >= 30:
        total_heures_arrondies = heures_arrondies + 0.5
    else:
        total_heures_arrondies = heures_arrondies

    return {
        "Nom": nom,
        "Tarif horaire": tarif_horaire,
        "Date": date,
        "Jour": jour_semaine,
        "Heure de début": heure_debut.strftime("%H:%M"),
        "Heure de fin": heure_fin.strftime("%H:%M"),
        "Pause (h)": pause,
        "Heures brutes": round(heures_brutes, 2),
        "Heures totales": round(total_heures, 2),
        "Heures totales arrondies": round(total_heures_arrondies, 2),
        "Heures de nuit": round(heures_nuit, 2),
        "Majoration nuit": maj_nuit,
        "Heures sup (>9h30)": f"{int(heures_sup)}:{int((heures_sup % 1)*60):02d}",
        "Majoration 25%": round(tarif_horaire * 0.25, 2),
        "Majoration heures sup": maj_sup,
        "Majoration samedi": maj_samedi,
        "Majoration dimanche": maj_dimanche,
        "Salaire de base": salaire_base,
        "Salaire total brut": total_brut
    }

st.title("🗞 Calculateur de salaire Manpower")
data = st.session_state.get("data", init_data())

with st.form("formulaire"):
    col1, col2, col3 = st.columns(3)
    with col1:
        nom = st.text_input("Nom")
        date = st.date_input("Date")
    with col2:
        tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.01)
        pause = st.number_input("Pause (h)", min_value=0.0, step=0.05)
    with col3:
        heure_debut = st.time_input("Heure de début")
        heure_fin = st.time_input("Heure de fin")

    submitted = st.form_submit_button("Ajouter")
    if submitted:
        result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause)
        data.append(result)
        st.session_state["data"] = data

        st.markdown("""
            <div style='background-color:#ffe6e6;padding:10px;border-radius:5px;'>
            <strong>Résumé :</strong><br>
            - Heures brutes : <strong>{:.2f} h</strong><br>
            - Pause : <strong>{:.1f} h</strong><br>
            - Heures totales : <strong>{:.2f} h</strong><br>
            - Salaire brut : <strong>CHF {:.2f}</strong><br>
            - Majoration 25% (heure sup) : <strong>CHF {:.2f} / h</strong><br>
            - Heures sup : <strong>{}</strong><br>
            - Heures dimanche : <strong>{:.2f} h</strong><br>
            - Heures samedi : <strong>{:.2f} h</strong>
            </div>
        """.format(
            result["Heures brutes"],
            result["Pause (h)"],
            result["Heures totales"],
            result["Salaire total brut"],
            result["Majoration 25%"],
            result["Heures sup (>9h30)"],
            result["Heures totales"] if result["Jour"] == "Dimanche" else 0.0,
            result["Heures totales"] if result["Jour"] == "Samedi" else 0.0
        ), unsafe_allow_html=True)

if data:
    df_result = pd.DataFrame(data)[[
        "Nom", "Tarif horaire", "Date",
        "Heures totales", "Heures totales arrondies",
        "Heure de début", "Heure de fin", "Pause (h)", "Jour",
        "Heures sup (>9h30)", "Majoration 25%", "Majoration heures sup",
        "Heures de nuit", "Majoration nuit",
        "Majoration samedi", "Majoration dimanche",
        "Salaire de base", "Salaire total brut"
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

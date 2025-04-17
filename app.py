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
        "monday": "Lundi",
        "tuesday": "Mardi",
        "wednesday": "Mercredi",
        "thursday": "Jeudi",
        "friday": "Vendredi",
        "saturday": "Samedi",
        "sunday": "Dimanche"
    }
    jour_semaine = jours_fr.get(jour_en, jour_en.capitalize())

    # Liste des jours fériés 2025 assimilés au dimanche
    jours_feries = {
        date_class(2025, 1, 1),   # Nouvel An
        date_class(2025, 4, 18),  # Vendredi Saint
        date_class(2025, 4, 21),  # Lundi de Pâques
        date_class(2025, 5, 29),  # Ascension
        date_class(2025, 6, 9),   # Lundi de Pentecôte
        date_class(2025, 8, 1),   # Fête nationale
        date_class(2025, 9, 22),  # Lundi du Jeûne
        date_class(2025, 12, 25)  # Noël
    }

    is_jour_ferie = date in jours_feries

    heures_nuit = 0.0
    heures_dimanche = 0.0
    heures_samedi = 0.0
    heures_normales = 0.0
    heures_sup = 0.0
    current = heure_debut
    minutes_total = 0

    while current < heure_fin:
        h = current.time()
        is_nuit = h >= time(23, 0) or h < time(6, 0)
        is_dimanche = jour_semaine == "Dimanche" or is_jour_ferie
        is_samedi = jour_semaine == "Samedi"

        minute_in_hour = minutes_total / 60

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
        minutes_total += 1

    salaire_base = round(total_heures * tarif_horaire, 2)
    maj_25_taux = round(tarif_horaire * 0.25, 2)
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
        "Pause (h)": round(pause, 2),
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

# Interface utilisateur
st.title("Calculateur de salaire Manpower")

with st.form("salaire_form"):
    nom = st.text_input("Nom du collaborateur")
    numero_mission = st.text_input("Numéro de mission")
    date = st.date_input("Date de la mission")
    tarif_horaire = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05)
    heure_debut = st.time_input("Heure de début", time(8, 0))
    heure_fin = st.time_input("Heure de fin", time(17, 0))
    pause_str = st.text_input("Pause (hh:mm ou décimal)", value="0:00")
    submit = st.form_submit_button("Calculer")

if submit:
    pause = convert_pause_to_decimal(pause_str)
    result = calcul_salaire(nom, date, tarif_horaire, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause, numero_mission)

    st.success("Calcul effectué !")
    
    with st.expander("Résumé des calculs", expanded=True):
        for k, v in result.items():
            if isinstance(v, float):
                if "CHF" not in k and not k.startswith("Heures"):
                    st.write(f"**{k}** : {v:.2f} CHF")
                else:
                    st.write(f"**{k}** : {v}")
            else:
                st.write(f"**{k}** : {v}")

    df_result = pd.DataFrame([result])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_result.to_excel(writer, index=False, sheet_name="Salaire")
        worksheet = writer.sheets["Salaire"]
        for idx, col in enumerate(df_result.columns):
            worksheet.set_column(idx, idx, max(15, len(col) + 2))
    
    st.download_button(
        label="📥 Télécharger le résultat en Excel",
        data=buffer.getvalue(),
        file_name="salaire_calculé.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

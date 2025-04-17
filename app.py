import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date as date_class
import io

# Fonction de calcul de salaire

def calcul_salaire(nom, date, tarif_horaire, heure_debut_str, heure_fin_str, pause_decimal, numero_mission):
    heure_debut = datetime.strptime(heure_debut_str, "%H:%M")
    heure_fin = datetime.strptime(heure_fin_str, "%H:%M")
    if heure_fin <= heure_debut:
        heure_fin += timedelta(days=1)

    total_minutes = (heure_fin - heure_debut).total_seconds() / 60
    total_minutes_travaillees = total_minutes - pause_decimal * 60
    heures_totales = round(total_minutes_travaillees / 60, 2)
    heures_totales_hhmm = f"{int(total_minutes_travaillees // 60)}:{int(total_minutes_travaillees % 60):02d}"

    heure_0930 = heure_debut + timedelta(hours=9, minutes=30)
    heure_sup_minutes = max((heure_fin - max(heure_0930, heure_debut)).total_seconds() / 60 - pause_decimal * 60, 0)

    jour = pd.Timestamp(date).day_name().lower()
    jours_feries = [
        date_class(2025, 1, 1), date_class(2025, 4, 18), date_class(2025, 4, 21),
        date_class(2025, 5, 29), date_class(2025, 6, 9), date_class(2025, 8, 1),
        date_class(2025, 9, 22), date_class(2025, 12, 25)
    ]

    def intervalle_commun(h1, h2, d1, d2):
        latest_start = max(h1, d1)
        earliest_end = min(h2, d2)
        delta = (earliest_end - latest_start).total_seconds() / 60
        return max(delta, 0)

    heure_23 = heure_debut.replace(hour=23, minute=0)
    heure_6 = heure_debut.replace(hour=6, minute=0)
    if heure_6 <= heure_debut:
        heure_6 += timedelta(days=1)
    if heure_23 <= heure_debut:
        heure_23 += timedelta(days=1)

    minutes_nuit = intervalle_commun(heure_debut, heure_fin, heure_23, heure_6)
    heures_nuit = minutes_nuit / 60

    is_samedi = jour == "saturday"
    is_dimanche = jour == "sunday" or pd.to_datetime(date).date() in jours_feries

    minutes_samedi = total_minutes_travaillees if is_samedi else 0
    minutes_dimanche = total_minutes_travaillees if is_dimanche else 0

    maj_dimanche = 4.80 * (minutes_dimanche / 60)
    maj_samedi = 2.40 * (minutes_samedi / 60)
    maj_nuit = 8.40 * heures_nuit

    maj_hsup = 0
    heures_supplementaires = 0
    maj_25 = 0
    heures_sup_hhmm = "0:00"

    if not is_samedi and not is_dimanche:
        heures_supplementaires = heure_sup_minutes / 60
        maj_25 = round(tarif_horaire * 0.25, 2)
        maj_hsup = maj_25 * heures_supplementaires
        heures_sup_hhmm = f"{int(heure_sup_minutes // 60)}:{int(heure_sup_minutes % 60):02d}"

    salaire_base = round(heures_totales * tarif_horaire, 2)
    salaire_total = round(salaire_base + maj_dimanche + maj_samedi + maj_nuit + maj_hsup, 2)

    return {
        "Nom": nom,
        "Tarif horaire": round(tarif_horaire, 2),
        "Date": date,
        "Heures brutes": round(total_minutes / 60, 2),
        "Pause (h)": pause_decimal,
        "Jour": jour.capitalize(),
        "Heures totales": heures_totales,
        "Heures totales (hh:mm)": heures_totales_hhmm,
        "Heure de début": heure_debut_str,
        "Heure de fin": heure_fin_str,
        "Mission": numero_mission,
        "Heures sup (>9h30)": round(heures_supplementaires, 2),
        "Majoration 25% (heure sup)": maj_25,
        "Majoration heures sup": round(maj_hsup, 2),
        "Heures sup (hh:mm)": heures_sup_hhmm,
        "Heures samedi (hh:mm)": f"{int(minutes_samedi // 60)}:{int(minutes_samedi % 60):02d}",
        "Heures dimanche (hh:mm)": f"{int(minutes_dimanche // 60)}:{int(minutes_dimanche % 60):02d}",
        "Heures de nuit (hh:mm)": f"{int(minutes_nuit // 60)}:{int(minutes_nuit % 60):02d}",
        "Majoration samedi": round(maj_samedi, 2),
        "Majoration dimanche": round(maj_dimanche, 2),
        "Majoration nuit": round(maj_nuit, 2),
        "Salaire de base": salaire_base,
        "Salaire total brut": salaire_total
    }

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
...

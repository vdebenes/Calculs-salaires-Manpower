import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import io
from fpdf import FPDF

st.title("Calculateur de salaire avec majorations")

# Initialiser une session pour stocker les résultats
import json
import os

TARIFS_FILE = "tarifs_par_nom.json"

# Charger les tarifs depuis un fichier s'ils existent
if os.path.exists(TARIFS_FILE):
    with open(TARIFS_FILE, "r") as f:
        st.session_state.tarifs_par_nom = json.load(f)
else:
    st.session_state.tarifs_par_nom = {}
if "tarifs_par_nom" not in st.session_state:
    st.session_state.tarifs_par_nom = {}
if "historique" not in st.session_state:
    st.session_state.historique = []

if "index_a_supprimer" not in st.session_state:
    st.session_state.index_a_supprimer = None

def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin, pause):
    fmt = "%H:%M"
    h_debut = datetime.strptime(heure_debut, fmt)
    h_fin = datetime.strptime(heure_fin, fmt)
    if h_fin <= h_debut:
        h_fin += timedelta(days=1)

    heures_brutes = (h_fin - h_debut).total_seconds() / 3600
    total_heures = heures_brutes - pause
    

    heure = h_debut
    heures_nuit = 0
    while heure < h_fin:
        if heure.time() >= datetime.strptime("23:00", fmt).time() or heure.time() < datetime.strptime("06:00", fmt).time():
            heures_nuit += 1
        heure += timedelta(hours=1)

    heures_sup = max(0, total_heures - 9.5)

    salaire_base = round(total_heures * tarif_horaire, 2)
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
    maj_dimanche = 4.80 * total_heures if jour_en == "sunday" else 0
    maj_samedi = 2.40 * total_heures if jour_en == "saturday" else 0
    maj_nuit = round(heures_nuit * 8.4, 2)
    maj_sup = round(heures_sup * tarif_horaire * 0.25, 2)
    total_brut = round(salaire_base + maj_dimanche + maj_samedi + maj_nuit + maj_sup, 2)
    majoration_ratio = round(total_brut / salaire_base, 3) if salaire_base > 0 else 1.0
    return {
        "Heure de début": heure_debut,
        "Heure de fin": heure_fin,
        "Heures brutes": round(heures_brutes, 2),
        "Pause (h)": pause,
        "Nom": nom,
        "Date": date,
        "Jour": jour_semaine,
        "Heures totales": round(total_heures, 2),
        "Heures de nuit": heures_nuit,
        "Heures sup (>9h30)": round(heures_sup, 2),
        "Majoration dimanche": round(maj_dimanche, 2),
        "Majoration samedi": round(maj_samedi, 2),
        "Majoration nuit": maj_nuit,
        "Majoration heures sup": maj_sup,
        "Salaire de base": salaire_base,
        "Salaire total brut": total_brut,
        "Tarif horaire": tarif_horaire,
        "Majoration 25%": round(tarif_horaire * 0.25, 2)
    }

with st.form("salaire_form"):
    nom = st.text_input("Nom du collaborateur")
    tarif_default = st.session_state.tarifs_par_nom.get(nom, 0.0)
    date = st.date_input("Date")
    tarif = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05, value=tarif_default)
    heure_debut = st.time_input("Heure de début")
    heure_fin = st.time_input("Heure de fin")
    pause_str = st.text_input("Durée de la pause (hh:mm)", help="Exemple : 0:30 pour 30 minutes, 2:10 pour 2h10")
    try:
        h, m = map(int, pause_str.split(":"))
        pause = h + m / 60
    except:
        pause = 0.0
    submitted = st.form_submit_button("Ajouter au tableau")

    if submitted:
        st.session_state.tarifs_par_nom[nom] = tarif
        with open(TARIFS_FILE, "w") as f:
            json.dump(st.session_state.tarifs_par_nom, f)
        result = calcul_salaire(nom, date, tarif, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"), pause)
        st.session_state.historique.append(result)
        st.success("Calcul ajouté au tableau !")
        # Affichage coloré selon le jour
        if result['Jour'].lower() == "dimanche":
            color = "#ffdddd"
        elif result['Jour'].lower() == "samedi":
            color = "#fff5cc"
        elif result['Heures de nuit'] > 0:
            color = "#ddeeff"
        else:
            color = "#f0f0f0"

        st.markdown(f"""
        <div style='background-color:{color};padding:15px;border-radius:10px'>
        <strong>Résumé :</strong><br>
        - Heures brutes : <strong>{result['Heures brutes']} h</strong><br>
        - Pause : <strong>{result['Pause (h)']} h</strong><br>
        - Heures totales : <strong>{result['Heures totales']} h</strong><br>
        - Salaire brut : <strong>CHF {result['Salaire total brut']}</strong><br>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.historique:
    df_result = pd.DataFrame(st.session_state.historique)

    if st.button("🧹 Réinitialiser les tarifs mémorisés"):
        st.session_state.tarifs_par_nom = {}
        if os.path.exists(TARIFS_FILE):
            os.remove(TARIFS_FILE)
        st.success("Les tarifs mémorisés ont été réinitialisés.")

    st.subheader("Filtrer l'historique")
    noms_disponibles = df_result["Nom"].unique()
    dates_disponibles = df_result["Date"].unique()

    nom_filtre = st.selectbox("Filtrer par nom", options=["Tous"] + list(noms_disponibles))
    date_filtre = st.selectbox("Filtrer par date", options=["Toutes"] + list(dates_disponibles))
    df_result["Date"] = pd.to_datetime(df_result["Date"])
    df_result["Date"] = df_result["Date"].dt.strftime("%d.%m.%Y")

    # Réorganiser les colonnes : Nom, Date en premier
    colonnes_ordre = ["Nom", "Date"] + [col for col in df_result.columns if col not in ["Nom", "Date"]]
    df_result = df_result[colonnes_ordre]

    df_filtré = df_result.copy()
    if nom_filtre != "Tous":
        df_filtré = df_filtré[df_filtré["Nom"] == nom_filtre]
    if date_filtre != "Toutes":
        df_filtré = df_filtré[df_filtré["Date"] == date_filtre]
    if nom_filtre != "Tous":
        df_filtré = df_filtré[df_filtré["Nom"] == nom_filtre]
    if date_filtre != "Toutes":
        df_filtré = df_filtré[df_filtré["Date"] == date_filtre]

    st.subheader("Historique des calculs")
    st.dataframe(df_filtré, use_container_width=True)

    # Modifier une ligne
    st.subheader("Modifier une ligne existante")
    if len(st.session_state.historique) > 0:
        index_to_edit = st.number_input("Numéro de ligne à modifier :", min_value=1, max_value=len(st.session_state.historique), step=1)
        selected_data = st.session_state.historique[index_to_edit - 1]

        new_tarif = st.number_input("Nouveau tarif horaire", value=selected_data["Tarif horaire"], step=0.05)
        new_date = st.date_input("Nouvelle date", value=pd.to_datetime(selected_data["Date"]))
        new_pause_str = st.text_input("Nouvelle pause (hh:mm)", value=f"{int(selected_data['Pause (h)'])}:{int(round((selected_data['Pause (h)']%1)*60))}")
        try:
            h, m = map(int, new_pause_str.split(":"))
            new_pause = h + m / 60
        except:
            new_pause = selected_data['Pause (h)']"], step=0.25)
        new_debut = st.time_input("Nouvelle heure de début", value=datetime.strptime(selected_data["Heure de début"], "%H:%M").time())
        new_fin = st.time_input("Nouvelle heure de fin", value=datetime.strptime(selected_data["Heure de fin"], "%H:%M").time())

        if st.button("Mettre à jour la ligne"):
            recalcul = calcul_salaire(
                selected_data["Nom"],
                pd.to_datetime(selected_data["Date"]),
                new_tarif,
                new_debut.strftime("%H:%M"),
                new_fin.strftime("%H:%M"),
                new_pause
            )
            st.session_state.historique[index_to_edit - 1] = recalcul
            st.success("Ligne mise à jour avec succès !")
            st.rerun()

    # Supprimer une ligne
    index_to_delete = st.number_input("Supprimer la ligne numéro :", min_value=1, max_value=len(df_result), step=1)
    if st.button("Supprimer"):
        del st.session_state.historique[index_to_delete - 1]
        st.rerun()

    # Vider tout l'historique
    if st.button("🗑️ Vider tout l'historique"):
        st.session_state.historique = []
        st.rerun()

    # Export Excel de l'historique filtré
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_filtré.to_excel(writer, index=False, sheet_name="Salaires")
        workbook = writer.book
        worksheet = writer.sheets["Salaires"]
        worksheet.freeze_panes(1, 0)

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'center',
            'align': 'center',
            'bg_color': '#dce6f1',
            'border': 1
        })

        for col_num, value in enumerate(df_filtré.columns):
            worksheet.write(0, col_num, value, header_format)
            max_len = max(df_filtré[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, max_len)

        for row_num, (_, row) in enumerate(df_filtré.iterrows(), start=1):
            cell_format = workbook.add_format({'bg_color': '#f9f9f9'} if row_num % 2 == 0 else {})
            for col_num, value in enumerate(row):
                worksheet.write(row_num, col_num, value, cell_format)
        
    buffer.seek(0)
    st.download_button(
        label="📥 Télécharger tout en Excel",
        data=buffer,
        file_name="salaires_historique.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

        # Export PDF de l'historique filtré (corrigé)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.set_fill_color(220, 230, 241)
    pdf.set_text_color(0)
    pdf.set_draw_color(200, 200, 200)

    # En-tête
    col_width = 190 / len(df_filtré.columns)
    pdf.set_font("Arial", style="B", size=10)
    for col in df_filtré.columns:
        pdf.cell(col_width, 8, str(col), border=1, align='C', fill=True)
    pdf.ln()

    # Lignes
    pdf.set_font("Arial", size=9)
    fill = False
    for _, row in df_filtré.iterrows():
        for value in row:
            pdf.cell(col_width, 8, str(value), border=1, align='C', fill=fill)
        pdf.ln()
        fill = not fill

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_buffer = io.BytesIO(pdf_bytes)

    st.download_button(
        label="📄 Télécharger tout en PDF",
        data=pdf_buffer,
        file_name="salaires_historique.pdf",
        mime="application/pdf"
    )

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import io
from fpdf import FPDF

st.title("Calculateur de salaire avec majorations")

# Initialiser une session pour stocker les résultats
if "historique" not in st.session_state:
    st.session_state.historique = []

if "index_a_supprimer" not in st.session_state:
    st.session_state.index_a_supprimer = None

def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin):
    fmt = "%H:%M"
    h_debut = datetime.strptime(heure_debut, fmt)
    h_fin = datetime.strptime(heure_fin, fmt)
    if h_fin <= h_debut:
        h_fin += timedelta(days=1)

    total_heures = (h_fin - h_debut).total_seconds() / 3600

    heure = h_debut
    heures_nuit = 0
    while heure < h_fin:
        if heure.time() >= datetime.strptime("23:00", fmt).time() or heure.time() < datetime.strptime("06:00", fmt).time():
            heures_nuit += 1
        heure += timedelta(hours=1)

    heures_sup = max(0, total_heures - 9.5)

    salaire_base = round(total_heures * tarif_horaire, 2)
    jour_semaine = pd.Timestamp(date).day_name().lower()
    maj_dimanche = 4.80 * total_heures if jour_semaine == "sunday" else 0
    maj_samedi = 2.40 * total_heures if jour_semaine == "saturday" else 0
    maj_nuit = round(heures_nuit * 8.4, 2)
    maj_sup = round(heures_sup * tarif_horaire * 0.25, 2)
    total_brut = round(salaire_base + maj_dimanche + maj_samedi + maj_nuit + maj_sup, 2)

    return {
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
        "Salaire total brut": total_brut
    }

with st.form("salaire_form"):
    nom = st.text_input("Nom du collaborateur")
    date = st.date_input("Date")
    tarif = st.number_input("Tarif horaire (CHF)", min_value=0.0, step=0.05)
    heure_debut = st.time_input("Heure de début")
    heure_fin = st.time_input("Heure de fin")
    submitted = st.form_submit_button("Ajouter au tableau")

    if submitted:
        result = calcul_salaire(nom, date, tarif, heure_debut.strftime("%H:%M"), heure_fin.strftime("%H:%M"))
        st.session_state.historique.append(result)
        st.success("Calcul ajouté au tableau !")

if st.session_state.historique:
    df_result = pd.DataFrame(st.session_state.historique)

    st.subheader("Filtrer l'historique")
    noms_disponibles = df_result["Nom"].unique()
    dates_disponibles = df_result["Date"].unique()

    nom_filtre = st.selectbox("Filtrer par nom", options=["Tous"] + list(noms_disponibles))
    date_filtre = st.selectbox("Filtrer par date", options=["Toutes"] + list(dates_disponibles))

    df_filtré = df_result.copy()
    if nom_filtre != "Tous":
        df_filtré = df_filtré[df_filtré["Nom"] == nom_filtre]
    if date_filtre != "Toutes":
        df_filtré = df_filtré[df_filtré["Date"] == date_filtre]

    st.subheader("Historique des calculs")
    st.dataframe(df_filtré, use_container_width=True)

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
    pdf.cell(200, 10, txt="Historique des calculs de salaire", ln=True, align="C")
    pdf.ln(5)
    for _, row in df_filtré.iterrows():
        for key, value in row.items():
            pdf.cell(200, 8, txt=f"{key}: {value}", ln=True)
        pdf.ln(4)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_buffer = io.BytesIO(pdf_bytes)

    st.download_button(
        label="📄 Télécharger tout en PDF",
        data=pdf_buffer,
        file_name="salaires_historique.pdf",
        mime="application/pdf"
    )

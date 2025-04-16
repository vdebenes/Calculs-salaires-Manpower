def calcul_salaire(nom, date, tarif_horaire, heure_debut, heure_fin, pause):
    heure_debut = datetime.strptime(heure_debut, "%H:%M")
    heure_fin = datetime.strptime(heure_fin, "%H:%M")
    if heure_fin <= heure_debut:
        heure_fin += timedelta(days=1)

    heures_brutes = (heure_fin - heure_debut).total_seconds() / 3600
    total_heures = heures_brutes - pause
    heures_sup = max(0, total_heures - 9.5)
    minutes_sup = round(heures_sup * 60)

    # Calcul des heures de nuit (entre 23h et 6h)
    heures_nuit = 0.0
    current = heure_debut
    while current < heure_fin:
        if current.time() >= time(23, 0) or current.time() < time(6, 0):
            next_point = min(
                heure_fin,
                datetime.combine(current.date(), time(6, 0))
                if current.time() < time(6, 0)
                else current + timedelta(minutes=1)
            )
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
    majoration_ratio = round(total_brut / salaire_base, 3) if salaire_base > 0 else 1.0

    heures_arrondies = int(total_heures)
    minutes = int((total_heures - heures_arrondies) * 60)
    if minutes >= 30:
        total_heures_arrondies = heures_arrondies + 0.5
    else:
        total_heures_arrondies = heures_arrondies

    return {
        "Heure de début": heure_debut.strftime("%H:%M"),
        "Heure de fin": heure_fin.strftime("%H:%M"),
        "Heures brutes": round(heures_brutes, 2),
        "Pause (h)": pause,
        "Nom": nom,
        "Date": date,
        "Jour": jour_semaine,
        "Heures totales": round(total_heures, 2),
        "Heures totales arrondies": round(total_heures_arrondies, 2),
        "Heures de nuit": round(heures_nuit, 2),
        "Heures sup (>9h30)": round(heures_sup, 4),
        "Minutes sup (>9h30)": minutes_sup,
        "Majoration dimanche": maj_dimanche,
        "Majoration samedi": maj_samedi,
        "Majoration nuit": maj_nuit,
        "Majoration heures sup": maj_sup,
        "Salaire de base": salaire_base,
        "Salaire total brut": total_brut,
        "Tarif horaire": tarif_horaire,
        "Majoration 25%": round(tarif_horaire * 0.25, 2)
    }

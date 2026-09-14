import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Funk Emotion 2.0 - Planning", page_icon="🎵", layout="wide")

# --- Optimisation de l'affichage (CSS compact mobile) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 250px !important;
    }
    .compact-box {
        padding: 5px;
        border-radius: 5px;
        border: 1px solid rgba(150, 150, 150, 0.2);
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Configuration et Mappage ---
MOIS_ONGLETS = {
    "2026-09": "Sept 26", "2026-10": "Oct 26", "2026-11": "Nov 26", "2026-12": "Dec 26",
    "2027-01": "Janv 27", "2027-02": "Fev 27", "2027-03": "Mars 27", "2027-04": "Avril 27",
    "2027-05": "Mai 27", "2027-06": "Juin 27", "2027-07": "Juillet 27", "2027-08": "Août 27",
    "2027-09": "Sept 27", "2027-10": "Oct 27", "2027-11": "Nov 27", "2027-12": "Dec 27"
}

MOIS_NOMS = {
    "2026-09": "Septembre 2026", "2026-10": "Octobre 2026", "2026-11": "Novembre 2026", "2026-12": "Décembre 2026",
    "2027-01": "Janvier 2027", "2027-02": "Février 2027", "2027-03": "Mars 2027", "2027-04": "Avril 2027",
    "2027-05": "Mai 2027", "2027-06": "Juin 2027", "2027-07": "Juillet 2027", "2027-08": "Août 2027",
    "2027-09": "Septembre 2027", "2027-10": "Octobre 2027", "2027-11": "Novembre 2027", "2027-12": "Décembre 2027"
}

COLONNES_MUSICIENS = {
    "&ric": 3, "Virginie": 4, "Sergio": 5, "Jean-Fi": 6, "Ben": 7, "Niko": 8,
    "Thom": 9, "Francis": 10, "Will": 11, "Alex": 12, "Ludo": 13, "Yayo": 14, "Yvan": 15
}

EMOJIS_MEMBRES = {
    "&ric": "🎤", "Virginie": "🎤", "Sergio": "🥁", "Jean-Fi": "🎸", "Ben": "🎸",
    "Will": "🎸", "Alex": "🎸", "Niko": "🎹", "Francis": "🎹",
    "Ludo": "🎛️🔊", "Yvan": "🎛️🔊", "Yayo": "🎛️🔊", "Thom": "🎛️🔊🎸🥁"
}

# --- Connexion Google Sheets ---
@st.cache_resource
def get_gsheets_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

# --- Fonction de Mise en Couleur (pour le récap global) ---
def coloriser_weekends(row):
    jour = str(row["Jour"]).strip().lower()
    if jour in ["vendredi", "samedi", "dimanche"]:
        return ["background-color: rgba(100, 150, 255, 0.15)"] * len(row)
    return [""] * len(row)

# --- UI : Barre latérale ---
st.sidebar.title("📅 Planning")
st.sidebar.image("funk_emotion_color_clean.png", use_container_width=True)
st.sidebar.header("👤 Qui es-tu ?")
nom_utilisateur = st.sidebar.selectbox("Sélectionne ton profil :", list(COLONNES_MUSICIENS.keys()))

if st.session_state.pop("succes_perso", False):
    st.success("🎉 Tes disponibilités ont été enregistrées avec succès !")
if st.session_state.pop("succes_evt", False):
    st.success("🎉 L'événement a bien été ajouté au planning général !")

# --- UI : Sélection du mois ---
emoji_membre = EMOJIS_MEMBRES.get(nom_utilisateur, "")
st.title(f"Salut {nom_utilisateur} ! {emoji_membre}")

mois_selectionne_nom = st.selectbox("📅 Choisir le mois :", list(MOIS_NOMS.values()))
cle_mois = [k for k, v in MOIS_NOMS.items() if v == mois_selectionne_nom][0]
nom_onglet = MOIS_ONGLETS[cle_mois]

# --- Récupération des données ---
try:
    client = get_gsheets_client()
    sheet = client.open_by_key("1V_0f_BDUJiaaV3Ps0bbyiOAX7MoPrNwWOyGIerdXiw4")
    worksheet = sheet.worksheet(nom_onglet)
    toutes_donnees = worksheet.get_all_values()
except Exception as e:
    st.error(f"Erreur de connexion au fichier : {e}")
    st.stop()

user_col_idx = COLONNES_MUSICIENS[nom_utilisateur] - 1
lignes_dates = {}
dispos_actuelles = {}
evenements_actuels = {}
recap_data_pour_tableau = []

for i in range(2, len(toutes_donnees)):
    row = toutes_donnees[i]
    if len(row) > 1 and row[1]: 
        date_str = row[1]
        jour_nom = row[0]
        
        jour_int = None
        if "-" in date_str: jour_int = int(date_str.split("-")[2][:2])
        elif "/" in date_str: jour_int = int(date_str.split("/")[0])
        
        if jour_int:
            lignes_dates[jour_int] = i + 1 
            
            val_dispo = row[user_col_idx].strip() if len(row) > user_col_idx else ""
            if val_dispo not in ["🟢", "🔴"]: val_dispo = "⚪"
            dispos_actuelles[jour_int] = val_dispo
            
            val_evt = row[16].strip() if len(row) > 16 else ""
            evenements_actuels[jour_int] = val_evt
            
            dict_recap = {
                "Jour_num": jour_int,
                "Jour": jour_nom,
                "Date": date_str,
                "Événement": val_evt
            }
            for membre in COLONNES_MUSICIENS.keys():
                col_i = COLONNES_MUSICIENS[membre] - 1
                dict_recap[membre] = row[col_i].strip() if len(row) > col_i else ""
            
            recap_data_pour_toucher = recap_data_pour_tableau.append(dict_recap)

# --- UI : Saisie Compacte par Lignes Synthétiques ---
st.divider()
st.subheader(f"🗓️ Tes dispos - {mois_selectionne_nom}")
st.caption("💡 Astuce : Modifie rapidement tes dispos ci-dessous (⚪ Neutre, 🟢 Dispo, 🔴 Indispo), puis clique sur Enregistrer.")

if "temp_dispos" not in st.session_state or st.session_state.get("dernier_mois") != mois_selectionne_nom:
    st.session_state["temp_dispos"] = dispos_actuelles.copy()
    st.session_state["dernier_mois"] = mois_selectionne_nom

# Affichage condensé sous forme de lignes épurées (Jour + Date + Sélecteur compact en face)
for jour_int, ligne_idx in sorted(lignes_dates.items()):
    info_ligne = next((item for item in recap_data_pour_tableau if item["Jour_num"] == jour_int), None)
    if info_ligne:
        c_jour = info_ligne["Jour"][:3].upper() # ex: LUN, MAR...
        c_date = info_ligne["Date"]
        
        # On utilise une seule ligne horizontale par jour très compacte
        cols = st.columns([3, 3, 4])
        with cols[0]:
            st.markdown(f"**{c_jour} {c_date}**")
        with cols[1]:
            actuel = st.session_state["temp_dispos"].get(jour_int, "⚪")
            # Un selectbox natif ultra-court ou des boutons très serrés
            nouveau_choix = st.selectbox(
                f"Dispo {jour_int}",
                options=["⚪", "🟢", "🔴"],
                index=["⚪", "🟢", "🔴"].index(actuel),
                key=f"sel_{mois_selectionne_nom}_{jour_int}",
                label_visibility="collapsed"
            )
            if nouveau_choix != actuel:
                st.session_state["temp_dispos"][jour_int] = nouveau_choix

st.markdown("")
if st.button("✅ Enregistrer mes disponibilités", type="primary", use_container_width=True):
    cellules_a_mettre_a_jour = []
    for jour_int, val_choisie in st.session_state["temp_dispos"].items():
        val_origine = dispos_actuelles.get(jour_int, "⚪")
        if val_choisie != val_origine:
            valeur_a_ecrire = "" if val_choisie == "⚪" else val_choisie
            cellules_a_mettre_a_jour.append(
                gspread.Cell(row=lignes_dates[jour_int], col=COLONNES_MUSICIENS[nom_utilisateur], value=valeur_a_ecrire)
            )
    
    if cellules_a_mettre_a_jour:
        worksheet.update_cells(cellules_a_mettre_a_jour)
        st.session_state["succes_perso"] = True
        st.rerun()
    else:
        st.info("Aucune modification à enregistrer.")

# --- UI : Récapitulatif Global et Saisie des Événements ---
st.divider()
st.subheader("👀 Récap' Général Dispos & Planning")
st.info("📝 N'hésitez pas à ajouter les événements ici (ex: 'Répétition', 'Concert à ...').")

df_recap = pd.DataFrame(recap_data_pour_tableau)
styled_df_recap = df_recap.style.apply(coloriser_weekends, axis=1)

with st.form("form_global"):
    edited_recap = st.data_editor(
        styled_df_recap,
        column_config={
            "Jour_num": None,
            "Jour": st.column_config.TextColumn("Jour", disabled=True),
            "Date": st.column_config.TextColumn("Date", disabled=True),
            "Événement": st.column_config.TextColumn("Événement")
        },
        disabled=["Jour", "Date"] + list(COLONNES_MUSICIENS.keys()),
        hide_index=True,
        use_container_width=True
    )
    
    soumis_global = st.form_submit_button("💾 Enregistrer l'événement au planning", type="secondary", use_container_width=True)
    
    if soumis_global:
        cellules_evt = []
        for index, new_row in edited_recap.iterrows():
            jour_int = new_row["Jour_num"]
            nouvel_evt = new_row["Événement"]
            
            if nouvel_evt != evenements_actuels[jour_int]:
                cellules_evt.append(
                    gspread.Cell(row=lignes_dates[jour_int], col=17, value=nouvel_evt)
                )
        
        if cellules_evt:
            worksheet.update_cells(cellules_evt)
            st.session_state["succes_evt"] = True
            st.rerun()
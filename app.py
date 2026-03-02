# =============================================================================
# DreamStream — Journal de rêves intelligent
# APIs utilisées : Groq uniquement (gratuit)
# Clés API      : fichier .env
# =============================================================================
# INSTALLATION (dans ton terminal) :
#   pip install streamlit groq python-dotenv
#
# CONFIGURATION :
#   Crée un fichier .env dans le même dossier avec :
#   GROQ_API_KEY=ta_clé_ici
#
# LANCEMENT :
#   streamlit run app.py
# =============================================================================

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv   # lit le fichier .env
from groq import Groq            # client officiel Groq

# --- Chargement des variables d'environnement depuis .env ---
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# =============================================================================
# CONFIG PAGE
# =============================================================================
st.set_page_config(
    page_title="DreamStream 🌙",
    page_icon="🌙",
    layout="centered",
)

# =============================================================================
# GESTION DU JOURNAL (sauvegarde dans un fichier JSON local)
# =============================================================================
FICHIER_JOURNAL = "mes_reves.json"

def charger_journal() -> list:
    """Retourne la liste des rêves depuis le fichier JSON."""
    if Path(FICHIER_JOURNAL).exists():
        with open(FICHIER_JOURNAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_reve(reve: dict) -> None:
    """Ajoute un rêve en tête du journal et sauvegarde."""
    journal = charger_journal()
    journal.insert(0, reve)   # plus récent en premier
    with open(FICHIER_JOURNAL, "w", encoding="utf-8") as f:
        json.dump(journal, f, ensure_ascii=False, indent=2)

# =============================================================================
# ANALYSE IA AVEC GROQ
# =============================================================================
def analyser_reve(texte: str) -> dict:
    """
    Envoie le texte du rêve à l'IA Groq (Llama 3).
    Retourne un dictionnaire avec : résumé, interprétation, mots-clés.
    """
    client = Groq(api_key=GROQ_API_KEY)

    # Prompt optimisé : on demande un format strict pour faciliter le parsing
    prompt = f"""
Tu es un expert en interprétation des rêves. Analyse le rêve ci-dessous.
Réponds UNIQUEMENT dans ce format (respecte exactement les étiquettes) :

RÉSUMÉ: [2 phrases max résumant le rêve]
INTERPRÉTATION: [2-3 phrases sur la signification symbolique]
MOTS_CLÉS: [5 mots-clés en anglais séparés par des virgules, très visuels]

Rêve : {texte}
"""

    réponse = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # modèle rapide et gratuit
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,           # créativité modérée
        max_tokens=400,
    )

    # On récupère le texte brut retourné par l'IA
    texte_ia = réponse.choices[0].message.content

    # On extrait chaque section grâce aux étiquettes
    résultat = {"resume": "", "interpretation": "", "mots_cles": []}

    for ligne in texte_ia.split("\n"):
        ligne = ligne.strip()
        if ligne.startswith("RÉSUMÉ:"):
            résultat["resume"] = ligne.replace("RÉSUMÉ:", "").strip()
        elif ligne.startswith("INTERPRÉTATION:"):
            résultat["interpretation"] = ligne.replace("INTERPRÉTATION:", "").strip()
        elif ligne.startswith("MOTS_CLÉS:"):
            brut = ligne.replace("MOTS_CLÉS:", "").strip()
            résultat["mots_cles"] = [m.strip() for m in brut.split(",")]

    return résultat

# =============================================================================
# SIDEBAR — Historique des rêves
# =============================================================================
with st.sidebar:
    st.markdown("## 🌙 DreamStream")
    st.divider()
    st.markdown("### 📖 Historique")

    journal = charger_journal()

    if not journal:
        st.info("Aucun rêve enregistré pour l'instant.")
    else:
        for reve in journal:
            with st.expander(f"🌀 {reve['date']}"):
                st.markdown(f"**Rêve :** {reve['texte']}")
                st.markdown(f"**Résumé :** {reve['resume']}")
                st.markdown(f"**Interprétation :** {reve['interpretation']}")
                if reve.get("mots_cles"):
                    st.markdown("**Mots-clés :** " + " · ".join(f"`{m}`" for m in reve["mots_cles"]))

# =============================================================================
# PAGE PRINCIPALE
# =============================================================================
st.title("🌙 DreamStream")
st.markdown("*Décris ton rêve, l'IA l'analyse et l'interprète pour toi.*")
st.divider()

# --- Saisie du rêve ---
st.markdown("### ✍️ Décris ton rêve")
texte_reve = st.text_area(
    label="ton rêve",
    placeholder="Cette nuit, je me trouvais dans une forêt immense où les arbres chantaient...",
    height=180,
    label_visibility="collapsed",
)

# --- Bouton d'analyse ---
if st.button("🔮 Analyser mon rêve", type="primary", use_container_width=True):

    if not texte_reve.strip():
        st.warning("⚠️ Écris d'abord ton rêve ci-dessus.")
    else:
        # Appel à l'IA
        with st.spinner("🔮 L'IA analyse ton rêve..."):
            try:
                résultat = analyser_reve(texte_reve)
            except Exception as erreur:
                st.error(f"❌ Erreur : {erreur}")
                st.stop()

        # --- Affichage des résultats ---
        st.divider()

        st.markdown("### 📝 Résumé")
        st.info(résultat["resume"] or "Aucun résumé généré.")

        st.markdown("### 🔮 Interprétation symbolique")
        st.success(résultat["interpretation"] or "Aucune interprétation générée.")

        if résultat["mots_cles"]:
            st.markdown("### 🏷️ Mots-clés visuels")
            st.markdown("  ".join(f"`{m}`" for m in résultat["mots_cles"]))

        # --- Sauvegarde automatique ---
        sauvegarder_reve({
            "date": datetime.now().strftime("%d/%m/%Y à %H:%M"),
            "texte": texte_reve,
            "resume": résultat["resume"],
            "interpretation": résultat["interpretation"],
            "mots_cles": résultat["mots_cles"],
        })

        st.caption("✅ Rêve sauvegardé dans ton historique (menu gauche).")
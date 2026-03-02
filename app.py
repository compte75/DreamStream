
import streamlit as st
import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Je charge mes clés API depuis le fichier .env
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
HF_API_KEY   = os.environ.get("HF_API_KEY", "")

# L'adresse du modèle d'image sur Hugging Face
IMAGE_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# Le fichier où je sauvegarde les rêves
JOURNAL_FILE = "mes_reves.json"


# ---------------------------------------------------------------------------
# Mes fonctions pour gérer le journal
# ---------------------------------------------------------------------------

def load_journal():
    # Si le fichier existe déjà, je le lis. Sinon je retourne une liste vide.
    if Path(JOURNAL_FILE).exists():
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_dream(new_dream):
    # Je récupère les rêves existants, j'ajoute le nouveau en haut, et je sauvegarde
    all_dreams = load_journal()
    all_dreams.insert(0, new_dream)
    with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
        json.dump(all_dreams, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Ma fonction qui envoie le rêve à Groq pour l'analyser
# ---------------------------------------------------------------------------

def analyze_dream(dream_text):
    # Je crée le client Groq avec ma clé
    client = Groq(api_key=GROQ_API_KEY)

    # Mon prompt : je demande à l'IA de répondre dans un format précis
    # pour que je puisse facilement extraire chaque partie ensuite
    my_prompt = f"""
Tu es un expert en interprétation des rêves.
Analyse ce rêve et réponds dans ce format exact, sans rien ajouter d'autre :

RÉSUMÉ: [résume le rêve en 2 phrases maximum]
INTERPRÉTATION: [explique la signification symbolique en 2-3 phrases]
MOTS_CLÉS: [donne 5 mots-clés en anglais séparés par des virgules, très visuels]

Le rêve à analyser : {dream_text}
"""

    # J'envoie la requête au modèle
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": my_prompt}],
        temperature=0.7,  # entre 0 (strict) et 1 (très créatif)
        max_tokens=400,
    )

    # Je récupère le texte brut de la réponse
    raw_text = response.choices[0].message.content

    # Je découpe la réponse ligne par ligne pour extraire chaque section
    summary        = ""
    interpretation = ""
    keywords       = []

    for line in raw_text.split("\n"):
        line = line.strip()
        if line.startswith("RÉSUMÉ:"):
            summary = line.replace("RÉSUMÉ:", "").strip()
        elif line.startswith("INTERPRÉTATION:"):
            interpretation = line.replace("INTERPRÉTATION:", "").strip()
        elif line.startswith("MOTS_CLÉS:"):
            raw_keywords = line.replace("MOTS_CLÉS:", "").strip()
            keywords = [kw.strip() for kw in raw_keywords.split(",")]

    return summary, interpretation, keywords


# ---------------------------------------------------------------------------
# Ma fonction qui génère une image avec Hugging Face
# ---------------------------------------------------------------------------

def generate_image(keywords):
    # Je transforme mes mots-clés en un prompt artistique pour l'IA
    image_prompt = (
        ", ".join(keywords)
        + ", dreamlike surreal painting, soft glowing colors, fantasy art, highly detailed"
    )

    # J'envoie la requête à Stable Diffusion via l'API Hugging Face
    response = requests.post(
        IMAGE_MODEL_URL,
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": image_prompt},
        timeout=60,
    )

    # Si ça marche (code 200), je retourne les données de l'image
    if response.status_code == 200:
        return response.content

    # Sinon je retourne None et je gère l'erreur dans l'interface
    return None


# ---------------------------------------------------------------------------
# Configuration de la page Streamlit
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="DreamStream 🌙",
    page_icon="🌙",
    layout="centered",
)


# ---------------------------------------------------------------------------
# Menu latéral : mon historique de rêves
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🌙 DreamStream")
    st.divider()
    st.markdown("### 📖 Mes rêves précédents")

    dreams = load_journal()

    if not dreams:
        st.info("Pas encore de rêves enregistrés.")
    else:
        for dream in dreams:
            with st.expander(f"🌀 {dream['date']}"):
                st.markdown(f"**Rêve :** {dream['text']}")
                st.markdown(f"**Résumé :** {dream['summary']}")
                st.markdown(f"**Interprétation :** {dream['interpretation']}")
                if dream.get("keywords"):
                    st.markdown("**Mots-clés :** " + " · ".join(f"`{kw}`" for kw in dream["keywords"]))


# ---------------------------------------------------------------------------
# Page principale
# ---------------------------------------------------------------------------

st.title("🌙 DreamStream")
st.markdown("*Décris ton rêve, l'IA l'analyse et l'illustre pour toi.*")
st.divider()


# Zone de saisie du rêve
st.markdown("### ✍️ Décris ton rêve")
dream_input = st.text_area(
    label="dream",
    placeholder="Cette nuit, je volais au-dessus d'une mer de nuages dorés...",
    height=180,
    label_visibility="collapsed",
)

# Bouton pour lancer l'analyse
if st.button("🔮 Analyser mon rêve", type="primary", use_container_width=True):

    if not dream_input.strip():
        st.warning("⚠️ Écris d'abord ton rêve !")

    else:
        # Étape 1 : j'envoie le rêve à Groq
        with st.spinner("🔮 Analyse en cours..."):
            try:
                summary, interpretation, keywords = analyze_dream(dream_input)
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse : {e}")
                st.stop()

        # J'affiche les résultats
        st.divider()

        st.markdown("### 📝 Résumé")
        st.info(summary or "Aucun résumé généré.")

        st.markdown("### 🔮 Interprétation symbolique")
        st.success(interpretation or "Aucune interprétation générée.")

        if keywords:
            st.markdown("### 🏷️ Mots-clés visuels")
            st.markdown("  ".join(f"`{kw}`" for kw in keywords))

        # Étape 2 : je génère l'image si la clé HF est disponible
        st.divider()
        st.markdown("### 🎨 Illustration générée par l'IA")

        if HF_API_KEY and keywords:
            with st.spinner("🎨 Génération de l'image... (peut prendre 30-60 secondes)"):
                try:
                    image = generate_image(keywords)
                    if image:
                        st.image(image, caption="✨ Ton rêve en image")
                    else:
                        st.warning("⚠️ Le modèle est occupé, réessaie dans quelques secondes.")
                except Exception as e:
                    st.warning(f"⚠️ Erreur image : {e}")
        else:
            st.info("💡 Ajoute `HF_API_KEY` dans ton `.env` pour générer l'image.")

        # Étape 3 : je sauvegarde le rêve dans mon journal
        save_dream({
            "date": datetime.now().strftime("%d/%m/%Y à %H:%M"),
            "text": dream_input,
            "summary": summary,
            "interpretation": interpretation,
            "keywords": keywords,
        })

        st.caption("✅ Rêve sauvegardé dans ton journal !")
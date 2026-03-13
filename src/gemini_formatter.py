import streamlit as st
import time
import os

# Importer nos modules personnalisés
from src.audio_processor import AudioProcessor
from src.groq_client import GroqTranscriber
from src.subscription import SubscriptionManager
from src.gemini_formatter import GeminiFormatter

# --- MODE DÉVELOPPEMENT ---
DEV_MODE = True

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="VoxWhisper Mali",
    page_icon="🇲🇱",
    layout="wide"
)

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #14b8a6; }
    .stApp header { background: linear-gradient(90deg, #14b8a6 0%, #fbbf24 50%, #ef4444 100%); }
    .stButton>button {
        border-radius: 50px;
        background: linear-gradient(135deg, #14b8a6 0%, #0f766e 100%);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
if not AudioProcessor.check_ffmpeg():
    st.error("❌ FFmpeg n'est pas installé.")
    st.stop()

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("🔐 Clé API Groq manquante.")
    st.stop()

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    gemini_available = True
except KeyError:
    gemini_available = False
    st.sidebar.warning("⚠️ Clé Gemini manquante - formatage désactivé")

SubscriptionManager.initialize_session()

# --- INTERFACE ---
st.title("🇲🇱 VoxWhisper Mali")
st.markdown("**Transcription audio multi-langues**")
st.divider()

# --- SOURCE ---
source_type = st.radio("Source :", ["📁 Fichier local", "🌐 Lien YouTube"], horizontal=True)

input_source = None
if source_type == "🌐 Lien YouTube":
    input_source = st.text_input("Lien YouTube")
else:
    input_source = st.file_uploader(
        "Choisissez un fichier",
        type=["mp3", "wav", "ogg", "opus", "mp4", "m4a"]
    )

# --- BOUTON LANCEMENT ---
launch_button = st.button("🚀 LANCER LA TRANSCRIPTION", use_container_width=True)

# --- HISTORIQUE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = None
if 'formatted_text' not in st.session_state:
    st.session_state.formatted_text = None

# --- TRANSCRIPTION ---
if launch_button and input_source:
    if not DEV_MODE and not SubscriptionManager.is_active():
        st.warning("🔒 Abonnement requis.")
        st.stop()

    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Étape 1: Préparation audio
        status.info("Préparation audio...")
        progress_bar.progress(30)
        
        if source_type == "🌐 Lien YouTube":
            audio_path = AudioProcessor.extract_youtube_audio(input_source)
        else:
            audio_path = AudioProcessor.prepare_audio_file(input_source)
        
        # Étape 2: Transcription
        status.info("Transcription en cours...")
        progress_bar.progress(60)
        
        transcriber = GroqTranscriber(GROQ_API_KEY)
        transcription = transcriber.transcribe(audio_path)
        
        # Sauvegarde
        st.session_state.current_text = transcription
        st.session_state.history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": input_source.name if hasattr(input_source, 'name') else input_source,
            "text": transcription[:100] + "..."
        })
        
        progress_bar.progress(100)
        status.success("Transcription terminée !")
        
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

# --- AFFICHAGE DE LA TRANSCRIPTION ---
if st.session_state.current_text:
    st.divider()
    st.subheader("📝 Transcription")
    
    # Afficher le texte
    st.text_area("Texte transcrit", st.session_state.current_text, height=200)
    
    # Bouton téléchargement
    st.download_button(
        "📥 Télécharger",
        st.session_state.current_text,
        "transcription.txt"
    )
    
    # --- SECTION GEMINI (OPTIONNELLE) ---
    if gemini_available:
        st.divider()
        st.subheader("✨ Améliorer avec Gemini")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🧹 Nettoyer"):
                with st.spinner("..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_text, style="propre"
                    )
        
        with col2:
            if st.button("📑 Structurer"):
                with st.spinner("..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_text, style="structure"
                    )
        
        with col3:
            if st.button("📌 Résumer"):
                with st.spinner("..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_text, style="resume"
                    )
        
        with col4:
            if st.button("🗣️ Bambara"):
                with st.spinner("..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_text, style="bambara"
                    )
        
        # Afficher le résultat formaté
        if st.session_state.formatted_text:
            st.divider()
            st.subheader("📋 Résultat formaté")
            st.text_area("", st.session_state.formatted_text, height=200)
            st.download_button(
                "📥 Télécharger version formatée",
                st.session_state.formatted_text,
                "transcription_formatee.txt"
            )

# --- HISTORIQUE ---
with st.sidebar:
    st.header("📜 Historique")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            st.text(f"🕒 {item['timestamp'][:16]}")
            st.caption(item['text'])
            st.divider()
    else:
        st.info("Aucune transcription")

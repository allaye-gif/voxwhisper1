import streamlit as st
import time
import os
import subprocess
import sys

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="AllayeVox Mali",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLE CSS ULTRA PREMIUM ---
st.markdown("""
    <style>
        /* Import des polices modernes */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Reset et base */
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Fond général avec dégradé subtil */
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Style du header */
        .header-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-radius: 20px;
            margin: 1rem 0 2rem 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* Titre principal */
        .main-title {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        /* Sous-titre */
        .sub-title {
            font-size: 1.2rem;
            font-weight: 300;
            color: #4a5568;
            opacity: 0.9;
        }
        
        /* Zone d'upload ultra stylisée */
        .upload-area {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 3px dashed rgba(102, 126, 234, 0.3);
            border-radius: 40px;
            padding: 80px 40px;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.1);
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: rgba(255, 255, 255, 0.98);
            transform: translateY(-5px);
            box-shadow: 0 40px 80px rgba(102, 126, 234, 0.2);
        }
        
        .upload-area svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .upload-text {
            font-size: 1.8rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            font-size: 1rem;
            color: #718096;
            font-weight: 300;
        }
        
        /* Bouton principal */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            font-size: 1.2rem;
            padding: 1rem 2rem;
            border-radius: 60px;
            border: none;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            width: 100%;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.6);
        }
        
        /* Cartes de fonctionnalités */
        .feature-card {
            background: white;
            padding: 30px;
            border-radius: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: all 0.3s ease;
            height: 100%;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(102, 126, 234, 0.3);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        .feature-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .feature-desc {
            color: #718096;
            font-weight: 300;
            line-height: 1.6;
        }
        
        /* Badges de langue */
        .lang-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 40px;
            font-weight: 500;
            font-size: 0.9rem;
            margin: 0 5px 10px 0;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        
        .lang-badge.fr { background: linear-gradient(135deg, #0055A4, #EF4135); color: white; }
        .lang-badge.en { background: linear-gradient(135deg, #012169, #C8102E); color: white; }
        .lang-badge.bm { background: linear-gradient(135deg, #14B8A6, #0F766E); color: white; }
        
        /* Résultat de transcription */
        .result-container {
            background: white;
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            margin-top: 30px;
        }
        
        .result-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Timer */
        .timer-badge {
            background: linear-gradient(135deg, #48BB78, #2F855A);
            color: white;
            padding: 10px 20px;
            border-radius: 40px;
            font-weight: 500;
            display: inline-block;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 0;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 300;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Importer nos modules
from src.audio_processor import AudioProcessor
from src.groq_client import GroqTranscriber
from src.subscription import SubscriptionManager

# --- INITIALISATION ---
if not AudioProcessor.check_ffmpeg():
    st.error("Configuration système requise...")
    st.stop()

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("Configuration en cours...")
    st.stop()

SubscriptionManager.initialize_session()

# Variables de session
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_transcription' not in st.session_state:
    st.session_state.current_transcription = None

# --- HEADER PREMIUM ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="header-container">
            <div class="main-title">AllayeVox Mali</div>
            <div class="sub-title">La voix du Mali, transcrite par l'IA</div>
        </div>
    """, unsafe_allow_html=True)

# --- BADGES LANGUES ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <span class="lang-badge fr">🇫🇷 Français</span>
        <span class="lang-badge en">🇬🇧 English</span>
        <span class="lang-badge bm">🇲🇱 Bamanankan</span>
    </div>
""", unsafe_allow_html=True)

# --- ZONE D'UPLOAD PREMIUM ---
source_type = st.radio(
    "",
    ["🎤 Fichier audio", "▶️ YouTube"],
    horizontal=True,
    label_visibility="collapsed"
)

input_source = None
if source_type == "▶️ YouTube":
    input_source = st.text_input(
        "",
        placeholder="https://youtube.com/watch?v=...",
        label_visibility="collapsed"
    )
else:
    st.markdown("""
        <div class="upload-area" id="upload-area">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            <div class="upload-text">Glissez votre fichier audio</div>
            <div class="upload-hint">MP3, WAV, M4A, OGG • WhatsApp, enregistrements, podcasts</div>
        </div>
    """, unsafe_allow_html=True)
    
    input_source = st.file_uploader(
        "",
        type=["mp3", "wav", "m4a", "ogg", "opus", "flac", "mp4", "mov"],
        label_visibility="collapsed"
    )

# --- BOUTON PRINCIPAL ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    launch_button = st.button("✨ Transcrire maintenant", use_container_width=True)

# --- LOGIQUE DE TRANSCRIPTION ---
if launch_button and input_source:
    # Barre de progression
    progress_bar = st.progress(0)
    status = st.empty()
    
    audio_path = None
    start_time = time.time()
    
    try:
        # Étape 1: Préparation
        status.info("🎵 Préparation du fichier...")
        progress_bar.progress(20)
        
        if source_type == "▶️ YouTube":
            audio_path = AudioProcessor.extract_youtube_audio(input_source)
        else:
            audio_path = AudioProcessor.prepare_audio_file(input_source)
        
        # Étape 2: Transcription
        status.info("🧠 L'IA analyse votre audio...")
        progress_bar.progress(50)
        
        transcriber = GroqTranscriber(GROQ_API_KEY)
        transcription = transcriber.transcribe(audio_path)
        
        # Étape 3: Finalisation
        progress_bar.progress(100)
        status.success("✅ Transcription terminée !")
        
        elapsed_time = time.time() - start_time
        
        # Sauvegarde
        st.session_state.current_transcription = transcription
        st.session_state.history.append({
            "timestamp": time.strftime("%H:%M"),
            "text": transcription[:50] + "..."
        })
        
    except Exception as e:
        st.error(f"Une erreur est survenue: {str(e)}")
    finally:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)

# --- AFFICHAGE DU RÉSULTAT ---
if st.session_state.current_transcription:
    st.markdown("""
        <div class="result-container">
            <div class="result-header">
                <span>📝 Transcription</span>
            </div>
    """, unsafe_allow_html=True)
    
    st.text_area(
        "",
        st.session_state.current_transcription,
        height=300,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            "📥 Télécharger",
            st.session_state.current_transcription,
            "transcription.txt",
            use_container_width=True
        )
    with col2:
        if st.button("📋 Copier", use_container_width=True):
            st.write("Copié !")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- HISTORIQUE (discret) ---
with st.sidebar:
    st.markdown("### 📜 Récent")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):
            st.markdown(f"**{item['timestamp']}**  \n{item['text']}")
            st.divider()

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        AllayeVox Mali • Propulsé par Groq • Conçu à Bamako 🇲🇱
    </div>
""", unsafe_allow_html=True)

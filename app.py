import streamlit as st
import time
import os

# Importer nos modules personnalisés
from src.audio_processor import AudioProcessor
from src.groq_client import GroqTranscriber
from src.subscription import SubscriptionManager
from src.gemini_formatter import GeminiFormatter
from src.bambara_transcriber import BambaraTranscriber
from src.multi_langue_transcriber import MultiLangueTranscriber

# --- MODE DÉVELOPPEMENT ---
DEV_MODE = True

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="VoxWhisper Mali",
    page_icon="🇲🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS MODERNE ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #14b8a6;
        font-weight: 700;
    }
    .stApp header {
        background: linear-gradient(90deg, #14b8a6 0%, #fbbf24 50%, #ef4444 100%);
    }
    .upload-area {
        border: 3px dashed #14b8a6;
        border-radius: 20px;
        padding: 50px;
        text-align: center;
        background-color: #ffffff;
        transition: 0.3s;
    }
    .upload-area:hover {
        border-color: #fbbf24;
        background-color: #fef9e7;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #14b8a6, #fbbf24);
    }
    .stButton>button {
        border-radius: 50px;
        height: 3em;
        background: linear-gradient(135deg, #14b8a6 0%, #0f766e 100%);
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(20, 184, 166, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---

# Vérification FFmpeg
if not AudioProcessor.check_ffmpeg():
    st.error("""
    ❌ **FFmpeg n'est pas installé sur le système.**  
    VoxWhisper Mali nécessite FFmpeg pour traiter les fichiers audio.
    """)
    st.stop()

# Clé API Groq
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("🔐 **Clé API Groq manquante.**")
    st.stop()

# Clé API Gemini
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    gemini_available = True
except KeyError:
    gemini_available = False
    st.sidebar.warning("⚠️ Clé Gemini manquante - formatage désactivé")

# Initialisation
SubscriptionManager.initialize_session()

# Variables de session
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_transcription' not in st.session_state:
    st.session_state.current_transcription = None
if 'current_lang' not in st.session_state:
    st.session_state.current_lang = None
if 'current_source' not in st.session_state:
    st.session_state.current_source = None
if 'formatted_text' not in st.session_state:
    st.session_state.formatted_text = None

# --- INTERFACE PRINCIPALE ---
col_title, col_flag = st.columns([5, 1])
with col_title:
    st.title("🇲🇱 VoxWhisper Mali")
    st.markdown("**Transcription audio multi-langues : Français • Anglais • Bambara**")
with col_flag:
    st.image("https://flagcdn.com/w320/ml.png", width=100)

st.divider()

# Sidebar - Mode développement
if DEV_MODE:
    with st.sidebar:
        st.success("🔧 **MODE DÉVELOPPEMENT**")
        st.info("Abonnement désactivé pour les tests")

# --- ZONE DE SAISIE ---
source_type = st.radio(
    "Choisissez votre source :",
    ["📁 Fichier local", "🌐 Lien YouTube"],
    horizontal=True
)

input_source = None
if source_type == "🌐 Lien YouTube":
    input_source = st.text_input("Collez le lien YouTube", placeholder="https://youtube.com/watch?v=...")
else:
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    input_source = st.file_uploader(
        "Glissez-déposez votre fichier",
        type=["mp3", "wav", "m4a", "ogg", "opus", "flac", "mp4", "mov", "3gp"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Formats supportés : MP3, WAV, OGG, OPUS (WhatsApp), MP4, etc.")

# --- OPTIONS DE TRANSCRIPTION ---
with st.expander("🌍 Options avancées", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.radio(
            "Langue à transcrire",
            [
                "🇫🇷 Français",
                "🇬🇧 Anglais",
                "🇲🇱 Bambara (modèle spécialisé)",
                "🔄 Mixte (Français + Bambara)",
                "🤖 Auto (détection automatique)"
            ],
            index=4
        )
        
        lang_map = {
            "🇫🇷 Français": "fr",
            "🇬🇧 Anglais": "en",
            "🇲🇱 Bambara (modèle spécialisé)": "bm",
            "🔄 Mixte (Français + Bambara)": "mixed",
            "🤖 Auto (détection automatique)": "auto"
        }
        selected_lang = lang_map[language]
    
    with col2:
        if selected_lang == "bm":
            st.markdown("### 🇲🇱 Modèle bambara")
            bambara_model = st.selectbox(
                "Choix du modèle",
                [
                    "small - Open source (recommandé)",
                    "v1 - Commercial (licence Apache)"
                ],
                index=0
            )
            
            model_info = BambaraTranscriber.get_model_info()[
                "small" if "small" in bambara_model else "v1"
            ]
            st.caption(f"**Précision:** {model_info['wer']} | **Licence:** {model_info['license']}")
        else:
            st.markdown("### 🤖 Modèle standard")
            st.caption("Whisper-large-v3 via Groq (multilingue)")

# Bouton de lancement
launch_button = st.button("🚀 LANCER LA TRANSCRIPTION", use_container_width=True)

# --- LOGIQUE PRINCIPALE ---
if launch_button and input_source:
    # Vérification abonnement
    if not DEV_MODE and not SubscriptionManager.is_active():
        st.warning("🔒 **Abonnement requis.**")
        st.stop()

    # Barre de progression
    progress_bar = st.progress(0, text="Initialisation...")
    status = st.empty()
    time_placeholder = st.empty()
    
    audio_path = None
    start_time = time.time()

    try:
        # ÉTAPE 1: Préparation audio
        status.info("🔄 **Étape 1/3 : Préparation audio...**")
        progress_bar.progress(20)

        if source_type == "🌐 Lien YouTube":
            with st.spinner("Téléchargement YouTube..."):
                audio_path = AudioProcessor.extract_youtube_audio(input_source)
        else:
            with st.spinner("Conversion et amélioration..."):
                audio_path = AudioProcessor.prepare_audio_file(input_source)

        progress_bar.progress(40)

        # ÉTAPE 2: Transcription selon la langue
        status.info("🧠 **Étape 2/3 : Transcription en cours...**")
        
        try:
            if selected_lang == "bm":
                # Transcription bambara
                model_key = "small" if "small" in bambara_model else "v1"
                
                try:
                    transcriber = BambaraTranscriber(model_key)
                    transcription = transcriber.transcribe(audio_path)
                except Exception as e:
                    st.warning(f"Le modèle bambara spécialisé a échoué: {str(e)}")
                    st.info("Utilisation du modèle standard Groq en secours...")
                    transcriber = GroqTranscriber(GROQ_API_KEY)
                    transcription = transcriber.transcribe(audio_path)
                    
            elif selected_lang == "mixed":
                # Mode mixte
                transcriber = MultiLangueTranscriber(GROQ_API_KEY, GEMINI_API_KEY if gemini_available else None)
                transcription = transcriber.transcribe(audio_path, language_choice="mixed")
                
            else:
                # Mode standard (Groq)
                transcriber = GroqTranscriber(GROQ_API_KEY)
                transcription = transcriber.transcribe(audio_path)
                
        except Exception as e:
            st.error(f"Erreur de transcription: {str(e)}")
            raise

        progress_bar.progress(80)

        # ÉTAPE 3: Finalisation
        elapsed_time = time.time() - start_time
        time_placeholder.success(f"⏱️ **Temps total : {elapsed_time:.2f} secondes**")
        progress_bar.progress(100)
        status.success("✅ **Transcription terminée !**")

        # Sauvegarde
        st.session_state.current_transcription = transcription
        st.session_state.current_lang = selected_lang
        st.session_state.current_source = input_source.name if hasattr(input_source, 'name') else input_source
        st.session_state.formatted_text = None
        
        # Historique
        st.session_state.history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": st.session_state.current_source,
            "lang": selected_lang,
            "text": transcription[:100] + "...",
            "full_text": transcription
        })

    except Exception as e:
        progress_bar.empty()
        status.error(f"❌ **Erreur :** {str(e)}")
        st.exception(e)
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass

# --- AFFICHAGE DE LA TRANSCRIPTION ---
if st.session_state.current_transcription:
    st.divider()
    st.subheader("📝 Résultat de la transcription")
    
    # Badge de langue
    lang_display = {
        "fr": "🇫🇷 Français",
        "en": "🇬🇧 Anglais",
        "bm": "🇲🇱 Bambara",
        "mixed": "🔄 Mixte (Français+Bambara)",
        "auto": "🤖 Auto"
    }.get(st.session_state.current_lang, "🇫🇷 Français")
    
    st.markdown(f"**Langue utilisée :** {lang_display}")
    
    # Texte transcrit
    st.text_area("Transcription", st.session_state.current_transcription, height=250, key="transcription_display")
    
    # Boutons de téléchargement
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "📥 Télécharger (.txt)",
            st.session_state.current_transcription,
            "transcription.txt",
            use_container_width=True
        )
    with col_dl2:
        st.download_button(
            "📥 Télécharger (.srt)",
            f"1\n00:00:00,000 --> 00:00:02,000\n{st.session_state.current_transcription}",
            "subtitles.srt",
            use_container_width=True
        )
    
    # --- SECTION GEMINI (formatage optionnel) ---
    if gemini_available:
        st.divider()
        st.subheader("✨ Améliorer avec Gemini")
        st.markdown("Choisissez un style de formatage :")
        
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        
        with col_g1:
            if st.button("🧹 Nettoyer", use_container_width=True):
                with st.spinner("Gemini nettoie le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription,
                        style="propre"
                    )
        
        with col_g2:
            if st.button("📑 Structurer", use_container_width=True):
                with st.spinner("Gemini structure le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription,
                        style="structure"
                    )
        
        with col_g3:
            if st.button("📌 Résumer", use_container_width=True):
                with st.spinner("Gemini résume le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription,
                        style="resume"
                    )
        
        with col_g4:
            if st.button("🗣️ Bambara", use_container_width=True):
                with st.spinner("Gemini améliore le bambara..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription,
                        style="bambara"
                    )
        
        # Affichage du texte formaté
        if st.session_state.formatted_text:
            st.divider()
            st.subheader("📋 Résultat formaté")
            st.text_area("", st.session_state.formatted_text, height=200, key="formatted_display")
            st.download_button(
                "📥 Télécharger version formatée",
                st.session_state.formatted_text,
                "transcription_formatee.txt",
                use_container_width=True
            )
    else:
        st.info("💡 Ajoutez GEMINI_API_KEY dans les secrets pour activer le formatage")

# --- HISTORIQUE ---
with st.sidebar:
    st.divider()
    st.header("📜 Historique")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-10:])):
            lang_emoji = {
                "bm": "🇲🇱",
                "mixed": "🔄",
                "fr": "🇫🇷",
                "en": "🇬🇧",
                "auto": "🤖"
            }.get(item.get('lang', 'fr'), "🇫🇷")
            
            with st.expander(f"{lang_emoji} {item['timestamp'][:16]}"):
                st.markdown(f"**Source:** {item['source']}")
                st.caption(item['text'])
                if st.button("Charger", key=f"hist_{i}"):
                    st.session_state.current_transcription = item['full_text']
                    st.session_state.current_lang = item.get('lang', 'fr')
                    st.session_state.formatted_text = None
                    st.rerun()
    else:
        st.info("Aucune transcription")

# --- PIED DE PAGE ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <strong>VoxWhisper Mali</strong> — Propulsé par Groq & Gemini • Modèles bambara par MALIBA-AI 🇲🇱<br>
        <small>Français • English • Bambara • Mixte</small>
    </div>
    """,
    unsafe_allow_html=True
)

import streamlit as st
import time
import os

# Importer nos modules personnalisés
from src.audio_processor import AudioProcessor
from src.groq_client import GroqTranscriber
from src.subscription import SubscriptionManager

# --- MODE DÉVELOPPEMENT ---
# Mettre à False en production pour activer l'abonnement
DEV_MODE = True

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="VoxWhisper Mali",
    page_icon="🇲🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS MODERNE (UX Premium) ---
st.markdown("""
    <style>
    /* Couleurs inspirées du Mali : Vert, Or, Rouge */
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
    /* Zone d'upload stylisée */
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
    /* Barre de progression fluide */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #14b8a6, #fbbf24);
    }
    /* Boutons */
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
    /* Messages de statut */
    .status-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION ---

# 1. Vérification de FFmpeg (indispensable)
if not AudioProcessor.check_ffmpeg():
    st.error("""
    ❌ **FFmpeg n'est pas installé sur le système.**  
    VoxWhisper Mali nécessite FFmpeg pour traiter les fichiers audio.  
    Veuillez suivre les instructions d'installation dans le README.
    """)
    st.stop()

# 2. Récupération de la clé API Groq depuis les secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("""
    🔐 **Clé API Groq manquante.**  
    Veuillez ajouter votre clé API dans les secrets de l'application.
    """)
    st.stop()

# 3. Initialisation du gestionnaire d'abonnement
SubscriptionManager.initialize_session()

# --- INTERFACE PRINCIPALE ---

# Titre et description
col_title, col_flag = st.columns([5, 1])
with col_title:
    st.title("🇲🇱 VoxWhisper Mali")
    st.markdown("**La transcription audio ultra-rapide, conçue pour le Mali.**")
with col_flag:
    st.image("https://flagcdn.com/w320/ml.png", width=100)

st.divider()

# --- GESTION DE L'ABONNEMENT (Sidebar) ---
# En mode développement, on n'affiche pas l'UI d'abonnement
if not DEV_MODE:
    SubscriptionManager.show_subscription_ui()
else:
    with st.sidebar:
        st.success("🔧 **MODE DÉVELOPPEMENT**")
        st.info("L'abonnement est désactivé pour les tests.")

# --- ZONE DE SAISIE PRINCIPALE (UX Premium) ---
source_type = st.radio(
    "Choisissez votre source :",
    ["📁 Fichier local (MP3, OGG, WhatsApp...)", "🌐 Lien YouTube"],
    horizontal=True
)

input_source = None
if source_type == "🌐 Lien YouTube":
    input_source = st.text_input(
        "Collez le lien YouTube",
        placeholder="https://www.youtube.com/watch?v=..."
    )
else:
    # Grande zone d'upload stylisée
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    input_source = st.file_uploader(
        "Glissez-déposez votre fichier audio ou vidéo, ou cliquez pour parcourir",
        type=["mp3", "wav", "m4a", "ogg", "opus", "flac", "aac", "mp4", "mov", "mkv", "3gp"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Formats supportés : MP3, WAV, M4A, OGG, OPUS (WhatsApp), FLAC, AAC, MP4, MOV, MKV, 3GP")

# Bouton de lancement principal
launch_button = st.button("🚀 LANCER LA TRANSCRIPTION", use_container_width=True)

# --- GESTION DE L'HISTORIQUE (session_state) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# --- LOGIQUE PRINCIPALE DE TRANSCRIPTION ---
if launch_button and input_source:
    # Vérification de l'abonnement (UNIQUEMENT si pas en mode développement)
    if not DEV_MODE:
        if not SubscriptionManager.is_active():
            st.warning("🔒 **Abonnement requis.** Veuillez vous abonner pour utiliser le service.")
            st.stop()
    else:
        # Message discret en mode développement
        st.info("⚙️ Mode développement : transcription gratuite activée")

    # Initialisation des éléments UI de progression
    progress_bar = st.progress(0, text="Initialisation...")
    status_placeholder = st.empty()
    time_placeholder = st.empty()

    audio_path = None
    start_time = time.time()

    try:
        # ÉTAPE 1: Préparation audio
        status_placeholder.info("🔄 **Étape 1/3 : Préparation du fichier audio...**")
        progress_bar.progress(10, text="Conversion et compression...")

        if source_type == "🌐 Lien YouTube":
            with st.spinner("Téléchargement depuis YouTube..."):
                audio_path = AudioProcessor.extract_youtube_audio(input_source)
        else:
            with st.spinner("Conversion et optimisation..."):
                audio_path = AudioProcessor.prepare_audio_file(input_source)

        progress_bar.progress(40, text="Audio prêt. Envoi à l'IA...")

        # ÉTAPE 2: Transcription via Groq
        status_placeholder.info("🧠 **Étape 2/3 : L'IA Groq transcrit votre audio...**")
        transcriber = GroqTranscriber(GROQ_API_KEY)

        # L'appel API
        transcription_text = transcriber.transcribe(audio_path)

        progress_bar.progress(80, text="Transcription reçue. Finalisation...")
        status_placeholder.info("✍️ **Étape 3/3 : Finalisation du résultat...**")

        # Calcul du temps écoulé
        elapsed_time = time.time() - start_time
        time_placeholder.success(f"⏱️ **Temps total : {elapsed_time:.2f} secondes**")

        # ÉTAPE 3: Affichage des résultats
        progress_bar.progress(100, text="Terminé !")
        status_placeholder.success("✅ **Transcription terminée avec succès !**")

        # Sauvegarde dans l'historique
        st.session_state.history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": input_source.name if hasattr(input_source, 'name') else input_source,
            "text": transcription_text[:100] + "...",  # Aperçu
            "full_text": transcription_text
        })

        # Affichage du résultat
        st.divider()
        st.subheader("📝 Résultat de la transcription")

        tab1, tab2 = st.tabs(["📄 Texte intégral", "📊 Aperçu audio"])

        with tab1:
            st.text_area("Transcription", transcription_text, height=400, label_visibility="collapsed")
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Télécharger en .txt",
                    data=transcription_text,
                    file_name="transcription_voxwhisper.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_dl2:
                # Pour SRT, il faudrait un traitement plus poussé (non fait ici pour rester simple)
                st.download_button(
                    label="📥 Télécharger en .srt",
                    data="1\n00:00:00,000 --> 00:00:02,000\n" + transcription_text,
                    file_name="subtitles.srt",
                    mime="text/plain",
                    use_container_width=True
                )

        with tab2:
            if audio_path and os.path.exists(audio_path):
                st.audio(audio_path)
            else:
                st.info("Aperçu audio non disponible.")

    except Exception as e:
        progress_bar.empty()
        status_placeholder.error(f"❌ Une erreur est survenue : {str(e)}")
        st.exception(e)  # Pour le debug, à retirer en production
    finally:
        # Nettoyage : supprimer le fichier temporaire
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass  # Ignorer les erreurs de nettoyage

# --- AFFICHAGE DE L'HISTORIQUE ---
with st.sidebar:
    st.divider()
    st.header("📜 Historique")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]):  # Afficher les 5 derniers
            with st.expander(f"🕒 {item['timestamp']}"):
                st.markdown(f"**Source:** {item['source']}")
                st.markdown(f"**Aperçu:** {item['text']}")
                if st.button("Recharger", key=item['timestamp']):
                    st.session_state['last_transcription'] = item['full_text']
                    st.rerun()
    else:
        st.info("Aucune transcription pour le moment.")

# --- PIED DE PAGE ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <strong>VoxWhisper Mali</strong> — Propulsé par l'IA Groq • Conçu pour le Mali 🇲🇱<br>
        <small>Paiements sécurisés via Orange Money & Wave (à venir)</small>
    </div>
    """,
    unsafe_allow_html=True
)

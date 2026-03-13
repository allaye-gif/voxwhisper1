import streamlit as st
import time
import os

# Importer nos modules personnalisés
from src.audio_processor import AudioProcessor
from src.groq_client import GroqTranscriber
from src.subscription import SubscriptionManager
from src.gemini_formatter import GeminiFormatter

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
    /* Style pour les boutons Gemini */
    .gemini-button {
        background: linear-gradient(135deg, #4285F4 0%, #9B72CB 50%, #DB4437 100%) !important;
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

# 3. Récupération de la clé API Gemini (optionnelle)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    gemini_available = True
except KeyError:
    gemini_available = False
    st.sidebar.warning("""
    ⚠️ **Clé Gemini manquante**  
    Ajoutez GEMINI_API_KEY dans les secrets pour activer le formatage avancé.
    """)

# 4. Initialisation du gestionnaire d'abonnement
SubscriptionManager.initialize_session()

# 5. Initialisation des variables de session
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_transcription' not in st.session_state:
    st.session_state.current_transcription = None
if 'current_source' not in st.session_state:
    st.session_state.current_source = None
if 'current_time' not in st.session_state:
    st.session_state.current_time = None
if 'formatted_text' not in st.session_state:
    st.session_state.formatted_text = None
if 'show_compare' not in st.session_state:
    st.session_state.show_compare = False

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

# --- OPTIONS DE LANGUE (optionnel, pour aider Whisper) ---
with st.expander("🌍 Options avancées", expanded=False):
    language = st.selectbox(
        "Langue principale (optionnel - laisse 'auto' pour détection automatique)",
        ["auto", "Français", "Anglais", "Bambara", "Autre"],
        index=0
    )
    
    lang_codes = {
        "auto": None,
        "Français": "fr",
        "Anglais": "en",
        "Bambara": "bm",
        "Autre": None
    }

# Bouton de lancement principal
launch_button = st.button("🚀 LANCER LA TRANSCRIPTION", use_container_width=True)

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

        # Transcription avec langue optionnelle
        if lang_codes[language] and lang_codes[language] != "auto":
            transcription_text = transcriber.transcribe(audio_path)
        else:
            transcription_text = transcriber.transcribe(audio_path)

        progress_bar.progress(80, text="Transcription reçue. Finalisation...")
        status_placeholder.info("✍️ **Étape 3/3 : Finalisation du résultat...**")

        # Calcul du temps écoulé
        elapsed_time = time.time() - start_time
        time_placeholder.success(f"⏱️ **Temps total : {elapsed_time:.2f} secondes**")

        # ÉTAPE 3: Affichage des résultats
        progress_bar.progress(100, text="Terminé !")
        status_placeholder.success("✅ **Transcription terminée avec succès !**")

        # Sauvegarde dans la session
        st.session_state.current_transcription = transcription_text
        st.session_state.current_source = input_source.name if hasattr(input_source, 'name') else input_source
        st.session_state.current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.formatted_text = None  # Reset formatage
        
        # Sauvegarde dans l'historique
        st.session_state.history.append({
            "timestamp": st.session_state.current_time,
            "source": st.session_state.current_source,
            "text": transcription_text[:100] + "...",  # Aperçu
            "full_text": transcription_text
        })

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

# --- AFFICHAGE DE LA TRANSCRIPTION (si disponible) ---
if st.session_state.current_transcription:
    st.divider()
    st.subheader("📝 Résultat de la transcription")
    
    # Afficher la transcription brute
    st.text_area("Texte transcrit", st.session_state.current_transcription, height=250)
    
    # Options de téléchargement pour le texte brut
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 Télécharger en .txt",
            data=st.session_state.current_transcription,
            file_name="transcription_voxwhisper.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col_dl2:
        # Version SRT simplifiée
        st.download_button(
            label="📥 Télécharger en .srt",
            data="1\n00:00:00,000 --> 00:00:02,000\n" + st.session_state.current_transcription,
            file_name="subtitles.srt",
            mime="text/plain",
            use_container_width=True
        )
    
    # --- SECTION GEMINI (formatage optionnel) ---
    if gemini_available:
        st.divider()
        st.subheader("✨ Améliorer avec Gemini")
        st.markdown("Choisissez un style de formatage pour améliorer votre transcription :")
        
        # Boutons de formatage
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        
        with col_g1:
            if st.button("🧹 Nettoyer", use_container_width=True):
                with st.spinner("Gemini nettoie le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription, 
                        style="propre"
                    )
                    st.session_state.format_style = "nettoyé"
                    st.session_state.show_compare = False
                    st.rerun()
        
        with col_g2:
            if st.button("📑 Structurer", use_container_width=True):
                with st.spinner("Gemini structure le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription, 
                        style="structure"
                    )
                    st.session_state.format_style = "structuré"
                    st.session_state.show_compare = False
                    st.rerun()
        
        with col_g3:
            if st.button("📌 Résumer", use_container_width=True):
                with st.spinner("Gemini résume le texte..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription, 
                        style="resume"
                    )
                    st.session_state.format_style = "résumé"
                    st.session_state.show_compare = False
                    st.rerun()
        
        with col_g4:
            if st.button("🗣️ Bambara", use_container_width=True):
                with st.spinner("Gemini formate en bambara..."):
                    formatter = GeminiFormatter(GEMINI_API_KEY)
                    st.session_state.formatted_text = formatter.format_transcription(
                        st.session_state.current_transcription, 
                        style="bambara"
                    )
                    st.session_state.format_style = "bambara"
                    st.session_state.show_compare = False
                    st.rerun()
        
        # Affichage du texte formaté si disponible
        if st.session_state.formatted_text:
            st.divider()
            
            # Options de comparaison
            col_comp1, col_comp2 = st.columns([3, 1])
            with col_comp1:
                st.subheader(f"📋 Texte {st.session_state.format_style}")
            with col_comp2:
                if st.button("🔄 Comparer avec l'original", use_container_width=True):
                    st.session_state.show_compare = not st.session_state.show_compare
                    st.rerun()
            
            # Mode comparaison ou simple affichage
            if st.session_state.show_compare:
                col_orig, col_form = st.columns(2)
                with col_orig:
                    st.markdown("**📄 Original**")
                    st.text_area("", st.session_state.current_transcription, height=250, key="orig_compare", label_visibility="collapsed")
                with col_form:
                    st.markdown(f"**✨ {st.session_state.format_style.capitalize()}**")
                    st.text_area("", st.session_state.formatted_text, height=250, key="form_compare", label_visibility="collapsed")
            else:
                st.text_area("", st.session_state.formatted_text, height=250, label_visibility="collapsed")
            
            # Bouton de téléchargement pour la version formatée
            st.download_button(
                label=f"📥 Télécharger version {st.session_state.format_style}",
                data=st.session_state.formatted_text,
                file_name=f"transcription_{st.session_state.format_style}.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("💡 Pour activer le formatage Gemini, ajoutez votre clé API Gemini dans les secrets Streamlit.")

# --- AFFICHAGE DE L'HISTORIQUE ---
with st.sidebar:
    st.divider()
    st.header("📜 Historique")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-10:])):
            with st.expander(f"🕒 {item['timestamp']}"):
                st.markdown(f"**Source:** {item['source']}")
                st.markdown(f"**Aperçu:** {item['text']}")
                if st.button("Charger cette transcription", key=f"hist_{i}"):
                    st.session_state.current_transcription = item['full_text']
                    st.session_state.current_source = item['source']
                    st.session_state.current_time = item['timestamp']
                    st.session_state.formatted_text = None
                    st.rerun()
    else:
        st.info("Aucune transcription pour le moment.")

# --- PIED DE PAGE ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <strong>VoxWhisper Mali</strong> — Propulsé par l'IA Groq • Formaté par Gemini • Conçu pour le Mali 🇲🇱<br>
        <small>Français • English • Bambara • Paiements sécurisés via Orange Money & Wave (à venir)</small>
    </div>
    """,
    unsafe_allow_html=True
)


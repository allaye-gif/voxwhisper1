"""
Module de transcription multi-langues
Détecte et utilise le bon modèle selon la langue
"""
import streamlit as st
from src.groq_client import GroqTranscriber
from src.bambara_transcriber import BambaraTranscriber

class MultiLangueTranscriber:
    """Transcription intelligente qui choisit le bon modèle"""
    
    def __init__(self, groq_api_key, bambara_model="small"):
        self.groq = GroqTranscriber(groq_api_key)
        self.bambara = BambaraTranscriber(bambara_model)
        self.bambara_model_loaded = False
    
    def detect_language_mix(self, audio_path):
        """
        Détecte si l'audio contient du bambara
        Utilise Gemini pour une détection rapide (si disponible)
        """
        try:
            # Option 1: Utiliser Gemini si disponible
            from src.gemini_formatter import GeminiFormatter
            import streamlit as st
            
            if "GEMINI_API_KEY" in st.secrets:
                # Transcrire un petit segment pour détection
                # (logique complexe - simplifiée ici)
                pass
        except:
            pass
        
        # Par défaut, on utilise l'option choisie par l'utilisateur
        return "mixed"
    
    def transcribe(self, audio_path, language_choice="auto"):
        """
        Transcrit en choisissant automatiquement le bon modèle
        
        Args:
            audio_path: chemin vers le fichier audio
            language_choice: "auto", "fr", "bm", "mixed"
        """
        if language_choice == "bm":
            # Forcer bambara
            return self.bambara.transcribe(audio_path)
        elif language_choice == "fr":
            # Forcer français (Groq)
            return self.groq.transcribe(audio_path)
        elif language_choice == "mixed":
            # Mélange: on utilise Groq puis on post-traite avec Gemini
            text = self.groq.transcribe(audio_path)
            
            # Utiliser Gemini pour mieux gérer le bambara dans le texte
            try:
                from src.gemini_formatter import GeminiFormatter
                if "GEMINI_API_KEY" in st.secrets:
                    formatter = GeminiFormatter(st.secrets["GEMINI_API_KEY"])
                    text = formatter.format_transcription(text, style="bambara")
            except:
                pass
            return text
        else:  # auto
            # Détection automatique (simplifié)
            # Dans une vraie implémentation, on analyserait l'audio
            # Pour l'instant, on utilise un paramètre utilisateur
            return self.groq.transcribe(audio_path)

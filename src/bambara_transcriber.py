"""
Module de transcription pour le bambara - Approche hybride
Utilise Groq pour la transcription brute + Gemini pour la correction bambara
"""
import streamlit as st
from src.groq_client import GroqTranscriber

class BambaraTranscriber:
    """Transcription bambara par approche hybride (Whisper + Gemini)"""
    
    def __init__(self, groq_api_key, gemini_api_key=None):
        self.groq = GroqTranscriber(groq_api_key)
        self.gemini_available = gemini_api_key is not None
        if self.gemini_available:
            from src.gemini_formatter import GeminiFormatter
            self.gemini = GeminiFormatter(gemini_api_key)
    
    def transcribe(self, audio_path):
        """
        Transcrit un fichier audio avec correction bambara
        """
        try:
            # Étape 1: Transcription brute avec Groq (Whisper)
            # Whisper détecte automatiquement les langues mélangées
            st.info("🎤 Transcription audio en cours...")
            raw_text = self.groq.transcribe(audio_path)
            
            # Étape 2: Si Gemini est disponible, corriger pour le bambara
            if self.gemini_available:
                st.info("🔄 Amélioration de la transcription bambara...")
                
                # Prompt spécial pour corriger le bambara
                prompt = f"""
                Cette transcription contient du bambara et du français.
                Corrige-la en suivant ces règles:
                1. Garde TOUS les mots dans leur langue originale (ne traduis pas)
                2. Corrige uniquement les fautes d'orthographe évidentes
                3. Remets les tons bambara si nécessaire (ɛ, ɔ, ɲ, ŋ)
                4. Garde la structure naturelle des phrases
                5. Si un mot bambara est mal transcrit, essaie de le deviner par le contexte
                
                Transcription originale:
                {raw_text}
                
                Transcription corrigée:
                """
                
                corrected_text = self.gemini.model.generate_content(prompt).text
                return corrected_text
            else:
                return raw_text
                
        except Exception as e:
            raise Exception(f"Erreur de transcription bambara: {str(e)}")
    
    @staticmethod
    def get_model_info():
        return {
            "hybrid": {
                "name": "Whisper + Gemini",
                "wer": "Variable (corrigé par IA)",
                "license": "Commercial",
                "description": "Approche hybride fiable pour production"
            }
        }

"""
Module de formatage avec Google Gemini
Version robuste avec gestion d'erreurs et prompts optimisés
"""
import streamlit as st
import google.generativeai as genai
import time

class GeminiFormatter:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Utiliser gemini-1.5-flash (le plus rapide et fiable)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def format_transcription(self, raw_text, style="propre", max_retries=2):
        """
        Formate avec retry automatique
        """
        prompts = {
            "propre": f"Nettoie cette transcription (ponctuation, fautes, répétitions) sans changer le sens:\n\n{raw_text}",
            "structure": f"Structure cette transcription en paragraphes logiques:\n\n{raw_text}",
            "resume": f"Résume cette transcription en 3-5 phrases:\n\n{raw_text}",
            "bambara": f"""
            Transcription d'un audio contenant du bambara et français.
            Règles:
            - Garde chaque mot dans sa langue d'origine
            - Corrige l'orthographe bambara (utilise ɛ, ɔ, ɲ, ŋ)
            - Ajoute la ponctuation
            - Ne traduis PAS
            - Garde les expressions typiques
            
            Texte: {raw_text}
            """
        }
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompts.get(style, prompts["propre"]))
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"{raw_text}\n\n[Note: Formatage temporairement indisponible]"
                time.sleep(1)
        return raw_text

"""
Module de formatage de texte avec Google Gemini
Permet de nettoyer et structurer les transcriptions
"""
import streamlit as st
import google.generativeai as genai

class GeminiFormatter:
    """Formate les transcriptions brutes avec l'IA Gemini"""

    def __init__(self, api_key):
        """Initialise le client Gemini"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def format_transcription(self, raw_text, style="propre"):
        """
        Formate une transcription brute selon le style demandé

        Styles disponibles:
        - "propre": Nettoie la ponctuation, corrige les fautes légères
        - "structure": Ajoute des paragraphes, structure logique
        - "resume": Résumé concis du contenu
        - "bambara": Formatage spécial pour le bambara
        """
        prompts = {
            "propre": f"""
            Nettoie cette transcription audio:
            - Corrige la ponctuation (points, virgules, majuscules)
            - Corrige les fautes d'orthographe évidentes
            - Garde le sens exact, ne change pas les mots
            - Supprime les répétitions inutiles (euh, hum, etc.)
            
            Texte brut: {raw_text}
            
            Texte nettoyé:
            """,
            
            "structure": f"""
            Structure cette transcription audio:
            - Divise en paragraphes logiques
            - Ajoute des titres de sections si pertinent
            - Mets en forme les dialogues (si plusieurs personnes)
            - Corrige la ponctuation
            
            Texte brut: {raw_text}
            
            Texte structuré:
            """,
            
            "resume": f"""
            Résume cette transcription en 3-5 phrases clés:
            - Garde l'essentiel du message
            - Format concis et professionnel
            
            Texte: {raw_text}
            
            Résumé:
            """,
            
            "bambara": f"""
            Nettoie cette transcription en bambara:
            - Garde la structure naturelle de la langue bambara
            - Corrige la ponctuation de base
            - Maintient les expressions typiques
            - Si des mots sont en français, garde-les tels quels
            
            Texte brut: {raw_text}
            
            Texte nettoyé en bambara:
            """
        }

        prompt = prompts.get(style, prompts["propre"])
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erreur de formatage: {str(e)}\n\nTexte original:\n{raw_text}"

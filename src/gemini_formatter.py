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
        # Utiliser le bon nom de modèle (sans flash car c'est l'ancien nom)
        self.model = genai.GenerativeModel('gemini-1.5-pro')  # ou 'gemini-pro'

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
            "propre": f"""Nettoie cette transcription audio en corrigeant uniquement:
- La ponctuation (points, virgules, majuscules)
- Les fautes d'orthographe évidentes
- Supprime les répétitions inutiles (euh, hum, etc.)
Ne change PAS le sens et ne réécris PAS les phrases.

Texte brut: {raw_text}

Texte nettoyé:""",
            
            "structure": f"""Structure cette transcription audio:
- Divise en paragraphes logiques
- Ajoute des titres de sections si pertinent
- Mets en forme les dialogues (si plusieurs personnes)
- Corrige la ponctuation

Texte brut: {raw_text}

Texte structuré:""",
            
            "resume": f"""Résume cette transcription en 3-5 phrases clés:
- Garde l'essentiel du message
- Format concis

Texte: {raw_text}

Résumé:""",
            
            "bambara": f"""Nettoie cette transcription qui mélange bambara et français:
- Garde la structure naturelle de la langue bambara
- Corrige la ponctuation de base
- Maintient les expressions typiques
- Si des mots sont en français, garde-les tels quels
- Ne traduis PAS, garde la langue originale

Texte brut: {raw_text}

Texte nettoyé en gardant le mélange bambara-français:"""
        }

        prompt = prompts.get(style, prompts["propre"])
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erreur de formatage: {str(e)}\n\nTexte original:\n{raw_text}"

"""
Module client pour l'API Groq.
Gère la transcription via l'API Groq.
"""
import os
import streamlit as st
from groq import Groq

class GroqTranscriber:
    """Client pour l'API de transcription Groq."""

    def __init__(self, api_key):
        """Initialise le client Groq avec la clé API."""
        if not api_key:
            raise ValueError("La clé API Groq est manquante. Vérifiez vos secrets Streamlit.")
        self.client = Groq(api_key=api_key)

    def transcribe(self, audio_file_path):
        """
        Envoie un fichier audio à l'API Groq pour transcription.
        Retourne le texte transcrit.
        """
        try:
            with open(audio_file_path, "rb") as file:
                # Utilisation du modèle whisper-large-v3
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_file_path), file.read()),
                    model="whisper-large-v3",
                    response_format="text",  # On veut du texte brut, pas du JSON
                    language="fr",  # Peut être optionnel, mais aide pour le français du Mali
                )
            return transcription
        except Exception as e:
            # Gestion fine des erreurs API
            error_message = str(e)
            if "rate_limit" in error_message.lower():
                raise Exception("Limite de taux de l'API atteinte. Veuillez réessayer dans quelques instants.")
            elif "authentication" in error_message.lower():
                raise Exception("Erreur d'authentification API. Contactez le support.")
            elif "timeout" in error_message.lower():
                raise Exception("L'API a mis trop de temps à répondre. Vérifiez votre connexion.")
            else:
                raise Exception(f"Erreur de transcription Groq : {error_message}")
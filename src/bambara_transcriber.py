"""
Module de transcription spécialisé pour le bambara
Version simplifiée et robuste qui évite les conflits de tokenizers
"""
import streamlit as st
import torch
import os
import tempfile
import subprocess
import numpy as np

class BambaraTranscriber:
    """Transcription spécialisée pour la langue bambara - Version simplifiée"""
    
    # Modèles disponibles
    MODELS = {
        "small": {
            "name": "kalilouisangare/whisper-small-bambara-v2-kis",
            "wer": "43.70%",
            "license": "CC BY 4.0",
            "description": "Modèle open source recommandé"
        },
        "v1": {
            "name": "MALIBA-AI/bambara-asr-v1",
            "wer": "61.74%",
            "license": "Apache 2.0",
            "description": "Version commerciale"
        }
    }
    
    def __init__(self, model_key="small"):
        """
        Initialise le transcriber bambara
        """
        self.model_key = model_key
        self.model_name = self.MODELS[model_key]["name"]
        self.pipe = None
        
    def load_model(self):
        """Charge le modèle avec gestion d'erreurs améliorée"""
        if self.pipe is None:
            with st.spinner(f"Chargement du modèle bambara..."):
                try:
                    # Import à l'intérieur pour éviter les conflits au chargement
                    from transformers import pipeline
                    
                    # Configuration du device
                    device = 0 if torch.cuda.is_available() else -1
                    
                    # Pipeline simplifié sans paramètres complexes
                    self.pipe = pipeline(
                        task="automatic-speech-recognition",
                        model=self.model_name,
                        device=device
                    )
                    
                except Exception as e:
                    st.error(f"Erreur de chargement détaillée: {str(e)}")
                    
                    # Solution de secours: retour à un modèle plus simple
                    try:
                        st.warning("Tentative avec modèle de secours...")
                        self.pipe = pipeline(
                            task="automatic-speech-recognition",
                            model="openai/whisper-small",
                            device=device
                        )
                    except:
                        raise Exception("Impossible de charger un modèle de transcription")
                        
        return self.pipe
    
    def transcribe(self, audio_path):
        """Transcrit un fichier audio en bambara"""
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(audio_path):
                raise Exception(f"Fichier audio introuvable: {audio_path}")
            
            # Charger le modèle
            pipe = self.load_model()
            
            # Transcription simple
            result = pipe(audio_path)
            
            return result["text"]
            
        except Exception as e:
            raise Exception(f"Erreur de transcription bambara: {str(e)}")
    
    @staticmethod
    def get_model_info():
        """Retourne les infos sur les modèles disponibles"""
        return BambaraTranscriber.MODELS

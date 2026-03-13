"""
Module de transcription spécialisé pour le bambara
Utilise des modèles fine-tunés par des chercheurs maliens
Version corrigée sans conflit de tokenizers
"""
import streamlit as st
import torch
import tempfile
import os
import warnings
warnings.filterwarnings("ignore", message=".*TokenizersBackend.*")

# Import conditionnel pour éviter les conflits
try:
    from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    st.error(f"Erreur d'import transformers: {e}")

class BambaraTranscriber:
    """Transcription spécialisée pour la langue bambara"""
    
    # Modèles disponibles
    MODELS = {
        "best": "MALIBA-AI/bambara-asr-v3",  # Meilleur mais non-commercial
        "small": "kalilouisangare/whisper-small-bambara-v2-kis",  # Open source
        "v1": "MALIBA-AI/bambara-asr-v1"  # Commercial (moins précis)
    }
    
    def __init__(self, model_key="small"):
        """
        Initialise le transcriber bambara
        
        Args:
            model_key: "best" (non-commercial), "small" (open source), ou "v1" (commercial)
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers n'est pas correctement installé")
            
        self.model_key = model_key
        self.model_id = self.MODELS[model_key]
        self.pipe = None
        
    def load_model(self):
        """Charge le modèle (peut prendre du temps la première fois)"""
        if self.pipe is None:
            with st.spinner(f"Chargement du modèle bambara ({self.model_key})..."):
                try:
                    device = "cuda:0" if torch.cuda.is_available() else "cpu"
                    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                    
                    # Version simplifiée qui évite les problèmes de tokenizers
                    self.pipe = pipeline(
                        "automatic-speech-recognition",
                        model=self.model_id,
                        device=device,
                        torch_dtype=torch_dtype
                    )
                except Exception as e:
                    st.error(f"Erreur de chargement du modèle: {e}")
                    raise
        return self.pipe
    
    def transcribe(self, audio_path):
        """Transcrit un fichier audio en bambara"""
        try:
            pipe = self.load_model()
            result = pipe(audio_path)
            return result["text"]
        except Exception as e:
            raise Exception(f"Erreur de transcription bambara: {str(e)}")
    
    @staticmethod
    def get_model_info():
        """Retourne les infos sur les modèles disponibles"""
        return {
            "best": {
                "name": "MALIBA-AI/bambara-asr-v3",
                "wer": "45.73%",
                "cer": "13.45%",
                "license": "Non-commercial (CC-BY-NC-4.0)",
                "description": "Meilleur modèle actuel, mais usage non-commercial uniquement"
            },
            "small": {
                "name": "whisper-small-bambara-v2-kis",
                "wer": "43.70%",
                "cer": "21.38%",
                "license": "CC BY 4.0",
                "description": "Modèle open source, bon compromis"
            },
            "v1": {
                "name": "MALIBA-AI/bambara-asr-v1",
                "wer": "61.74%",
                "cer": "17.90%",
                "license": "Apache 2.0",
                "description": "Version commerciale, moins précise"
            }
        }

"""
Module de transcription spécialisé pour le bambara
Utilise des modèles fine-tunés par des chercheurs maliens
"""
import streamlit as st
import torch
import tempfile
import os
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor

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
        self.model_key = model_key
        self.model_id = self.MODELS[model_key]
        self.pipe = None
        
    def load_model(self):
        """Charge le modèle (peut prendre du temps la première fois)"""
        if self.pipe is None:
            with st.spinner(f"Chargement du modèle bambara ({self.model_key})..."):
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
                # Charger le modèle et le processor
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True,
                    use_safetensors=True
                )
                model.to(device)
                
                processor = AutoProcessor.from_pretrained(self.model_id)
                
                # Créer le pipeline
                self.pipe = pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor,
                    device=device,
                )
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

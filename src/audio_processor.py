"""
Module de prétraitement audio.
Responsabilités : Conversion, compression, validation, extraction YouTube.
"""
import os
import tempfile
import subprocess
import streamlit as st
from pydub import AudioSegment
import yt_dlp
import validators

# Configuration de pydub pour utiliser ffmpeg système
AudioSegment.converter = "ffmpeg"

class AudioProcessor:
    """Gère toute la logique de traitement des fichiers audio."""

    # Limite de taille pour l'API Groq (en octets)
    MAX_FILE_SIZE_BYTES = 24 * 1024 * 1024
    TARGET_BITRATE = "64k"

    @staticmethod
    def check_ffmpeg():
        """Vérifie si FFmpeg est installé et accessible."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def extract_youtube_audio(url):
        """
        Télécharge l'audio d'une vidéo YouTube et le convertit en MP3.
        Retourne le chemin du fichier audio.
        """
        if not validators.url(url):
            raise ValueError("URL YouTube invalide.")

        temp_dir = tempfile.gettempdir()
        output_template = os.path.join(temp_dir, 'yt_audio_%(id)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base_filename = ydl.prepare_filename(info).rsplit('.', 1)[0]
                audio_path = f"{base_filename}.mp3"
                return audio_path
        except Exception as e:
            raise Exception(f"Échec du téléchargement YouTube : {str(e)}")

    @staticmethod
    def enhance_audio_for_speech(input_path, output_path):
        """
        Améliore la qualité audio pour la transcription vocale.
        - Réduction du bruit de fond
        - Filtrage pour isoler la voix
        - Normalisation du volume
        """
        try:
            # Commande ffmpeg pour améliorer la voix
            # highpass: coupe les basses fréquences (<200Hz)
            # lowpass: coupe les hautes fréquences (>3000Hz)
            # afftdn: réduction de bruit adaptative
            # volume: amplification légère
            cmd = [
                'ffmpeg', '-i', input_path,
                '-af', 'highpass=f=200, lowpass=f=3000, afftdn=nf=-25, volume=2',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return output_path
            else:
                # Si l'amélioration échoue, retourner le fichier original
                return input_path
        except Exception as e:
            # En cas d'erreur, continuer sans amélioration
            return input_path

    @staticmethod
    def prepare_audio_file(uploaded_file):
        """
        Prend un fichier uploadé, le convertit en MP3 et le compresse si nécessaire.
        Applique une amélioration pour la voix.
        Retourne le chemin du fichier MP3 prêt à l'emploi.
        """
        # Sauvegarder le fichier uploadé
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_input:
            tmp_input.write(uploaded_file.getvalue())
            input_path = tmp_input.name

        # Fichier de sortie temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_output:
            output_path = tmp_output.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix="_enhanced.mp3") as tmp_enhanced:
            enhanced_path = tmp_enhanced.name

        try:
            # Charger l'audio avec pydub
            audio = AudioSegment.from_file(input_path)

            # Exporter en MP3 avec bitrate contrôlé
            audio.export(output_path, format="mp3", bitrate=AudioProcessor.TARGET_BITRATE)

            # Vérifier la taille
            file_size = os.path.getsize(output_path)
            if file_size > AudioProcessor.MAX_FILE_SIZE_BYTES:
                audio.export(output_path, format="mp3", bitrate="32k")
            
            # Améliorer l'audio pour la voix (réduction bruit, isolation voix)
            final_path = AudioProcessor.enhance_audio_for_speech(output_path, enhanced_path)
            
            return final_path

        except Exception as e:
            raise Exception(f"Échec du traitement audio : {str(e)}")
        finally:
            # Nettoyer les fichiers temporaires
            for path in [input_path, output_path]:
                if os.path.exists(path) and path != final_path:
                    try:
                        os.unlink(path)
                    except:
                        pass

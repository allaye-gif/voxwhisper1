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

    # Limite de taille pour l'API Groq (en octets) - on vise 24MB pour être sûr
    MAX_FILE_SIZE_BYTES = 24 * 1024 * 1024
    TARGET_BITRATE = "64k"  # Bitrate pour la compression (excellent pour la parole)

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
                'preferredquality': '64',  # Qualité faible pour économiser du temps/taille
            }],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Le chemin final après post-traitement
                # yt-dlp ajoute l'ID de la vidéo au nom
                base_filename = ydl.prepare_filename(info).rsplit('.', 1)[0]
                audio_path = f"{base_filename}.mp3"
                return audio_path
        except Exception as e:
            raise Exception(f"Échec du téléchargement YouTube : {str(e)}")

    @staticmethod
    def prepare_audio_file(uploaded_file):
        """
        Prend un fichier uploadé, le convertit en MP3 et le compresse si nécessaire.
        Retourne le chemin du fichier MP3 prêt à l'emploi.
        """
        # Sauvegarder le fichier uploadé dans un fichier temporaire avec son extension d'origine
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_input:
            tmp_input.write(uploaded_file.getvalue())
            input_path = tmp_input.name

        # Fichier de sortie temporaire (toujours en .mp3)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_output:
            output_path = tmp_output.name

        try:
            # Charger l'audio avec pydub (supporte énormément de formats)
            # Gère .opus, .ogg, .m4a, etc.
            audio = AudioSegment.from_file(input_path)

            # Exporter en MP3 avec un bitrate contrôlé
            audio.export(output_path, format="mp3", bitrate=AudioProcessor.TARGET_BITRATE)

            # Vérifier la taille du fichier final
            file_size = os.path.getsize(output_path)
            if file_size > AudioProcessor.MAX_FILE_SIZE_BYTES:
                # Si toujours trop gros, on peut re-compresser avec un bitrate plus faible
                st.warning("Le fichier est volumineux. Une compression supplémentaire est appliquée.")
                audio.export(output_path, format="mp3", bitrate="32k")

            return output_path

        except Exception as e:
            raise Exception(f"Échec du traitement audio : {str(e)}. Format non supporté ou fichier corrompu.")
        finally:
            # Nettoyer le fichier d'entrée temporaire
            if os.path.exists(input_path):
                os.unlink(input_path)
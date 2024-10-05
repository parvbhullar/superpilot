# script to dub a voice from one language to another mostly from en to indian languages
import os
import whisper
from openai import OpenAI
from elevenlabs import generate, play, set_api_key,clone
import io
from pydub import AudioSegment
import wave


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
set_api_key(os.environ.get("ELEVEN_LABS_KEY"))


class VoiceDub():
    def __init__(self, audio_path, srclang, tgtlang,clone_flag=False,clone_voice_description=None,clone_voice_files=None,clone_name=None):
        self.audio_path = audio_path
        self.srclang = srclang
        self.tgtlang = tgtlang
        self.model = None  # Initialize model storage
        self.clone_flag = clone_flag
        self.clone_voice_description = clone_voice_description
        self.clone_voice_files = clone_voice_files
        self.clone_name = clone_name

    # Initialize the speech-to-text model
    def initialize_speech_to_text(self, model_name="base"):
        # Load the model only if it hasn't been loaded yet
        if self.model is None:
            self.model = whisper.load_model(model_name)


    # Convert audio to text
    def speech_to_text(self, audio_path):
        # Ensure model is loaded before using it
        if self.model is None:
            raise ValueError("Speech-to-text model not initialized. Call initialize_speech_to_text() first.")
        text = self.model.transcribe(audio_path)
        return text

    # translate text from one language to another using GPT4
    def translate_text(self, text, src_lang, tgt_lang):
        query = f"Translate the following text from {src_lang} to {tgt_lang}: {text}"
        response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that translate text from one language to another and only return translated text."},
                    {"role": "user", "content": query}
            ]
            )
        return response.choices[0].message.content

    def save_audio_bytes(audio_bytes, output_filename, format="mp3", bitrate=None, sample_width=None):
        if format not in ("mp3", "wav"):
            raise ValueError("Invalid format. Valid formats are 'mp3' and 'wav'.")

        with io.BytesIO(audio_bytes) as audio_file:
            segment = AudioSegment.from_file(audio_file)

            if format == "mp3":
                segment.export(output_filename, format="mp3", bitrate=bitrate)
            elif format == "wav":
                with wave.open(output_filename, "wb") as wav_file:
                    nchannels = segment.channels
                    sample_width = segment.sample_width if sample_width is None else sample_width
                    framerate = segment.frame_rate
                    comptype = "NONE"  # Uncompressed audio (PCM)
                    compname = "not compressed"
                    wav_file.setparams((nchannels, sample_width, framerate, segment.frame_count, comptype, compname))
                    wav_file.writeframes(segment.raw_data)
            else:
                raise ValueError("Unexpected format:", format)

    def text_to_audio(self, text, lang,output_filename, format="mp3", bitrate=None, sample_width=None):
        audio = generate(
                text = text,
                voice="Rachel",
                model="eleven_multilingual_v2"
            )
        filename = output_filename + "." +format
        with open(filename, "wb") as f:
            f.write(audio)

        return filename

    def text_to_audio_clone(self, text, lang, output_filename, clone_name, clone_voice_files, clone_voice_description=None, bitrate=None, sample_width=None,format="mp3"):
        voice = clone(
            name=clone_name,
            description=clone_voice_description, # Optional
            files=clone_voice_files,
            )
        audio = generate(
                text = text,
                voice=voice,
                model="eleven_multilingual_v2"
            )
        filename = output_filename + "." +format
        with open(filename, "wb") as f:
            f.write(audio)

        return filename


    def dub(self, output_filename):
        self.initialize_speech_to_text()
        print("STT")
        text = self.speech_to_text(self.audio_path)
        print("TRANSLATING")
        translated_text = self.translate_text(text, self.srclang, self.tgtlang)
        print("TTS")
        if self.clone_flag:
            audio_file = self.text_to_audio_clone(translated_text, self.tgtlang, output_filename, clone_name=self.clone_name, clone_voice_files=self.clone_voice_files, clone_voice_description=self.clone_voice_description)
        else:
            audio_file = self.text_to_audio(translated_text, self.tgtlang, output_filename)
        return audio_file


if __name__ == "__main__":
    audio_path = "Ravi1.mp3"
    srclang = "en"
    tgtlang = "hi"
    output_filename = "dubbed_audio"
    clone_flag = True
    clone_name = "Ravi"
    clone_voice_description = "An old indian male voice with a calm tone. Perfect for commentry of cricket"
    clone_voice_files = ["Ravi1.mp3","Ravi2.mp3","Ravi3.mp3"]
    dub = VoiceDub(audio_path, srclang, tgtlang,clone_flag=True,clone_voice_description=clone_voice_description,clone_voice_files=clone_voice_files,clone_name=clone_name)
    dub.initialize_speech_to_text(model_name="tiny")
    audio_file = dub.dub(output_filename)
    play(audio_file)



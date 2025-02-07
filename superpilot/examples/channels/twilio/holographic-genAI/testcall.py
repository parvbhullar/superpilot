from gtts import gTTS
import pyaudio
import wave

def generate_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")

generate_speech("Hello, welcome to LiveKit!")

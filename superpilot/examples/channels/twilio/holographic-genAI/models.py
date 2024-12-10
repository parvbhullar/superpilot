import os
import logging
import numpy as np
import soundfile as sf
import noisereduce as nr
from livekit import rtc
from livekit.plugins import openai
from livekit.agents import llm
from livekit.agents.multimodal import MultimodalAgent
import asyncio
import time
import pyttsx3
import gender_guesser.detector as gender_detector


logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

class OpenAIRealtimeModel:
    """हिंदी भाषा समर्थन के साथ OpenAI रियलटाइम मॉडल को कॉन्फ़िगर करने के लिए क्लास। 
       यह एजेंट उपयोगकर्ता को नई संपत्ति खरीदने के लिए सहमत करने का प्रयास करेगा।"""

    def __init__(self):
        self.model = openai.realtime.RealtimeModel(
            instructions=(
                "आप एक रियल एस्टेट प्रॉपर्टी सलाहकार हैं। उपयोगकर्ता के साथ आपका इंटरफ़ेस आवाज होगा। "
                "आपका मुख्य उद्देश्य उपयोगकर्ता को यह विश्वास दिलाना है कि दी गई संपत्ति उनके लिए एक बेहतरीन विकल्प है। "
                "जब आप उपयोगकर्ता से बातचीत शुरू करें, तो सबसे पहले कहें: "
                "नमस्ते सर, मैं आपको प्रॉपर्टीज़ के बारे में कुछ जानकारी देना चाहती हूँ। क्या मैं आपका कुछ कीमती समय ले सकती हूँ। "
                "इसके बाद पूछें: 'सर, आप किस तरह की प्रॉपर्टी ढूंढ रहे हैं - कमर्शियल, होम, या कुछ और?' "
                "अगर उपयोगकर्ता किसी प्रॉपर्टी की तलाश में है, तो पूछें: 'सर, आप किस जगह प्रॉपर्टी देख रहे हैं?' "
                "इसके बाद पूछें: 'प्रॉपर्टी का आकार कितना होना चाहिए आपके हिसाब से?' "
                "फिर पूछें: 'क्या आप फर्निश्ड या अनफर्निश्ड प्रॉपर्टी देख रहे हैं?' "
                "अगर उपयोगकर्ता किसी प्रॉपर्टी के बारे में बताता है, तो सुझाव दें: 'यह प्रॉपर्टी आपके लिए बहुत फायदेमंद रहेगी, "
                "क्योंकि यह सिटी के पास है। यहां बैंक, हॉस्पिटल, और मार्केट जैसी सुविधाएं उपलब्ध हैं जो आपकी दैनिक जरूरतों के लिए जरूरी हैं। "
                "यह प्रॉपर्टी खरीदने के लिए भी एक बेहतरीन विकल्प हो सकती है, या अगर आप किराये पर देख रहे हैं, तो किराया भी बहुत उचित है।' "
                "आप छोटे, स्पष्ट और उपयोगकर्ता को सहमत करने वाले उत्तर देंगी।"
            ),
            modalities=["audio", "text"],
        )
        self.tts_engine = pyttsx3.init()
        self.gender_detector = gender_detector.Detector()

    def get_response(self, input_text):
        """Fetches the response from the model and includes a pause for confirmation."""
        print("Processing your request...")
        time.sleep(2)  

        # Detect gender based on the input text (can be based on name or pronouns)
        user_gender = self.predict_gender(input_text)
        
        if user_gender == "male":
            self.say_response("नमस्ते सर, मैं आपको प्रॉपर्टीज़ के बारे में कुछ जानकारी देना चाहती हूँ। क्या मैं आपका कुछ कीमती समय ले सकती हूँ।")
        elif user_gender == "female":
            self.say_response("नमस्ते मैम, मैं आपको प्रॉपर्टीज़ के बारे में कुछ जानकारी देना चाहती हूँ। क्या मैं आपका कुछ कीमती समय ले सकती हूँ?")
        else:
            self.say_response("नमस्ते, मैं आपको प्रॉपर्टीज़ के बारे में कुछ जानकारी देना चाहती हूँ। क्या मैं आपका कुछ कीमती समय ले सकती हूँ?")

        # Continue with the rest of the conversation
        if "प्रॉपर्टी" in input_text and "कहाँ" in input_text:
            self.say_response("सर, आप किस जगह प्रॉपर्टी देख रहे हैं?")

        elif "आकार" in input_text:
            self.say_response("प्रॉपर्टी का आकार कितना होना चाहिए आपके हिसाब से?")

        elif "फर्निश्ड" in input_text or "अनफर्निश्ड" in input_text:
            self.say_response("क्या आप फर्निश्ड या अनफर्निश्ड प्रॉपर्टी देख रहे हैं?")

        elif "बैंक" in input_text or "सिटी" in input_text:
            self.say_response("क्या आपको अपनी प्रॉपर्टी बैंक के पास, यानी सिटी साइड में चाहिए?")

        else:
            self.say_response("मुझे खेद है, कृपया अपना प्रश्न दोबारा पूछें।")

    def say_response(self, message):
        """Helper method to speak the given message using text-to-speech"""
        print(message)
        self.tts_engine.say(message)
        self.tts_engine.runAndWait()
        time.sleep(3)

    def predict_gender(self, text):
        """Predict the gender of the user based on the input text."""
        words = text.split()
        if words:
            gender = self.gender_detector.get_gender(words[0])
            if gender == "male" or gender == "mostly_male":
                return "male"
            elif gender == "female" or gender == "mostly_female":
                return "female"
        return "unknown" 

    def get_model(self):
        """Returns the OpenAI Realtime Model"""
        return self.model

class MultimodalAgentHandler:
    """Handles the interaction with the multimodal agent"""

    def __init__(self, model):
        self.assistant = MultimodalAgent(model=model)

    def start_assistant(self, ctx, participant):
        """Starts the multimodal agent with the given context and participant."""
        logger.info("Starting assistant in MultimodalAgentHandler.")
        self.assistant.start(ctx.room, participant)

    @staticmethod
    def is_valid_speech(audio_data, threshold_db=-40):
        """Determine if the audio contains valid speech based on a decibel threshold."""
        if audio_data is None or len(audio_data) == 0:
            logger.warning("Empty or None audio data received.")
            return False

        rms = np.sqrt(np.mean(np.square(audio_data)))
        db = 20 * np.log10(rms) if rms > 0 else float('-inf')
        return db > threshold_db

    @staticmethod
    def reduce_noise(audio_data, noise_sample_rate=16000):
        """Apply noise reduction on the audio data."""
        try:
            if audio_data is None:
                logger.warning("No audio data provided for noise reduction.")
                return None
            reduced_noise = nr.reduce_noise(y=audio_data, sr=noise_sample_rate)
            logger.info("Noise reduction applied successfully.")
            return reduced_noise
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio_data

    async def ask_questions_continuously(self, ctx, participant: rtc.RemoteParticipant):
        """Start the assistant and keep asking questions regardless of user input"""
        try:
            self.assistant.start(ctx.room, participant)
            logger.info("Agent started successfully.")

            session = self.assistant.model.sessions[0]
            if not session:
                raise ValueError("Session not found in the assistant model.")

            questions = [
                "How are you feeling today?",
                "What can I help you with?",
                "Do you have any plans for today?",
                "Is there anything you'd like to know?",
            ]
            question_index = 0

            while True:
                audio_data = getattr(participant, "audio_data", None)
                if audio_data is None:
                    logger.warning("Participant audio data is not available.")
                    await asyncio.sleep(3)
                    continue

                clean_audio = self.reduce_noise(audio_data)
                if not self.is_valid_speech(clean_audio):
                    logger.warning("Invalid or low-quality speech detected.")
                    await asyncio.sleep(3)
                    continue

                session.create_message(
                    llm.ChatMessage(
                        role="assistant",
                        content=questions[question_index],
                    )
                )
                logger.info(f"Asked: {questions[question_index]}")

                question_index = (question_index + 1) % len(questions)

                await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"Error in multimodal agent: {e}")

async def main():
    openai_model = OpenAIRealtimeModel()
    agent_handler = MultimodalAgentHandler(openai_model.get_model())
    

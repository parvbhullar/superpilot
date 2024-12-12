import os
import logging
import numpy as np
import noisereduce as nr
from livekit import rtc
import speech_recognition as sr

from livekit.plugins import openai
from livekit.agents import llm
from livekit.agents.multimodal import MultimodalAgent
import asyncio

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

class OpenAIRealtimeModel:
    """
    OpenAI Realtime Model to configure a real estate agent interacting in Hindi.
    The agent will attempt to assist the user in finding a property and gather requirements through a conversational flow.
    """

    def __init__(self):
        self.model = openai.realtime.RealtimeModel(
            instructions=(
            "आप एक रियल एस्टेट प्रॉपर्टी सलाहकार हैं। उपयोगकर्ता के साथ आपका इंटरफ़ेस आवाज होगा। "
            "उपयोगकर्ता की आवाज के आधार पर 'सर' या 'मैम' का प्रयोग करें। "
            "'नमस्कार, मैं आपकी प्रॉपर्टी खोज में मदद करना चाहूंगी।' "
            "मुझे पता चला है कि आप प्रॉपर्टी देख रहे हैं। मेरे पास आपके लिए बेहतरीन ऑफर्स में प्रॉपर्टी उपलब्ध है। "
            "क्या मैं आपसे कुछ कीमती समय ले सकती हूँ?' "
            "बातचीत के अंत में, उनकी प्रॉपर्टी की कीमत, स्थान, क्षेत्रफल और अन्य विवरणों की पुष्टि करें।"
        ),
            modalities=["audio", "text"],
        )

    def say_response(self, response, gender=""):
        """Enhanced response with gender inclusion."""
        if gender.lower() == "male":
            response = f"{response} सर।"
        elif gender.lower() == "female":
            response = f"{response} मैम।"
        logger.info(f"Agent says: {response}")
        self.model.speak(response)

    async def gather_requirements(self):
        """Conversation flow to gather property requirements."""
        self.say_response("नमस्कार, मैं आपकी प्रॉपर्टी खोज में मदद करना चाहूंगी।", gender="")

        gender = await self.detect_gender()

        self.say_response("आप किस प्रकार की प्रॉपर्टी खोज रहे हैं?", gender=gender)
        await asyncio.sleep(5)

        self.say_response("आपका बजट कितना है?", gender=gender)
        await asyncio.sleep(5)

        self.say_response("आपको किस लोकेशन में प्रॉपर्टी चाहिए?", gender=gender)
        await asyncio.sleep(5)

        self.say_response("प्रॉपर्टी का क्षेत्रफल कितना होना चाहिए?", gender=gender)
        await asyncio.sleep(5)

        await self.confirm_details(gender)

    async def confirm_details(self, gender):
        """Confirmation of property details."""
        self.say_response(
            "मैं आपसे कुछ पुष्टि करना चाहती हूँ, जैसे कि आपने जो कहा है।", gender=gender
        )

        details = {
            "कीमत": "आपकी प्रॉपर्टी की कीमत क्या यही है?",
            "लोकेशन": "क्या यह सही लोकेशन है?",
            "क्षेत्रफल": "क्या यह क्षेत्रफल सही है?",
        }

        for key, question in details.items():
            self.say_response(question, gender=gender)
            if await self.get_confirmation():
                self.say_response(f"धन्यवाद, {key} की पुष्टि हो गई।", gender=gender)
            else:
                self.say_response(f"कृपया सही {key} बताएं।", gender=gender)


    async def get_confirmation(self):
        """Capture and interpret user input for yes/no confirmation."""
        response = await self.capture_user_input()  
        if response.lower() in ["yes", "haa", "haanji", "correct"]:
            return True
        elif response.lower() in ["no", "nahi", "galat"]:
            return False
        else:
            self.say_response("कृपया हाँ या नहीं में जवाब दें।")
            return await self.get_confirmation() 


    async def detect_gender(self):
        """Detect gender based on voice input."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logger.info("Listening for voice input to detect gender...")
            audio = recognizer.listen(source)

            try:
                
                if self.analyze_audio(audio) == "male":
                    return "male"
                else:
                    return "female"
            except Exception as e:
                logger.error(f"Error detecting gender: {e}")
                return "unknown"  
            
    def analyze_audio(self, audio):
        """Analyze audio to determine gender (stub)."""
       
        return "male" if np.random.rand() > 0.5 else "female"
    
    def get_model(self):
        """Return the realtime model."""
        return self.model

class MultimodalAgentHandler:
    """Handles the interaction with the multimodal agent."""

    def __init__(self, model):
        self.assistant = MultimodalAgent(model=model)

    def start_assistant(self, ctx, participant):
        """Starts the multimodal agent with the given context and participant."""
        logger.info("Starting assistant in MultimodalAgentHandler.")
        self.assistant.start(ctx.room, participant)

    @staticmethod
    def is_valid_speech(audio_data, threshold_db=-35):
        """Determine if the audio contains valid speech based on a decibel threshold."""
        if audio_data is None or len(audio_data) == 0:
            logger.warning("Empty or None audio data received.")
            return False

        rms = np.sqrt(np.mean(np.square(audio_data)))
        db = 20 * np.log10(rms) if rms > 0 else float('-inf')
        logger.debug(f"Audio decibel level: {db}")
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

    async def safe_model_response(self, session, message, retries=3, delay=2):
        """Retry mechanism to handle delayed responses."""
        for attempt in range(retries):
            try:
                response = session.create_message(llm.ChatMessage(role="assistant", content=message))
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(delay)
        logger.error("All retries failed.")
        return None

async def main():
    openai_model = OpenAIRealtimeModel()
    await openai_model.gather_requirements()

if __name__ == "__main__":
    asyncio.run(main())

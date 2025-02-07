import asyncio
import logging
import os
import random
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero, elevenlabs
import webrtcvad 

load_dotenv()
logger = logging.getLogger("voice-assistant")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class WebRTCNoiseSupressor:
    def __init__(self):
        self.vad = webrtcvad.Vad(2)  # Mode 2 for moderate aggressiveness
        logger.info("WebRTC noise suppression initialized")

    def process_audio(self, frame: rtc.AudioFrame):
        try:
            # Convert frame data to bytes
            pcm_data = frame.data.tobytes()
            
            # Check if we have enough samples for VAD (10ms at 16kHz = 160 samples * 2 bytes)
            if len(pcm_data) < 320:
                logger.warning("Frame too short for VAD")
                return frame
                
            # Process in 10ms chunks
            chunk_size = 320  # 10ms at 16kHz
            is_speech = False
            
            # Check each chunk for speech
            for i in range(0, len(pcm_data) - chunk_size + 1, chunk_size):
                chunk = pcm_data[i:i + chunk_size]
                if self.vad.is_speech(chunk, 16000):
                    is_speech = True
                    break
            
            if is_speech:
                return frame
            else:
                # Return silence frame of same length
                silence = b'\x00' * len(pcm_data)
                return rtc.AudioFrame(
                    data=silence,
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                    samples_per_channel=frame.samples_per_channel
                )
                
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return frame

class VoiceAssistant:
    def __init__(self, agent, noise_suppressor):
        self.agent = agent
        self.noise_suppressor = noise_suppressor
        self.tts_fallback_attempted = False
        self._is_running = True
        self.response_event = asyncio.Event()
        self.last_response = None
        
        # Initialize conversation state
        self.conversation_state = {
            "waiting_for_response": False,
            "user_details": {
                "name": "",
                "child_name": "",
                "child_grade": "",
                "location": "pune",
                "source": "instagram"
            }
        }
        
        # Hindi conversation script
        self.conversation_script = {
            "initial_greeting": (
                "Namaste! Main CuriousKid se Ahaana bol rahi hoon. Kya main {name} se baat kar rahi hoon?"
            ),
            "confirmation_prompts": {
                "retry1": "Kya aap confirm kar sakte hain ki aap {name} hi hain?",
                "retry2": "Maaf kijiye, kya aap {name} hi bol rahe hain?",
                "retry3": "Main confirm karna chahti hoon, kya aap {name} hain?"
            },
            "registration_confirmation": (
                "Mujhe pata chala ki aapne {source} pe register kiya tha aur CuriousKid ke "
                "Robotics aur AI courses mein interest dikhaya tha. Kya aapko yaad hai?"
            ),
            "availability_check": (
                "Main aapke bache ki STEM learning journey ke bare mein baat karna chahti hoon. "
                "Kya aapke paas kuch minute hain?"
            ),
            "student_details": (
                "Kya aap apne bache ka naam aur grade bata sakte hain?"
            ),
            "age_verification": (
                "Grade ke hisaab se, {child_name} ki umar {age} saal hogi. Kya yeh sahi hai?"
            ),
            "location_verification": (
                "Kya aap {location} mein rehte hain?"
            ),
            "technical_setup": (
                "Kya {child_name} ke paas laptop aur stable internet connection hai?"
            ),
            "professional_background": (
                "Aap kya karte hain?"
            ),
            "spouse_profession": (
                "Aapke spouse kya karte hain?"
            ),
            "course_interest": (
                "Robotics aur AI ke hamare advertisement ke baare mein aapne dekha. "
                "{child_name} ko register karne ka kya reason tha?"
            ),
            "company_overview": (
                "Bahut accha, {name}! CuriousKid India ki sabse badi innovation training company hai. "
                "Kya aapko pata hai ki 8 se 16 saal ke bachon ne hamare programs se 170 se zyada patents hasil kiye hain?"
            ),
            "diagnostic_session": (
                "Hum ek free diagnostic session offer karte hain jisme hum aapke bache ki interests "
                "ko samajh sakte hain. Kya aap ise schedule karna chahenge?"
            ),
            "callback_time": (
                "Kis date aur time pe yeh session rakh sakte hain?"
            ),
            "closing": (
                "Aapka bahut bahut dhanyavaad, {name}! Agar koi sawal ho to aap humse zaroor "
                "puchh sakte hain. Apna khayal rakhiyega!"
            ),
            "busy_response": (
                "Main samajh sakti hoon ki aap busy honge. Hum aapko kab call back kar sakte hain?"
            ),
            "little_innovator_program": (
                "Hamare Little Innovator Program ke bare mein batati hoon, jo grade 1-2 ke liye design kiya gaya hai. "
                "Yeh ek entry-level course hai jisme do 6-month modules hain: Little Innovator 1 aur 2. "
                "Is program mein basic coding, hands-on robotics projects, aur electronics activities sikhayee jaati hain. "
                "Classes week mein do baar hoti hain, maximum 10 students ke groups mein. "
                "Har module ki fees atharah hazaar rupaye hai."
            ),
            "emerging_tech_course": (
                "Hamare Emerging Tech Course mein paanch 6-month modules hain: "
                "Electronics, Embedded Design and Robotics, Internet of Things, Artificial Intelligence, "
                "aur Entrepreneurship. Classes week mein do baar hoti hain. "
                "Har module ki fees chaubis hazaar rupaye hai."
            )
        }
        
        self.setup_handlers()

    def setup_handlers(self):
        @self.agent.on("audio_frame")
        def process_audio_frame(frame):
            if not self._is_running:
                return frame
            try:
                return self.noise_suppressor.process_audio(frame)
            except Exception as e:
                logger.error(f"Error processing audio frame: {e}")
                return frame

        @self.agent.on("transcription")
        def handle_transcription(text):
            if self._is_running and text:
                self.last_response = text
                self.response_event.set()

    async def say(self, text, timeout=5):
        if not self._is_running:
            return
        try:
            await asyncio.wait_for(
                self.agent.say(text, allow_interruptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"TTS timeout for text: {text[:50]}...")
        except Exception as e:
            if "quota_exceeded" in str(e) or "voice_not_found" in str(e):
                if not self.tts_fallback_attempted:
                    logger.warning("TTS issue, attempting fallback")
                    self.tts_fallback_attempted = True
                    self.agent.tts = openai.TTS(
                        model="deepgram",
                        voice="nova2",
                        api_key=os.getenv("OPENAI_API_KEY")
                    )
                    if self._is_running:
                        await self.say(text, timeout)
                else:
                    logger.error("Both TTS services failed")
                    raise
            else:
                raise

    async def wait_for_response(self, timeout=30):
        try:
            self.response_event.clear()
            await asyncio.wait_for(self.response_event.wait(), timeout)
            response = self.last_response
            self.last_response = None
            return response
        except asyncio.TimeoutError:
            logger.warning("Response timeout")
            return None
        finally:
            self.response_event.clear()

    async def cleanup(self):
        self._is_running = False
        try:
            if hasattr(self.agent, '_audio_source'):
                await self.agent._audio_source.stop()
            if hasattr(self.agent, '_audio_sink'):
                await self.agent._audio_sink.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def run_conversation(self):
        try:
            name = self.conversation_state['user_details']['name']
            source = self.conversation_state['user_details']['source']

            await self.say(self.conversation_script["initial_greeting"].format(name=name))
            response = await self.wait_for_response()
            
            if not response:
                await self.say("Maaf kijiye, mujhe aapki awaaz nahi sun paa rahi. Humari team aapko dubara call karegi.")
                return

            await self.say(self.conversation_script["registration_confirmation"].format(source=source))
            response = await self.wait_for_response()

            await self.say(self.conversation_script["availability_check"])
            response = await self.wait_for_response()
            
            if response and any(word in response.lower() for word in ['nahi', 'busy', 'baad']):
                await self.say(self.conversation_script["busy_response"])
                await self.wait_for_response(timeout=3)
                await self.say("Theek hai, hum aapko tab call karenge. Dhanyavaad!")
                return

            await self.say(self.conversation_script["student_details"])
            response = await self.wait_for_response()
            if response:
                words = response.split()
                if len(words) >= 2:
                    self.conversation_state["user_details"]["child_name"] = words[0]
                    try:
                        self.conversation_state["user_details"]["child_grade"] = int(words[-1])
                    except ValueError:
                        pass

            child_name = self.conversation_state["user_details"]["child_name"]
            grade = self.conversation_state["user_details"].get("child_grade")
            
            if grade and 1 <= grade <= 2:
                await self.say(self.conversation_script["little_innovator_program"])
            else:
                await self.say(self.conversation_script["emerging_tech_course"])

            await self.say(self.conversation_script["diagnostic_session"])
            response = await self.wait_for_response()
            
            if response and any(word in response.lower() for word in ['haan', 'theek', 'okay']):
                await self.say(self.conversation_script["callback_time"])
                response = await self.wait_for_response()
                if response:
                    await self.say(f"Bahut accha! Maine {response} ka time note kar liya hai. Humari team jald hi confirm karegi.")

            await self.say(self.conversation_script["closing"].format(name=name))
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            await self.say("Maaf kijiye, kuch technical problem aa gaya hai. Humari team aapko jald hi call back karegi.")
        finally:
            await self.cleanup()

def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
        proc.userdata["noise_suppressor"] = WebRTCNoiseSupressor()
        logger.info("VAD and noise suppression initialized successfully")

        try:
            proc.userdata["elevenlabs_tts"] = elevenlabs.tts.TTS(
                model="eleven_multilingual_v2",
                voice=elevenlabs.tts.Voice(
                    id="EXAVITQu4vr4xnSDxMaL",  
                    name="Devi",
                    category="general",
                    settings=elevenlabs.tts.VoiceSettings(
                        stability=0.75,
                        similarity_boost=0.80,
                        style=0.35,
                        use_speaker_boost=True
                    )
                ),
                # Removed language parameter as it is not supported by the model
                streaming_latency=3,
                enable_ssml_parsing=False,
                chunk_length_schedule=[80, 120, 200, 260],
                api_key=os.getenv("ELEVEN_API_KEY")
            )
            logger.info("ElevenLabs TTS initialized successfully")
        except Exception as e:
            if "quota_exceeded" in str(e):
                logger.warning("ElevenLabs quota exceeded, falling back to OpenAI TTS")
                proc.userdata["elevenlabs_tts"] = openai.TTS(
                    model="deepgram",
                    voice="nova2",
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI TTS fallback initialized successfully")
            else:
                raise

        proc.userdata["openai"] = openai.STT()
        logger.info("OpenAI STT initialized successfully")
        
    except Exception as e:
        logger.error(f"Error in prewarm: {e}", exc_info=True)
        raise

async def entrypoint(ctx: JobContext):
    voice_assistant = None
    try:
        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        participant = await ctx.wait_for_participant()
        logger.info(f"Starting voice assistant for participant {participant.identity}")
        
        # Create voice pipeline agent
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=ctx.proc.userdata["openai"],
            tts=ctx.proc.userdata["elevenlabs_tts"],
            llm=openai.LLM(
                model="gpt-4",
                temperature=0.7
            )
        )
        
        noise_suppressor = WebRTCNoiseSupressor()
        voice_assistant = VoiceAssistant(agent, noise_suppressor)
        
        agent.start(ctx.room, participant)
        logger.info("Agent started successfully")
        
        await voice_assistant.run_conversation()
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {e}")
        raise
    finally:
        if voice_assistant:
            await voice_assistant.cleanup()

if __name__ == "__main__":
    try:
        cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=entrypoint))
    except Exception as e:
        logger.error(f"Error running app: {e}")
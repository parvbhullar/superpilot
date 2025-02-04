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
    metrics,
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
        self.vad = webrtcvad.Vad()
        # Set aggressiveness mode (0-3), 3 being the most aggressive
        self.vad.set_mode(3)
        logger.info("WebRTC noise suppression initialized")

    def process_audio(self, audio_frame, sample_rate=16000):
        """Process audio frame with noise suppression"""
        try:
            # Check if the frame contains speech
            is_speech = self.vad.is_speech(audio_frame, sample_rate)
            if is_speech:
                return audio_frame
            return b'\x00' * len(audio_frame)  # Return silence if no speech detected
        except Exception as e:
            logger.error(f"Error in noise suppression: {e}")
            return audio_frame

def prewarm(proc: JobProcess):
    """Initialize components with WebRTC noise suppression and TTS fallback"""
    try:
        # Initialize VAD
        proc.userdata["vad"] = silero.VAD.load()
        proc.userdata["noise_suppressor"] = WebRTCNoiseSupressor()
        logger.info("VAD and noise suppression initialized successfully")

        # Try to initialize ElevenLabs TTS with fallback to OpenAI TTS
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
                    voice="nova2",  # Female voice that works well with english
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                logger.info("OpenAI TTS fallback initialized successfully")
            else:
                raise

        # Initialize OpenAI STT
        proc.userdata["openai"] = openai.STT()
        logger.info("OpenAI STT initialized successfully")
        
        # Initialize GPT-4 LLM
        proc.userdata["gpt4o"] = openai.LLM(
            model="gpt-4",
            temperature=0.7
        )
        logger.info("GPT-4 LLM initialized successfully")
        
    except Exception as e:
        logger.error(f"Error in prewarm: {e}", exc_info=True)
        raise

class VoiceAssistant:
    def __init__(self, agent, noise_suppressor):
        self.agent = agent
        self.noise_suppressor = noise_suppressor
        self.tts_fallback_attempted = False
        self.conversation_state = {
            "current_step": 0,
            "waiting_for_response": False,
            "response_event": asyncio.Event(),
            "last_response": None,
            "user_details": {
                "name": "priya",
                "child_name": "",
                "child_grade": "",
                "location": "pune",
                "source": "instagram",
                "parent_name": "",
                "parent_profession": "",
                "spouse_profession": "",
            }
        }
        self.setup_handlers()

    def setup_handlers(self):
        @self.agent.on("audio_frame")
        def process_audio_frame(frame):
            try:
                processed_frame = self.noise_suppressor.process_audio(frame)
                return processed_frame
            except Exception as e:
                logger.error(f"Error processing audio frame: {e}")
                return frame

    async def wait_for_response(self, timeout=30):
        """Wait for user response with timeout."""
        try:
            self.conversation_state["waiting_for_response"] = True
            self.conversation_state["response_event"].clear()
            await asyncio.wait_for(self.conversation_state["response_event"].wait(), timeout)
            return self.conversation_state["last_response"]
        except asyncio.TimeoutError:
            logger.warning("Response timeout")
            return None
        finally:
            self.conversation_state["waiting_for_response"] = False

    async def _get_thinking_filler(self):
        """Get random thinking filler"""
        thinking_fillers = [
            "Hmm... ",
            "Oh, I see... ",
            "Ah, got it... ",
            "Let me think... ",
            "Oh, interesting... ",
            "Right, right... ",
            "Mmm hmm... ",
            "Oh, yes... ",
            "Ah, okay... ",
            "I understand... ",
            "That makes sense... ",
            "Oh, wonderful... ",
            "Ah, perfect... ",
            "Let me process that... ",
            "Just a second... ",
            "Oh, I hear you... ",
        ]
        return random.choice(thinking_fillers)

    async def _get_processing_filler(self):
        """Get random processing filler"""
        processing_fillers = [
            "Based on what you're saying... ",
            "From what I understand... ",
            "If I'm hearing you correctly... ",
            "That's really helpful to know... ",
            "Taking that into account... ",
            "Given what you've shared... ",
            "Considering your situation... ",
            "With that in mind... ",
            "Looking at this information... ",
            "After hearing about this... ",
        ]
        return random.choice(processing_fillers)

    async def _get_filler(self):
        """Get random conversation filler"""
        fillers = [
            "Just a moment... ",
            "Let me see... ",
            "Now... ",
            "You know... ",
            "Well... ",
            "So... ",
            "Actually... ",
            "By the way... "
        ]
        return random.choice(fillers)

    async def say_with_fallback(self, text):
        """Say text with fallback and optional thinking filler."""
        try:
            # 30% chance to add a thinking filler before speaking
            if random.random() < 0.3:
                thinking = await self._get_thinking_filler()
                text = thinking + text
            
            # 20% chance to add a processing filler for longer responses
            if len(text) > 100 and random.random() < 0.2:
                processing = await self._get_processing_filler()
                text = processing + text

            await self.agent.say(text, allow_interruptions=True)
        except Exception as e:
            if "quota_exceeded" in str(e) or "voice_not_found" in str(e):
                if not self.tts_fallback_attempted:
                    logger.warning("TTS issue, attempting fallback to OpenAI TTS")
                    self.tts_fallback_attempted = True
                    self.agent.tts = openai.TTS(
                        model="deepgram",
                        voice="nova2",
                        api_key=os.getenv("OPENAI_API_KEY")
                    )
                    await self.agent.say(text, allow_interruptions=True)
                else:
                    logger.error("Both TTS services failed")
                    raise
            else:
                raise

    async def ask_question(self, question):
        try:
            filler = await self._get_filler()
            await self.say_with_fallback(filler + question)
            response = await self.wait_for_response()
            
            if response:
                acknowledgment = await self._get_acknowledgment(response)
                await self.say_with_fallback(acknowledgment)
            
            return response
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return None

    async def _get_acknowledgment(self, response):
        """Generate contextual acknowledgments based on response"""
        positive_responses = ['yes', 'yeah', 'sure', 'okay', 'right', 'correct']
        negative_responses = ['no', 'nope', 'not', "don't", 'busy', 'later']
        
        if any(word in response.lower() for word in positive_responses):
            acknowledgments = [
                "That's wonderful! ",
                "Perfect! ",
                "Excellent! ",
                "Great to hear! ",
                "Fantastic! ",
                "Wonderful! ",
                "That's great! "
            ]
        elif any(word in response.lower() for word in negative_responses):
            acknowledgments = [
                "I understand. ",
                "No problem at all. ",
                "That's alright. ",
                "I see. ",
                "Thank you for letting me know. "
            ]
        else:
            acknowledgments = [
                "I see. ",
                "Alright. ",
                "Hmm, I understand. ",
                "Thank you for sharing that. ",
                "Got it. "
            ]
        
        return random.choice(acknowledgments)

    async def _present_little_innovator_program(self):
        await self.say_with_fallback(
            "Oh, this is perfect for their age group! For grades 1-2, we have our special Little Innovator Program. "
            "You know what's really exciting about this? It's an entry-level course that makes technology fun and engaging. "
            "Hmm, let me tell you about the structure... "
            "The program has two 6-month modules, and here's what I love about it - "
            "we cover basic coding, hands-on robotics projects, and really fun electronics activities. "
            "Oh, and you'll be happy to know that classes are held twice a week in small groups of up to 10 students, "
            "so each child gets proper attention. Each module is priced at eighteen thousand rupees."
        )

    async def _present_emerging_tech_course(self):
        await self.say_with_fallback(
            "Ah, I'm really excited to tell you about this! Our Emerging Tech Course is perfect for this age group. "
            "You see, it's a comprehensive program with five amazing modules, each lasting 6 months. "
            "Oh, let me break it down for you... "
            "We cover everything from electronics and robotics to IoT, AI, and even entrepreneurship! "
            "Hmm, what's really special about this course is how hands-on it is. "
            "The classes are held twice weekly in small groups, and you know what's great? "
            "They're led by expert instructors who are passionate about teaching. "
            "Each module is priced at twenty-four thousand rupees, and I really believe it's an investment in your child's future."
        )

    async def run_conversation(self):
        try:
            # Initial greeting and identity confirmation
            name = self.conversation_state['user_details']['name']
            
            # First greeting
            await self.say_with_fallback(f"Hi, this is Ahaana from CuriousKid.")
            await asyncio.sleep(1)  # Small pause
            
            # Ask for name confirmation
            response = await self.ask_question(f"Am I speaking with {name}?")
            
            # If no response or unclear, try again
            if not response or not any(word in response.lower() for word in ['yes', 'yeah', 'correct', 'right']):
                await self.say_with_fallback("Hmm, I understand it might be a bit noisy...")
                response = await self.ask_question(f"Let me try again... Is this {name}?")
                
                # If still no clear confirmation
                if not response or not any(word in response.lower() for word in ['yes', 'yeah', 'correct', 'right']):
                    await self.say_with_fallback(
                        f"Ah, I see there might be some confusion... Just to double-check, is your name {name}? "
                        "I want to make sure I'm speaking with the right person."
                    )
                    response = await self.wait_for_response()
                    if not response or not any(word in response.lower() for word in ['yes', 'yeah', 'correct', 'right']):
                        await self.say_with_fallback(
                            "Oh, I sincerely apologize for the mix-up. Hmm, let me have our team verify your contact details "
                            "and get back to you. Have a great day ahead!"
                        )
                        return

            # Confirm identity and check timing
            await self.say_with_fallback("Oh, wonderful! Thank you for confirming!")
            await asyncio.sleep(0.5)  # Small pause
            
            # Ask about timing
            response = await self.ask_question("I hope I'm not catching you at a busy time?")
            if not response or any(word in response.lower() for word in ['busy', 'bad', 'not good']):
                await self.say_with_fallback(
                    "Oh, I completely understand! When would be a better time to call you back?"
                )
                callback_time = await self.wait_for_response()
                if callback_time:
                    await self.say_with_fallback(
                        f"Perfect! I'll make sure we call you back {callback_time}. "
                        "Thank you so much for your time, and have a wonderful day ahead!"
                    )
                return

            # Registration confirmation
            source = self.conversation_state['user_details']['source']
            await asyncio.sleep(0.5)  # Small pause
            response = await self.ask_question(
                f"You know, I noticed that you recently registered through {source} "
                "and showed interest in our Robotics and AI courses. Do you remember registering with us?"
            )
            
            if not response or not any(word in response.lower() for word in ['yes', 'yeah', 'remember', 'recall']):
                await self.say_with_fallback(
                    "No worries at all! Let me give you a quick overview of what makes us special. "
                    "CuriousKid is doing some amazing things in teaching kids about technology."
                )
                await asyncio.sleep(0.5)

            # Ask about time to talk
            response = await self.ask_question(
                "I'm really passionate about helping children explore STEM learning, "
                "and I'd love to tell you about how we could support your child's journey. "
                "Do you have a few minutes to chat about this? I promise to be brief!"
            )
            
            if not response or any(word in response.lower() for word in ['no', 'busy', 'later']):
                await self.say_with_fallback(
                    "Of course, I completely understand how busy things can get! "
                    "When would be a better time for me to call you back?"
                )
                callback_time = await self.wait_for_response()
                if callback_time:
                    await self.say_with_fallback(
                        f"Perfect! I'll make sure we call you back {callback_time}. "
                        "Thank you so much for your time, and have a wonderful day ahead!"
                    )
                return

            # Child's details
            response = await self.ask_question(
                "Before we dive in, could you tell me a bit about your child? "
                "I'd love to know their name and which grade they're in, "
                "so I can recommend the most suitable program."
            )
            
            if response:
                # Try to extract name and grade
                words = response.split()
                if len(words) >= 2:
                    # Assume the last word is the grade and everything before is the name
                    grade = words[-1]
                    child_name = ' '.join(words[:-1])
                    self.conversation_state['user_details']['child_name'] = child_name
                    self.conversation_state['user_details']['child_grade'] = grade
                    
                    # Calculate approximate age (grade + 5)
                    try:
                        age = int(grade) + 5
                        await self.ask_question(f"Based on their grade, {child_name} would approximately be around {age} years old. Is that correct?")
                    except ValueError:
                        pass

            # Location confirmation
            address = self.conversation_state['user_details'].get('mailing_address', '')
            response = await self.ask_question(f"May I confirm your current location? Is it {address}?")
            
            # Technical setup
            child_name = self.conversation_state['user_details'].get('child_name', 'your child')
            await self.ask_question(f"Does {child_name} have access to a laptop and a stable internet connection for the sessions?")

            # Professional background
            response = await self.ask_question("If I may ask, what is your profession?")
            if response:
                self.conversation_state['user_details']['parent_profession'] = response

            response = await self.ask_question("Could you also share what your husband does professionally?")
            if response:
                self.conversation_state['user_details']['spouse_profession'] = response

            # Motivation and interest
            await self.ask_question(
                "I believe you've seen our advertisement on emerging technologies like robotics and "
                "artificial intelligence. Could you share what motivated you to register?"
            )

            # Company overview
            await self.say_with_fallback(
                "That's fantastic to hear! CuriousKid is India's largest innovation training company, "
                "specializing in teaching kids advanced technologies like electronics, robotics, "
                "artificial intelligence, and entrepreneurship. Did you know that kids aged 8 to 16 years "
                "have achieved over 170 patents through our programs? It's truly inspiring!"
            )

            # Present appropriate course based on grade
            grade = self.conversation_state['user_details'].get('child_grade', '')
            try:
                grade_num = int(grade)
                if 1 <= grade_num <= 2:
                    await self._present_little_innovator_program()
                else:
                    await self._present_emerging_tech_course()
            except ValueError:
                await self._present_emerging_tech_course()

            # Schedule diagnostic session
            await self.ask_question("Would you like to schedule a free diagnostic session for your child?")
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            await self.say_with_fallback(
                "I apologize, but we're experiencing some technical difficulties. "
                "Our team will call you back shortly to continue our conversation."
            )

async def entrypoint(ctx: JobContext):
    try:
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=(
                "You are Ahaana from CuriousKid, speaking in English. "
                "Follow the conversation flow exactly. "
                "Keep responses concise and natural."
            ),
        )

        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await ctx.wait_for_participant()
        logger.info(f"Starting voice assistant for participant {participant.identity}")

        # Create agent with potential fallback handling
        agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=ctx.proc.userdata["openai"],
        llm=ctx.proc.userdata["gpt4o"],
        tts=ctx.proc.userdata["elevenlabs_tts"],
        chat_ctx=llm.ChatContext().append(
            role="system",
            text="You are Ahaana from CuriousKid."
        ),
    )


        voice_assistant = VoiceAssistant(agent, ctx.proc.userdata["noise_suppressor"])
        agent.start(ctx.room, participant)
        logger.info("Agent started successfully")

        # Start conversation with error handling
        try:
            await voice_assistant.run_conversation()
        except Exception as e:
            if "quota_exceeded" in str(e) or "voice_not_found" in str(e):
                logger.warning("TTS issue during conversation, attempting to continue with fallback")
                # Switch to OpenAI TTS and continue
                agent.tts = openai.TTS(
                    model="tts-1",
                    voice="nova2",
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                await voice_assistant.run_conversation()
            else:
                logger.error(f"Error in conversation: {e}")
                raise
        finally:
            try:
                agent.disconnect()  # Use disconnect() instead of stop()
                logger.info("Agent disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting agent: {e}")

    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)
    finally:
        if 'agent' in locals():
            try:
                agent.disconnect()  # Use disconnect() instead of stop()
                logger.info("Agent cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=entrypoint))
    except Exception as e:
        logger.error(f"Application error: {e}")
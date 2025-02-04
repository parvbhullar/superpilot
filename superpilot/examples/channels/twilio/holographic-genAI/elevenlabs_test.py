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
        self.vad = webrtcvad.Vad(2)
        self._resampler = audio.AudioResampler(
            source_sample_rate=48000,  # adjust based on input
            target_sample_rate=16000,
            num_channels=1
        )

    def process_audio(self, frame: rtc.AudioFrame):
        # Resample to 16kHz mono
        resampled = self._resampler.resample(frame)

        pcm_data = resampled.data.tobytes()
        
        if len(pcm_data) != 320 * 2:  # 16-bit = 2 bytes per sample
            logger.warning("Invalid frame length for VAD")
            return frame.data

        is_speech = self.vad.is_speech(pcm_data, 16000)
        return pcm_data if is_speech else b'\x00' * len(pcm_data)

def prewarm(proc: JobProcess):
    """Initialize components with WebRTC noise suppression and TTS fallback"""
    try:
        # Initialize VAD
        proc.userdata["vad"] = silero.VAD.load()
        proc.userdata["noise_suppressor"] = WebRTCNoiseSupressor()
        logger.info("VAD and noise suppression initialized successfully")

        try:
            proc.userdata["elevenlabs_tts"] = elevenlabs.tts.TTS(
                model="eleven_multilingual_v2",
                voice=elevenlabs.tts.Voice(
                    id="", 
                    name="",
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
                    voice="nova2",
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
        
        # Define the conversation script and prompts
        self.conversation_script = {
            "initial_greeting": (
                "Hi, this is Ahaana from CuriousKid. Am I speaking with {name}?"
            ),
            "confirmation_prompts": {
                "retry1": "Just to confirm, is this {name}?",
                "retry2": "Sorry for the confusion, just to double-check, is your name {name}?",
                "retry3": "Just to confirm, is this {name}?"
            },
            "registration_confirmation": (
                "I see you registered through {source} and expressed interest in our Robotics and AI courses. Do you recall this?"
            ),
            "availability_check": (
                "Thank you! I wanted to discuss supporting your child's STEM learning journey. Do you have a few minutes?"
            ),
            "student_details": (
                "Could you please tell me your child's name and grade?"
            ),
            "age_verification": (
                "Based on their grade, {child_name} would be around {age} years old. Is that correct?"
            ),
            "location_verification": (
                "Can I confirm your current location? Is it {location}?"
            ),
            "technical_setup": (
                "Does {child_name} have access to a laptop and stable internet for the sessions?"
            ),
            "professional_background": (
                "What is your profession?"
            ),
            "spouse_profession": (
                "What does your spouse do professionally?"
            ),
            "course_interest": (
                "I believe you've seen our advertisement on robotics and AI. What motivated you to register {child_name}?"
            ),
            "company_overview": (
                "That's fantastic, {name}! CuriousKid is India's largest innovation training company, specializing in advanced technologies. Did you know kids aged 8 to 16 have achieved over 170 patents through our programs?"
            ),
            "diagnostic_session": (
                "We offer a free diagnostic session to explore your child's interests. Would you like to schedule this?"
            ),
            "callback_time": (
                "What date and time would work best for you to schedule this session?"
            ),
            "closing": (
                "Thank you for your time, {name}! If you have questions or need assistance, feel free to reach out. Have a great day!"
            ),
            "busy_response": (
                "I understand how busy schedules can be. When would be a better time to call you back?"
            )
        }

        self.conversation_state = {
            "current_step": 0,
            "waiting_for_response": False,
            "response_event": asyncio.Event(),
            "last_response": None,
            "user_details": {
                "name": "",
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
        def process_audio_frame(frame: rtc.AudioFrame):
            try:
                processed = self.noise_suppressor.process_audio(frame)
                return rtc.AudioFrame(
                    data=processed,
                    sample_rate=16000,
                    num_channels=1,
                    samples_per_channel=len(processed) // 2  
                )
            except Exception as e:
                logger.error(f"Audio processing failed: {e}")
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

    async def wait_and_check_response(self, question):
        """Helper method to ask question and properly wait for response"""
        response = await self.ask_question(question)
        await asyncio.sleep(1)  # Give time for response
        response = await self.wait_for_response()
        return response

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
        """Present the Little Innovator Program details"""
        await self.say_with_fallback(
            "Let me tell you about our Little Innovator Program, designed specifically for grades 1-2. "
            "It's an entry-level course with two 6-month modules: Little Innovator 1 and 2. "
            "The program covers basic coding, hands-on robotics projects, and fun electronics activities. "
            "Classes are held twice weekly in small groups of up to 10 students. "
            "Each module is priced at eighteen thousand rupees."
        )

    async def _present_emerging_tech_course(self):
        """Present the Emerging Tech Course details"""
        await self.say_with_fallback(
            "Our Emerging Tech Course is a comprehensive program with five 6-month modules: "
            "Electronics, Embedded Design and Robotics, Internet of Things, Artificial Intelligence, "
            "and Entrepreneurship. Classes are held twice weekly in small groups. "
            "Each module is priced at twenty-four thousand rupees."
        )

    async def run_conversation(self):
        try:
            name = self.conversation_state['user_details']['name']
            source = self.conversation_state['user_details']['source']

            # Initial greeting and identity confirmation
            await self.say_with_fallback(self.conversation_script["initial_greeting"].format(name=name))
            response = await self.wait_for_response()
            identity_confirmed = False

            # Confirm identity with retries
            for retry in range(3):
                if response and any(word in response.lower() for word in ['yes', 'correct']):
                    identity_confirmed = True
                    await self.say_with_fallback("Awesome, thank you for confirming!")
                    break
                else:
                    await self.say_with_fallback(self.conversation_script["confirmation_prompts"][f"retry{retry + 1}"].format(name=name))
                    response = await self.wait_for_response()

            if identity_confirmed:
                # Proceed with registration confirmation
                response = await self.wait_and_check_response(
                    self.conversation_script["registration_confirmation"].format(source=source)
                )

                # Check availability
                response = await self.wait_and_check_response(
                    self.conversation_script["availability_check"]
                )

                if response and any(word in response.lower() for word in ['yes', 'sure']):
                    await self.say_with_fallback(
                        f"That's wonderful, {name}! I'll assist you with details about our programs."
                    )

                    # Gather student details
                    response = await self.wait_and_check_response(
                        self.conversation_script["student_details"]
                    )
                    
                    if response:
                        # Parse child's name and grade
                        words = response.split()
                        if len(words) >= 2:
                            try:
                                grade = int(words[-1])
                                child_name = ' '.join(words[:-1])
                                self.conversation_state['user_details']['child_name'] = child_name
                                self.conversation_state['user_details']['child_grade'] = grade
                                
                                # Age verification
                                age = grade + 5
                                await self.wait_and_check_response(
                                    self.conversation_script["age_verification"].format(child_name=child_name, age=age)
                                )
                            except ValueError:
                                pass

                    # Location verification
                    await self.wait_and_check_response(
                        self.conversation_script["location_verification"].format(location=self.conversation_state['user_details']['location'])
                    )

                    # Technical setup
                    child_name = self.conversation_state['user_details'].get('child_name', 'your child')
                    await self.wait_and_check_response(
                        self.conversation_script["technical_setup"].format(child_name=child_name)
                    )

                    # Professional background
                    await self.wait_and_check_response(
                        self.conversation_script["professional_background"]
                    )
                    await self.wait_and_check_response(
                        self.conversation_script["spouse_profession"]
                    )

                    # Course interest
                    await self.wait_and_check_response(
                        self.conversation_script["course_interest"].format(child_name=child_name)
                    )

                    # Company overview
                    await self.say_with_fallback(
                        self.conversation_script["company_overview"].format(name=name)
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

                    # Diagnostic session scheduling
                    await self.say_with_fallback(
                        self.conversation_script["diagnostic_session"]
                    )

                    response = await self.wait_and_check_response(
                        self.conversation_script["callback_time"]
                    )

                    if response:
                        await self.say_with_fallback(
                            f"Great! I've scheduled the session for {response}. You'll receive a call "
                            "from our STEM expert shortly for confirmation."
                        )

                    # Closing
                    await self.say_with_fallback(
                        self.conversation_script["closing"].format(name=name)
                    )

                else:
                    await self.say_with_fallback(
                        self.conversation_script["busy_response"]
                    )
                    callback_time = await self.wait_for_response()
                    if callback_time:
                        await self.say_with_fallback(
                            f"Perfect! We'll call you back {callback_time}. Have a great day!"
                        )

            else:
                await self.say_with_fallback(
                    "I apologize, but I couldn't confirm your identity. "
                    "Our team will call you back shortly to continue our conversation."
                )

        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            await self.say_with_fallback(
                "I apologize, but we're experiencing some technical difficulties. "
                "Our team will call you back shortly to continue our conversation."
            )

async def entrypoint(ctx: JobContext):
    try:
        conversation_prompt = """
        Context: You are Ahaana, an AI assistant for CuriousKid
        Current Date and Time: 2025-01-29 12:24:02
        User: Arshdeep

        IMPORTANT: You MUST follow this exact conversation flow and wait for responses!

        CONVERSATION FLOW:

        1. INITIAL GREETING AND IDENTITY CONFIRMATION:
        Say exactly: "Hi, this is Ahaana from CuriousKid. Am I speaking with {name}?"
        (WAIT FOR RESPONSE)


        If still unclear:
        Say: "Sorry for the confusion, just to double-check, is your name {name}?"
        (WAIT FOR RESPONSE)

        After confirmation:
        Say: "Awesome, thank you for confirming!"

        2. REGISTRATION VERIFICATION:
        Say exactly: "I see you registered on our website through {source} and expressed interest in "
        "our Robotics and AI courses. Do you recall this registration?"
        (WAIT FOR CONFIRMATION)

        3. AVAILABILITY CHECK:
        Say exactly: "Thank you! I wanted to discuss supporting your child's STEM learning journey. "
        "Do you have a few minutes to talk?"
        (WAIT FOR CONFIRMATION)

        4. PROCEED AFTER CONFIRMATION:
        Say exactly: "That's wonderful, {name}! I'll be happy to assist you in getting more details "
        "about our programs and setting up a session for your child."

        5. GATHER STUDENT DETAILS:
        Say exactly: "Could you please tell me your child's name and their grade?"
        (WAIT FOR RESPONSE)

        After receiving grade:
        Say: "Based on their grade, [Child's Name] would approximately be around [Calculated Age] years old. "
        "Is that correct?"
        (WAIT FOR CONFIRMATION)

        6. INFORMATION GATHERING:
        - Ask: "May I confirm your current location? Is it {mailing_address}?"
        (WAIT FOR RESPONSE)

        - Ask: "Does [Child's Name] have access to a laptop and a stable internet connection for the sessions?"
        (WAIT FOR RESPONSE)

        - Ask: "If I may ask, what is your profession?"
        (WAIT FOR RESPONSE)

        - Ask: "Could you also share what your husband does professionally?"
        (WAIT FOR RESPONSE)

        7. MOTIVATION:
        Ask exactly: "I believe you've seen our advertisement on emerging technologies like robotics and "
        "artificial intelligence. Could you share what motivated you to register [Child's Name]?"
        (WAIT FOR RESPONSE)

        8. COMPANY OVERVIEW:
        Present exactly: "That's fantastic to hear, [Parent's Name]! CuriousKid is India's largest innovation "
        "training company, specializing in teaching kids advanced technologies like electronics, robotics, "
        "artificial intelligence, and entrepreneurship. Did you know that kids aged 8 to 16 years have achieved "
        "over 170 Patents through our programs? It's truly inspiring!"

        9. COURSE PRESENTATION:
        FOR GRADES 1-2:
        Present the Little Innovator Program details exactly as provided in the script.

        FOR GRADES 3+:
        Present the Emerging Tech Course details exactly as provided in the script.

        10. DIAGNOSTIC SESSION:
        Say exactly: "We offer a free diagnostic session to explore your child's interests through engaging "
        "experiments. Would you like to schedule this session today?"
        (WAIT FOR RESPONSE)

        If yes:
        Ask: "What date and time would work best for you to schedule this session? We are available at various "
        "times throughout the week."
        (WAIT FOR RESPONSE)

        After scheduling:
        Say exactly: "Great! I've scheduled the session for [Time] on [Date]. You'll receive a call from our STEM "
        "expert shortly for confirmation."

        11. HANDLING CONCERNS:
        If time concern:
        Say: "I completely understand how busy schedules can be. If this is not the right time, we can set up a "
        "follow-up call at a more convenient time for you. Does that work?"
        (WAIT FOR RESPONSE)

        12. CLOSING:
        Say exactly: "Thank you for your time! If you have any questions or need further assistance, please don't "
        "hesitate to reach out. Have a great day!"

        CRITICAL INSTRUCTIONS:
        - YOU MUST WAIT FOR USER RESPONSE after each question
        - DO NOT proceed until you get a clear response
        - Use exact phrases as provided
        - Acknowledge each response before moving forward
        - Handle interruptions gracefully
        - Keep track of all responses
        - Show empathy and patience
        """

        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await ctx.wait_for_participant()
        logger.info(f"Starting voice assistant for participant {participant.identity}")

        # Create agent with the exact conversation script
        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],   
            stt=ctx.proc.userdata["openai"],
            llm=ctx.proc.userdata["gpt4o"],
            tts=ctx.proc.userdata["elevenlabs_tts"],
            chat_ctx=llm.ChatContext().append(
                role="system",
                text=conversation_prompt
            )
        )

        # Rest of your code remains the same...

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
                await agent.disconnect()
                logger.info("Agent disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting agent: {e}")

    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)
    finally:
        if 'agent' in locals():
            try:
                await agent.disconnect()
                logger.info("Agent cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=entrypoint))
    except Exception as e:
        logger.error(f"Application error: {e}")
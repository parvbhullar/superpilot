import asyncio
import logging
import os
import random
import json
from datetime import datetime
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
from livekit.plugins import openai, silero, deepgram, cartesia, turn_detector
import webrtcvad 
import sys
from openai import OpenAI
from livekit.agents._exceptions import AssignmentTimeoutError

load_dotenv()
logger = logging.getLogger("voice-assistant")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


#HANDLE_NOISE
class WebRTCNoiseSupressor:
    def __init__(self):
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)  # Aggressive mode
        
    async def filter_frame(self, audio_frame):
        try:
            # Get raw audio data
            audio_data = audio_frame.data
            
            # Apply noise suppression
            is_speech = self.vad.is_speech(audio_data, audio_frame.sample_rate, audio_frame.num_channels)
            
            if not is_speech:
                # Return silence if no speech detected
                return rtc.AudioFrame(
                    data=b'\x00' * len(audio_data),
                    sample_rate=audio_frame.sample_rate,
                    num_channels=audio_frame.num_channels
                )
            return audio_frame
        except Exception as e:
            logger.error(f"Error in noise suppression: {e}")
            return audio_frame

def prewarm(proc: JobProcess):
    """Initialize components with WebRTC noise suppression and OpenAI TTS"""
    try:
        # Initialize VAD with optimized settings
        proc.userdata["vad"] = silero.VAD.load()
        proc.userdata["noise_suppressor"] = WebRTCNoiseSupressor()
        logger.info("VAD and noise suppression initialized successfully")

        # Initialize OpenAI TTS
        proc.userdata["tts"] = openai.TTS(
            model="tts-1",
            voice="alloy",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("OpenAI TTS initialized successfully")

        # Initialize OpenAI STT with optimized settings
        proc.userdata["openai"] = openai.STT(
            model="whisper-1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("OpenAI STT initialized successfully")
        
        # Initialize GPT-4 LLM with optimized settings
        proc.userdata["gpt4o"] = openai.LLM(
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY")
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
        
        # For call summary
        self.call_start_time = None
        self.call_summary = {
            "call_id": "",
            "timestamp": "",
            "duration": 0,
            "outcome": "",
            "user_details": {},
            "conversation_flow": [],
            "next_steps": []
        }
        
        #prompts
        self.conversation_script = {
            "initial_greeting": (
                "Hi, this is Ahaana from CuriousKid. Am I speaking with {name}?"
            ),
            "confirmation_prompts": {
                "retry1": "I apologize, could you please confirm if I'm speaking with {name}?",
                "retry2": "Just to make sure, is this {name} I'm speaking with?",
                "retry3": "I want to ensure I have the right person. Are you {name}?"
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
        def process_audio_frame(frame):
            try:
                processed_frame = self.noise_suppressor.filter_frame(frame)
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
            # Optimize text for faster TTS processing
            text = text.strip()
            if len(text) > 200:  # Break long responses into chunks
                sentences = text.split('.')
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < 200:
                        current_chunk += sentence + "."
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence + "."
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Process chunks in parallel
                tasks = [self.agent.say(chunk, allow_interruptions=True) for chunk in chunks]
                await asyncio.gather(*tasks)
            else:
                await self.agent.say(text, allow_interruptions=True)
                
        except Exception as e:
            logger.error(f"Error in say_with_fallback: {e}")
            if not self.tts_fallback_attempted:
                self.tts_fallback_attempted = True
                logger.info("Attempting fallback TTS")
                # Add fallback TTS logic here if needed

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

    async def save_call_summary(self):
        """Save call summary to file."""
        try:
            filename = "/home/dev2/projects/super-pilot/transcript.txt"
            with open(filename, 'w') as f:
                json.dump(self.call_summary, f, indent=2)
            logger.info(f"Call summary saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving call summary: {e}")

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

    async def run_conversation(self):
        try:
            self.call_start_time = datetime.now()
            name = self.conversation_state['user_details']['name']
            source = self.conversation_state['user_details']['source']

            # Initial greeting and identity confirmation
            greeting = self.conversation_script["initial_greeting"].format(name=name)
            await self.say_with_fallback(greeting)
            response = await self.wait_for_response()
            self.log_conversation_step(greeting, response)
            
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

            if not identity_confirmed:
                self.call_summary["outcome"] = "identity_not_confirmed"
                self.call_summary["next_steps"].append("Team to call back for identity confirmation")
                await self.say_with_fallback(
                    "I apologize, but I couldn't confirm your identity. "
                    "Our team will call you back shortly to continue our conversation."
                )
                return

            # Proceed with registration confirmation
            prompt = self.conversation_script["registration_confirmation"].format(source=source)
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)
            
            if not response or any(word in response.lower() for word in ['no', 'dont', 'not']):
                self.call_summary["outcome"] = "registration_not_confirmed"
                self.call_summary["next_steps"].append("Verify registration details")
                await self.say_with_fallback(
                    "I understand there might be some confusion about the registration. "
                    "Our team will verify the details and get back to you."
                )
                return

            # Check availability
            prompt = self.conversation_script["availability_check"]
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)

            if not response or any(word in response.lower() for word in ['no', 'busy', 'later', 'not']):
                self.call_summary["outcome"] = "callback_requested"
                await self.say_with_fallback(self.conversation_script["busy_response"])
                callback_time = await self.wait_for_response()
                if callback_time:
                    self.call_summary["next_steps"].append(f"Call back at {callback_time}")
                    await self.say_with_fallback(
                        f"Perfect! We'll call you back {callback_time}. Have a great day!"
                    )
                return

            # Start gathering details
            self.call_summary["outcome"] = "in_progress"
            
            # Gather student details
            prompt = self.conversation_script["student_details"]
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)
            
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
                        prompt = self.conversation_script["age_verification"].format(child_name=child_name, age=age)
                        response = await self.wait_and_check_response(prompt)
                        self.log_conversation_step(prompt, response)
                    except ValueError:
                        self.call_summary["outcome"] = "invalid_grade_format"
                        self.call_summary["next_steps"].append("Verify child's grade")
                        return

            # Location verification
            prompt = self.conversation_script["location_verification"].format(
                location=self.conversation_state['user_details']['location']
            )
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)

            # Technical setup
            child_name = self.conversation_state['user_details'].get('child_name', 'your child')
            prompt = self.conversation_script["technical_setup"].format(child_name=child_name)
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)
            
            if not response or any(word in response.lower() for word in ['no', 'dont', 'not']):
                self.call_summary["outcome"] = "technical_setup_needed"
                self.call_summary["next_steps"].append("Follow up on technical requirements")
                await self.say_with_fallback(
                    "I understand you might need help with the technical setup. "
                    "Our technical team will reach out to assist you."
                )
                return

            # Professional background
            prompt = self.conversation_script["professional_background"]
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)
            
            prompt = self.conversation_script["spouse_profession"]
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)

            # Course interest
            prompt = self.conversation_script["course_interest"].format(child_name=child_name)
            response = await self.wait_and_check_response(prompt)
            self.log_conversation_step(prompt, response)

            # Company overview and course presentation
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
            prompt = self.conversation_script["diagnostic_session"]
            await self.say_with_fallback(prompt)
            response = await self.wait_for_response()
            self.log_conversation_step(prompt, response)

            if response and any(word in response.lower() for word in ['yes', 'sure', 'okay']):
                prompt = self.conversation_script["callback_time"]
                response = await self.wait_and_check_response(prompt)
                self.log_conversation_step(prompt, response)

                if response:
                    self.call_summary["outcome"] = "diagnostic_scheduled"
                    self.call_summary["next_steps"].append(f"Confirm diagnostic session at {response}")
                    await self.say_with_fallback(
                        f"Great! I've scheduled the session for {response}. You'll receive a call from our STEM expert shortly for confirmation."
                    )
            else:
                self.call_summary["outcome"] = "no_diagnostic_scheduled"
                self.call_summary["next_steps"].append("Follow up about diagnostic session")

            # Closing
            await self.say_with_fallback(
                self.conversation_script["closing"].format(name=name)
            )

            # Extract and explain the call outcome
            self.extract_and_explain_outcome()

        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            self.call_summary["outcome"] = "error"
            self.call_summary["next_steps"].append(f"Technical team to investigate error: {str(e)}")
            await self.say_with_fallback(
                "I apologize, but we're experiencing some technical difficulties. "
                "Our team will call you back shortly to continue our conversation."
            )
        finally:
            # If outcome is still in_progress, set it to completed
            if self.call_summary["outcome"] == "in_progress":
                self.call_summary["outcome"] = "completed"
            await self.save_call_summary()
            await self.extract_and_save_call_analysis()

    def extract_and_explain_outcome(self):
        # Analyze conversation flow to determine detailed outcome
        last_prompt = self.call_summary['conversation_flow'][-1]
        if last_prompt['response']:
            self.call_summary['outcome'] = "successful_conversation"
            self.call_summary['next_steps'].append("No further action needed")
        else:
            self.call_summary['outcome'] = "incomplete_conversation"
            self.call_summary['next_steps'].append("Follow up required")

        # Detailed analysis of the conversation
        analysis = ""
        for step in self.call_summary['conversation_flow']:
            analysis += f"Prompt: {step['prompt']}\nResponse: {step['response'] if step['response'] else 'No response'}\n"

        self.call_summary['detailed_analysis'] = analysis

    def finalize_call_summary(self):
        """Finalize the call summary with analysis."""
        if self.call_summary["outcome"] is None:
            self.call_summary["outcome"] = "completed"
        
        self.call_summary["duration"] = int((datetime.now() - self.call_start_time).total_seconds())
        
        # Extract call summary from transcript
        self.call_summary["analysis"] = self.analyze_conversation()

    def analyze_conversation(self):
        """Analyze the conversation flow and generate a call summary."""
        analysis = {
            "total_exchanges": len(self.call_summary["conversation_flow"]),
            "completion_status": "complete" if self.call_summary["outcome"] == "completed" else "incomplete",
            "key_points": [],
            "action_items": []
        }

        # Extract key points from conversation
        for step in self.call_summary["conversation_flow"]:
            if step["response"]:
                analysis["key_points"].append({
                    "topic": step["prompt"],
                    "response": step["response"]
                })

        # Generate action items based on outcome
        if self.call_summary["outcome"] == "diagnostic_scheduled":
            analysis["action_items"].append("Schedule diagnostic session")
        elif self.call_summary["outcome"] == "callback_requested":
            analysis["action_items"].append("Follow up at scheduled time")

        # Sample call analysis
        analysis["summary"] = "Kanika from Unpod introduced their AI Caller product to a potential customer, highlighting its key features for automating outbound calls and improving efficiency. The customer listened politely but did not show strong interest, repeatedly thanking Kanika without asking questions or requesting more information."

        return analysis

    def log_conversation_step(self, prompt, response, outcome=None):
        """Log a conversation step"""
        step = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "outcome": outcome
        }
        self.call_summary["conversation_flow"].append(step)

    async def extract_and_save_call_analysis(self):
        """Extract transcript from msgs.json and save call analysis to test.txt."""
        try:
            # Extract transcript from msgs.json
            with open("/home/dev2/projects/super-pilot/super-pilot/work/superpilot/superpilot/superpilot/examples/channels/twilio/holographic-genAI/msgs.json", 'r') as file:
                transcript_data = json.load(file)

            # Generate call analysis
            call_analysis = []
            for call in transcript_data:
                outcome = call.get("outcome", "No outcome available")
                next_steps = call.get("next_steps", [])
                
                # Prepare the analysis output
                analysis_output = {
                    "call_id": call.get("call_id"),
                    "outcome": outcome,
                    "next_steps": next_steps
                }
                call_analysis.append(analysis_output)

            # Write the call analysis to test.txt
            with open("/home/dev2/projects/super-pilot/test.txt", 'w') as file:
                for i, analysis in enumerate(call_analysis, start=1):
                    file.write(f"{i}. Call ID: {analysis['call_id']}\n")
                    file.write(f"- Outcome: {analysis['outcome']}\n")
                    file.write("- Key Points: None\n")
                    file.write("- Next Steps:\n")
                    for step in analysis['next_steps']:
                        file.write(f"- {step}\n")
                    file.write("\n")
            logger.info("Call analysis saved to test.txt")
        except Exception as e:
            logger.error(f"Error during call analysis extraction: {e}")

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

async def setup_agent(ctx: JobContext):
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # Create agent with the exact conversation script
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],   
        stt=ctx.proc.userdata["openai"],
        llm=ctx.proc.userdata["gpt4o"],
        tts=ctx.proc.userdata["tts"],
        chat_ctx=llm.ChatContext().append(
            role="system",
            text="""Context: You are Ahaana, an AI assistant for CuriousKid
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
        ),
        allow_interruptions=True,
        interrupt_speech_duration=0.3, 
        min_endpointing_delay=0.3,     
        max_endpointing_delay=2.0,     
        vad_threshold=0.5              
    )

    return agent

async def entrypoint(ctx: JobContext):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            initial_ctx = llm.ChatContext().append(
                role="system",
                text=(
                    "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
                    "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
                    "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
                ),
            )

            logger.info(f"connecting to room {ctx.room.name}")
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

            # Wait for the first participant to connect
            participant = await ctx.wait_for_participant()
            logger.info(f"starting voice assistant for participant {participant.identity}")
            
            agent = VoicePipelineAgent(
                vad=ctx.proc.userdata["vad"],
                stt=deepgram.STT(),
                llm=openai.LLM(model="gpt-4o-mini"),
                tts=cartesia.TTS(),
                turn_detector=turn_detector.EOUModel(),
                min_endpointing_delay=0.5,
                max_endpointing_delay=5.0,
                chat_ctx=initial_ctx,
            )
            
            noise_suppressor = ctx.proc.userdata.get("noise_suppressor")
            voice_assistant = VoiceAssistant(agent, noise_suppressor)
            
            try:
                await voice_assistant.run_conversation()
                break  # If successful, exit the retry loop
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, cleaning up...")
                break
            except AssignmentTimeoutError:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Assignment timeout, retrying ({retry_count}/{MAX_RETRIES})...")
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error("Max retries reached for assignment timeout")
                    raise
            finally:
                if hasattr(voice_assistant, 'cleanup'):
                    await voice_assistant.cleanup()
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal during setup, exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"Error in entrypoint: {e}", exc_info=True)
            break
        finally:
            logger.info("Cleaning up and exiting...")

async def run(ctx: JobContext):
    try:
        await entrypoint(ctx)
    except AssignmentTimeoutError:
        logger.error("Failed to complete assignment after maximum retries")
    except KeyboardInterrupt:
        logger.info("Received interrupt in main run loop, exiting gracefully...")
    except Exception as e:
        logger.error(f"Error in run: {e}", exc_info=True)
        raise
    finally:
        logger.info("Main run loop completed")

if __name__ == "__main__":
    try:
        cli.run_app(WorkerOptions(prewarm_fnc=prewarm, entrypoint_fnc=run))
    except KeyboardInterrupt:
        logger.info("Application interrupted, shutting down...")
    except Exception as e:
        logger.error(f"Error running app: {e}", exc_info=True)
        sys.exit(1)

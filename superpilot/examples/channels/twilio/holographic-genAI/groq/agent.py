import logging
import random
import asyncio
import json
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import silero, openai, elevenlabs

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

# Conversation fillers and pauses
THINKING_FILLERS = [
    "Let me think...", 
    "Hmm...",
    "Just a moment...",
    "Let me check that...",
    "One second...",
    "Let me see...",
    "Ah, yes...",
    "Okay...",
]

PROCESSING_FILLERS = [
    "I see...",
    "Interesting...",
    "That's great to know...",
    "Thanks for sharing that...",
    "Understood...",
    "Got it...",
    "Makes sense...",
]

ACKNOWLEDGMENTS = [
    "Alright,",
    "Perfect,",
    "Great,",
    "Wonderful,",
    "Fantastic,",
    "Excellent,",
    "Got it,",
]

class UserDetails:
    def __init__(self, metadata=None):
        # Default values only used if metadata parsing fails
        self.name = "your name"
        self.location = "your location"
        self.source = "website"
        
        if metadata:
            try:
                # Log the raw metadata for debugging
                logger.info(f"Raw metadata received: {metadata}")
                
                # If metadata is already a string, parse it
                if isinstance(metadata, str):
                    user_data = json.loads(metadata)
                # If metadata is already a dict, use it directly
                elif isinstance(metadata, dict):
                    user_data = metadata
                else:
                    raise ValueError(f"Unexpected metadata type: {type(metadata)}")
                
                logger.info(f"Parsed user data: {user_data}")
                
                # Extract values with strict checking
                if 'name' in user_data and user_data['name']:
                    self.name = user_data['name'].strip()
                if 'location' in user_data and user_data['location']:
                    self.location = user_data['location'].strip()
                if 'source' in user_data and user_data['source']:
                    self.source = user_data['source'].strip()
                
                logger.info(f"Extracted user details: name={self.name}, location={self.location}, source={self.source}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse metadata JSON: {e}")
            except Exception as e:
                logger.error(f"Error extracting user details: {e}")
                logger.error(f"Metadata content: {metadata}")

def get_filler():
    return random.choice(THINKING_FILLERS) + " "

def get_acknowledgment():
    return random.choice(ACKNOWLEDGMENTS) + " "

async def natural_pause(seconds=1.2):
    await asyncio.sleep(seconds)

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant connected: {participant.identity}")
    
    # Wait briefly for metadata to be set
    for _ in range(5):  # Try up to 5 times
        metadata_str = participant.metadata
        logger.info(f"Checking metadata (attempt {_ + 1}): {metadata_str}")
        
        if metadata_str:
            break
        await asyncio.sleep(1)  # Wait 1 second between attempts
    
    # Process metadata
    try:
        if metadata_str:
            logger.info(f"Processing metadata: {metadata_str}")
            try:
                # Try parsing as JSON first
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                # If not JSON, try using the string directly
                metadata = metadata_str
                if isinstance(metadata, str):
                    try:
                        # Try to evaluate as a Python dict
                        metadata = eval(metadata)
                    except:
                        logger.error("Failed to parse metadata string")
                        metadata = {}
            
            logger.info(f"Parsed metadata: {metadata}")
            
            if isinstance(metadata, dict):
                user_details = UserDetails(metadata)
                logger.info(f"Created user details from metadata: {user_details.__dict__}")
            else:
                logger.error(f"Invalid metadata type: {type(metadata)}")
                user_details = UserDetails()
        else:
            logger.warning("No metadata received from participant")
            # Try getting metadata from room as fallback
            try:
                room_metadata = ctx.room.metadata
                if room_metadata:
                    logger.info(f"Using room metadata instead: {room_metadata}")
                    metadata = json.loads(room_metadata)
                    user_details = UserDetails(metadata)
                else:
                    user_details = UserDetails()
            except Exception as e:
                logger.error(f"Failed to get room metadata: {e}")
                user_details = UserDetails()
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        user_details = UserDetails()

    logger.info(f"Final user details: {user_details.__dict__}")

    initial_ctx = llm.ChatContext().append(
        role="system",
        text=f"""You are Ahaana, a friendly AI assistant for CuriousKid. Use this exact conversation flow:

        {get_filler()}Hi, this is Ahaana from CuriousKid. Am I speaking with {user_details.name}?
        {get_filler()}(Wait for confirmation)

        {get_filler()}I see you registered through {user_details.source} and expressed interest in our Robotics and AI courses. {get_filler()}Do you recall this registration?
        {get_filler()}(Wait for confirmation)

        {get_acknowledgment()}Thank you! {get_filler()}I wanted to discuss supporting your child's STEM learning journey. {get_filler()}Do you have a few minutes to talk?
        {get_filler()}(Wait for confirmation)

        [If no confirmation after 5 seconds]
        {get_filler()}Just to confirm, is this {user_details.name}?
        {get_filler()}(Wait for response)

        [After confirmation]
        {get_acknowledgment()}That's wonderful, {user_details.name}! {get_filler()}I'll be happy to assist you with our programs.

        {get_filler()}Could you please tell me your child's name and their grade?
        {get_filler()}(Wait for response)

        {get_acknowledgment()}Based on their grade, [Child's Name] would be around [age] years old. {get_filler()}Is that correct?
        {get_filler()}(Wait for confirmation)

        {get_filler()}May I confirm your current location? {get_filler()}Is it {user_details.location}?
        {get_filler()}(Wait for response)

        {get_filler()}Does [Child's Name] have access to a laptop and stable internet?
        {get_filler()}(Wait for response)

        {get_filler()}If I may ask, what is your profession?
        {get_filler()}(Wait for response)

        {get_filler()}Could you share what your spouse does professionally?
        {get_filler()}(Wait for response)

        {get_filler()}I believe you saw our ad about robotics and AI. {get_filler()}What motivated you to register [Child's Name]?
        {get_filler()}(Wait for response)

        {get_acknowledgment()}That's fantastic! {get_filler()}Let me tell you about CuriousKid. {get_filler()}We are India's largest innovation training company, 
        and our students have achieved remarkable success. {get_filler()}Did you know kids aged 8-16 have achieved over 170 patents through our programs?

        {get_filler()}Before I explain the course details, let me share our fee structure which is quite flexible:
        - We offer monthly installment options
        - There's a 10% sibling discount
        - Early bird registration gets a 15% discount
        - We also provide a 100% refund if you're not satisfied with the first two classes
        {get_filler()}Would you like to know the specific program details for [Child's Name]'s grade?
        {get_filler()}(Wait for response)

        [For Grades 1-2]
        {get_filler()}For [Child's Name]'s grade, we have our Little Innovator Program:
        
        Overview:
        - Two 6-month modules: Little Innovator 1 and 2
        - Small groups of up to 10 students
        - Twice weekly classes, 45 minutes each
        
        Content:
        - Introduction to basic coding concepts
        - Hands-on robotics projects
        - Fun electronics activities
        - Focus on creativity and problem-solving
        
        Investment Details:
        - ₹18,000 per module (₹3,000 per month)
        - Includes all learning materials and project kits
        - Registration fee: ₹2,000 (adjustable in first month's fee)
        - Special offer: First two classes free
        
        {get_filler()}We also have an early registration discount of 15% if you enroll within this week.
        
        [For Grades 3 and Above]
        {get_filler()}For [Child's Name]'s grade, we offer our Emerging Tech Course:
        
        Five 6-month modules:
        1. Electronics - Circuits and components
        2. Embedded Design and Robotics
        3. Internet of Things (IoT)
        4. Artificial Intelligence basics
        5. Entrepreneurship skills
        
        Class Structure:
        - Twice weekly sessions, 1 hour each
        - Small group learning
        - Expert instructors from IITs and NITs
        
        Investment Details:
        - ₹24,000 per module (₹4,000 per month)
        - All learning materials and project kits included
        - Registration fee: ₹2,500 (adjustable in first month's fee)
        - Special offer: First two classes free
        
        {get_filler()}Currently, we're offering a 15% early bird discount for registrations this week.
        
        [After course details]
        {get_filler()}Would you like me to explain our monthly payment options or the sibling discount?
        {get_filler()}(Wait for response)

        [If asks about payment options]
        {get_filler()}We offer flexible payment plans:
        1. Monthly installments with no extra charge
        2. Quarterly payments with 5% additional discount
        3. Full payment with 10% additional discount
        {get_filler()}Which payment option interests you?
        {get_filler()}(Wait for response)

        {get_filler()}We offer a free diagnostic session to explore your child's interests. {get_filler()}This 10-15 minute session helps us assess their aptitude through simple experiments.
        {get_filler()}Would you like to schedule this? {get_filler()}Remember, the first two classes are completely free!
        {get_filler()}(Wait for response)

        [If yes]
        {get_acknowledgment()}What date and time works best?
        {get_filler()}(Wait for response)
        {get_acknowledgment()}Perfect! Scheduled for [time] on [date]. {get_filler()}Our STEM expert will call to confirm.
        {get_filler()}They'll also explain our special offers and payment plans in detail.

        [If hesitant about fees]
        {get_filler()}I understand that investment in education is an important decision. 
        {get_filler()}We can customize a payment plan that works best for you.
        {get_filler()}Would you like to discuss this with our academic counselor?
        {get_filler()}(Wait for response)

        [Closing]
        {get_acknowledgment()}Thank you for your time! {get_filler()}You'll receive all program details and fee structures by email.
        {get_filler()}Feel free to reach out if you have any questions about the courses or payment options. {get_filler()}Have a great day!""",
    )

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT.with_groq(model="whisper-large-v3"),
        llm=openai.LLM.with_groq(model="llama-3.3-70b-versatile"),
        tts=elevenlabs.TTS(),
        chat_ctx=initial_ctx,
    )

    agent.start(ctx.room, participant)

    # Start the conversation with user details
    initial_greeting = f"{get_filler()}Hi, this is Ahaana from CuriousKid. {get_filler()}Am I speaking with {user_details.name}?"
    await agent.say(initial_greeting)

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
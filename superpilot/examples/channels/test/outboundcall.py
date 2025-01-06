import logging
import asyncio
import json
from dotenv import load_dotenv
from twilio.rest import Client
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero
from livekit.agents._exceptions import AssignmentTimeoutError

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# Twilio credentials
TWILIO_PHONE_NUMBER = "your_twilio_phone_number"  # Replace with your Twilio phone number
TWILIO_SID = "your_twilio_account_sid"  # Replace with your Twilio SID
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"  # Replace with your Twilio Auth Token

# Initialize Twilio client
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def load_json_data(file_path):
    """Load and return JSON data from the specified file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"JSON file not found at path: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def prewarm(proc: JobProcess):
    """Preload resources before starting the job."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for the voice assistant."""
    try:
        logger.info("Starting connection process...")
        
        initial_ctx = llm.ChatContext()
        initial_ctx.append(
            role="system",
            text=(
                "Aap ek voice assistant hain jo LiveKit dwara banaya gaya hai. Aapka naam Meera hai aur aap ek professional property advisor hain. "
                "Aapka kaam customer ki property requirements ko samajhna aur unhe unke requirements ke anusar options provide karna hai."
            ),
        )

        json_file_path = (
            "/home/dev2/projects/super-pilot/super-pilot/work/superpilot/"
            "superpilot/superpilot/examples/channels/test/test.json"
        )
        json_data = load_json_data(json_file_path)

        for line in json_data:
            initial_ctx.append(role=line["role"], text=line["content"][0]["text"])

        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        logger.info("Waiting for participant to connect...")
        try:
            participant = await asyncio.wait_for(ctx.wait_for_participant(), timeout=60)
            logger.info(f"Starting voice assistant for participant {participant.identity}")
        except asyncio.TimeoutError:
            logger.error("Timeout occurred while waiting for participant to connect.")
            return

        agent = VoicePipelineAgent(
            vad=ctx.proc.userdata["vad"],
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            chat_ctx=initial_ctx,
        )

        agent.start(ctx.room, participant)
        await agent.say(
            "Namaste, main Meera hoon, ek professional property advisor. Main aapko property dhoondhne mein madad kar sakti hoon.",
            allow_interruptions=True,
        )

        # Instructions
        instructions = (
            "आप एक रियल एस्टेट प्रॉपर्टी सलाहकार हैं। उपयोगकर्ता के साथ आपका इंटरफ़ेस आवाज होगा। "
            "उपयोगकर्ता की आवाज के आधार पर 'सर' या 'मैम' का प्रयोग करें। "
            "'नमस्कार, मैं आपकी प्रॉपर्टी खोज में मदद करना चाहूंगी।' "
            "मुझे पता चला है कि आप प्रॉपर्टी देख रहे हैं। मेरे पास आपके लिए बेहतरीन ऑफर्स में प्रॉपर्टी उपलब्ध है। "
            "क्या मैं आपसे कुछ कीमती समय ले सकती हूँ?' "
            "बातचीत के अंत में, उनकी प्रॉपर्टी की कीमत, स्थान, क्षेत्रफल और अन्य विवरणों की पुष्टि करें।"
        )

        logger.info(f"Instructions loaded: {instructions}")

        await agent.say(instructions, allow_interruptions=True)

        # Initiate an outbound call using Twilio
        to_phone_number = "+1234567890"  # Replace with the recipient's phone number

        call = twilio_client.calls.create(
            to=to_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say>{instructions}</Say></Response>"
        )

        logger.info(f"Outbound call initiated to {to_phone_number}. Call SID: {call.sid}")

    except AssignmentTimeoutError:
        logger.error("Timeout occurred while waiting for the assignment to be accepted.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )

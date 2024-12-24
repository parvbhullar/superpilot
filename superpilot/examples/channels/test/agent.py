import logging
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
from livekit.plugins import openai, deepgram, silero
from livekit.agents._exceptions import AssignmentTimeoutError  # Import AssignmentTimeoutError
import asyncio

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    try:
        logger.info("Starting connection process...")
        initial_ctx = llm.ChatContext()

        # Update system message for real estate app experience
        initial_ctx.append(
            role="system",
            text=(
                "Aap ek voice assistant hain jo LiveKit dwara banaya gaya hai. Aapka naam Meera hai aur aap ek professional property advisor hain. "
                "Aapka kaam customer ki property requirements ko samajhna aur unhe unke requirements ke anusar options provide karna hai."
            ),
        )
        
        initial_ctx.append(role="system", text="Namaste, main Meera hoon, ek professional property advisor. Main aapko property dhoondhne mein madad kar sakti hoon.")

        questions = [

        {"type": "property_type", "message": "Aap kis tarah ki property dhoond rahe hain? (Flat, Independent House, Plot ya Commercial Space)"},
        {"type": "location", "message": "Aap kis location mein property dhoond rahe hain? Kya aapko specific location ki preference hai?"},
        {"type": "budget", "message": "Aapka budget kya hai? Kripya apna budget bataayein."},
        {"type": "bedrooms", "message": "Kitne bedrooms wali property aapko chahiye?"},
        {"type": "amenities", "message": "Kya aapko kisi khas amenities jaise ki air conditioning, gym ya parking ki zarurat hai?"},
        {"type": "property_age", "message": "Aapko kitne purani property pasand hai? (Nayi, 1-5 saal purani, 5-10 saal purani, 10 saal se zyada)"},
        {"type": "floor_preference", "message": "Kya aapko ground floor ya upper floor pasand hai?"},
        {"type": "parking", "message": "Kya aapko parking ki zarurat hai? Agar haan, to kitne vehicles ke liye?"},
        {"type": "furnishing", "message": "Kya aap furnished ya unfurnished property dhoond rahe hain?"},
        {"type": "nearby_facilities", "message": "Kya aapko aas-paas ki facilities jaise ki school, hospital ya shopping center ki zarurat hai?"},
        {"type": "pet_policy", "message": "Kya aap pets ke liye property dhoond rahe hain?"},
        {"type": "security_features", "message": "Kya aapko security features jaise ki CCTV ya security guard ki zarurat hai?"},
        {"type": "balcony_garden", "message": "Kya aapko balcony ya garden ki zarurat hai?"},
        {"type": "view_preference", "message": "Kya aapko property ka view pasand hai? (Sea view, Garden view, City view)"},
        {"type": "balcony_size", "message": "Kya aapko chhoti balcony ya badi balcony chahiye?"},
        {"type": "building_age", "message": "Aapko kitne purane building mein rehna pasand hai?"},
        {"type": "community_features", "message": "Kya aapko gated community ya society pasand hai?"},
        {"type": "accessibility", "message": "Kya aapko kisi khas accessibility features ki zarurat hai?"},
        {"type": "ownership_type", "message": "Kya aapko leasehold ya freehold property chahiye?"},
        {"type": "maintenance_charges", "message": "Kya aapko maintenance charges ke bare mein jankari chahiye?"},
        {"type": "public_transport", "message": "Kya aapko aas-paas public transport ki suvidha chahiye?"},
        {"type": "emergency_services", "message": "Kya aapko aas-paas emergency services jaise ki hospital ki zarurat hai?"},
        {"type": "internet_connectivity", "message": "Kya aapko high-speed internet connection ki zarurat hai?"},
        {"type": "pet_friendly", "message": "Kya aapko pet-friendly property chahiye?"},
        {"type": "outdoor_space", "message": "Kya aapko outdoor space jaise ki garden ya terrace chahiye?"},
        {"type": "local_schools", "message": "Kya aapko aas-paas ke schoolon ki jankari chahiye?"},
        {"type": "local_markets", "message": "Kya aapko aas-paas ke markets ya grocery stores ki zarurat hai?"},
        {"type": "security_features", "message": "Kya aapko security features jaise ki CCTV cameras ki zarurat hai?"},
        {"type": "property_type", "message": "Kya aapko residential ya commercial property chahiye?"},
        {"type": "swimming_pool", "message": "Kya aapko swimming pool wali property chahiye?"},
        {"type": "gym_facilities", "message": "Kya aapko gym facilities wali property chahiye?"},
        {"type": "neighbor_age", "message": "Kya aapko young ya elderly neighbors pasand hain?"},
        {"type": "home_office", "message": "Kya aapko home office space ki zarurat hai?"}
]
        
        for question in questions:
            initial_ctx.append(role="system", text=question["message"])
        
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
            stt=deepgram.STT(language="hi-IN"), 
            llm=openai.LLM(model="gpt-4o-mini"),
            voice_name="hi-IN-Wavenet-A", 

            tts=openai.TTS(), 
            chat_ctx=initial_ctx,
        )

        agent.start(ctx.room, participant)

        await agent.say("Namaste, main Meera hoon, ek professional property advisor. Main aapko property dhoondhne mein madad kar sakti hoon.", allow_interruptions=True)

        for question in questions:
            await agent.say(question["message"], allow_interruptions=True)

        await agent.say("Aapke jawab ka intezaar rahega. Shukriya!", allow_interruptions=True)

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

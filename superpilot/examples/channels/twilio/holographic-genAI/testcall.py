from __future__ import annotations
import os
import logging
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import JobContext, WorkerOptions, AutoSubscribe, cli
from models import OpenAIRealtimeModel, MultimodalAgentHandler
from base import BaseAgent  

load_dotenv(dotenv_path=".env.local")

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

class Agent(BaseAgent):
    async def entrypoint(self, ctx: JobContext):
        """Main entry point for the worker"""
        logger.info(f"Connecting to room {ctx.room.name}")
        
        try:
            await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
            logger.info("Connected to room successfully.")
            
            participant = await ctx.wait_for_participant()
            logger.info(f"Participant {participant.identity} connected.")

            await self.run_multimodal_agent(ctx, participant)

        except Exception as e:
            logger.error(f"Error during entry point execution: {e}")

    async def run_multimodal_agent(self, ctx: JobContext, participant: rtc.RemoteParticipant):
        """Run the multimodal agent, interacting with the OpenAI model"""
        logger.info("Starting multimodal agent")

        openai_model = OpenAIRealtimeModel().get_model()
        agent_handler = MultimodalAgentHandler(openai_model)

        await agent_handler.start_assistant(ctx, participant)

    async def respond(self, message: str):
        """Send a response to the messaging platform."""
        pass

async def create_sip_participant(phone_number: str, room_name: str):
    """Create a SIP participant and add them to a room"""
    Agent.check_env_vars()

    LIVEKIT_URL = os.getenv('LIVEKIT_URL')
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
    SIP_TRUNK_ID = os.getenv('SIP_TRUNK_ID')

    livekit_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    try:
        logger.info(f"Attempting to create SIP participant for {phone_number} in room {room_name}")
        response = await livekit_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=f"sip_{phone_number}",
                participant_name="SIP Caller"
            )
        )
        logger.info(f"SIP participant created for {phone_number} in room {room_name}: {response}")
    except Exception as e:
        logger.error(f"Failed to create SIP participant: {e}")
    finally:
        await livekit_api.aclose()

async def main():
    """Main function to create SIP participant and start the OpenAI agent"""
    phone_number = os.getenv('SIP_CALL_TO')  
    room_name = os.getenv('ROOMNAME')         
    await create_sip_participant(phone_number, room_name)

    try:
        logger.info("Starting OpenAI agent...")
        agent = Agent()  
        await cli.run_app(
            WorkerOptions(
                entrypoint_fnc=agent.entrypoint, 
            )
        )
    except Exception as e:
        logger.error(f"Error running OpenAI agent: {e}")

if __name__ == "__main__":
    """Ensure the event loop is properly handled"""
    try:
        nest_asyncio.apply() 
        asyncio.run(main())  
        
    except RuntimeError:
        logger.warning("Event loop is already running, using await directly.")
        
        loop = asyncio.get_event_loop()
        
        loop.create_task(main())
        
        cli.run_app(
            WorkerOptions(
                entrypoint_fnc=Agent().entrypoint,  
            )
        )

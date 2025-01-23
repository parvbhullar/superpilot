from __future__ import annotations
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, AutoSubscribe, WorkerOptions, cli
from base import BaseAgent
from models import OpenAIRealtimeModel, MultimodalAgentHandler

load_dotenv(dotenv_path=".env.local")

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)


class LiveKitAgent(BaseAgent):
    async def entrypoint(self, ctx: JobContext):
        logger.info(f"Connecting to room {ctx.room.name}")
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await ctx.wait_for_participant()

        await self.run_multimodal_agent(ctx, participant)

        logger.info("Agent started")

    async def run_multimodal_agent(self, ctx: JobContext, participant: rtc.RemoteParticipant):
        logger.info("Starting multimodal agent")

        openai_model = OpenAIRealtimeModel().get_model()
        agent_handler = MultimodalAgentHandler(openai_model)
        await agent_handler.start_assistant(ctx, participant)

    async def respond(self, message: str):
        """Send a response to the messaging platform."""
        logger.info(f"Responding with message: {message}")


if __name__ == "__main__":
    agent = LiveKitAgent()

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=agent.entrypoint, 
        )
    )
from __future__ import annotations
import os
import logging
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import JobContext, WorkerOptions, AutoSubscribe, cli
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, silero, openai
from elevenlabs.client import ElevenLabs
from livekit.plugins import Plugin

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv(dotenv_path=".env.local")

class ElevenLabsTTS(Plugin):
    """Custom ElevenLabs TTS plugin for LiveKit"""
    
    def __init__(self):
        self.client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        
        # Get available voices and log them
        try:
            voices = self.client.voices.get_all()
            logger.info("Available voices:")
            for voice in voices.voices:
                logger.info(f"Voice ID: {voice.voice_id}, Name: {voice.name}")
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        
        super().__init__()

    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs"""
        try:
            # Voice settings for more control
            voice_settings = {
                "stability": 0.71,           # Higher stability = more consistent voice
                "similarity_boost": 0.75,     # Higher similarity = more similar to original voice
                "style": 0.0,               # Speaking style (0-1)
                "use_speaker_boost": True    # Enhance speaker clarity
            }
            
            # Generate audio using ElevenLabs with voice settings
            audio = self.client.generate(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=voice_settings
            )
            return audio
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {str(e)}")
            raise

    def set_voice(self, voice_id: str):
        """Change the voice ID"""
        self.voice_id = voice_id
        logger.info(f"Voice changed to: {voice_id}")

async def list_available_voices():
    """Utility function to list all available voices"""
    client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
    try:
        voices = client.voices.get_all()
        print("\nAvailable ElevenLabs Voices:")
        print("----------------------------")
        for voice in voices.voices:
            print(f"Voice ID: {voice.voice_id}")
            print(f"Name: {voice.name}")
            print(f"Description: {voice.description}")
            print("----------------------------")
    except Exception as e:
        print(f"Error listing voices: {e}")

async def entrypoint(ctx: JobContext):
    """Main entry point for the voice assistant"""
    initial_ctx = openai.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
        ),
    )

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create voice assistant with ElevenLabs TTS
    tts = ElevenLabsTTS()
    assistant = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4"),
        tts=tts,
        chat_ctx=initial_ctx,
    )
    
    assistant.start(ctx.room)
    await assistant.say("Hey, how can I help you today?", allow_interruptions=True)

async def main():
    """Main function to run the voice assistant"""
    try:
        # List available voices first
        await list_available_voices()
        
        logger.info("Starting voice assistant with ElevenLabs TTS...")
        await cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint,
                room_name=os.getenv('ROOMNAME', 'test-room'),
                url=os.getenv('LIVEKIT_URL'),
                api_key=os.getenv('LIVEKIT_API_KEY'),
                api_secret=os.getenv('LIVEKIT_API_SECRET')
            )
        )
    except Exception as e:
        logger.error(f"Error running voice assistant: {str(e)}")

if __name__ == "__main__":
    try:
        # Apply nest_asyncio to handle nested event loops
        nest_asyncio.apply()
        
        # Create and get event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logger.info("Event loop is already running, creating task")
            loop.create_task(main())
        else:
            logger.info("Starting new event loop")
            loop.run_until_complete(main())
            
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")

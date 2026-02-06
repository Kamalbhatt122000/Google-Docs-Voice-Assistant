"""
DocBot - Google Docs Teaching Assistant
Uses LiveKit Worker pattern for Playground compatibility
Helps users learn how to use Google Docs, Sheets, and Slides
"""
import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import google

import config
from automation_tools import ALL_TOOLS, get_browser

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docbot")


async def entrypoint(ctx: JobContext):
    """Main entry point for each participant session"""
    
    logger.info(f"New teaching session started for room: {ctx.room.name}")
    
    # Wait for a participant to connect
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Pre-launch browser with Google Docs in the background
    # This reduces latency when user asks for help
    logger.info("Pre-launching browser with Google Docs...")
    browser_task = asyncio.create_task(get_browser())
    
    # Wait for a participant
    participant = await ctx.wait_for_participant()
    logger.info(f"Learner joined: {participant.identity}")
    
    # Ensure browser is fully initialized before proceeding
    try:
        await browser_task
        logger.info("✅ Browser pre-launched and ready!")
    except Exception as e:
        logger.warning(f"Browser pre-launch warning: {e}")
    
    try:
        # Create AgentSession with Gemini Realtime API
        session = AgentSession(
            llm=google.realtime.RealtimeModel(
                voice="Puck",
                temperature=0.7,
            ),
            # Cartesia TTS for concurrent speech via session.say()
            tts="cartesia/sonic-3:f786b574-daa5-4673-aa0c-cbe3e8534c02",
        )
        
        # Create Agent with Google Docs teaching instructions and tools
        assistant = Agent(
            instructions=config.SYSTEM_INSTRUCTIONS,
            tools=ALL_TOOLS,
        )
        
        # Start agent session
        await session.start(
            room=ctx.room,
            agent=assistant,
        )
        
        logger.info("Session started")
        
        # Generate greeting
        logger.info("Greeting learner...")
        await session.generate_reply(
            instructions=(
                f"Greet the user as {config.ASSISTANT_NAME}, their Google Docs teaching assistant. "
                f"Say: Hi! I'm DocBot. I can teach you how to use Google Docs, Sheets, and Slides. "
                f"Just ask me 'How do I...' and I'll show you step by step! "
                f"For example, try asking 'How do I create a new document?' or 'How do I make text bold?'"
            )
        )
        logger.info("Greeting sent")
        
        # Keep session alive - wait for room to close
        disconnect_event = asyncio.Event()
        
        @ctx.room.on("disconnected")
        def on_disconnect():
            disconnect_event.set()
        
        await disconnect_event.wait()
        
    except Exception as e:
        logger.error(f"Session error: {e}")
        raise
    finally:
        logger.info("Teaching session ended")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )

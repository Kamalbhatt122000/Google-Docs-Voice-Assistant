"""
Google Docs Teaching Assistant - Browser Automation Tools
Uses Gemini Computer Use to demonstrate how to use Google Docs, Sheets, and Slides
"""
import asyncio
from typing import Annotated
from pydantic import Field
from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from browser_controller import BrowserAutomation


# Global browser instance
_browser: BrowserAutomation = None

# Lock to prevent concurrent browser actions
_action_lock = asyncio.Lock()
_action_in_progress = False


async def get_browser() -> BrowserAutomation:
    """Get browser instance"""
    global _browser
    if _browser is None:
        _browser = await BrowserAutomation.get_instance()
    return _browser


@function_tool()
async def browser_action(
    context: RunContext,
    task: Annotated[str, Field(description="The user's question about how to do something in Google Docs/Sheets/Slides")]
) -> str:
    """Demonstrate how to do something in Google Docs, Sheets, or Slides.
    
    This tool shows the user step-by-step how to perform tasks by actually
    doing it in the browser while explaining each step.
    
    Examples:
        - "How do I create a new document?"
        - "How do I make text bold?"
        - "How do I add a table?"
        - "How do I share this document?"
        - "How do I insert an image?"
    """
    global _action_in_progress
    
    # Validate task - don't execute empty or meaningless tasks
    if not task or task.strip() in [".", "", " "]:
        print(f"Skipping invalid task: '{task}'")
        return "invalid task"
    
    # Check if another action is already in progress
    if _action_in_progress:
        print(f"Task already in progress, skipping: {task}")
        return "already running"
    
    # Acquire lock to prevent concurrent execution
    async with _action_lock:
        _action_in_progress = True
        try:
            print(f"Teaching task: {task}")
            browser = await get_browser()
            
            # Create an async speech callback that wraps session.say()
            async def speech_callback(text: str):
                """Speak teaching explanations using the agent session"""
                context.session.say(text, allow_interruptions=True)
            
            # Execute the task with speech callback for step-by-step teaching
            result = await browser.execute_task(task, speech_callback=speech_callback)
            
            if result["success"]:
                return "demonstration complete"
            else:
                error_msg = f"I had some trouble demonstrating that. {result.get('error', 'Unknown error')}."
                context.session.say(error_msg, allow_interruptions=True)
                return "error handled"
        finally:
            _action_in_progress = False


@function_tool()
async def close_browser() -> str:
    """Close the browser when the teaching session is done."""
    global _browser
    if _browser:
        await _browser.close()
        _browser = None
        return "I've closed the browser. Just ask me anything about Google Docs when you want to learn more!"
    return "The browser is already closed. Ask me a question to start a new demonstration!"


# Tools for teaching Google Docs/Sheets/Slides
ALL_TOOLS = [
    browser_action,
    close_browser,
]

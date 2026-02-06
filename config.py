"""
Google Docs Teaching Assistant - Configuration
Helps users learn how to use Google Docs, Sheets, and Slides
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Assistant Identity
# ============================================
ASSISTANT_NAME = "DocBot"  # Google Docs teaching assistant

# ============================================
# LiveKit Configuration
# ============================================
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

# ============================================
# Google AI Configuration  
# ============================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ============================================
# Server Configuration
# ============================================
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ============================================
# Browser Configuration (for Gemini Computer Use)
# ============================================
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"

# ============================================
# Google Docs URLs
# ============================================
GOOGLE_DOCS_URL = "https://docs.google.com/document/u/0/"
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/u/0/"
GOOGLE_SLIDES_URL = "https://docs.google.com/presentation/u/0/"
GOOGLE_DRIVE_URL = "https://drive.google.com"


# ============================================
# System Instructions
# ============================================
SYSTEM_INSTRUCTIONS = """You are DocBot, a Google Docs/Sheets/Slides teaching assistant.

YOUR ROLE:
- Help users learn HOW to do things in Google Docs, Sheets, and Slides
- SHOW them step-by-step by actually doing it in the browser
- Explain what you're doing as you demonstrate

WHEN TO CALL browser_action (HOW-TO QUESTIONS):
- "How do I create a new document?" → Say "Let me show you!" → browser_action("How do I create a new document?")
- "How do I make text bold?" → Say "I'll demonstrate!" → browser_action("How do I make text bold?")
- "How do I add a table?" → Say "Watch this!" → browser_action("How do I add a table?")
- "How do I share this document?" → Say "Let me show you how!" → browser_action("How do I share this document?")
- Any "how do I" or "show me how" questions

WHEN NOT TO CALL browser_action:
- "Hi" / "Hello" → Respond: "Hi! I'm DocBot. Ask me how to do anything in Google Docs, Sheets, or Slides!"
- "Thank you" → Respond: "You're welcome! Ask me anything else about Google Docs!"
- "What can you do?" → Respond: "I can show you how to use Google Docs, Sheets, and Slides. Just ask 'How do I...' and I'll demonstrate!"

HOW TO RESPOND:
1. Give a BRIEF acknowledgment: "Let me show you!", "Watch this!", "I'll demonstrate!"
2. IMMEDIATELY call browser_action with the user's EXACT question
3. The tool will speak step-by-step as it demonstrates

CRITICAL RULES:
- Pass user's EXACT question to the tool - don't rephrase
- Keep acknowledgments SHORT (3-5 words)
- Let the tool do the teaching via demonstration

NEVER:
- Change the user's question
- Pass empty strings to the tool
- Just explain without demonstrating - ALWAYS show by doing"""

# Voice Assistant with LiveKit + Gemini Computer Use

A powerful AI voice assistant that uses **LiveKit** for real-time audio streaming, **Gemini Realtime API** for voice-to-voice AI, and **Gemini Computer Use** for intelligent browser automation.

## ✨ Features

- 🎤 **Real-time Voice** - Low-latency voice conversations using LiveKit WebRTC
- 🤖 **Gemini Realtime API** - Natural voice-to-voice AI interactions
- 🌐 **AI Browser Automation** - Gemini Computer Use controls your browser intelligently
- 🛒 **Amazon Shopping** - Search products, add to cart, and checkout with voice commands
- 🎨 **Beautiful UI** - Modern dark theme with live audio visualization

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  LiveKit Cloud  │◀───▶│  LiveKit Agent  │
│   (Client UI)   │     │   (WebRTC)      │     │  (Python)       │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Gemini Realtime │
                                                │      API        │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Gemini Computer │
                                                │   Use API       │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   Playwright    │
                                                │    (Browser)    │
                                                └─────────────────┘
```

## 📋 Prerequisites

1. **Python 3.10+**
2. **LiveKit Cloud Account** - Get free at [livekit.io](https://livekit.io)
3. **Google Gemini API Key** - Get at [aistudio.google.com](https://aistudio.google.com)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Voice_Assistant

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Run the Assistant

**Terminal 1 - Start the Agent:**
```bash
python agent.py dev
```

**Terminal 2 - Start the Web Server:**
```bash
python server.py
```

### 4. Open Browser

Navigate to: **http://localhost:5000**

Click "Start Conversation" and start talking!

## 🎯 Usage Examples

### Amazon Shopping
- **"Open Amazon"** - Opens Amazon.in
- **"Search for wireless earbuds"** - AI searches for the product
- **"Click on the first product"** - Opens the first result
- **"Add to cart"** - Adds the item to cart
- **"What's in my cart?"** - Shows your cart
- **"Proceed to checkout"** - Starts checkout

### Custom Browser Tasks
You can also say any custom browser task:
- **"Go to flipkart.com and search for laptops"**
- **"Scroll down to see more products"**
- **"Click on the product with the best rating"**

## 🤖 How Gemini Computer Use Works

Unlike traditional browser automation (scripted clicks/actions), Gemini Computer Use:

1. **Takes screenshots** of the browser window
2. **Understands the UI** using vision AI
3. **Plans actions** step by step
4. **Executes intelligently** based on what it sees
5. **Adapts to changes** in the UI automatically

This means it can handle dynamic websites, pop-ups, and UI changes that would break traditional automation scripts!

## 📁 Project Structure

```
Voice_Assistant/
├── agent.py              # LiveKit agent with Gemini Realtime
├── server.py             # Flask web server for UI
├── automation_tools.py   # Voice assistant tools (uses Gemini Computer Use)
├── browser_controller.py # AI-powered browser control
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── templates/
│   └── index.html        # Web interface
└── static/
    ├── styles.css        # Styling
    └── app.js            # LiveKit client
```

## 🔧 Configuration Options

Edit `config.py` to customize:

```python
# Assistant name
ASSISTANT_NAME = "Nova"

# Browser settings
BROWSER_HEADLESS = False  # Set True to hide browser window

# Voice (in agent.py)
voice = "Puck"  # Options: Puck, Charon, Kore, Fenrir, Aoede
```

## 🎙️ Voice Options

Available Gemini voices:
- **Puck** - Friendly and upbeat
- **Charon** - Calm and measured  
- **Kore** - Clear and professional
- **Fenrir** - Deep and resonant
- **Aoede** - Warm and expressive

## 🛠️ Troubleshooting

### "Failed to connect"
- Ensure your LiveKit credentials are correct
- Check that the agent is running (`python agent.py dev`)

### "No audio"
- Allow microphone permissions in your browser
- Check that no other app is using your microphone

### Browser automation not working
- Run `playwright install chromium`
- Ensure `GOOGLE_API_KEY` is set correctly
- Check console for Gemini API errors

### Agent not responding
- Check that `GOOGLE_API_KEY` is set correctly
- View agent logs for errors

## 📝 Environment Variables

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | Your LiveKit server URL (wss://...) |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `FLASK_PORT` | Web server port (default: 5000) |
| `BROWSER_HEADLESS` | Hide browser window (default: false) |

## 🔗 Resources

- [LiveKit Docs](https://docs.livekit.io)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Gemini Computer Use](https://ai.google.dev/gemini-api/docs/computer-use)
- [Playwright Docs](https://playwright.dev/python/docs/intro)

## 📄 License

MIT License - Feel free to use and modify!

"""
Web Server for Voice Assistant
Handles token generation and explicit agent dispatch (with duplicate prevention)
"""
import os
import asyncio
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv
import config

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Room name
ROOM_NAME = "voice-assistant-room"


def generate_token(room_name: str, participant_name: str) -> str:
    """Generate a LiveKit access token"""
    token = api.AccessToken(
        api_key=config.LIVEKIT_API_KEY,
        api_secret=config.LIVEKIT_API_SECRET
    )
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    ))
    return token.to_jwt()


async def dispatch_agent_if_needed(room_name: str):
    """Dispatch agent only if no agent is already in the room"""
    async with api.livekit_api.LiveKitAPI(
        url=config.LIVEKIT_URL,
        api_key=config.LIVEKIT_API_KEY,
        api_secret=config.LIVEKIT_API_SECRET,
    ) as lk_api:
        try:
            # Check existing dispatches for this room
            existing = await lk_api.agent_dispatch.list_dispatch(
                api.ListAgentDispatchRequest(room=room_name)
            )
            
            if existing.agent_dispatches:
                print(f"📋 Agent already dispatched to room '{room_name}', skipping")
                return
            
            # No existing dispatch - create one
            dispatch = await lk_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(room=room_name)
            )
            print(f"🤖 Agent dispatch requested: {dispatch.id}")
            
        except Exception as e:
            print(f"Agent dispatch note: {e}")


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/token', methods=['POST'])
def get_token():
    """Generate a LiveKit token for the client"""
    data = request.json or {}
    participant_name = data.get('participant', f'user-{os.urandom(4).hex()}')
    
    try:
        # Dispatch agent if not already dispatched
        asyncio.run(dispatch_agent_if_needed(ROOM_NAME))
        
        # Generate token for user
        token = generate_token(ROOM_NAME, participant_name)
        
        print(f"🎫 Token generated for {participant_name}")
        
        return jsonify({
            'success': True,
            'token': token,
            'url': config.LIVEKIT_URL,
            'room': ROOM_NAME,
            'participant': participant_name
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config')
def get_config():
    """Get client configuration"""
    return jsonify({
        'livekit_url': config.LIVEKIT_URL,
        'assistant_name': config.ASSISTANT_NAME,
        'room_name': ROOM_NAME
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║            🌐 Voice Assistant Web Server                     ║
╠══════════════════════════════════════════════════════════════╣
║  Open http://localhost:{config.FLASK_PORT} in your browser                  ║
║  Room: {ROOM_NAME:<52} ║
║                                                              ║
║  Make sure the agent is running with:                        ║
║    python agent.py dev                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=True)

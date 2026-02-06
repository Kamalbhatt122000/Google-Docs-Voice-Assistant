"""
Web Server for Voice Assistant
Handles token generation - agent dispatch is automatic via LiveKit Cloud
"""
import os
import uuid
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv
import config

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)


def generate_room_name() -> str:
    """Generate a unique room name for each session"""
    return f"voice-room-{uuid.uuid4().hex[:8]}"



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


# NOTE: We rely on LiveKit Cloud's automatic agent dispatch feature
# When a participant joins a room, LiveKit Cloud automatically dispatches an agent
# No explicit dispatch needed - this avoids double agents joining


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/token', methods=['POST'])
def get_token():
    """Generate a LiveKit token for the client"""
    data = request.json or {}
    participant_name = data.get('participant', f'user-{os.urandom(4).hex()}')
    
    # Generate a unique room name for each session
    room_name = generate_room_name()
    
    try:
        # Generate token for user
        # Agent will be auto-dispatched by LiveKit Cloud when user joins
        token = generate_token(room_name, participant_name)
        
        print(f"🎫 Token generated for {participant_name} in room {room_name}")
        
        return jsonify({
            'success': True,
            'token': token,
            'url': config.LIVEKIT_URL,
            'room': room_name,
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
        'room_name': 'dynamic'  # Room is generated per session
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
║  Rooms: Generated dynamically per session                    ║
║                                                              ║
║  Make sure the agent is running with:                        ║
║    python agent.py dev                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=True)

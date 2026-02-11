/**
 * Voice Assistant - LiveKit Client
 * Handles real-time audio communication with the LiveKit agent
 */

// ==================== LiveKit Setup ====================
const { Room, RoomEvent, Track, ParticipantEvent } = LivekitClient;

let room = null;
let localAudioTrack = null;
let isConnected = false;
let isAgentConnected = false;
let isSpeaking = false;

// ==================== DOM Elements ====================
const elements = {
    statusCard: document.getElementById('status-card'),
    statusTitle: document.getElementById('status-title'),
    statusSubtitle: document.getElementById('status-subtitle'),
    statusIcon: document.getElementById('status-icon'),
    waveform: document.getElementById('waveform'),
    connectButton: document.getElementById('connect-button'),
    connectText: document.getElementById('connect-text'),
    connectIcon: document.getElementById('connect-icon'),
    controlHint: document.getElementById('control-hint'),
    connectionStatus: document.getElementById('connection-status'),
    transcriptMessages: document.getElementById('transcript-messages'),
    audioCanvas: document.getElementById('audio-canvas'),
    audioVisualizer: document.getElementById('audio-visualizer'),
};

// ==================== Audio Visualization ====================
let audioContext = null;
let analyser = null;
let animationId = null;

function setupAudioVisualization(stream) {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const canvas = elements.audioCanvas;
    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    canvas.width = canvas.offsetWidth * 2;
    canvas.height = canvas.offsetHeight * 2;

    function draw() {
        animationId = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        ctx.fillStyle = 'rgba(10, 10, 15, 0.3)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.5;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

            const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight);
            gradient.addColorStop(0, '#6366f1');
            gradient.addColorStop(0.5, '#8b5cf6');
            gradient.addColorStop(1, '#a855f7');

            ctx.fillStyle = gradient;
            ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);

            x += barWidth;
        }
    }

    draw();
}

function stopAudioVisualization() {
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }
}

// ==================== Status Updates ====================
function updateStatus(status, message = '', subtitle = '') {
    elements.statusCard.className = 'status-card ' + status;

    const statusMessages = {
        disconnected: { title: 'Click to Connect', subtitle: 'Start a voice session with Aria' },
        connecting: { title: 'Connecting...', subtitle: 'Setting up secure connection' },
        waiting: { title: 'Waiting for Agent...', subtitle: 'Agent is joining the room' },
        connected: { title: 'Connected', subtitle: 'Listening... Speak now!' },
        speaking: { title: 'Aria is Speaking', subtitle: 'Wait for response or interrupt' },
        listening: { title: 'Listening...', subtitle: 'Go ahead, I\'m listening!' },
        error: { title: 'Connection Error', subtitle: 'Please try again' },
    };

    const info = statusMessages[status] || statusMessages.disconnected;
    elements.statusTitle.textContent = message || info.title;
    elements.statusSubtitle.textContent = subtitle || info.subtitle;

    // Update connection status badge
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');

    if (status === 'connected' || status === 'speaking' || status === 'listening') {
        statusDot.style.background = '#22c55e';
        statusText.textContent = 'Connected';
    } else if (status === 'connecting') {
        statusDot.style.background = '#f59e0b';
        statusText.textContent = 'Connecting...';
    } else if (status === 'waiting') {
        statusDot.style.background = '#f59e0b';
        statusText.textContent = 'Waiting for Agent...';
    } else {
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Disconnected';
    }
}

function updateConnectButton(connected) {
    if (connected) {
        elements.connectButton.classList.add('connected');
        elements.connectText.textContent = 'End Conversation';
        elements.controlHint.textContent = 'Click to disconnect';
    } else {
        elements.connectButton.classList.remove('connected');
        elements.connectText.textContent = 'Start Conversation';
        elements.controlHint.textContent = 'Click to connect and start talking';
    }
}

// ==================== Transcript ====================
function addTranscript(role, text) {
    const item = document.createElement('div');
    item.className = `transcript-item ${role}`;

    const roleLabel = role === 'user' ? '🎤 You' : '🤖 Aria';
    item.innerHTML = `<span class="role">${roleLabel}</span><p>${text}</p>`;

    elements.transcriptMessages.appendChild(item);
    elements.transcriptMessages.scrollTop = elements.transcriptMessages.scrollHeight;
}

// ==================== LiveKit Connection ====================
async function connect() {
    if (isConnected) {
        await disconnect();
        return;
    }

    updateStatus('connecting');
    updateConnectButton(false);

    try {
        // Get token from server (server generates unique room per session)
        const response = await fetch('/api/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                participant: 'user-' + Math.random().toString(36).substring(7)
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to get token');
        }

        console.log('🎫 Got token, connecting to:', data.url);

        // Create room with optimized audio settings
        room = new Room({
            adaptiveStream: true,
            dynacast: true,
            // Audio optimization for real-time voice
            audioCaptureDefaults: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            },
            audioOutput: {
                deviceId: 'default',
            },
        });

        // Set up event handlers
        setupRoomEvents(room);

        // Connect to room
        await room.connect(data.url, data.token);
        console.log('✅ Connected to room:', room.name);

        // Publish microphone
        await room.localParticipant.setMicrophoneEnabled(true);
        localAudioTrack = room.localParticipant.getTrackPublication(Track.Source.Microphone);

        if (localAudioTrack && localAudioTrack.track) {
            const stream = new MediaStream([localAudioTrack.track.mediaStreamTrack]);
            setupAudioVisualization(stream);
        }

        isConnected = true;
        isAgentConnected = false;  // Will be set true when we receive agent's audio track
        updateConnectButton(true);
        updateStatus('waiting');
        addTranscript('system', 'Room joined. Waiting for agent to connect...');

        // Log existing participants for debugging
        console.log('📋 Remote participants in room:', room.remoteParticipants.size);
        room.remoteParticipants.forEach((participant) => {
            console.log('  - ', participant.identity);
        });

    } catch (error) {
        console.error('❌ Connection failed:', error);
        updateStatus('error', 'Connection Failed', error.message);
        addTranscript('system', 'Failed to connect: ' + error.message);
    }
}

async function disconnect() {
    if (room) {
        await room.disconnect();
        room = null;
    }

    stopAudioVisualization();
    isConnected = false;
    isAgentConnected = false;
    updateStatus('disconnected');
    updateConnectButton(false);
    addTranscript('system', 'Disconnected from voice session.');
}

function setupRoomEvents(room) {
    room.on(RoomEvent.Connected, () => {
        console.log('🔗 Room connected');
    });

    room.on(RoomEvent.Disconnected, () => {
        console.log('🔌 Room disconnected');
        isConnected = false;
        updateStatus('disconnected');
        updateConnectButton(false);
    });

    room.on(RoomEvent.ParticipantConnected, (participant) => {
        console.log('👤 Participant connected:', participant.identity);
        // Don't set connected here - wait for audio track subscription
        // This ensures we only show connected when we can actually hear them
    });

    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
        console.log('👤 Participant disconnected:', participant.identity);
        // Check if this was our agent (any remote participant)
        if (participant.identity !== room.localParticipant.identity) {
            // Double-check no other remote participants exist
            if (room.remoteParticipants.size === 0) {
                isAgentConnected = false;
                updateStatus('waiting', 'Agent Disconnected', 'Click End then Start to reconnect.');
                addTranscript('system', 'Agent disconnected.');
            }
        }
    });

    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log('🎵 Track subscribed:', track.kind, 'from:', participant.identity);

        if (track.kind === Track.Kind.Audio) {
            // Remove any existing audio element for this participant to prevent duplicates
            const existingAudio = document.getElementById('agent-audio-' + participant.identity);
            if (existingAudio) {
                existingAudio.remove();
            }

            // Attach audio with optimized settings for smooth WebRTC playback
            const audioElement = track.attach();
            audioElement.id = 'agent-audio-' + participant.identity;
            audioElement.autoplay = true;
            audioElement.playsInline = true;
            audioElement.muted = false;

            // IMPORTANT: Do NOT call audioElement.load() on WebRTC streams
            // It resets the stream and causes choppy/breaking audio

            // Passive error logging only — no .load() recovery for live streams
            audioElement.onerror = (e) => {
                console.error('🔊 Audio playback error:', e);
            };

            // Passive stall logging — WebRTC handles its own buffering
            audioElement.onstalled = () => {
                console.warn('⚠️ Audio stream stalled (WebRTC will auto-recover)');
            };

            audioElement.onwaiting = () => {
                console.log('⏳ Audio buffering...');
            };

            audioElement.onplaying = () => {
                console.log('▶️ Audio playing smoothly');
            };

            document.body.appendChild(audioElement);

            // Ensure playback starts (needed for browsers that block autoplay)
            audioElement.play().catch(err => {
                console.warn('Initial play failed (user interaction may be needed):', err);
            });

            // If we receive audio from someone else, agent is connected
            if (participant.identity !== room.localParticipant.identity) {
                console.log('✅ Agent audio track received - marking as connected');
                isAgentConnected = true;
                updateStatus('connected');
                addTranscript('system', 'Agent connected! Start speaking now.');
            }
        }
    });

    room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
        console.log('🔇 Track unsubscribed:', track.kind, 'from:', participant?.identity);
        track.detach().forEach(el => el.remove());

        // If we lost audio from a remote participant, agent might have disconnected
        if (track.kind === Track.Kind.Audio && participant &&
            participant.identity !== room.localParticipant.identity) {
            console.log('⚠️ Agent audio track lost - checking participants');

            // Check if there are any other remote participants still connected
            let hasRemoteParticipant = false;
            room.remoteParticipants.forEach((p) => {
                if (p.identity !== participant.identity) {
                    hasRemoteParticipant = true;
                }
            });

            if (!hasRemoteParticipant) {
                isAgentConnected = false;
                updateStatus('waiting', 'Agent Disconnected', 'Reconnect to continue');
                addTranscript('system', 'Agent disconnected.');
            }
        }
    });

    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        // Only update speaking status if agent is actually connected
        if (!isAgentConnected) {
            return; // Don't change status if agent isn't connected
        }

        const agentSpeaking = speakers.some(s => s.identity !== room.localParticipant.identity);
        const userSpeaking = speakers.some(s => s.identity === room.localParticipant.identity);

        if (agentSpeaking) {
            updateStatus('speaking');
            isSpeaking = true;
        } else if (userSpeaking) {
            updateStatus('listening');
        } else if (isConnected && isAgentConnected) {
            updateStatus('connected');
            isSpeaking = false;
        }
    });

    // Handle transcription (if available)
    room.on(RoomEvent.TranscriptionReceived, (segments, participant) => {
        segments.forEach(segment => {
            if (segment.final) {
                const role = participant?.identity.includes('agent') ? 'assistant' : 'user';
                addTranscript(role, segment.text);
            }
        });
    });

    room.on(RoomEvent.DataReceived, (payload, participant) => {
        try {
            const data = JSON.parse(new TextDecoder().decode(payload));
            console.log('📦 Data received:', data);

            if (data.type === 'transcript') {
                addTranscript(data.role, data.text);
            }
        } catch (e) {
            // Ignore non-JSON data
        }
    });
}

// ==================== Event Listeners ====================
elements.connectButton.addEventListener('click', connect);

// Quick action chips
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const prompt = chip.dataset.prompt;
        if (prompt) {
            addTranscript('system', `Try saying: "${prompt}"`);
        }
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        elements.connectButton.click();
    }

    if (e.code === 'Escape' && isConnected) {
        disconnect();
    }
});

// ==================== Initialize ====================
console.log('🚀 Voice Assistant UI initialized');
updateStatus('disconnected');

let room;
let userInfo = {};

document.getElementById('userForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Collect user information
    userInfo = {
        name: document.getElementById('name').value,
        location: document.getElementById('location').value,
        source: document.getElementById('source').value
    };

    console.log('User info collected:', userInfo);

    // Validate required fields
    if (!userInfo.name || !userInfo.location || !userInfo.source) {
        alert('Please fill in all required fields marked with *');
        return;
    }

    // Hide form and show call section
    document.getElementById('userForm').classList.add('d-none');
    document.getElementById('callSection').classList.remove('d-none');
    document.getElementById('status').textContent = 'Initializing call...';

    // Initialize LiveKit connection
    await connectToRoom();
});

async function connectToRoom() {
    try {
        console.log('Connecting to room with user info:', userInfo);
        
        // Get token from server
        const response = await fetch('/get-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userInfo)
        });
        
        if (!response.ok) {
            throw new Error('Failed to get token');
        }
        
        const { token, url, room: roomName, metadata } = await response.json();
        console.log('Got token response with metadata:', { url, roomName, metadata });

        // Create LiveKit room
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true
        });

        // Set up metadata handling before connecting
        room.on('participant-connected', (participant) => {
            console.log('Participant connected, setting metadata');
            if (participant.identity === room.localParticipant.identity) {
                participant.setMetadata(metadata);
            }
        });

        // Connect to LiveKit server
        await room.connect(url, token);
        console.log('Connected to LiveKit room');
        
        // Set metadata on local participant immediately after connection
        if (room.localParticipant) {
            console.log('Setting metadata on local participant');
            await room.localParticipant.setMetadata(metadata);
            
            // Double check metadata was set
            const currentMetadata = room.localParticipant.metadata;
            console.log('Current participant metadata:', currentMetadata);
            
            if (!currentMetadata) {
                console.warn('Metadata not set, retrying...');
                // Retry setting metadata after a short delay
                setTimeout(async () => {
                    await room.localParticipant.setMetadata(metadata);
                    console.log('Metadata set after retry:', room.localParticipant.metadata);
                }, 1000);
            }
        } else {
            console.error('No local participant available');
        }
        
        document.getElementById('status').textContent = 'Connected! Starting audio...';
        
        // Start local audio
        await startLocalAudio();
        
    } catch (error) {
        console.error('Error connecting to room:', error);
        document.getElementById('status').textContent = 'Error: ' + error.message;
    }
}

async function startLocalAudio() {
    try {
        // Create local audio track
        const audioTrack = await LiveKit.createLocalAudioTrack();
        
        // Publish track
        await room.localParticipant.publishTrack(audioTrack);
        
        document.getElementById('status').textContent = 'Call connected!';
        document.getElementById('muteAudio').classList.remove('d-none');
        
    } catch (error) {
        console.error('Error starting audio:', error);
        document.getElementById('status').textContent = 'Error starting audio: ' + error.message;
    }
}

function setupRoomHandlers() {
    // Handle participant joining
    room.on(LiveKit.RoomEvent.ParticipantConnected, participant => {
        console.log('Participant connected:', participant.identity);
        document.getElementById('status').textContent = 'AI Assistant joined the call';
    });

    // Handle participant leaving
    room.on(LiveKit.RoomEvent.ParticipantDisconnected, participant => {
        console.log('Participant disconnected:', participant.identity);
        document.getElementById('status').textContent = 'AI Assistant left the call';
    });

    // Handle room disconnection
    room.on(LiveKit.RoomEvent.Disconnected, () => {
        document.getElementById('status').textContent = 'Call ended';
        document.getElementById('status').className = 'alert alert-warning';
        document.getElementById('userForm').classList.remove('d-none');
        document.getElementById('callSection').classList.add('d-none');
    });
}

// Mute/unmute button handler
document.getElementById('muteAudio').addEventListener('click', async () => {
    const button = document.getElementById('muteAudio');
    const tracks = room.localParticipant.audioTracks;
    
    for (const [_, publication] of tracks) {
        if (publication.track.isMuted) {
            await publication.track.unmute();
            button.textContent = 'Mute';
            button.classList.remove('btn-success');
            button.classList.add('btn-danger');
        } else {
            await publication.track.mute();
            button.textContent = 'Unmute';
            button.classList.remove('btn-danger');
            button.classList.add('btn-success');
        }
    }
});

// End call button handler
document.getElementById('endCall').addEventListener('click', async () => {
    if (room) {
        await room.disconnect();
        document.getElementById('callSection').classList.add('d-none');
        document.getElementById('userForm').classList.remove('d-none');
    }
});

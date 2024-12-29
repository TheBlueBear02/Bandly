from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import requests
from flask import Response
from flask_socketio import join_room, leave_room, rooms

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

rooms = {}  # Dictionary to store room data temporarily
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    response = requests.get(url)
    return Response(response.content, content_type=response.headers['Content-Type'])

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = request.form.get('room_id')
    if room_id in rooms:
        flash('Room already exists!')  # Optional: Show a message if room exists
        return redirect(url_for('index'))
    rooms[room_id] = {"url": None, "users": []}  # Initialize room with no URL and an empty list for users

    print("****************************************************")
    print("Current rooms dictionary:", rooms)
    print("Room ID being accessed:", room_id)
    return redirect(url_for('room', room_id=room_id))

# WebSocket event to join a room
@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    join_room(room_id)
    
    # Ensure the room exists in the rooms dictionary
    if room_id not in rooms:
        rooms[room_id] = {"url": None, "users": []}
    
    # Add user to the room
    user_id = request.sid  # Unique session ID for the user
    if user_id not in rooms[room_id]["users"]:
        rooms[room_id]["users"].append(user_id)
    
    # Send the current URL to the new user
    if rooms[room_id]["url"]:
        emit('update_iframe', {'new_url': rooms[room_id]["url"]}, to=request.sid)

# WebSocket event to leave a room
@socketio.on('leave_room')
def on_leave(data):
    room_id = data['room_id']
    leave_room(room_id)
    print(f"User {request.sid} left room {room_id}")

@socketio.on('get_users')
def send_user_list(data):
    room_id = data['room_id']
    users_in_room = list(socketio.server.manager.get_participants('/', room_id))
    emit('user_list', {'users': users_in_room}, room=request.sid)


@app.route('/room/<room_id>', methods=['GET', 'POST'])
def room(room_id):
    if request.method == 'POST':
        chord_url = request.form.get('chord_url')
        rooms[room_id]["url"] = chord_url
    chord_url = rooms.get(room_id, {}).get("url")
    return render_template('room.html', room_id=room_id, chord_url=chord_url)

@socketio.on('url_changed')
def handle_url_changed(data):
    room_id = data['room_id']
    new_url = data['new_url']
    
    # Ensure the room exists
    if room_id not in rooms:
        rooms[room_id] = {"url": None, "users": []}
    
    # Update the URL for the room
    rooms[room_id]["url"] = new_url
    
    # Notify all users in the room
    emit('update_iframe', {'new_url': new_url}, room=room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

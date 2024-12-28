from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import requests
from flask import Response

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
    return redirect(url_for('room', room_id=room_id))

@app.route('/join_room', methods=['POST'])
def join_room():
    room_id = request.form.get('room_id')
    if room_id not in rooms:
        flash('Room not found!')  # Show an error message if the room doesn't exist
        return redirect(url_for('index'))
    return redirect(url_for('room', room_id=room_id))

@app.route('/room/<room_id>', methods=['GET', 'POST'])
def room(room_id):
    if request.method == 'POST':
        chord_url = request.form.get('chord_url')
        rooms[room_id]["url"] = chord_url
    chord_url = rooms.get(room_id, {}).get("url")
    return render_template('room.html', room_id=room_id, chord_url=chord_url)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

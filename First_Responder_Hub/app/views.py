from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from textToSpeech import transcriber
from textToSpeech.transcriber import run_transcriber

# This file carries all the routes so it doesn't clutter the main file

# Use name of file: view
views = Blueprint(__name__, "views")
incidents = []  
transcription_thread = None

@views.route("/")
def home(): # Home page
    return render_template("index.html")

@views.route("/EventMarker")
def eventmarker():
    return render_template("EventMarker.html")

@views.route('/start-call', methods=['POST'])
def start_call():
    global transcription_thread
    if transcription_thread and transcription_thread.is_alive():
        return jsonify({'status': 'Transcription already running.'})
    
    # Start transcription in a background thread
    transcription_thread = threading.Thread(target=transcriber.run_transcriber)
    transcription_thread.start()
    
    return jsonify({'status': 'Transcription started.'})

@views.route("/new_incident", methods=["POST"])
def new_incident():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Store incident
    incidents.append(data)
    print(f"New incident added: {data}")
    return jsonify({"status": "Incident added successfully", "incident": data}), 200
@views.route('/get_incidents', methods=['GET'])
def get_incidents():
    return jsonify(incidents), 200

@views.route("/incidents")
def incident_list():
    return render_template("incidents.html", incidents=incidents)
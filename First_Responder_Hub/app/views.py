from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from textToSpeech import transcriber
from textToSpeech.transcriber import run_transcriber

from data import incidents
# This file carries all the routes so it doesn't clutter the main file

# Use name of file: view
views = Blueprint(__name__, "views")
transcription_thread = None # global thread

@views.route("/")
def home(): # Home page for users
    return render_template("index.html")

@views.route('/start-call', methods=['POST'])
def start_call():
    global transcription_thread
    if transcription_thread and transcription_thread.is_alive():
        return jsonify({'status': 'Transcription already running.'}) # Return if thread is still running - the transcription function
    
    # Start transcription in a background thread
    transcription_thread = threading.Thread(target=transcriber.run_transcriber) #Passes the func to a thread to run in the next line
    # We can also add args=__ for any parameters given to our transcriber function
    transcription_thread.start()
    
    return jsonify({'status': 'Transcription started.'})

@views.route("/incident/<int:index>")
def incident_detail(index):
    if index < 0 or index >= len(incidents):
        return "Incident not found", 404
    return render_template("incident_detail.html", incident=incidents[index])

@views.route('/get_incidents', methods=['GET'])
def get_incidents():
    return jsonify(incidents)

@views.route("/dashboard")
def dashboard():
    return render_template('dashboard.html', incidents=incidents)


from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import threading
from models import Incident
from textToSpeech.transcriber import transcribe_audio
# This file carries all the routes so it doesn't clutter the main file

# Use name of file: view
views = Blueprint(__name__, "views")

webpages = ['transcriber.html', 'index.html', 'EventMarker.html']

@views.route("/")
def home(): # Home page
    return render_template("index.html")

@views.route("/EventMarker")
def eventmarker():
    return render_template("EventMarker.html")

@views.route('/start-call', methods=['POST'])
def start_call():
    # Run transcription and processing in a separate thread to avoid blocking
    thread = threading.Thread(target=transcribe_audio)
    thread.start()
    return jsonify({"status": "Transcription started"}), 202

@views.route('/incidents')
def incidents():
    incidents_list = Incident.query.order_by(Incident.time_of_emergency.desc()).all()
    return render_template('incidents.html', incidents=incidents_list)

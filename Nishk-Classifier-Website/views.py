from flask import Blueprint, render_template, request, redirect, url_for, session
# This file carries all the routes so it doesn't clutter the main file

# Use name of file: view
views = Blueprint(__name__, "views")

webpages = ['transcriber']


@views.route("/")
def home():
    return render_template("index.html")

@views.route("/EventMarker")
def eventmarker():
    return render_template("Event_Marker.html")

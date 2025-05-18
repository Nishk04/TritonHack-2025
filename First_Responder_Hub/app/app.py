# app/app.py
from flask import Flask
from views import views
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///incidents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "hello"

db.init_app(app)
app.register_blueprint(views, url_prefix="/")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database file if not exists
    app.run(debug=True, use_reloader=False, port=8000)

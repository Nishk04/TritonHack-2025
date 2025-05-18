from flask import Flask
from views import views

app = Flask(__name__)
app.secret_key = "hello"

app.register_blueprint(views, url_prefix="/")

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8000)

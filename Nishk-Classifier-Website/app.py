from flask import Flask
from views import views

app = Flask(__name__)
# The url_prefix has to be the first thing used and then the routes
# Example: ...8000/views/'route name' 
# Keep url_prefix empty for now
app.register_blueprint(views, url_prefix="/")
app.secret_key = "hello"

if __name__ == '__main__':
# Debug set to true allows the website to automatically refresh as we change the code
# Default port is 5000
    app.run(debug=True, port=8000)
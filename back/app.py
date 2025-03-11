from flask import Flask
from flask_cors import CORS

from routes import init_routes

app = Flask(__name__)
CORS(app, resources={
        r"/generate/image/prompt": {"origins": "*"},
        r"/generate/image/image": {"origins": "*"},
        r"/generate/image/animation": {"origins": "*"},
        r"/generate/sound": {"origins": "*"},
        r"/generate/tags": {"origins": "*"}
    },
    supports_credentials=True,
)

init_routes(app)

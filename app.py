from flask import Flask, jsonify
from flask_cors import CORS
from mongoengine import connect
import config 
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.SECRET_KEY
CORS(app)

# connect to MongoDB
connect(host=config.MONGO_URI)

# register blueprints
from auth import bp as auth_bp
from routes import bp as api_bp
from flask_jwt_extended import JWTManager

jwt = JWTManager(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def root():
    return jsonify({'msg': 'handcrafted marketplace backend running'})

if __name__ == '__main__':
    # create local static upload folder if not using cloudinary
    if not config.CLOUDINARY_URL:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'uploads'), exist_ok=True)
    app.run(debug=True, port=5000)

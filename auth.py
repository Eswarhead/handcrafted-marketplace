from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    name = data.get('name') or ''
    role = data.get('role') or 'buyer'
    if not email or not password:
        return jsonify({'msg': 'email and password required'}), 400
    if User.objects(email=email).first():
        return jsonify({'msg': 'user exists'}), 400
    user = User(email=email, name=name, role=role, password_hash=generate_password_hash(password))
    user.save()
    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user': {'id': str(user.id), 'email': user.email, 'name': user.name, 'role': user.role}}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    user = User.objects(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'msg': 'invalid credentials'}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user': {'id': str(user.id), 'email': user.email, 'name': user.name, 'role': user.role}})

@bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.objects(id=uid).first()
    if not user:
        return jsonify({'msg': 'not found'}), 404
    return jsonify({'id': str(user.id), 'email': user.email, 'name': user.name, 'role': user.role})

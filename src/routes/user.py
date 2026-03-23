from flask import Blueprint, jsonify, request
from src.models.user import User, db
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    """Listar todos os usuários"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Criar novo usuário
    
    Body:
    {
        "username": "atendente1",
        "email": "atendente1@lachapa.com",
        "password": "123456",
        "role": "cashier"
    }
    """
    try:
        data = request.json
        
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username, email e password são obrigatórios'
            }), 400
        
        # Verificar se já existe
        existing = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Username ou email já cadastrado'
            }), 409
        
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'cashier')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"Usuário criado: {user.username}")
        return jsonify(user.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({ 'success': False, 'message': f'Erro ao criar usuário: {str(e)}' }), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    if data.get('password'):
        user.set_password(data['password'])
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

from flask import Blueprint, jsonify, request
from src.models.user import User, db
from datetime import datetime, timedelta
import jwt
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
TOKEN_EXPIRATION_HOURS = 24

def generate_token(user):
    """Gera um token JWT para o usuário"""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ============================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Endpoint de login
    
    Body esperado:
    {
        "username": "admin@lachapa.com",
        "password": "123456"
    }
    """
    try:
        dados = request.json
        
        if not dados:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos'
            }), 400
        
        username = dados.get('username', '').strip()
        password = dados.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Usuário e senha são obrigatórios'
            }), 400
        
        # Buscar usuário por username ou email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Usuário ou senha inválidos'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Conta desativada. Contate o administrador.'
            }), 403
        
        # Atualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Gerar token
        token = generate_token(user)
        
        logger.info(f"Login bem-sucedido: {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'token': token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao realizar login'
        }), 500

@auth_bp.route('/auth/verify', methods=['GET'])
def verify():
    """Verifica se o token é válido"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return jsonify({
            'success': False,
            'message': 'Token não fornecido'
        }), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Token inválido ou expirado'
        }), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/auth/change-password', methods=['POST'])
def change_password():
    """
    Alterar senha do usuário
    
    Body:
    {
        "current_password": "123456",
        "new_password": "nova_senha"
    }
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return jsonify({ 'success': False, 'message': 'Token não fornecido' }), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload:
        return jsonify({ 'success': False, 'message': 'Token inválido' }), 401
    
    try:
        dados = request.json
        current_password = dados.get('current_password', '')
        new_password = dados.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({ 'success': False, 'message': 'Senhas são obrigatórias' }), 400
        
        if len(new_password) < 6:
            return jsonify({ 'success': False, 'message': 'A nova senha deve ter pelo menos 6 caracteres' }), 400
        
        user = User.query.get(payload['user_id'])
        
        if not user or not user.check_password(current_password):
            return jsonify({ 'success': False, 'message': 'Senha atual incorreta' }), 401
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({ 'success': True, 'message': 'Senha alterada com sucesso' }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': 'Erro ao alterar senha' }), 500

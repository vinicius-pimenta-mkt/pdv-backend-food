import os
import sys
import logging

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from models.user import db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CONFIGURAÇÃO DE CORS
# ============================================
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# ============================================
# CONFIGURAÇÃO DE SEGURANÇA
# ============================================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
app.config['JSON_SORT_KEYS'] = False

# ============================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================
database_url = os.getenv('DATABASE_URL')

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    logger.info(f"✓ Usando DATABASE_URL")
else:
    db_driver = os.getenv('DB_DRIVER', 'mysql+pymysql')
    db_username = os.getenv('DB_USERNAME', 'root')
    db_password = os.getenv('DB_PASSWORD', 'password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'pdv_lachapa')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"{db_driver}://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info(f"✓ Usando variáveis individuais de banco de dados")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

# Inicializar o Banco de Dados com o app
db.init_app(app)

# ============================================
# IMPORTAR E REGISTRAR ROTAS
# ============================================
try:
    from src.routes.user import user_bp
    from src.routes.pedido import pedido_bp
    from src.routes.impressora import impressora_bp
    from src.routes.webhook import webhook_bp
    from src.routes.reports import reports_bp
    from src.routes.auth import auth_bp  # NOVO: Rota de autenticação
    
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(pedido_bp, url_prefix='/api')
    app.register_blueprint(impressora_bp, url_prefix='/api/impressora')
    app.register_blueprint(webhook_bp, url_prefix='/api/webhook')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')  # NOVO
    
    logger.info("✓ Todas as rotas registradas com sucesso")
except ImportError as e:
    logger.error(f"✗ Erro ao importar rotas: {e}")
    raise

# ============================================
# CRIAR TABELAS E ADMIN PADRÃO
# ============================================
with app.app_context():
    try:
        db.create_all()
        logger.info("✓ Tabelas do banco de dados criadas/verificadas")
        
        # Criar admin padrão se não existir
        from src.models.user import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@lachapa.com',
                role='admin'
            )
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
            logger.info("✓ Usuário admin padrão criado (admin / 123456)")
        
    except Exception as e:
        logger.error(f"✗ Erro ao criar tabelas: {e}")
        raise

# ============================================
# ROTAS DE SAÚDE E INFORMAÇÕES
# ============================================

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "API do PDV LaChapa rodando perfeitamente!",
        "version": "1.1.0",
        "environment": os.getenv('ENVIRONMENT', 'production')
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health():
    try:
        db.session.execute('SELECT 1')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        "status": "online",
        "database": db_status,
        "message": "API do PDV LaChapa está operacional"
    }), 200

@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        "name": "PDV LaChapa API",
        "version": "1.1.0",
        "description": "API para gerenciamento de pedidos e relatórios do PDV LaChapa",
        "endpoints": {
            "auth": "/api/auth/login",
            "pedidos": "/api/pedidos",
            "reports": "/api/reports",
            "impressora": "/api/impressora",
            "webhook": "/api/webhook",
            "usuarios": "/api/users"
        }
    }), 200

# ============================================
# TRATAMENTO DE ERROS GLOBAL
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({ "success": False, "error": "Rota não encontrada" }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({ "success": False, "error": "Erro interno do servidor" }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({ "success": False, "error": "Requisição inválida", "message": str(error) }), 400

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    environment = os.getenv('ENVIRONMENT', 'production')
    
    logger.info(f"🚀 Iniciando API PDV LaChapa v1.1.0")
    logger.info(f"📍 Ambiente: {environment}")
    logger.info(f"🔧 Debug: {debug}")
    logger.info(f"🌐 Servidor: {host}:{port}")
    
    if environment == 'production':
        logger.warning("⚠️  Em produção, use: gunicorn -w 4 -b 0.0.0.0:5000 src.main:app")
    
    app.run(host=host, port=port, debug=debug, use_reloader=debug)

import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS  # Importante para o frontend externo
from models.user import db

app = Flask(__name__)

# Habilita o CORS para todas as rotas da API
CORS(app)

app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# 1. Configurar o Banco de Dados PRIMEIRO
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Inicializar o Banco de Dados com o app
db.init_app(app)

# 3. Importar e registrar rotas DEPOIS do init_app
# Isso resolve o RuntimeError do SQLAlchemy
from src.routes.user import user_bp
from src.routes.pedido import pedido_bp
from src.routes.impressora import impressora_bp
from src.routes.webhook import webhook_bp

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(pedido_bp, url_prefix='/api')
app.register_blueprint(impressora_bp, url_prefix='/api/impressora')
app.register_blueprint(webhook_bp, url_prefix='/api/webhook')

# 4. Criar as tabelas no banco
with app.app_context():
    db.create_all()

# 5. Rota de teste (Health Check) em vez de servir HTML
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "API do PDV LaChapa rodando perfeitamente!"
    }), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

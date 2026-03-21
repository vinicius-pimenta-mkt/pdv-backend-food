from flask import Blueprint

pedido_bp = Blueprint('pedido', __name__)

from src.routes.pedido import routes

from flask import jsonify, request, current_app
from src.models.pedido.pedido import Pedido, ItemPedido
from src.models.user import db
from src.routes.pedido import pedido_bp
import datetime
import random
import string

# Gerar número de pedido único
def gerar_numero_pedido():
    agora = datetime.datetime.now()
    prefixo = agora.strftime("%Y%m%d")
    sufixo = ''.join(random.choices(string.digits, k=4))
    return f"{prefixo}-{sufixo}"

# Listar todos os pedidos
@pedido_bp.route('/pedidos', methods=['GET'])
def listar_pedidos():
    status = request.args.get('status', None)
    
    query = Pedido.query
    if status:
        query = query.filter_by(status=status)
    
    pedidos = query.order_by(Pedido.data_criacao.desc()).all()
    return jsonify([pedido.to_dict() for pedido in pedidos]), 200

# Obter pedido por ID
@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['GET'])
def obter_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return jsonify(pedido.to_dict()), 200

# Criar novo pedido
@pedido_bp.route('/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.json
    
    novo_pedido = Pedido(
        numero=gerar_numero_pedido(),
        cliente_nome=dados.get('cliente_nome'),
        cliente_telefone=dados.get('cliente_telefone'),
        endereco_entrega=dados.get('endereco_entrega'),
        valor_total=dados.get('valor_total', 0.0),
        metodo_pagamento=dados.get('metodo_pagamento'),
        status=dados.get('status', 'em_analise'),
        origem=dados.get('origem', 'app'),
        observacoes=dados.get('observacoes')
    )
    
    # Adicionar itens ao pedido
    itens = dados.get('itens', [])
    for item_dados in itens:
        item = ItemPedido(
            produto_nome=item_dados.get('produto_nome'),
            quantidade=item_dados.get('quantidade', 1),
            valor_unitario=item_dados.get('valor_unitario'),
            observacoes=item_dados.get('observacoes')
        )
        novo_pedido.itens.append(item)
    
    db.session.add(novo_pedido)
    db.session.commit()
    
    return jsonify(novo_pedido.to_dict()), 201

# Atualizar status do pedido
@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
def atualizar_status_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    dados = request.json
    
    if 'status' not in dados:
        return jsonify({'erro': 'Status não fornecido'}), 400
    
    status = dados['status']
    if status not in ['em_analise', 'em_producao', 'em_entrega']:
        return jsonify({'erro': 'Status inválido'}), 400
    
    pedido.status = status
    db.session.commit()
    
    return jsonify(pedido.to_dict()), 200

# Excluir pedido
@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
def excluir_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    db.session.delete(pedido)
    db.session.commit()
    
    return jsonify({'mensagem': 'Pedido excluído com sucesso'}), 200

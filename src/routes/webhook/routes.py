from flask import jsonify, request
from src.models.pedido.pedido import Pedido, ItemPedido
from src.models.user import db
from src.routes.webhook import webhook_bp
import datetime
import random
import string

# Gerar número de pedido único
def gerar_numero_pedido():
    agora = datetime.datetime.now()
    prefixo = agora.strftime("%Y%m%d")
    sufixo = ''.join(random.choices(string.digits, k=4))
    return f"{prefixo}-{sufixo}"

# Webhook para receber pedidos do n8n
@webhook_bp.route('/pedido-whatsapp', methods=['POST'])
def webhook_pedido_whatsapp():
    """
    Recebe pedidos enviados pelo fluxo do n8n via WhatsApp
    
    Estrutura esperada do payload:
    {
        "cliente_nome": "João Silva",
        "cliente_telefone": "(11) 99999-9999",
        "endereco_entrega": "Av. Paulista, 1000",
        "valor_total": 35.90,
        "metodo_pagamento": "pix",
        "itens": [
            {
                "produto_nome": "X-Tudo",
                "quantidade": 1,
                "valor_unitario": 25.90,
                "observacoes": "Sem cebola"
            }
        ],
        "observacoes": "Entregar com guardanapos extras"
    }
    """
    try:
        dados = request.json
        
        # Validar dados obrigatórios
        if not dados.get('cliente_nome') or not dados.get('cliente_telefone'):
            return jsonify({'erro': 'Cliente e telefone são obrigatórios'}), 400
        
        if not dados.get('itens') or len(dados.get('itens', [])) == 0:
            return jsonify({'erro': 'Pedido deve ter pelo menos um item'}), 400
        
        # Criar novo pedido
        novo_pedido = Pedido(
            numero=gerar_numero_pedido(),
            cliente_nome=dados.get('cliente_nome'),
            cliente_telefone=dados.get('cliente_telefone'),
            endereco_entrega=dados.get('endereco_entrega', ''),
            valor_total=dados.get('valor_total', 0.0),
            metodo_pagamento=dados.get('metodo_pagamento', 'pix'),
            status='em_analise',  # Sempre começa em análise
            origem='whatsapp',  # Marca origem como WhatsApp
            observacoes=dados.get('observacoes', '')
        )
        
        # Adicionar itens ao pedido
        itens = dados.get('itens', [])
        for item_dados in itens:
            item = ItemPedido(
                produto_nome=item_dados.get('produto_nome'),
                quantidade=item_dados.get('quantidade', 1),
                valor_unitario=item_dados.get('valor_unitario', 0.0),
                observacoes=item_dados.get('observacoes', '')
            )
            novo_pedido.itens.append(item)
        
        # Salvar no banco de dados
        db.session.add(novo_pedido)
        db.session.commit()
        
        # Retornar pedido criado
        return jsonify({
            'success': True,
            'message': 'Pedido recebido com sucesso',
            'pedido': novo_pedido.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'erro': f'Erro ao processar pedido: {str(e)}'
        }), 500

# Webhook para atualizar status de pedido
@webhook_bp.route('/pedido-status', methods=['PUT'])
def webhook_atualizar_status():
    """
    Atualiza o status de um pedido
    
    Estrutura esperada:
    {
        "numero_pedido": "20250208-1234",
        "status": "em_producao"
    }
    """
    try:
        dados = request.json
        numero_pedido = dados.get('numero_pedido')
        novo_status = dados.get('status')
        
        if not numero_pedido or not novo_status:
            return jsonify({'erro': 'Número do pedido e status são obrigatórios'}), 400
        
        # Buscar pedido pelo número
        pedido = Pedido.query.filter_by(numero=numero_pedido).first()
        if not pedido:
            return jsonify({'erro': 'Pedido não encontrado'}), 404
        
        # Validar status
        status_validos = ['em_analise', 'em_producao', 'em_entrega']
        if novo_status not in status_validos:
            return jsonify({'erro': f'Status inválido. Valores aceitos: {status_validos}'}), 400
        
        # Atualizar status
        pedido.status = novo_status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Pedido {numero_pedido} atualizado para {novo_status}',
            'pedido': pedido.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'erro': f'Erro ao atualizar pedido: {str(e)}'
        }), 500

# Health check do webhook
@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """Verifica se o webhook está funcionando"""
    return jsonify({
        'status': 'ok',
        'message': 'Webhook do PDV LaChapa está operacional'
    }), 200

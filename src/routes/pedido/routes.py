from flask import jsonify, request, current_app
from src.models.pedido.pedido import Pedido, ItemPedido
from src.models.user import db
from src.routes.pedido import pedido_bp
import datetime
import random
import string
import logging

logger = logging.getLogger(__name__)

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def gerar_numero_pedido():
    """Gera número de pedido único com formato YYYYMMDD-XXXX"""
    agora = datetime.datetime.now()
    prefixo = agora.strftime("%Y%m%d")
    sufixo = ''.join(random.choices(string.digits, k=4))
    return f"{prefixo}-{sufixo}"

# ============================================
# ENDPOINTS DE PEDIDOS
# ============================================

@pedido_bp.route('/pedidos', methods=['GET'])
def listar_pedidos():
    """
    Lista todos os pedidos com filtros opcionais
    
    Parâmetros query:
    - status: Filtrar por status (em_analise, em_producao, em_entrega)
    - limit: Número máximo de pedidos a retornar (padrão: 100)
    - offset: Número de pedidos a pular (padrão: 0)
    - order_by: Campo para ordenação (data_criacao, valor_total)
    
    Exemplo:
    GET /api/pedidos?status=em_analise&limit=10
    """
    try:
        # Obter parâmetros
        status = request.args.get('status', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        order_by = request.args.get('order_by', 'data_criacao')
        
        # Construir query
        query = Pedido.query
        
        # Filtrar por status se fornecido
        if status:
            status_validos = ['em_analise', 'em_producao', 'em_entrega']
            if status not in status_validos:
                return jsonify({
                    'success': False,
                    'message': f'Status inválido. Valores aceitos: {status_validos}'
                }), 400
            query = query.filter_by(status=status)
        
        # Ordenar
        if order_by == 'valor_total':
            query = query.order_by(Pedido.valor_total.desc())
        else:
            query = query.order_by(Pedido.data_criacao.desc())
        
        # Aplicar paginação
        total = query.count()
        pedidos = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [pedido.to_dict() for pedido in pedidos],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'returned': len(pedidos)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao listar pedidos: {str(e)}'
        }), 500

@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['GET'])
def obter_pedido(pedido_id):
    """
    Obtém um pedido específico por ID
    
    Exemplo:
    GET /api/pedidos/123
    """
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        return jsonify({
            'success': True,
            'data': pedido.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao obter pedido {pedido_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao obter pedido: {str(e)}'
        }), 500

@pedido_bp.route('/pedidos', methods=['POST'])
def criar_pedido():
    """
    Cria um novo pedido
    
    Body esperado:
    {
        "cliente_nome": "João Silva",
        "cliente_telefone": "(82) 98214-1000",
        "endereco_entrega": "Av. Paulista, 1000",
        "valor_total": 35.90,
        "metodo_pagamento": "pix",
        "origem": "app",
        "observacoes": "Sem cebola",
        "itens": [
            {
                "produto_nome": "X-Tudo",
                "quantidade": 1,
                "valor_unitario": 35.90,
                "observacoes": "Sem cebola"
            }
        ]
    }
    """
    try:
        dados = request.json
        
        # Validar dados obrigatórios
        if not dados.get('cliente_nome') or not dados.get('cliente_telefone'):
            return jsonify({
                'success': False,
                'message': 'Cliente e telefone são obrigatórios'
            }), 400
        
        if not dados.get('itens') or len(dados.get('itens', [])) == 0:
            return jsonify({
                'success': False,
                'message': 'Pedido deve ter pelo menos um item'
            }), 400
        
        # Criar novo pedido
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
        
        # Salvar no banco
        db.session.add(novo_pedido)
        db.session.commit()
        
        logger.info(f"Pedido criado: {novo_pedido.numero}")
        
        return jsonify({
            'success': True,
            'message': 'Pedido criado com sucesso',
            'data': novo_pedido.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar pedido: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao criar pedido: {str(e)}'
        }), 500

@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
def atualizar_status_pedido(pedido_id):
    """
    Atualiza o status de um pedido
    
    Body esperado:
    {
        "status": "em_producao"
    }
    
    Status válidos: em_analise, em_producao, em_entrega
    """
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        dados = request.json
        
        if 'status' not in dados:
            return jsonify({
                'success': False,
                'message': 'Status não fornecido'
            }), 400
        
        status = dados['status']
        status_validos = ['em_analise', 'em_producao', 'em_entrega']
        
        if status not in status_validos:
            return jsonify({
                'success': False,
                'message': f'Status inválido. Valores aceitos: {status_validos}'
            }), 400
        
        pedido.status = status
        db.session.commit()
        
        logger.info(f"Pedido {pedido.numero} atualizado para {status}")
        
        return jsonify({
            'success': True,
            'message': f'Pedido atualizado para {status}',
            'data': pedido.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar status: {str(e)}'
        }), 500

@pedido_bp.route('/pedidos/<int:pedido_id>', methods=['DELETE'])
def excluir_pedido(pedido_id):
    """
    Exclui um pedido
    
    Exemplo:
    DELETE /api/pedidos/123
    """
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        numero_pedido = pedido.numero
        
        db.session.delete(pedido)
        db.session.commit()
        
        logger.info(f"Pedido {numero_pedido} excluído")
        
        return jsonify({
            'success': True,
            'message': 'Pedido excluído com sucesso'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir pedido {pedido_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir pedido: {str(e)}'
        }), 500

@pedido_bp.route('/pedidos/numero/<numero>', methods=['GET'])
def obter_pedido_por_numero(numero):
    """
    Obtém um pedido pelo número
    
    Exemplo:
    GET /api/pedidos/numero/20250322-1234
    """
    try:
        pedido = Pedido.query.filter_by(numero=numero).first_or_404()
        return jsonify({
            'success': True,
            'data': pedido.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao obter pedido por número {numero}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Pedido não encontrado'
        }), 404

@pedido_bp.route('/pedidos/buscar', methods=['GET'])
def buscar_pedidos():
    """
    Busca pedidos por cliente, telefone ou número
    
    Parâmetros query:
    - q: Termo de busca (cliente, telefone ou número)
    - limit: Número máximo de resultados (padrão: 20)
    
    Exemplo:
    GET /api/pedidos/buscar?q=João&limit=10
    """
    try:
        termo = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not termo:
            return jsonify({
                'success': False,
                'message': 'Termo de busca não fornecido'
            }), 400
        
        # Buscar em cliente, telefone ou número
        pedidos = Pedido.query.filter(
            (Pedido.cliente_nome.ilike(f'%{termo}%')) |
            (Pedido.cliente_telefone.ilike(f'%{termo}%')) |
            (Pedido.numero.ilike(f'%{termo}%'))
        ).order_by(Pedido.data_criacao.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [pedido.to_dict() for pedido in pedidos],
            'total': len(pedidos)
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao buscar pedidos: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar pedidos: {str(e)}'
        }), 500

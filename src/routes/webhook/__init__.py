from flask import Blueprint, jsonify, request
from src.models.pedido.pedido import Pedido, ItemPedido
from src.models.user import db
import json
import requests
from datetime import datetime

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/cardapio', methods=['POST'])
def receber_pedido_cardapio():
    """
    Endpoint para receber pedidos do cardápio digital
    
    Este endpoint recebe os pedidos feitos pelos clientes no cardápio digital
    e os insere no sistema PDV, colocando-os na coluna "Em análise"
    """
    try:
        dados = request.json
        
        # Validar dados mínimos necessários
        if not dados.get('itens') or not isinstance(dados.get('itens'), list):
            return jsonify({'erro': 'Pedido inválido: itens não fornecidos ou formato incorreto'}), 400
            
        # Gerar número de pedido
        from src.routes.pedido.routes import gerar_numero_pedido
        numero_pedido = gerar_numero_pedido()
        
        # Criar novo pedido
        novo_pedido = Pedido(
            numero=numero_pedido,
            cliente_nome=dados.get('cliente_nome'),
            cliente_telefone=dados.get('cliente_telefone'),
            endereco_entrega=dados.get('endereco_entrega'),
            valor_total=dados.get('valor_total', 0.0),
            metodo_pagamento=dados.get('metodo_pagamento'),
            status='em_analise',  # Pedidos do cardápio sempre começam em análise
            origem='app',
            observacoes=dados.get('observacoes')
        )
        
        # Adicionar itens ao pedido
        for item_dados in dados.get('itens', []):
            item = ItemPedido(
                produto_nome=item_dados.get('nome', item_dados.get('produto_nome')),
                quantidade=item_dados.get('quantidade', 1),
                valor_unitario=item_dados.get('preco', item_dados.get('valor_unitario', 0)),
                observacoes=item_dados.get('observacoes')
            )
            novo_pedido.itens.append(item)
        
        # Calcular valor total se não fornecido
        if not dados.get('valor_total'):
            valor_total = sum(item.quantidade * item.valor_unitario for item in novo_pedido.itens)
            novo_pedido.valor_total = valor_total
        
        # Salvar no banco de dados
        db.session.add(novo_pedido)
        db.session.commit()
        
        # Enviar notificação para WhatsApp (manter compatibilidade com fluxo atual)
        try:
            enviar_notificacao_whatsapp(novo_pedido)
        except Exception as e:
            # Não falhar se a notificação WhatsApp falhar
            print(f"Erro ao enviar notificação WhatsApp: {str(e)}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Pedido recebido com sucesso',
            'pedido_id': novo_pedido.id,
            'numero_pedido': novo_pedido.numero
        }), 201
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar pedido: {str(e)}'}), 500

@webhook_bp.route('/whatsapp', methods=['POST'])
def receber_pedido_whatsapp():
    """
    Endpoint para receber pedidos do fluxo do WhatsApp (n8n)
    
    Este endpoint recebe os pedidos processados pelo fluxo n8n do WhatsApp
    e os insere no sistema PDV, colocando-os na coluna "Em análise"
    """
    try:
        dados = request.json
        
        # Validar dados mínimos necessários
        if not dados.get('pedido'):
            return jsonify({'erro': 'Pedido inválido: dados do pedido não fornecidos'}), 400
            
        pedido_dados = dados.get('pedido')
        
        # Gerar número de pedido
        from src.routes.pedido.routes import gerar_numero_pedido
        numero_pedido = gerar_numero_pedido()
        
        # Criar novo pedido
        novo_pedido = Pedido(
            numero=numero_pedido,
            cliente_nome=pedido_dados.get('cliente_nome'),
            cliente_telefone=pedido_dados.get('cliente_telefone'),
            endereco_entrega=pedido_dados.get('endereco_entrega'),
            valor_total=pedido_dados.get('valor_total', 0.0),
            metodo_pagamento=pedido_dados.get('metodo_pagamento'),
            status='em_analise',  # Pedidos do WhatsApp sempre começam em análise
            origem='whatsapp',
            observacoes=pedido_dados.get('observacoes')
        )
        
        # Adicionar itens ao pedido
        for item_dados in pedido_dados.get('itens', []):
            item = ItemPedido(
                produto_nome=item_dados.get('nome', item_dados.get('produto_nome')),
                quantidade=item_dados.get('quantidade', 1),
                valor_unitario=item_dados.get('preco', item_dados.get('valor_unitario', 0)),
                observacoes=item_dados.get('observacoes')
            )
            novo_pedido.itens.append(item)
        
        # Calcular valor total se não fornecido
        if not pedido_dados.get('valor_total'):
            valor_total = sum(item.quantidade * item.valor_unitario for item in novo_pedido.itens)
            novo_pedido.valor_total = valor_total
        
        # Salvar no banco de dados
        db.session.add(novo_pedido)
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Pedido do WhatsApp recebido com sucesso',
            'pedido_id': novo_pedido.id,
            'numero_pedido': novo_pedido.numero
        }), 201
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar pedido do WhatsApp: {str(e)}'}), 500

@webhook_bp.route('/notificar-status/<int:pedido_id>', methods=['POST'])
def notificar_status_pedido(pedido_id):
    """
    Endpoint para notificar cliente sobre mudança de status do pedido
    
    Este endpoint envia uma notificação para o cliente quando o status
    do pedido é alterado (ex: aprovado, em produção, em entrega)
    """
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        dados = request.json
        
        # Verificar se há um novo status
        novo_status = dados.get('status')
        if novo_status and novo_status != pedido.status:
            pedido.status = novo_status
            db.session.commit()
        
        # Enviar notificação para o cliente via WhatsApp
        resultado = enviar_notificacao_status_whatsapp(pedido)
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Notificação de status enviada com sucesso',
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao notificar status: {str(e)}'}), 500

def enviar_notificacao_whatsapp(pedido):
    """
    Função para enviar notificação de novo pedido para o WhatsApp da lanchonete
    
    Esta função mantém a compatibilidade com o fluxo atual do n8n
    """
    # Em um ambiente real, aqui seria feita a chamada para o webhook do n8n
    # Para fins de demonstração, apenas simulamos o envio
    
    # Formatar mensagem
    itens_texto = "\n".join([
        f"- {item.quantidade}x {item.produto_nome}: R$ {item.quantidade * item.valor_unitario:.2f}"
        for item in pedido.itens
    ])
    
    mensagem = f"""
*NOVO PEDIDO #{pedido.numero}*

*Cliente:* {pedido.cliente_nome or 'Não informado'}
*Telefone:* {pedido.cliente_telefone or 'Não informado'}
*Endereço:* {pedido.endereco_entrega or 'Não informado'}

*ITENS:*
{itens_texto}

*TOTAL: R$ {pedido.valor_total:.2f}*
*Pagamento:* {pedido.metodo_pagamento or 'Não informado'}

*Observações:* {pedido.observacoes or 'Nenhuma'}
    """
    
    # Simular envio para webhook do n8n
    # Em produção, seria algo como:
    # requests.post('https://n8n.seudominio.com/webhook/pedido', json={'mensagem': mensagem})
    
    print(f"[SIMULAÇÃO] Notificação WhatsApp enviada: {mensagem}")
    
    return {
        'enviado': True,
        'mensagem': 'Notificação simulada com sucesso'
    }

def enviar_notificacao_status_whatsapp(pedido):
    """
    Função para enviar notificação de atualização de status para o cliente via WhatsApp
    """
    # Em um ambiente real, aqui seria feita a chamada para o webhook do n8n
    # Para fins de demonstração, apenas simulamos o envio
    
    status_texto = {
        'em_analise': 'em análise',
        'em_producao': 'em produção',
        'em_entrega': 'saiu para entrega'
    }.get(pedido.status, pedido.status)
    
    # Corrigido: Extraímos a lógica de mensagem extra para fora da f-string
    mensagens_extras = {
        'em_producao': 'Estamos preparando seu pedido com todo carinho!',
        'em_entrega': 'Seu pedido já está a caminho! Logo chegará até você.',
        'em_analise': 'Estamos analisando seu pedido e logo iniciaremos a preparação.'
    }
    mensagem_extra = mensagens_extras.get(pedido.status, '')
    
    mensagem = f"""
*Atualização do Pedido #{pedido.numero}*

Olá {pedido.cliente_nome or 'Cliente'},

Seu pedido está agora *{status_texto}*.

{mensagem_extra}

Agradecemos a preferência!
La Chapa Lanches
    """
    
    # Simular envio para webhook do n8n
    # Em produção, seria algo como:
    # requests.post('https://n8n.seudominio.com/webhook/status', json={'mensagem': mensagem, 'telefone': pedido.cliente_telefone})
    
    print(f"[SIMULAÇÃO] Notificação de status enviada: {mensagem}")
    
    return {
        'enviado': True,
        'mensagem': 'Notificação de status simulada com sucesso'
    }

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.pedido.pedido import Pedido, ItemPedido
import logging

logger = logging.getLogger(__name__)

from src.routes.reports import reports_bp

# ============================================
# RELATÓRIO DE VENDAS
# ============================================

@reports_bp.route('/reports/sales', methods=['GET'])
def get_sales_report():
    """
    Endpoint para relatório de vendas agregado por período
    
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD) - obrigatório
    - end_date: Data final (formato YYYY-MM-DD) - obrigatório
    - group_by: Agrupamento (day, week, month) - opcional, padrão: day
    
    Exemplo:
    GET /api/reports/sales?start_date=2025-10-01&end_date=2025-10-31&group_by=day
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        pedidos = Pedido.query.filter(
            Pedido.data_criacao >= start_date_obj,
            Pedido.data_criacao <= end_date_obj
        ).all()
        
        total_revenue = sum(pedido.valor_total for pedido in pedidos)
        total_orders = len(pedidos)
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        period_data = []
        
        if group_by == 'day':
            current_date = start_date_obj.date()
            while current_date <= end_date_obj.date():
                daily_orders = [p for p in pedidos if p.data_criacao.date() == current_date]
                daily_revenue = sum(p.valor_total for p in daily_orders)
                
                period_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'revenue': round(daily_revenue, 2),
                    'orders': len(daily_orders)
                })
                
                current_date += timedelta(days=1)
        
        elif group_by == 'week':
            current_date = start_date_obj.date()
            while current_date <= end_date_obj.date():
                week_end = current_date + timedelta(days=6)
                if week_end > end_date_obj.date():
                    week_end = end_date_obj.date()
                
                weekly_orders = [p for p in pedidos if current_date <= p.data_criacao.date() <= week_end]
                weekly_revenue = sum(p.valor_total for p in weekly_orders)
                
                period_data.append({
                    'week': f"{current_date.strftime('%Y-%m-%d')} a {week_end.strftime('%Y-%m-%d')}",
                    'revenue': round(weekly_revenue, 2),
                    'orders': len(weekly_orders)
                })
                
                current_date = week_end + timedelta(days=1)
        
        elif group_by == 'month':
            current_date = start_date_obj.date()
            while current_date <= end_date_obj.date():
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                
                month_end = min(next_month - timedelta(days=1), end_date_obj.date())
                
                monthly_orders = [p for p in pedidos if current_date <= p.data_criacao.date() <= month_end]
                monthly_revenue = sum(p.valor_total for p in monthly_orders)
                
                period_data.append({
                    'month': current_date.strftime('%Y-%m'),
                    'revenue': round(monthly_revenue, 2),
                    'orders': len(monthly_orders)
                })
                
                current_date = month_end + timedelta(days=1)
        
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'group_by': group_by
                },
                'total_revenue': round(total_revenue, 2),
                'total_orders': total_orders,
                'average_ticket': round(average_ticket, 2),
                'sales': period_data
            }
        }
        
        logger.info(f"Relatório de vendas gerado: {start_date} a {end_date}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de vendas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar relatório de vendas: {str(e)}'
        }), 500

# ============================================
# RELATÓRIO DE PRODUTOS
# ============================================

@reports_bp.route('/reports/products', methods=['GET'])
def get_products_report():
    """
    Endpoint para relatório de vendas por produto
    
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD) - obrigatório
    - end_date: Data final (formato YYYY-MM-DD) - obrigatório
    - limit: Número máximo de produtos a retornar (opcional, padrão: 20)
    - sort_by: Campo para ordenação (quantity, revenue) - opcional, padrão: revenue
    - order: Direção da ordenação (asc, desc) - opcional, padrão: desc
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 20, type=int)
        sort_by = request.args.get('sort_by', 'revenue')
        order = request.args.get('order', 'desc')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        itens = ItemPedido.query.join(Pedido).filter(
            Pedido.data_criacao >= start_date_obj,
            Pedido.data_criacao <= end_date_obj
        ).all()
        
        products_dict = {}
        for item in itens:
            produto_nome = item.produto_nome
            if produto_nome not in products_dict:
                products_dict[produto_nome] = {
                    'name': produto_nome,
                    'quantity': 0,
                    'revenue': 0.0
                }
            
            products_dict[produto_nome]['quantity'] += item.quantidade
            products_dict[produto_nome]['revenue'] += item.quantidade * item.valor_unitario
        
        products_data = list(products_dict.values())
        
        total_revenue = sum(p['revenue'] for p in products_data)
        
        for product in products_data:
            product['percentage'] = round((product['revenue'] / total_revenue * 100) if total_revenue > 0 else 0, 2)
            product['revenue'] = round(product['revenue'], 2)
        
        if sort_by == 'quantity':
            products_data.sort(key=lambda x: x['quantity'], reverse=(order == 'desc'))
        else:
            products_data.sort(key=lambda x: x['revenue'], reverse=(order == 'desc'))
        
        if limit > 0:
            products_data = products_data[:limit]
        
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_revenue': round(total_revenue, 2),
                'products': products_data
            }
        }
        
        logger.info(f"Relatório de produtos gerado: {start_date} a {end_date}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de produtos: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar relatório de produtos: {str(e)}'
        }), 500

# ============================================
# RELATÓRIO DO DASHBOARD
# ============================================

@reports_bp.route('/reports/dashboard', methods=['GET'])
def get_dashboard_report():
    """
    Endpoint para dados do dashboard com resumo geral
    
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD) - obrigatório
    - end_date: Data final (formato YYYY-MM-DD) - obrigatório
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        pedidos = Pedido.query.filter(
            Pedido.data_criacao >= start_date_obj,
            Pedido.data_criacao <= end_date_obj
        ).all()
        
        total_revenue = sum(pedido.valor_total for pedido in pedidos)
        total_orders = len(pedidos)
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        itens = ItemPedido.query.join(Pedido).filter(
            Pedido.data_criacao >= start_date_obj,
            Pedido.data_criacao <= end_date_obj
        ).all()
        
        products_dict = {}
        for item in itens:
            produto_nome = item.produto_nome
            if produto_nome not in products_dict:
                products_dict[produto_nome] = {
                    'name': produto_nome,
                    'quantity': 0,
                    'revenue': 0.0
                }
            
            products_dict[produto_nome]['quantity'] += item.quantidade
            products_dict[produto_nome]['revenue'] += item.quantidade * item.valor_unitario
        
        top_products = sorted(
            list(products_dict.values()),
            key=lambda x: x['revenue'],
            reverse=True
        )[:5]
        
        for product in top_products:
            product['revenue'] = round(product['revenue'], 2)
        
        period_delta = end_date_obj - start_date_obj
        previous_start = start_date_obj - period_delta - timedelta(days=1)
        previous_end = start_date_obj - timedelta(days=1)
        
        previous_pedidos = Pedido.query.filter(
            Pedido.data_criacao >= previous_start,
            Pedido.data_criacao <= previous_end
        ).all()
        
        previous_revenue = sum(pedido.valor_total for pedido in previous_pedidos)
        
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        payment_methods = {}
        for pedido in pedidos:
            metodo = pedido.metodo_pagamento or 'Não especificado'
            if metodo not in payment_methods:
                payment_methods[metodo] = {
                    'method': metodo,
                    'total': 0.0,
                    'orders': 0
                }
            
            payment_methods[metodo]['total'] += pedido.valor_total
            payment_methods[metodo]['orders'] += 1
        
        payment_methods_list = list(payment_methods.values())
        for method in payment_methods_list:
            method['total'] = round(method['total'], 2)
        
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_revenue': round(total_revenue, 2),
                    'total_orders': total_orders,
                    'average_ticket': round(average_ticket, 2),
                    'revenue_change_percent': round(revenue_change, 2)
                },
                'top_products': top_products,
                'payment_methods': payment_methods_list
            }
        }
        
        logger.info(f"Dashboard gerado: {start_date} a {end_date}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Erro ao gerar dados do dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar dados do dashboard: {str(e)}'
        }), 500

# ============================================
# RELATÓRIO DE MÉTODOS DE PAGAMENTO
# ============================================

@reports_bp.route('/reports/payment-methods', methods=['GET'])
def get_payment_methods_report():
    """
    Endpoint para relatório de métodos de pagamento
    
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD) - obrigatório
    - end_date: Data final (formato YYYY-MM-DD) - obrigatório
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        pedidos = Pedido.query.filter(
            Pedido.data_criacao >= start_date_obj,
            Pedido.data_criacao <= end_date_obj
        ).all()
        
        payment_methods = {}
        for pedido in pedidos:
            metodo = pedido.metodo_pagamento or 'Não especificado'
            if metodo not in payment_methods:
                payment_methods[metodo] = {
                    'method': metodo,
                    'total': 0.0,
                    'orders': 0
                }
            
            payment_methods[metodo]['total'] += pedido.valor_total
            payment_methods[metodo]['orders'] += 1
        
        payment_methods_list = list(payment_methods.values())
        
        total_revenue = sum(p['total'] for p in payment_methods_list)
        
        for method in payment_methods_list:
            method['total'] = round(method['total'], 2)
            method['percentage'] = round((method['total'] / total_revenue * 100) if total_revenue > 0 else 0, 2)
        
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_revenue': round(total_revenue, 2),
                'payment_methods': payment_methods_list
            }
        }
        
        logger.info(f"Relatório de métodos de pagamento gerado: {start_date} a {end_date}")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de métodos de pagamento: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar relatório de métodos de pagamento: {str(e)}'
        }), 500

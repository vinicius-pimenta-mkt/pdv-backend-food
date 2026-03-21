from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from ...models.pedido.pedido import Pedido, PedidoItem
from ...models.produto.produto import Produto

reports = Blueprint('reports', __name__)

@reports.route('/api/reports/sales', methods=['GET'])
def get_sales_report():
    """
    Endpoint para relatório de vendas agregado por período
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD)
    - end_date: Data final (formato YYYY-MM-DD)
    - group_by: Agrupamento (day, week, month) - opcional
    """
    try:
        # Obter parâmetros
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')
        
        # Validar parâmetros
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        # Converter datas
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajustar end_date para incluir o dia inteiro
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        # Validar período
        if start_date > end_date:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        # Buscar dados de vendas
        pedidos = Pedido.get_by_date_range(start_date, end_date)
        
        # Calcular métricas
        total_revenue = sum(pedido.total for pedido in pedidos)
        total_orders = len(pedidos)
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        # Agrupar dados por período
        period_data = []
        
        if group_by == 'day':
            # Agrupar por dia
            current_date = start_date.date()
            while current_date <= end_date.date():
                daily_orders = [p for p in pedidos if p.data.date() == current_date]
                daily_revenue = sum(p.total for p in daily_orders)
                
                period_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'revenue': round(daily_revenue, 2),
                    'orders': len(daily_orders)
                })
                
                current_date += timedelta(days=1)
        
        elif group_by == 'week':
            # Implementação para agrupamento semanal
            # Código para agrupamento semanal seria implementado aqui
            pass
        
        elif group_by == 'month':
            # Implementação para agrupamento mensal
            # Código para agrupamento mensal seria implementado aqui
            pass
        
        # Montar resposta
        response = {
            'success': True,
            'data': {
                'total_revenue': round(total_revenue, 2),
                'total_orders': total_orders,
                'average_ticket': round(average_ticket, 2),
                'period_data': period_data
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar relatório de vendas: {str(e)}'
        }), 500

@reports.route('/api/reports/products', methods=['GET'])
def get_products_report():
    """
    Endpoint para relatório de vendas por produto
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD)
    - end_date: Data final (formato YYYY-MM-DD)
    - limit: Número máximo de produtos a retornar (opcional)
    - sort_by: Campo para ordenação (quantity, revenue) - opcional
    - order: Direção da ordenação (asc, desc) - opcional
    """
    try:
        # Obter parâmetros
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 20, type=int)
        sort_by = request.args.get('sort_by', 'revenue')
        order = request.args.get('order', 'desc')
        
        # Validar parâmetros
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
        # Converter datas
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajustar end_date para incluir o dia inteiro
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        # Validar período
        if start_date > end_date:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        # Buscar dados de vendas por produto
        product_sales = PedidoItem.get_sales_by_product(start_date, end_date)
        
        # Ordenar resultados
        if sort_by == 'quantity':
            product_sales.sort(key=lambda x: x['quantity'], reverse=(order == 'desc'))
        else:  # revenue é o padrão
            product_sales.sort(key=lambda x: x['revenue'], reverse=(order == 'desc'))
        
        # Limitar resultados
        if limit > 0:
            product_sales = product_sales[:limit]
        
        # Montar resposta
        response = {
            'success': True,
            'data': {
                'products': product_sales
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar relatório de produtos: {str(e)}'
        }), 500

@reports.route('/api/reports/dashboard', methods=['GET'])
def get_dashboard_report():
    """
    Endpoint para dados resumidos do dashboard
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD)
    - end_date: Data final (formato YYYY-MM-DD)
    """
    try:
        # Obter parâmetros
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Se não foram fornecidas datas, usar o dia atual
        if not start_date or not end_date:
            today = datetime.now().date()
            start_date = today.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        
        # Converter datas
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Ajustar end_date para incluir o dia inteiro
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Formato de data inválido. Use YYYY-MM-DD'
            }), 400
        
        # Validar período
        if start_date_obj > end_date_obj:
            return jsonify({
                'success': False,
                'message': 'A data inicial não pode ser posterior à data final'
            }), 400
        
        # Buscar dados de vendas
        pedidos = Pedido.get_by_date_range(start_date_obj, end_date_obj)
        
        # Calcular métricas
        total_revenue = sum(pedido.total for pedido in pedidos)
        total_orders = len(pedidos)
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        # Buscar produtos mais vendidos
        top_products = PedidoItem.get_top_products(start_date_obj, end_date_obj, limit=5)
        
        # Calcular comparação com período anterior
        previous_start = start_date_obj - (end_date_obj - start_date_obj) - timedelta(days=1)
        previous_end = start_date_obj - timedelta(days=1)
        previous_pedidos = Pedido.get_by_date_range(previous_start, previous_end)
        previous_revenue = sum(pedido.total for pedido in previous_pedidos)
        
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        # Montar resposta
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
                'top_products': top_products
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar dados do dashboard: {str(e)}'
        }), 500

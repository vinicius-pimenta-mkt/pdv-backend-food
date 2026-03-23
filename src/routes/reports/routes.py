from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.pedido.pedido import Pedido, ItemPedido
import logging

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

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
        
        # Buscar resumo de vendas
        sales_summary = Pedido.get_sales_summary_by_date_range(start_date_obj, end_date_obj)
        
        # Buscar dados agrupados por período
        if group_by == 'day':
            period_data = Pedido.get_daily_sales(start_date_obj, end_date_obj)
        else:
            # Para simplificar, usamos dados diários para todos os tipos de agrupamento
            period_data = Pedido.get_daily_sales(start_date_obj, end_date_obj)
        
        # Calcular média de ticket
        average_ticket = sales_summary['total_revenue'] / sales_summary['total_orders'] if sales_summary['total_orders'] > 0 else 0
        
        # Montar resposta
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'group_by': group_by
                },
                'total_revenue': round(sales_summary['total_revenue'], 2),
                'total_orders': sales_summary['total_orders'],
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
    
    Exemplo:
    GET /api/reports/products?start_date=2025-10-01&end_date=2025-10-31&sort_by=revenue&order=desc&limit=10
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
        
        # Buscar dados de vendas por produto
        products_data = ItemPedido.get_sales_by_product(start_date_obj, end_date_obj)
        
        # Buscar resumo de vendas para o período
        sales_summary = Pedido.get_sales_summary_by_date_range(start_date_obj, end_date_obj)
        total_revenue = sales_summary['total_revenue']
        
        # Adicionar porcentagem do total para cada produto
        for product in products_data:
            product['percentage'] = round((product['revenue'] / total_revenue * 100) if total_revenue > 0 else 0, 2)
        
        # Ordenar resultados
        if sort_by == 'quantity':
            products_data.sort(key=lambda x: x['quantity'], reverse=(order == 'desc'))
        else:  # revenue é o padrão
            products_data.sort(key=lambda x: x['revenue'], reverse=(order == 'desc'))
        
        # Limitar resultados
        if limit > 0:
            products_data = products_data[:limit]
        
        # Montar resposta
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
    Endpoint para dados resumidos do dashboard
    
    Parâmetros:
    - start_date: Data inicial (formato YYYY-MM-DD) - opcional
    - end_date: Data final (formato YYYY-MM-DD) - opcional
    
    Se não fornecidas, usa o dia atual.
    
    Exemplo:
    GET /api/reports/dashboard?start_date=2025-10-22&end_date=2025-10-22
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
        
        # Buscar resumo de vendas
        sales_summary = Pedido.get_sales_summary_by_date_range(start_date_obj, end_date_obj)
        total_revenue = sales_summary['total_revenue']
        total_orders = sales_summary['total_orders']
        
        # Calcular média de ticket
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        # Buscar produtos mais vendidos
        top_products = ItemPedido.get_top_products(start_date_obj, end_date_obj, limit=5)
        
        # Calcular comparação com período anterior
        period_delta = end_date_obj - start_date_obj
        previous_start = start_date_obj - period_delta - timedelta(days=1)
        previous_end = start_date_obj - timedelta(days=1)
        
        previous_summary = Pedido.get_sales_summary_by_date_range(previous_start, previous_end)
        previous_revenue = previous_summary['total_revenue']
        
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        # Buscar dados por método de pagamento
        payment_methods = Pedido.get_by_payment_method(start_date_obj, end_date_obj)
        
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
                'top_products': top_products,
                'payment_methods': payment_methods
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
    
    Exemplo:
    GET /api/reports/payment-methods?start_date=2025-10-01&end_date=2025-10-31
    """
    try:
        # Obter parâmetros
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Validar parâmetros
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': 'Os parâmetros start_date e end_date são obrigatórios'
            }), 400
        
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
        
        # Buscar dados por método de pagamento
        payment_methods = Pedido.get_by_payment_method(start_date_obj, end_date_obj)
        
        # Buscar total de vendas
        sales_summary = Pedido.get_sales_summary_by_date_range(start_date_obj, end_date_obj)
        total_revenue = sales_summary['total_revenue']
        
        # Adicionar porcentagem do total para cada método
        for method in payment_methods:
            method['percentage'] = round((method['total'] / total_revenue * 100) if total_revenue > 0 else 0, 2)
        
        # Montar resposta
        response = {
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_revenue': round(total_revenue, 2),
                'payment_methods': payment_methods
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

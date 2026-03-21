import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.models.pedido.pedido import Pedido, PedidoItem
from src.routes.reports import reports

class TestReportsAPI(unittest.TestCase):
    """Testes para a API de relatórios"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.app = reports.app.test_client()
        
    @patch('src.models.pedido.pedido.Pedido.get_by_date_range')
    def test_sales_report(self, mock_get_by_date_range):
        """Testa o endpoint de relatório de vendas"""
        # Mock de dados
        mock_pedidos = [
            MagicMock(id=1, data=datetime.now(), total=100.0, status="concluido"),
            MagicMock(id=2, data=datetime.now(), total=150.0, status="concluido"),
            MagicMock(id=3, data=datetime.now(), total=75.0, status="concluido")
        ]
        mock_get_by_date_range.return_value = mock_pedidos
        
        # Teste com datas válidas
        response = self.app.get('/api/reports/sales?start_date=2025-10-01&end_date=2025-10-30')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['sales']), 3)
        self.assertEqual(data['data']['total_revenue'], 325.0)
        
        # Teste sem datas (deve usar data atual)
        response = self.app.get('/api/reports/sales')
        self.assertEqual(response.status_code, 200)
        
        # Teste com datas inválidas
        response = self.app.get('/api/reports/sales?start_date=2025-13-01&end_date=2025-10-30')
        self.assertEqual(response.status_code, 400)
        
    @patch('src.models.pedido.pedido.PedidoItem.get_sales_by_product')
    def test_products_report(self, mock_get_sales_by_product):
        """Testa o endpoint de relatório de produtos"""
        # Mock de dados
        mock_products = [
            {'id': 1, 'name': 'Hambúrguer', 'quantity': 50, 'revenue': 500.0},
            {'id': 2, 'name': 'Batata Frita', 'quantity': 30, 'revenue': 150.0},
            {'id': 3, 'name': 'Refrigerante', 'quantity': 45, 'revenue': 180.0}
        ]
        mock_get_sales_by_product.return_value = mock_products
        
        # Teste com datas válidas
        response = self.app.get('/api/reports/products?start_date=2025-10-01&end_date=2025-10-30')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['products']), 3)
        
        # Teste com ordenação por quantidade
        response = self.app.get('/api/reports/products?start_date=2025-10-01&end_date=2025-10-30&sort_by=quantity')
        self.assertEqual(response.status_code, 200)
        
        # Teste com limite
        response = self.app.get('/api/reports/products?start_date=2025-10-01&end_date=2025-10-30&limit=2')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data['data']['products']), 2)
        
    @patch('src.models.pedido.pedido.Pedido.get_by_date_range')
    @patch('src.models.pedido.pedido.PedidoItem.get_top_products')
    def test_dashboard_report(self, mock_get_top_products, mock_get_by_date_range):
        """Testa o endpoint de relatório do dashboard"""
        # Mock de dados
        mock_pedidos = [
            MagicMock(id=1, data=datetime.now(), total=100.0, status="concluido"),
            MagicMock(id=2, data=datetime.now(), total=150.0, status="concluido")
        ]
        mock_get_by_date_range.return_value = mock_pedidos
        
        mock_top_products = [
            {'id': 1, 'name': 'Hambúrguer', 'quantity': 50, 'revenue': 500.0},
            {'id': 2, 'name': 'Batata Frita', 'quantity': 30, 'revenue': 150.0}
        ]
        mock_get_top_products.return_value = mock_top_products
        
        # Teste com datas válidas
        response = self.app.get('/api/reports/dashboard?start_date=2025-10-01&end_date=2025-10-30')
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['summary']['total_revenue'], 250.0)
        self.assertEqual(data['data']['summary']['total_orders'], 2)
        self.assertEqual(len(data['data']['top_products']), 2)

if __name__ == '__main__':
    unittest.main()

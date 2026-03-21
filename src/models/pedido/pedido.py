from src.models.user import db
from datetime import datetime
from sqlalchemy import func, desc

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    cliente_nome = db.Column(db.String(100), nullable=True)
    cliente_telefone = db.Column(db.String(20), nullable=True)
    endereco_entrega = db.Column(db.String(255), nullable=True)
    valor_total = db.Column(db.Float, nullable=False, default=0.0)
    metodo_pagamento = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='em_analise')  # em_analise, em_producao, em_entrega
    origem = db.Column(db.String(20), nullable=False, default='app')  # app, whatsapp, pdv
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Pedido {self.numero}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'cliente_nome': self.cliente_nome,
            'cliente_telefone': self.cliente_telefone,
            'endereco_entrega': self.endereco_entrega,
            'valor_total': self.valor_total,
            'metodo_pagamento': self.metodo_pagamento,
            'status': self.status,
            'origem': self.origem,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'itens': [item.to_dict() for item in self.itens]
        }
    
    @classmethod
    def get_by_date_range(cls, start_date, end_date):
        """
        Retorna todos os pedidos dentro de um período específico
        """
        return cls.query.filter(
            cls.data_criacao >= start_date,
            cls.data_criacao <= end_date
        ).all()
    
    @classmethod
    def get_revenue_by_date(cls, start_date, end_date):
        """
        Retorna o faturamento agrupado por data dentro de um período
        """
        result = db.session.query(
            func.date(cls.data_criacao).label('date'),
            func.sum(cls.valor_total).label('revenue'),
            func.count(cls.id).label('orders')
        ).filter(
            cls.data_criacao >= start_date,
            cls.data_criacao <= end_date
        ).group_by(
            func.date(cls.data_criacao)
        ).all()
        
        return [
            {
                'date': str(row.date),
                'revenue': float(row.revenue),
                'orders': row.orders
            }
            for row in result
        ]


class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    valor_unitario = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<ItemPedido {self.produto_nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'produto_nome': self.produto_nome,
            'quantidade': self.quantidade,
            'valor_unitario': self.valor_unitario,
            'valor_total': self.quantidade * self.valor_unitario,
            'observacoes': self.observacoes
        }
    
    @classmethod
    def get_sales_by_product(cls, start_date, end_date):
        """
        Retorna as vendas agrupadas por produto dentro de um período
        """
        result = db.session.query(
            cls.produto_nome.label('name'),
            func.sum(cls.quantidade).label('quantity'),
            func.sum(cls.quantidade * cls.valor_unitario).label('revenue'),
            func.avg(cls.valor_unitario).label('average_price')
        ).join(
            Pedido, cls.pedido_id == Pedido.id
        ).filter(
            Pedido.data_criacao >= start_date,
            Pedido.data_criacao <= end_date
        ).group_by(
            cls.produto_nome
        ).all()
        
        return [
            {
                'name': row.name,
                'quantity': int(row.quantity),
                'revenue': float(row.revenue),
                'average_price': float(row.average_price)
            }
            for row in result
        ]
    
    @classmethod
    def get_top_products(cls, start_date, end_date, limit=5, by_revenue=True):
        """
        Retorna os produtos mais vendidos dentro de um período
        """
        query = db.session.query(
            cls.produto_nome.label('name'),
            func.sum(cls.quantidade).label('quantity'),
            func.sum(cls.quantidade * cls.valor_unitario).label('revenue')
        ).join(
            Pedido, cls.pedido_id == Pedido.id
        ).filter(
            Pedido.data_criacao >= start_date,
            Pedido.data_criacao <= end_date
        ).group_by(
            cls.produto_nome
        )
        
        if by_revenue:
            query = query.order_by(desc(func.sum(cls.quantidade * cls.valor_unitario)))
        else:
            query = query.order_by(desc(func.sum(cls.quantidade)))
        
        result = query.limit(limit).all()
        
        return [
            {
                'name': row.name,
                'quantity': int(row.quantity),
                'revenue': float(row.revenue)
            }
            for row in result
        ]

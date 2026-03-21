# Documentação da API de Relatórios do PDV LaChapa

## Visão Geral

A API de Relatórios do PDV LaChapa fornece endpoints para obtenção de dados analíticos sobre vendas, produtos e métricas de desempenho do negócio. Esta API permite filtrar dados por período, visualizar vendas por produto, receita gerada e faturamento total.

## Endpoints

### 1. Relatório de Vendas

**Endpoint:** `/api/reports/sales`

**Método:** GET

**Descrição:** Retorna dados de vendas agregados por período.

**Parâmetros:**
- `start_date`: Data inicial (formato YYYY-MM-DD)
- `end_date`: Data final (formato YYYY-MM-DD)
- `group_by`: Agrupamento dos resultados (opcional, valores: 'day', 'week', 'month')

**Exemplo de Resposta:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2025-10-01",
      "end_date": "2025-10-30"
    },
    "sales": [
      {
        "date": "2025-10-01",
        "total": 1250.75,
        "orders": 42
      },
      {
        "date": "2025-10-02",
        "total": 1345.50,
        "orders": 45
      }
    ],
    "total_revenue": 25678.50,
    "total_orders": 850
  }
}
```

### 2. Relatório de Produtos

**Endpoint:** `/api/reports/products`

**Método:** GET

**Descrição:** Retorna dados de vendas por produto no período selecionado.

**Parâmetros:**
- `start_date`: Data inicial (formato YYYY-MM-DD)
- `end_date`: Data final (formato YYYY-MM-DD)
- `sort_by`: Campo para ordenação (opcional, valores: 'revenue', 'quantity')
- `order`: Ordem de classificação (opcional, valores: 'asc', 'desc')
- `limit`: Limite de resultados (opcional, padrão: 0 - sem limite)

**Exemplo de Resposta:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 1,
        "name": "Hambúrguer Tradicional",
        "quantity": 120,
        "revenue": 2400.00
      },
      {
        "id": 2,
        "name": "Batata Frita Grande",
        "quantity": 95,
        "revenue": 1425.00
      }
    ]
  }
}
```

### 3. Dados do Dashboard

**Endpoint:** `/api/reports/dashboard`

**Método:** GET

**Descrição:** Retorna dados resumidos para o dashboard, incluindo métricas principais e produtos mais vendidos.

**Parâmetros:**
- `start_date`: Data inicial (formato YYYY-MM-DD)
- `end_date`: Data final (formato YYYY-MM-DD)

**Exemplo de Resposta:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2025-10-01",
      "end_date": "2025-10-30"
    },
    "summary": {
      "total_revenue": 25678.50,
      "total_orders": 850,
      "average_ticket": 30.21,
      "revenue_change_percent": 12.5
    },
    "top_products": [
      {
        "id": 1,
        "name": "Hambúrguer Tradicional",
        "quantity": 120,
        "revenue": 2400.00
      },
      {
        "id": 2,
        "name": "Batata Frita Grande",
        "quantity": 95,
        "revenue": 1425.00
      }
    ]
  }
}
```

## Códigos de Status

- `200 OK`: Requisição bem-sucedida
- `400 Bad Request`: Parâmetros inválidos ou ausentes
- `500 Internal Server Error`: Erro interno do servidor

## Integração com o Frontend

A API de Relatórios foi projetada para integração com o frontend do PDV LaChapa, especificamente com a página de relatórios que inclui:

1. Seletor de período (DateRangePicker)
2. Gráficos de vendas (SalesChart)
3. Tabelas de produtos (ProductsTable)
4. Métricas de desempenho (MetricCard)

## Considerações Técnicas

- Todos os valores monetários são retornados em reais (BRL)
- As datas devem ser fornecidas no formato YYYY-MM-DD
- A data final é ajustada para incluir o dia inteiro (23:59:59)
- Quando não são fornecidas datas, o sistema usa o dia atual como padrão

from flask import Blueprint, jsonify, request, current_app
import os
import platform
import json
import tempfile
import base64
from datetime import datetime

impressora_bp = Blueprint('impressora', __name__)

# Classe para gerenciar impressoras ESC/POS
class GerenciadorImpressora:
    def __init__(self):
        self.config = {
            'tipo_conexao': 'usb',  # 'usb' ou 'bluetooth'
            'porta': 'auto',        # 'auto' ou porta específica como 'COM3' ou '/dev/usb/lp0'
            'bluetooth_mac': '',    # Endereço MAC para conexão Bluetooth
            'modelo': 'generic',    # 'generic', 'elgin', 'epson', 'bematech'
            'colunas': 42,          # Número de colunas da impressora
            'encoding': 'cp850',    # Codificação de caracteres
            'cortar_papel': True,   # Se deve cortar papel automaticamente
            'gaveta': False         # Se deve abrir gaveta após impressão
        }
    
    def salvar_config(self, nova_config):
        """Atualiza e salva a configuração da impressora"""
        self.config.update(nova_config)
        return self.config
    
    def gerar_comando_impressao(self, pedido):
        """Gera os comandos ESC/POS para impressão do pedido"""
        # Inicialização dos comandos ESC/POS
        comandos = []
        
        # Códigos ESC/POS comuns
        ESC = b'\x1B'
        GS = b'\x1D'
        
        # Inicialização da impressora
        comandos.append(ESC + b'@')
        
        # Centralizar texto
        comandos.append(ESC + b'a' + b'\x01')
        
        # Texto em negrito
        comandos.append(ESC + b'E' + b'\x01')
        
        # Nome do estabelecimento
        comandos.append(b'LA CHAPA LANCHES\n')
        comandos.append(b'--------------------------------\n')
        
        # Desativar negrito
        comandos.append(ESC + b'E' + b'\x00')
        
        # Alinhar à esquerda
        comandos.append(ESC + b'a' + b'\x00')
        
        # Informações do pedido
        comandos.append(f"PEDIDO #{pedido['numero']}\n".encode('cp850'))
        comandos.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp850'))
        comandos.append(b'\n')
        
        # Cliente
        if pedido.get('cliente_nome'):
            comandos.append(f"Cliente: {pedido['cliente_nome']}\n".encode('cp850'))
        if pedido.get('cliente_telefone'):
            comandos.append(f"Telefone: {pedido['cliente_telefone']}\n".encode('cp850'))
        if pedido.get('endereco_entrega'):
            comandos.append(f"Endereco: {pedido['endereco_entrega']}\n".encode('cp850'))
        comandos.append(b'\n')
        
        # Itens do pedido
        comandos.append(b'ITENS DO PEDIDO\n')
        comandos.append(b'--------------------------------\n')
        
        for item in pedido.get('itens', []):
            nome = item['produto_nome']
            qtd = item['quantidade']
            valor = item['valor_unitario']
            subtotal = qtd * valor
            
            # Formatar item para caber nas colunas da impressora
            linha_item = f"{qtd}x {nome[:20]}"
            linha_item = linha_item.ljust(30)
            linha_item += f"R$ {subtotal:.2f}\n"
            comandos.append(linha_item.encode('cp850'))
            
            # Adicionar observações do item se houver
            if item.get('observacoes'):
                obs = f"  Obs: {item['observacoes']}\n"
                comandos.append(obs.encode('cp850'))
        
        comandos.append(b'--------------------------------\n')
        
        # Total
        comandos.append(f"TOTAL: R$ {pedido['valor_total']:.2f}\n".encode('cp850'))
        comandos.append(b'\n')
        
        # Forma de pagamento
        if pedido.get('metodo_pagamento'):
            comandos.append(f"Pagamento: {pedido['metodo_pagamento'].upper()}\n".encode('cp850'))
            comandos.append(b'\n')
        
        # Observações gerais
        if pedido.get('observacoes'):
            comandos.append(b'OBSERVACOES:\n')
            comandos.append(f"{pedido['observacoes']}\n".encode('cp850'))
            comandos.append(b'\n')
        
        # Centralizar texto
        comandos.append(ESC + b'a' + b'\x01')
        
        # Mensagem final
        comandos.append(b'Obrigado pela preferencia!\n')
        comandos.append(b'\n\n\n')
        
        # Cortar papel se configurado
        if self.config['cortar_papel']:
            comandos.append(GS + b'V' + b'\x42' + b'\x00')
        
        # Abrir gaveta se configurado
        if self.config['gaveta']:
            comandos.append(ESC + b'p' + b'\x00' + b'\x19' + b'\x19')
        
        return b''.join(comandos)
    
    def imprimir_pedido(self, pedido):
        """Imprime um pedido na impressora configurada"""
        try:
            comandos = self.gerar_comando_impressao(pedido)
            
            # Verificar o sistema operacional
            sistema = platform.system()
            
            if sistema == 'Windows':
                return self._imprimir_windows(comandos)
            elif sistema == 'Linux':
                return self._imprimir_linux(comandos)
            elif sistema == 'Darwin':  # macOS
                return self._imprimir_macos(comandos)
            else:
                return {'sucesso': False, 'mensagem': f'Sistema operacional não suportado: {sistema}'}
                
        except Exception as e:
            return {'sucesso': False, 'mensagem': f'Erro ao imprimir: {str(e)}'}
    
    def _imprimir_windows(self, comandos):
        """Imprime em impressoras no Windows"""
        try:
            # Em produção, usaria a biblioteca win32print
            # Como estamos em ambiente de desenvolvimento, salvamos em arquivo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin', mode='wb') as f:
                f.write(comandos)
                temp_file = f.name
            
            return {
                'sucesso': True, 
                'mensagem': f'Comando de impressão gerado com sucesso (simulação)',
                'arquivo_temp': temp_file
            }
        except Exception as e:
            return {'sucesso': False, 'mensagem': f'Erro ao imprimir no Windows: {str(e)}'}
    
    def _imprimir_linux(self, comandos):
        """Imprime em impressoras no Linux"""
        try:
            # Em produção, enviaria diretamente para a porta
            # Como estamos em ambiente de desenvolvimento, salvamos em arquivo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin', mode='wb') as f:
                f.write(comandos)
                temp_file = f.name
            
            return {
                'sucesso': True, 
                'mensagem': f'Comando de impressão gerado com sucesso (simulação)',
                'arquivo_temp': temp_file
            }
        except Exception as e:
            return {'sucesso': False, 'mensagem': f'Erro ao imprimir no Linux: {str(e)}'}
    
    def _imprimir_macos(self, comandos):
        """Imprime em impressoras no macOS"""
        try:
            # Em produção, usaria CUPS
            # Como estamos em ambiente de desenvolvimento, salvamos em arquivo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin', mode='wb') as f:
                f.write(comandos)
                temp_file = f.name
            
            return {
                'sucesso': True, 
                'mensagem': f'Comando de impressão gerado com sucesso (simulação)',
                'arquivo_temp': temp_file
            }
        except Exception as e:
            return {'sucesso': False, 'mensagem': f'Erro ao imprimir no macOS: {str(e)}'}
    
    def imprimir_teste(self):
        """Imprime um cupom de teste"""
        pedido_teste = {
            'numero': 'TESTE',
            'cliente_nome': 'Cliente Teste',
            'cliente_telefone': '(11) 99999-9999',
            'endereco_entrega': 'Av. Teste, 123',
            'valor_total': 99.99,
            'metodo_pagamento': 'Dinheiro',
            'observacoes': 'Impressão de teste',
            'itens': [
                {
                    'produto_nome': 'Produto Teste 1',
                    'quantidade': 2,
                    'valor_unitario': 25.00,
                    'observacoes': 'Sem cebola'
                },
                {
                    'produto_nome': 'Produto Teste 2',
                    'quantidade': 1,
                    'valor_unitario': 49.99,
                    'observacoes': None
                }
            ]
        }
        
        return self.imprimir_pedido(pedido_teste)
    
    def gerar_qrcode_android(self, pedido):
        """Gera um QR code para impressão via app Android"""
        dados = {
            'tipo': 'pedido',
            'dados': pedido,
            'timestamp': datetime.now().isoformat()
        }
        
        # Em produção, geraria um QR code real
        # Para simulação, retornamos os dados em base64
        dados_json = json.dumps(dados)
        dados_base64 = base64.b64encode(dados_json.encode('utf-8')).decode('utf-8')
        
        return {
            'sucesso': True,
            'qrcode_data': dados_base64
        }


# Instância global do gerenciador
gerenciador_impressora = GerenciadorImpressora()

# Rotas da API

@impressora_bp.route('/config', methods=['GET'])
def obter_config():
    """Obtém a configuração atual da impressora"""
    return jsonify(gerenciador_impressora.config)

@impressora_bp.route('/config', methods=['POST'])
def atualizar_config():
    """Atualiza a configuração da impressora"""
    nova_config = request.json
    config = gerenciador_impressora.salvar_config(nova_config)
    return jsonify(config)

@impressora_bp.route('/teste', methods=['POST'])
def imprimir_teste():
    """Imprime um cupom de teste"""
    resultado = gerenciador_impressora.imprimir_teste()
    return jsonify(resultado)

@impressora_bp.route('/pedido/<int:pedido_id>', methods=['POST'])
def imprimir_pedido(pedido_id):
    """Imprime um pedido específico"""
    from src.models.pedido.pedido import Pedido
    
    pedido = Pedido.query.get_or_404(pedido_id)
    resultado = gerenciador_impressora.imprimir_pedido(pedido.to_dict())
    
    return jsonify(resultado)

@impressora_bp.route('/android/qrcode/<int:pedido_id>', methods=['GET'])
def gerar_qrcode_android(pedido_id):
    """Gera um QR code para impressão via app Android"""
    from src.models.pedido.pedido import Pedido
    
    pedido = Pedido.query.get_or_404(pedido_id)
    resultado = gerenciador_impressora.gerar_qrcode_android(pedido.to_dict())
    
    return jsonify(resultado)

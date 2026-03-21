// Kanban Board JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Referências aos elementos do DOM
    const emAnaliseContainer = document.getElementById('em-analise');
    const emProducaoContainer = document.getElementById('em-producao');
    const emEntregaContainer = document.getElementById('em-entrega');
    
    const countEmAnalise = document.getElementById('count-em-analise');
    const countEmProducao = document.getElementById('count-em-producao');
    const countEmEntrega = document.getElementById('count-em-entrega');
    
    // API URL base
    const API_URL = '/api';
    
    // Função para carregar todos os pedidos do backend
    async function carregarPedidos() {
        try {
            const response = await fetch(`${API_URL}/pedidos`);
            if (!response.ok) {
                throw new Error('Erro ao carregar pedidos');
            }
            
            const pedidos = await response.json();
            
            // Limpar os containers
            emAnaliseContainer.innerHTML = '';
            emProducaoContainer.innerHTML = '';
            emEntregaContainer.innerHTML = '';
            
            // Filtrar e renderizar pedidos por status
            const pedidosEmAnalise = pedidos.filter(p => p.status === 'em_analise');
            const pedidosEmProducao = pedidos.filter(p => p.status === 'em_producao');
            const pedidosEmEntrega = pedidos.filter(p => p.status === 'em_entrega');
            
            // Atualizar contadores
            countEmAnalise.textContent = pedidosEmAnalise.length;
            countEmProducao.textContent = pedidosEmProducao.length;
            countEmEntrega.textContent = pedidosEmEntrega.length;
            
            // Renderizar pedidos em cada coluna
            pedidosEmAnalise.forEach(pedido => {
                emAnaliseContainer.appendChild(criarCardPedido(pedido, 'em_analise'));
            });
            
            pedidosEmProducao.forEach(pedido => {
                emProducaoContainer.appendChild(criarCardPedido(pedido, 'em_producao'));
            });
            
            pedidosEmEntrega.forEach(pedido => {
                emEntregaContainer.appendChild(criarCardPedido(pedido, 'em_entrega'));
            });
            
            // Adicionar mensagem quando não houver pedidos
            if (pedidosEmAnalise.length === 0) {
                emAnaliseContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                        <p class="mt-2">Nenhum pedido em análise</p>
                    </div>
                `;
            }
            
            if (pedidosEmProducao.length === 0) {
                emProducaoContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="bi bi-tools" style="font-size: 2rem;"></i>
                        <p class="mt-2">Nenhum pedido em produção</p>
                    </div>
                `;
            }
            
            if (pedidosEmEntrega.length === 0) {
                emEntregaContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="bi bi-truck" style="font-size: 2rem;"></i>
                        <p class="mt-2">Nenhum pedido em entrega</p>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Erro:', error);
            // Usar dados de exemplo para demonstração quando API não estiver disponível
            usarDadosExemplo();
        }
    }
    
    // Função para criar um card de pedido
    function criarCardPedido(pedido, status) {
        const card = document.createElement('div');
        card.className = 'card mb-3 kanban-item';
        card.dataset.id = pedido.id;
        
        // Formatar data
        const data = new Date(pedido.data_criacao);
        const horaFormatada = `${data.getHours().toString().padStart(2, '0')}:${data.getMinutes().toString().padStart(2, '0')}`;
        
        // Determinar o texto do botão de ação baseado no status
        let botaoAcao = '';
        if (status === 'em_analise') {
            botaoAcao = `<button class="btn btn-sm btn-success avancar-pedido" data-id="${pedido.id}" data-next="em_producao">Aprovar</button>`;
        } else if (status === 'em_producao') {
            botaoAcao = `<button class="btn btn-sm btn-primary avancar-pedido" data-id="${pedido.id}" data-next="em_entrega">Avançar pedido</button>`;
        } else {
            botaoAcao = `<button class="btn btn-sm btn-outline-success" disabled>Entregue</button>`;
        }
        
        // Determinar a badge do método de pagamento
        let badgeClass = 'bg-info';
        if (pedido.metodo_pagamento === 'dinheiro') {
            badgeClass = 'bg-success';
        } else if (pedido.metodo_pagamento === 'pix') {
            badgeClass = 'bg-primary';
        }
        
        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <span>Pedido #${pedido.numero}</span>
                <span class="text-muted">${horaFormatada}</span>
            </div>
            <div class="card-body">
                <div class="mb-2">
                    <strong>Cliente:</strong> ${pedido.cliente_nome || 'Não informado'}<br>
                    <strong>Telefone:</strong> ${pedido.cliente_telefone || 'Não informado'}
                </div>
                ${pedido.endereco_entrega ? `
                <div class="mb-2">
                    <strong>Delivery:</strong> ${pedido.endereco_entrega}
                </div>
                ` : ''}
                <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-bold">Total: R$ ${pedido.valor_total.toFixed(2)}</span>
                    <span class="badge ${badgeClass}">${pedido.metodo_pagamento || 'Não informado'}</span>
                </div>
                <div class="mt-3 d-flex justify-content-between">
                    <button class="btn btn-sm btn-outline-secondary ver-detalhes" data-id="${pedido.id}">Detalhes</button>
                    ${botaoAcao}
                </div>
            </div>
        `;
        
        // Adicionar event listeners
        setTimeout(() => {
            const btnDetalhes = card.querySelector('.ver-detalhes');
            btnDetalhes.addEventListener('click', () => abrirModalDetalhes(pedido));
            
            const btnAvancar = card.querySelector('.avancar-pedido');
            if (btnAvancar) {
                btnAvancar.addEventListener('click', (e) => {
                    const pedidoId = e.target.dataset.id;
                    const nextStatus = e.target.dataset.next;
                    avancarPedido(pedidoId, nextStatus);
                });
            }
        }, 0);
        
        return card;
    }
    
    // Função para avançar o status de um pedido
    async function avancarPedido(pedidoId, novoStatus) {
        try {
            const response = await fetch(`${API_URL}/pedidos/${pedidoId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: novoStatus })
            });
            
            if (!response.ok) {
                throw new Error('Erro ao atualizar status do pedido');
            }
            
            const pedidoAtualizado = await response.json();
            
            // Se o pedido foi aprovado para produção, imprimir comanda
            if (novoStatus === 'em_producao') {
                imprimirComanda(pedidoId);
            }
            
            // Recarregar pedidos para atualizar a interface
            carregarPedidos();
            
            // Mostrar notificação de sucesso
            mostrarNotificacao('Pedido atualizado com sucesso!', 'success');
            
        } catch (error) {
            console.error('Erro:', error);
            mostrarNotificacao('Erro ao atualizar pedido. Tente novamente.', 'danger');
            
            // Para demonstração, mover o card manualmente
            const card = document.querySelector(`.kanban-item[data-id="${pedidoId}"]`);
            if (card) {
                card.remove();
                
                if (novoStatus === 'em_producao') {
                    emProducaoContainer.appendChild(card);
                    countEmAnalise.textContent = parseInt(countEmAnalise.textContent) - 1;
                    countEmProducao.textContent = parseInt(countEmProducao.textContent) + 1;
                    
                    // Simular impressão para demonstração
                    console.log('Simulando impressão da comanda do pedido:', pedidoId);
                    mostrarNotificacao('Comanda enviada para impressão!', 'info');
                } else if (novoStatus === 'em_entrega') {
                    emEntregaContainer.appendChild(card);
                    countEmProducao.textContent = parseInt(countEmProducao.textContent) - 1;
                    countEmEntrega.textContent = parseInt(countEmEntrega.textContent) + 1;
                }
                
                // Adicionar classe de animação
                card.classList.add('card-move');
                setTimeout(() => {
                    card.classList.remove('card-move');
                }, 500);
            }
        }
    }
    
    // Função para imprimir comanda
    function imprimirComanda(pedidoId) {
        // Esta função será implementada com a biblioteca ESC/POS
        console.log('Enviando pedido para impressão:', pedidoId);
        
        // Aqui será feita a chamada para o endpoint de impressão
        fetch(`${API_URL}/pedidos/${pedidoId}/imprimir`, {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                mostrarNotificacao('Comanda enviada para impressão!', 'success');
            } else {
                throw new Error('Erro ao imprimir comanda');
            }
        })
        .catch(error => {
            console.error('Erro de impressão:', error);
            mostrarNotificacao('Erro ao imprimir comanda. Verifique a impressora.', 'warning');
        });
    }
    
    // Função para abrir modal de detalhes do pedido
    function abrirModalDetalhes(pedido) {
        const modal = new bootstrap.Modal(document.getElementById('modalDetalhesPedido'));
        
        // Atualizar conteúdo do modal com dados do pedido
        document.querySelector('#modalDetalhesPedido .modal-title').textContent = `Detalhes do Pedido #${pedido.numero}`;
        
        // Formatar data
        const data = new Date(pedido.data_criacao);
        const dataFormatada = `${data.getDate().toString().padStart(2, '0')}/${(data.getMonth() + 1).toString().padStart(2, '0')}/${data.getFullYear()} ${data.getHours().toString().padStart(2, '0')}:${data.getMinutes().toString().padStart(2, '0')}`;
        
        // Informações do cliente
        const infoCliente = document.querySelector('#modalDetalhesPedido .modal-body .row .col-md-6:first-child p');
        infoCliente.innerHTML = `
            <strong>Nome:</strong> ${pedido.cliente_nome || 'Não informado'}<br>
            <strong>Telefone:</strong> ${pedido.cliente_telefone || 'Não informado'}<br>
            <strong>Endereço:</strong> ${pedido.endereco_entrega || 'Não informado'}<br>
            <strong>Método de Pagamento:</strong> ${pedido.metodo_pagamento || 'Não informado'}
        `;
        
        // Informações do pedido
        let statusClass = 'bg-warning';
        if (pedido.status === 'em_producao') statusClass = 'bg-primary';
        if (pedido.status === 'em_entrega') statusClass = 'bg-success';
        
        let statusText = 'Em análise';
        if (pedido.status === 'em_producao') statusText = 'Em produção';
        if (pedido.status === 'em_entrega') statusText = 'Foi para entrega';
        
        const infoPedido = document.querySelector('#modalDetalhesPedido .modal-body .row .col-md-6:last-child p');
        infoPedido.innerHTML = `
            <strong>Número:</strong> #${pedido.numero}<br>
            <strong>Data/Hora:</strong> ${dataFormatada}<br>
            <strong>Status:</strong> <span class="badge ${statusClass}">${statusText}</span><br>
            <strong>Origem:</strong> ${pedido.origem === 'app' ? 'App' : pedido.origem === 'whatsapp' ? 'WhatsApp' : 'PDV'}
        `;
        
        // Itens do pedido
        const tbody = document.querySelector('#modalDetalhesPedido .modal-body table tbody');
        tbody.innerHTML = '';
        
        if (pedido.itens && pedido.itens.length > 0) {
            pedido.itens.forEach(item => {
                const tr = document.createElement('tr');
                const subtotal = item.quantidade * item.valor_unitario;
                
                tr.innerHTML = `
                    <td>${item.produto_nome}</td>
                    <td>${item.quantidade}</td>
                    <td>R$ ${item.valor_unitario.toFixed(2)}</td>
                    <td>R$ ${subtotal.toFixed(2)}</td>
                `;
                
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center">Nenhum item encontrado</td>
                </tr>
            `;
        }
        
        // Total
        document.querySelector('#modalDetalhesPedido .modal-body table tfoot th:last-child').textContent = `R$ ${pedido.valor_total.toFixed(2)}`;
        
        // Observações
        const obsContainer = document.querySelector('#modalDetalhesPedido .modal-body .mb-3 p');
        obsContainer.textContent = pedido.observacoes || 'Nenhuma observação';
        
        // Botão de impressão
        const btnImprimir = document.getElementById('btnImprimir');
        btnImprimir.onclick = () => imprimirComanda(pedido.id);
        
        modal.show();
    }
    
    // Função para mostrar notificações
    function mostrarNotificacao(mensagem, tipo) {
        // Criar elemento de notificação
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${tipo} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${mensagem}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>
            </div>
        `;
        
        // Adicionar ao container de notificações (criar se não existir)
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Inicializar e mostrar toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
        
        // Remover após fechar
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // Função para usar dados de exemplo quando API não estiver disponível
    function usarDadosExemplo() {
        console.log('Usando dados de exemplo para demonstração');
        // Os dados de exemplo já estão no HTML
    }
    
    // Inicializar a aplicação
    carregarPedidos();
    
    // Atualizar pedidos a cada 30 segundos
    setInterval(carregarPedidos, 30000);
});

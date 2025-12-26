// Funções de Interação da Página do Dashboard
// Este arquivo contém os scripts para interatividade da página de dashboard,
// incluindo logout, navegação, e atualizações dinâmicas.

/**
 * @description Exibe uma confirmação de logout e, se confirmado, simula o logout.
 */
function logout() {
    if (confirm('Tem certeza que deseja sair do sistema?')) {
        window.location.href = '/logout';
    }
}

/**
 * @description Funções para os botões de "Ações Rápidas".
 * Simulam o redirecionamento para outras páginas.
 */
function novoAgendamento() {
    alert('Redirecionando para tela de novo agendamento...');
    // window.location.href = 'agendamento.html';
}

function novoCliente() {
    alert('Redirecionando para cadastro de cliente...');
    // window.location.href = 'cliente.html';
}

function verAgenda() {
    alert('Redirecionando para visualização da agenda...');
    window.location.href = '/agenda';
}

function gerarRelatorio() {
    alert('Redirecionando para geração de relatórios...');
    // window.location.href = 'relatorios.html';
}

// Delegação de Eventos para o Menu de Navegação
document.addEventListener('DOMContentLoaded', () => {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.addEventListener('click', (e) => {
            const link = e.target.closest('.nav-link');
            if (!link) return;

            document.querySelectorAll('.nav-link').forEach((l) => l.classList.remove('active'));
            link.classList.add('active');

            if (!link.getAttribute('href') || link.getAttribute('href') === '#') {
                e.preventDefault();
            }
        });
    }

    // Animação "Fade-in" para os Cards de Estatística
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 }); // O callback é chamado quando 10% do elemento está visível

        statCards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.6s ease';
            observer.observe(card);
        });
    }

    /**
     * @description Atualiza em tempo real as estatísticas do dashboard consultando a API.
     */
    function updateStats() {
        fetch('/api/dashboard/stats')
            .then(response => response.json())
            .then(data => {
                if (data.consultas_hoje !== undefined) {
                    const el = document.getElementById('stat-consultas-hoje');
                    if (el && el.textContent != data.consultas_hoje) {
                        el.textContent = data.consultas_hoje;
                        // Animação sutil
                        el.style.transform = 'scale(1.1)';
                        setTimeout(() => { el.style.transform = 'scale(1)'; }, 200);
                    }
                }
                if (data.salas_disponiveis !== undefined) {
                    const el = document.getElementById('stat-salas-disponiveis');
                    if (el) el.textContent = data.salas_disponiveis;
                }
                if (data.salas_ocupadas !== undefined) {
                    const el = document.getElementById('stat-salas-ocupadas');
                    if (el) el.textContent = data.salas_ocupadas;
                }
                if (data.clientes_ativos !== undefined) {
                    const el = document.getElementById('stat-clientes-ativos');
                    if (el) el.textContent = data.clientes_ativos;
                }
            })
            .catch(error => console.error('Erro ao atualizar dashboard:', error));
    }

    // Inicia a atualização a cada 5 segundos
    setInterval(updateStats, 5000);
});

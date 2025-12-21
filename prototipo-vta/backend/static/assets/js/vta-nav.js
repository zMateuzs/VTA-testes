/* ===========================
   VTA Navigator – roteador simples para HTMLs separados
   =========================== */

// Este script centraliza a lógica de navegação entre as páginas HTML
// do protótipo da Agenda VTA. Ele também lida com a persistência de
// sessão usando localStorage e realiza pequenos ajustes de layout.

(function () {
// Ajuste aqui para as rotas do Flask
const ROUTES = {
  dashboard: '/dashboard',
  agenda: '/agenda',
  agendamentos: '/agendamento',
  clientes: '/clientes',
  pets: '/pets',
  usuarios: '/usuarios',
  salas: '/salas',
  relatoriosDashboard: '/relatorios',
  relatoriosPets: '/relatorios/pets',
  notificacoes: '11.%20notificacoes_vta.html',
  login: '/' // A rota de login é a raiz
};

  // Usuário de demonstração (pode ser ajustado conforme necessário)
  const DEMO_USER = {
    email: '1',
    senha: '1',
    nome: 'Usuário Demo',
    papel: 'Veterinário'
  };
  const SESSION_KEY = 'vta.session';

  function setSession(user) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
  }
  function getSession() {
    try {
      return JSON.parse(localStorage.getItem(SESSION_KEY));
    } catch {
      return null;
    }
  }
  function clearSession() {
    localStorage.removeItem(SESSION_KEY);
  }

  function isLoginPage() {
    const t = document.title.toLowerCase();
    return t.includes('login');
  }

  function goTo(file) {
    window.location.href = file;
  }

  function enforceAuth() {
    if (isLoginPage()) return; // página de login é pública
    if (!getSession()) goTo(ROUTES.login);
  }

  // Intercepta envio do formulário de login e realiza autenticação simples
  function wireLogin() {
    if (!isLoginPage()) return;

    const form = document.querySelector('form') || document.getElementById('loginForm');
    if (!form) return;

    const emailInput = form.querySelector('input[type="email"], input[name="email"], input#email');
    const senhaInput = form.querySelector('input[type="password"], input[name="senha"], input#senha');
    const btn = form.querySelector('button[type="submit"], .login-button');

    function showMsg(selectorOrCreate, text, ok = false) {
      let box = document.querySelector(selectorOrCreate);
      if (!box) {
        box = document.createElement('div');
        box.className = ok ? 'success-message' : 'error-message';
        form.prepend(box);
      }
      box.style.display = 'block';
      box.textContent = text;
      if (ok) box.classList.remove('error-message');
    }

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = (emailInput?.value ?? '').trim();
      const senha = (senhaInput?.value ?? '').trim();

      if (email === DEMO_USER.email && senha === DEMO_USER.senha) {
        setSession({ ...DEMO_USER, email });
        showMsg('.success-message', 'Login realizado! Redirecionando…', true);
        if (btn) btn.classList?.add('loading');
        setTimeout(() => goTo(ROUTES.dashboard), 400);
      } else {
        showMsg('.error-message', 'Credenciais inválidas. Tente 1 / 1 (protótipo).');
      }
    });
  }

  // Ajusta links da sidebar para apontarem para os arquivos corretos
  function wireSidebarLinks() {
    const navs = document.querySelectorAll(
      '.nav-menu a.nav-link, aside .nav-menu a, .sidebar .nav-menu a'
    );
    if (!navs.length) return;

    navs.forEach((a) => {
      const label = (a.textContent || '').toLowerCase();

      if (label.includes('dashboard')) a.setAttribute('href', ROUTES.dashboard);
      else if (label.includes('agenda') && !label.includes('agendamento'))
        a.setAttribute('href', ROUTES.agenda);
      else if (label.includes('agendamento')) a.setAttribute('href', ROUTES.agendamentos);
      else if (label.includes('clientes')) a.setAttribute('href', ROUTES.clientes);
      else if (label.includes('pets')) a.setAttribute('href', ROUTES.pets);
      else if (
        label.includes('usuário') ||
        label.includes('usuarios') ||
        label.includes('usuários')
      )
        a.setAttribute('href', ROUTES.usuarios);
      else if (label.includes('salas') || label.includes('sala'))
        a.setAttribute('href', ROUTES.salas);
      else if (
        label.includes('relatórios') &&
        (label.includes('adm') || label.includes('dashboard'))
      )
        a.setAttribute('href', ROUTES.relatoriosDashboard);
      else if (label.includes('relatórios') && label.includes('pets'))
        a.setAttribute('href', ROUTES.relatoriosPets);
      else if (label.includes('notific')) a.setAttribute('href', ROUTES.notificacoes);

      // Sempre navega via script para garantir que o espaço (codificado) seja interpretado corretamente.
      a.addEventListener('click', (e) => {
        const hrefAttr = a.getAttribute('href');
        if (!hrefAttr || hrefAttr === '#') {
          // Se ainda for link vazio, apenas previne a navegação
          e.preventDefault();
          return;
        }
        // Previne navegação padrão e usa goTo para mudar de página
        e.preventDefault();
        goTo(hrefAttr);
      });
    });
  }

  // Liga botões de logout para limpar sessão
  function wireLogout() {
    const logoutBtns = document.querySelectorAll('.logout-btn, [data-action="logout"]');
    logoutBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (confirm('Tem certeza que deseja sair do sistema?')) {
            clearSession();
            window.location.href = '/logout';
        }
      });
    });
  }

  // Liga botões de voltar (caso existam)
  function wireBack() {
    const backBtns = document.querySelectorAll('.back-btn, [data-action="back"]');
    backBtns.forEach((btn) =>
      btn.addEventListener('click', () => window.history.back())
    );
  }

  // Pequeno fix de layout para garantir estrutura entre sidebar e conteúdo
  function applyLayoutFixIfNeeded() {
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main-content');
    
    // Só aplica o fix se a sidebar estiver DENTRO do main-content (estrutura antiga)
    if (sidebar && main && main.contains(sidebar)) {
      const s = document.createElement('style');
      s.textContent = `
        .main-content { display: grid !important; grid-template-columns: 250px 1fr !important; gap: 2rem !important; }
        @media (max-width:1024px){ .main-content { grid-template-columns: 1fr !important; } }
      `;
      document.head.appendChild(s);
    }
  }

  // Preenche informações do usuário logado (se existirem elementos no header)
  function hydrateUserHeader() {
    const session = getSession();
    if (!session) return;
    const nameEl = document.querySelector('.user-details h3');
    const roleEl = document.querySelector('.user-role');
    if (nameEl && !nameEl.textContent.trim()) nameEl.textContent = session.nome || 'Usuário';
    if (roleEl && !roleEl.textContent.trim()) roleEl.textContent = session.papel || 'Equipe';
  }

  // Execução ao carregar documento
  document.addEventListener('DOMContentLoaded', () => {
    // enforceAuth(); // Desabilitado: Autenticação gerenciada pelo Backend (Flask)
    // wireLogin();   // Desabilitado: Login gerenciado pelo Backend
    // wireSidebarLinks(); // Desabilitado: Links gerenciados pelo Jinja2
    wireLogout();
    wireBack();
    applyLayoutFixIfNeeded();
    // hydrateUserHeader(); // Desabilitado: Dados do usuário renderizados pelo Backend
  });
})();
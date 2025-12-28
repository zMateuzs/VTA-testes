
﻿# Agenda VTA - Sistema de Agendamento para Clínica Veterinária

## Sobre o projeto

O **Agenda VTA** é um sistema web de agendamento desenvolvido para otimizar a gestão de consultas e o uso das salas de atendimento da clínica veterinária **Vet Assistance**. O projeto surgiu para substituir o controle manual em planilhas, reduzindo erros, agendamentos duplicados e a falta de visibilidade sobre a disponibilidade de recursos.

O foco da solução é oferecer uma ferramenta **estável, rápida e intuitiva** para a equipe interna (especialmente a recepção), que lida diariamente com um alto volume de agendamentos simultâneos.

**Importante:** o sistema é de **uso interno da clínica** (recepcionistas, veterinários e gestores) e não possui portal de acesso para tutores ou clientes finais.

---

## Principais funcionalidades (MVP)

O escopo mínimo viável foi definido em conjunto com a clínica para atender às necessidades mais críticas do dia a dia:

- **UC01 – Autenticação de usuários:** login com perfis de acesso (recepcionista, veterinário, administrador).
- **UC02 – Gestão de clientes e pets:** cadastro, consulta, edição e exclusão de tutores e seus animais, centralizando as informações em um único sistema.
- **UC03 – Visualização da agenda por sala:** grade de horários organizada por sala, com visão diária e semanal, permitindo acompanhar em tempo real a ocupação.
- **UC04 – Realizar agendamento:** fluxo simples para criação de novos agendamentos, com validação de conflitos de horário e disponibilidade de sala.
- **UC05 – Bloqueio de horários:** bloqueio de horários, datas ou salas inteiras para manutenção, eventos internos ou indisponibilidades.
- **Geração de texto para notificação:** criação de um texto padrão para confirmação de consulta, que pode ser copiado e enviado manualmente via WhatsApp pela equipe.
- **UC07 – Relatórios gerenciais:** geração de relatórios de atendimentos e ocupação das salas.
- **UC08 – Histórico do pet:** acesso rápido ao histórico de agendamentos de cada animal.

---

## Arquitetura e princípios de design

Algumas premissas orientaram o desenho da solução:

1. **Estabilidade em primeiro lugar:** as decisões técnicas privilegiam simplicidade e robustez. O sistema foi pensado para estar sempre disponível durante o expediente da clínica.
2. **Segurança contra erros operacionais:** ações sensíveis (como exclusões) exigem confirmação em mais de uma etapa para reduzir o risco de perda acidental de dados.
3. **Comunicação controlada e humanizada:** o sistema não envia mensagens automáticas. Em vez disso, gera um texto padronizado para que a recepção possa revisar, copiar e enviar manualmente ao tutor, preservando o contato pessoal.
4. **Foco na usabilidade da recepção:** telas, fluxos e textos foram desenhados pensando na rotina de quem precisa ser rápido e assertivo em um ambiente com múltiplos atendimentos simultâneos.

No back-end, a aplicação segue um modelo monolítico em Flask, com todas as rotas centralizadas em `backend/routes.py`. As telas são renderizadas por templates HTML na pasta `backend/templates`, com JavaScript e CSS específicos de cada página quando necessário.

---

## Tecnologias utilizadas

| Categoria        | Tecnologia                                                                 |
|------------------|----------------------------------------------------------------------------|
| Front-end        | HTML5, CSS3, JavaScript (renderização server-side via templates Flask)    |
| Back-end         | Python, Flask                                                              |
| Banco de dados   | PostgreSQL (acesso via `psycopg2`)                                        |
| Versionamento    | Git, GitHub                                                                |
| Gerenciamento    | Trello                                                                     |
| Prototipagem     | Figma                                                                      |

Observação: a stack ativa usa **PostgreSQL** e o script de provisionamento está em `backend/setup_db.py` (seed do admin e salas padrão).

---

## Como executar o projeto

Abaixo, um guia resumido para subir o ambiente localmente.

### 1. Pré-requisitos

- Python 3.10 ou superior
- `pip` atualizado
- Opcional: `virtualenv` ou ambiente virtual equivalente

### 2. Clonar o repositório

```bash
git clone https://github.com/trickGit/TIC55-AGENDA-VTA.git
cd TIC55-AGENDA-VTA/prototipo-vta
```

### 3. Configurar o back-end (Flask + PostgreSQL)

Dentro da pasta `prototipo-vta`, navegue até o diretório `backend` e crie o ambiente virtual:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na pasta `backend` para configurar a aplicação e o banco PostgreSQL:

```bash
SECRET_KEY=sua-chave-secreta-segura
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agenda_vta
DB_USER=postgres
DB_PASS=postgres
```

Se o arquivo `.env` não for configurado, a aplicação utiliza valores padrão apenas para desenvolvimento.

### 4. Inicializar o banco de dados PostgreSQL

Ainda dentro de `backend`, execute o script de criação das tabelas e seed:

```bash
python setup_db.py
```

Ele cria todas as tabelas necessárias (agendamentos, usuários, clientes, pets, salas e notificações) e garante o usuário administrador padrão:

- E-mail: `admin@vta.com`
- Senha: `admin123`

### 5. Executar a aplicação

Com o ambiente virtual ativo e o banco de dados inicializado, execute:

```bash
python app.py
```

Por padrão, o servidor Flask sobe em modo de desenvolvimento em `http://127.0.0.1:5000`.

### 6. Acessar o sistema

- Página inicial (landing page): `http://127.0.0.1:5000/`
- Tela de login: `http://127.0.0.1:5000/login`
- Após autenticação, o usuário é redirecionado para o dashboard principal.

As demais telas (agenda, clientes, pets, usuários, salas e relatórios) são acessadas pelo menu lateral do próprio sistema.

---

## Equipe do projeto

| Integrante                         | Papel                    |
|------------------------------------|--------------------------|
| Augusto Azambuya M. da Silva       | Desenvolvedor Back-end   |
| Lucas Ramos Alves                  | Communicator             |
| Mateus Franceschet Pereira         | Desenvolvedor Front-end  |
| Patrick Vargas Santos              | Desenvolvedor Full-Stack |
| Roger Luiz do Nascimento Vesely    | Scrum Master             |

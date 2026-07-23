# Clinicorp ETL Web Interface — Design Spec

**Data:** 2026-07-23  
**Status:** Aprovado

---

## Visão Geral

Interface web para o time da Praxis disparar e monitorar importações de dados do Clinicorp para o banco PostgreSQL. Elimina a necessidade de acesso ao terminal para executar os scripts ETL.

---

## Contexto

O projeto atual é um conjunto de scripts Python que extraem dados da API do Clinicorp e carregam em um banco de dados. Hoje o banco é o Supabase; o plano é migrar para PostgreSQL local durante o desenvolvimento e depois para uma VPS em produção. A troca de banco deve ser transparente — apenas a `DATABASE_URL` no `.env` muda.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | React + Vite + TypeScript |
| Banco | PostgreSQL local → VPS |
| Auth | JWT (8h) + bcrypt |
| Logs ao vivo | WebSocket |
| Deploy local | `uvicorn` + `vite dev` |
| Deploy VPS | `gunicorn` + build estático servido pelo FastAPI |

---

## Estrutura de Arquivos

```
clinicorp/
└── web/
    ├── backend/
    │   ├── main.py          # FastAPI app, rotas e CORS
    │   ├── auth.py          # JWT: login, verificação de token
    │   ├── jobs.py          # Executor de scripts como subprocesso + streaming
    │   ├── db.py            # Conexão asyncpg, queries de contagem
    │   ├── users.json       # Usuários: [{email, password_hash}]
    │   └── requirements.txt # fastapi, uvicorn, asyncpg, bcrypt, python-jose
    └── frontend/
        ├── package.json
        ├── vite.config.ts
        └── src/
            ├── main.tsx
            ├── App.tsx          # Router: /login → /dashboard
            ├── api.ts           # fetch wrapper com JWT header
            ├── pages/
            │   ├── Login.tsx    # Formulário email + senha
            │   └── Dashboard.tsx
            └── components/
                ├── StatusCards.tsx    # Grid de cards com contagens do banco
                ├── OperationGrid.tsx  # Grade 3×2 de botões de operação
                └── JobLog.tsx         # Terminal ao vivo via WebSocket
```

---

## Layout

```
┌─────────────────────────────────────────────────────────┐
│  ⚡ Clinicorp ETL              admpraxis@praxis | Sair  │
├─────────────────────────────────────────────────────────┤
│  DASHBOARD                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  8.422   │ │  2.810   │ │  2.729   │ │   953    │  │
│  │Agendamen.│ │Pagamentos│ │  Faturas │ │Pacientes │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌────────────────┐ ┌───────────────────┐ │
│  │   140    │ │ 2026-07-23 ... │ │  ● Conectado      │ │
│  │Profission│ │  Última Sync   │ │ Status PostgreSQL  │ │
│  └──────────┘ └────────────────┘ └───────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  OPERAÇÕES                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │↻ Sync Incr. │ │📦 Carga Comp│ │👤 Pacientes  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │🩺 Profission│ │🔍 Integridade│ │⟳ Atualizar  │      │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│  LOG — Sync Incremental  ● em execução                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [OK] 9 novos patients inseridos (0 erros)       │   │
│  │ [OK] 15 novos professionals inseridos           │   │
│  │ [FALLBACK] 60 pacientes via agendamento         │   │
│  │ [OK] 87 agendamentos sincronizados ▌            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

O painel de log aparece apenas quando um job está em execução ou acabou de terminar. Enquanto nenhum job roda, a área fica oculta.

---

## API — Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/auth/login` | Recebe `{email, password}`, retorna JWT |
| `GET` | `/api/status` | Contagens de registros por tabela (requer JWT) |
| `POST` | `/api/jobs` | Dispara um job `{type: "incremental" \| "full_load" \| ...}` |
| `GET` | `/api/jobs/{id}` | Status do job (pending/running/done/error) |
| `WS` | `/api/jobs/{id}/logs` | Stream de stdout/stderr do job em tempo real |

### Tipos de job

| `type` | Script executado |
|---|---|
| `incremental` | `incremental_sync.py` |
| `full_load` | `load_complete_2020.py` |
| `patients` | `load_all_patients.py` |
| `professionals` | `load_professionals_direct.py` |
| `verify` | `verify_data_integrity.py` |

---

## Autenticação

- Login via `POST /api/auth/login` retorna token JWT com expiração de 8h
- Token enviado em todas as requisições no header `Authorization: Bearer <token>`
- Usuários armazenados em `web/backend/users.json` com senha em bcrypt
- Primeiro usuário criado via script CLI: `python -m backend.auth create-user`
- Sem cadastro de usuários pela UI — gerenciamento manual pelo arquivo

---

## Execução de Jobs

- Cada job roda como subprocesso Python (`asyncio.create_subprocess_exec`)
- stdout e stderr são capturados linha a linha e enviados ao cliente via WebSocket
- Apenas um job pode rodar por vez — botões ficam desabilitados durante execução
- Estado do job mantido em memória (dict em `jobs.py`); sem persistência de histórico nesta versão
- Timeout de 10 minutos por job; processo é encerrado se exceder

---

## Banco de Dados

- Conexão via `DATABASE_URL` no `.env` (formato: `postgresql://user:pass@host:port/db`)
- Backend usa `asyncpg` para queries de contagem assíncronas
- Os scripts ETL existentes continuam usando `psycopg2` diretamente via `DATABASE_URL`
- **Migração Supabase → PostgreSQL local:** ajustar `.env` e remover dependência do `supabase` client nos scripts ETL (substituir por `psycopg2`)
- **Migração local → VPS:** apenas trocar `DATABASE_URL`

---

## Deploy

### Desenvolvimento local
```bash
# Backend
cd web/backend && uvicorn main:app --reload --port 8000

# Frontend
cd web/frontend && npm run dev  # proxy para :8000
```

### VPS (produção)
```bash
# Build frontend
cd web/frontend && npm run build  # gera web/frontend/dist/

# Backend serve o build estático + API
cd web/backend && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

O FastAPI serve os arquivos estáticos do React em produção — sem Nginx necessário na primeira versão.

---

## Fora de Escopo (esta versão)

- Histórico persistente de execuções de jobs
- Múltiplos jobs simultâneos
- Notificações por email/Slack ao completar
- Agendamento automático (cron) pela UI
- Gerenciamento de usuários pela interface

---

## Ordem de Implementação

1. Backend: estrutura FastAPI + auth JWT + endpoint `/api/status`
2. Frontend: login page + dashboard com StatusCards
3. Backend: executor de jobs + WebSocket de logs
4. Frontend: OperationGrid + JobLog ao vivo
5. Migração dos scripts ETL de Supabase client para psycopg2
6. Testes end-to-end locais
7. Deploy na VPS

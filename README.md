# Hórus — Fiscalização de Dados Públicos

Sistema que cruza bases públicas brasileiras (CGU, BrasilAPI, TSE, Portal da Transparência) para detectar irregularidades em contratos federais: conflitos de interesse, retorno de favor, empresas sancionadas com contrato ativo.

**Projeto Integrador III — TADS / FAESA** (Prof. Howard Cruz).

## Stack

| Camada | Tecnologia |
|---|---|
| API HTTP | FastAPI 0.115 + Uvicorn |
| ORM / Banco | SQLAlchemy 2.0 + PostgreSQL 16 (Docker) |
| Grafo | Apache AGE (extensão Postgres) + NetworkX |
| Validação | Pydantic 2 |
| HTTP client | httpx |
| Dataframes | Polars + Pandas |
| ML | scikit-learn — Isolation Forest |
| NLP | spaCy (pt_core_news_lg) |
| Filas | Celery + Redis |
| Frontend | Next.js 15 + React 19 + Tailwind + Recharts + React Force Graph |
| Infra | Docker Compose |
| CI | GitHub Actions |

## Estrutura

```
Horus/
├── docker-compose.yml           # postgres+age + redis
├── docker/age-init.sql          # cria extensão AGE no boot
├── requirements.txt             # deps Python
├── .env                         # DATABASE_URL, REDIS_URL, API_PORTAL_TRANSPARENCIA_KEY
│
├── backend/
│   ├── ingestao.py              # ★ SCRIPT 1 — APIs públicas → Postgres
│   ├── cruzamento.py            # ★ SCRIPT 2 — cruza dados → resultados
│   │
│   ├── api/                     # FastAPI
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py            # 6 entidades SQLAlchemy
│   │   ├── schemas.py           # Pydantic
│   │   └── routers/
│   │       ├── cruzamentos.py
│   │       ├── dashboard.py
│   │       ├── busca.py
│   │       ├── grafo.py
│   │       ├── ml.py
│   │       └── nlp.py
│   │
│   ├── analytics/
│   │   ├── score.py             # score determinístico 0–100
│   │   ├── isolation_forest.py  # sklearn (7 features)
│   │   ├── fuzzy_match.py       # rapidfuzz (cruzamento por nome)
│   │   ├── grafo.py             # NetworkX a partir das tabelas
│   │   └── nlp.py               # spaCy sobre objetos de contrato
│   │
│   ├── ingestao_lib/
│   │   ├── cgu.py               # CEIS + contratos federais
│   │   ├── siape.py             # servidores SIAPE
│   │   ├── brasilapi.py         # QSA
│   │   └── tse.py               # doações eleitorais
│   │
│   └── tasks/
│       ├── celery_app.py        # Celery + beat schedule
│       └── jobs.py              # tasks (re-ingestão semanal, scores diários)
│
├── frontend/                    # Next.js 15
│   ├── app/
│   │   ├── page.tsx             # dashboard com KPIs + Recharts
│   │   └── grafo/page.tsx       # Force Graph
│   ├── components/
│   │   ├── KPICard.tsx
│   │   ├── TopEmpresasChart.tsx
│   │   ├── DistribuicaoSancoes.tsx
│   │   └── GrafoForce.tsx
│   └── lib/api.ts
│
├── .github/workflows/ci.yml
├── docs/                        # PDFs do edital + plano
└── sources/                     # referências visuais
```

## Como rodar

### 1. Subir infraestrutura (Postgres com AGE + Redis)

```bash
docker compose up -d
```

Postgres em `localhost:5433`, Redis em `localhost:6380`. A extensão Apache AGE é criada automaticamente na 1ª subida via `docker/age-init.sql`.

### 2. Instalar dependências Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg     # modelo NLP (~500 MB)
```

### 3. Ingestão de dados — pipeline em duas camadas

```
  SITE  ─→  data/raw/*.csv  ─→  Postgres
            (bronze)             (silver)
```

A camada **bronze** (CSV em `data/raw/`) preserva o dado bruto exatamente como
veio da API, permite reprocessar sem bater na fonte de novo, vira **dataset
reproduzível** pra análise de dados, e funciona como evidência (você anexa o
CSV no relatório do PI III).

A camada **silver** (Postgres) é o dado normalizado, pronto pros cruzamentos.

#### Comandos

```bash
# camada bronze (API → CSV)
python -m backend.ingestao baixar-ceis --paginas 30
python -m backend.ingestao baixar-contratos --max-empresas 100

# camada silver (CSV → BD) — pega o CSV mais recente automaticamente
python -m backend.ingestao carregar-ceis
python -m backend.ingestao carregar-contratos

# OU fluxo completo (4 passos em sequência):
python -m backend.ingestao tudo

# inspeção
python -m backend.ingestao listar-csvs

# fontes secundárias (ainda direto pro BD, sem camada CSV)
python -m backend.ingestao servidores --mes-ano 202602 --top 1000
python -m backend.ingestao qsa
python -m backend.ingestao doacoes
```

Os CSVs gerados são versionados por data: `ceis_2026-05-10.csv`,
`contratos_2026-05-10.csv` — assim você acompanha a evolução do dataset.

### 4. Cruzamentos (Script 2)

```bash
python -m backend.cruzamento conflito                  # cruzamento 1 — CPF
python -m backend.cruzamento conflito-nome             # cruzamento 1 — fuzzy
python -m backend.cruzamento retorno-favor             # cruzamento 2
python -m backend.cruzamento empresa-sancionada        # cruzamento 5
python -m backend.cruzamento todos --out resultados.json
python -m backend.cruzamento score                     # recalcula scores
python -m backend.cruzamento ml-treinar
python -m backend.cruzamento ml-anomalias
```

### 5. Subir a API

```bash
uvicorn backend.api.main:app --reload
```

Swagger em http://localhost:8000/docs.

### 6. Subir o frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard em http://localhost:3000. As chamadas `/api/...` são proxied para o backend em `:8000` (config no `next.config.js`).

### 7. (Opcional) Subir Celery worker + beat

```bash
celery -A backend.tasks.celery_app worker --loglevel=info       # worker
celery -A backend.tasks.celery_app beat --loglevel=info         # scheduler
```

Tasks agendadas:
- Re-ingestão de CEIS toda **segunda 03:00**
- Recálculo de scores **diariamente 04:00**

## Cruzamentos (5 do escopo PI III)

| # | Cruzamento | Status | Endpoint |
|---|---|---|---|
| 1 | Político sócio de empresa contratada | ✅ (CPF) + ✅ (fuzzy) | `/cruzamentos/conflito-interesse[-por-nome]` |
| 2 | Doador → contrato (retorno de favor) | ✅ | `/cruzamentos/retorno-favor` |
| 3 | Familiar de servidor → contrato (nepotismo) | ⏳ aguardando fonte | — |
| 4 | Patrimônio × salário (enriquecimento) | ⏳ Portal só publica em PDF | — |
| 5 | Empresa CEIS × contrato | ✅ | `/cruzamentos/empresa-sancionada` |

## Ciência de dados

- **Score determinístico** (`analytics/score.py`) — agente e empresa, 0–100, baseado em 5 critérios cada
- **Isolation Forest** (`analytics/isolation_forest.py`) — 7 features, detecção de anomalias multivariadas em empresas
- **NetworkX** (`analytics/grafo.py`) — grafo direcionado agente↔empresa↔órgão, métricas de centralidade
- **spaCy** (`analytics/nlp.py`) — entidades nomeadas em objetos de contrato (PER/ORG/LOC)
- **Fuzzy match** (`analytics/fuzzy_match.py`) — rapidfuzz `token_sort_ratio` para cruzamento por nome (LGPD mascara CPF)

## Banco de dados — 6 tabelas

```
agentes_publicos    (cpf PK, nome, orgao, cargo, remuneracao, score_risco)
empresas            (cnpj PK, razao_social, situacao, score_risco)
socios_empresa      (id PK, cnpj_empresa FK, cpf_socio, nome_socio, qualificacao)
contratos_publicos  (id PK, cnpj_fornecedor FK, orgao_contratante, valor, objeto, datas)
ceis                (id PK, cnpj FK, tipo_sancao, orgao_sancionador, datas)
doacoes_eleitorais  (id PK, cnpj_doador, cpf_candidato, valor, ano_eleicao, cargo)
```

Acesso direto: `docker exec -it horus-db psql -U horus -d horus`.

## Limitações

- CPFs em fontes públicas vêm mascarados por LGPD — cruzamento 1 cai pra fuzzy match por nome (validar antes de acusar).
- Rate-limit CGU: 90 req/min. BrasilAPI: dinâmico (esperar ~30% de erro 429 numa rodada).
- TSE pode estar fora do ar (CDN em manutenção) — usar `--csv-local` se baixar manualmente.
- Cruzamentos 3 e 4 ficam para evolução: dependem de fontes que o Portal só publica em PDF ou que exigem cruzamento jurídico.

## Documentação

- `docs/horus_v2.pdf` — escopo aprovado pelo orientador
- `docs/document_pdf.pdf` — edital oficial do PI III
- `docs/HORUS_PLANO.md` — plano de execução
- `docs/api_portal_transparencia.md` — notas da API CGU

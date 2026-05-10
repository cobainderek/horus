# Hórus — Fiscalização Pública

Script Python que baixa o **CEIS** (Cadastro de Empresas Inidôneas e Suspensas) da CGU, cruza com **contratos federais** do Portal da Transparência, e gera uma página estática mostrando empresas sancionadas que ainda têm contrato ativo — junto com estatísticas descritivas dos valores envolvidos.

Projeto Integrador III — TADS / FAESA (Prof. Howard Cruz).

## Stack

- **Python 3.11+** — SQLAlchemy 2.0, httpx, psycopg2, python-dotenv
- **PostgreSQL 16** — em Docker
- **HTML/CSS estático** — sem framework, sem build, abre direto no navegador

## Como rodar

```bash
# 1. subir o Postgres
docker compose up -d

# 2. criar o venv e instalar deps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. rodar o pipeline (ingestão + cruzamento + gera dados.json)
python horus.py

# 4. abrir a página no navegador
xdg-open index.html
```

## Estrutura

```
Horus/
├── horus.py             # pipeline completo: CGU → Postgres → dados.json
├── index.html           # página estática (lê dados.json)
├── style.css
├── dados.json           # gerado por horus.py
├── docker-compose.yml   # só Postgres (porta 5433)
├── requirements.txt     # 4 dependências
├── .env                 # API_PORTAL_TRANSPARENCIA_KEY + DATABASE_URL
└── docs/                # PDFs do edital PI III
```

## O que o pipeline faz

1. **Ingere CEIS** — baixa páginas da API CGU `/api-de-dados/ceis` (15 itens por página) e grava em `ceis` + `empresas`.
2. **Ingere contratos** — para cada empresa do CEIS, consulta `/api-de-dados/contratos/cpf-cnpj` e grava em `contratos_publicos`.
3. **Cruza e analisa** — roda uma query SQL com `JOIN ceis × contratos_publicos`, calcula KPIs e estatísticas descritivas, e escreve `dados.json`.

## O que a página mostra

- **4 KPIs** — total no CEIS, quantas têm contrato, valor total suspeito, % do CEIS contratando
- **Top 20 empresas** — razão social, sanções, # contratos, valor total
- **Top 10 órgãos** — quem mais contrata sancionadas
- **Estatística descritiva** dos valores — média, mediana, mín, máx, desvio padrão
- **Distribuição de tipos de sanção** — quantos "Inidônea", "Suspensa", etc.

## Argumentos do CLI

```bash
python horus.py --paginas 50              # baixa 50 páginas de CEIS (default 30)
python horus.py --paginas-contrato 3      # 3 páginas por empresa (default 2)
python horus.py --so-analise              # pula ingestão, só regera dados.json
```

## Banco de dados (3 tabelas)

| Tabela | Conteúdo |
|---|---|
| `empresas` | cnpj, razão social |
| `ceis` | cnpj, tipo_sancao, orgao_sancionador, datas |
| `contratos_publicos` | cnpj_fornecedor, orgao_contratante, valor, objeto |

Acesso direto via psql:

```bash
docker exec -it horus-db psql -U horus -d horus
```

## Limitações conhecidas

- Cobertura: apenas contratos **federais** (escopo CGU). Não inclui estaduais/municipais.
- Rate-limit da CGU: 90 req/min. Ingestão completa (~447 empresas) leva 5–10 min.
- O cruzamento detecta **co-ocorrência**, não causalidade: a empresa pode ter contrato anterior à sanção. A análise temporal fica para evolução futura.
- Chave da CGU obrigatória — cadastro gratuito em https://portaldatransparencia.gov.br/api-de-dados/cadastrar.

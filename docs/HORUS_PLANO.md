# 🏛️ HÓRUS — Plano de Desenvolvimento

> Sistema Inteligente de Fiscalização de Dados Públicos  
> Projeto Integrador III — FAESA / TADS — Prof. Howard Cruz  
> Dev: Derek Cobain

---

## 📌 Visão Geral

| Item | Detalhe |
|------|---------|
| Stack Backend | Python + FastAPI + PostgreSQL + Polars |
| Stack Frontend | Next.js 15 + Tailwind CSS + Recharts |
| IA / Dados | scikit-learn + spaCy |
| Infra | Docker Compose + GitHub |
| Entrega 2 | 04–08 de maio de 2026 |
| Entrega 3 (MVP) | 08–12 de junho de 2026 |

---

## 🗓️ Sua Rotina Real

| Período | Tempo disponível |
|---------|-----------------|
| Seg–Sex (manhã, 6h–7h) | 1h — antes do trabalho |
| Seg–Sex (noite, após facul) | Cansado demais — **não force** |
| Sábado | 4–6h — sessão principal |
| Domingo | 3–4h — revisão + próxima sprint |

> **Regra de ouro:** Nos dias de semana, faça só **1 tarefa pequena** por dia.  
> Não tente resolver tudo numa noite. Consistência bate intensidade.

---

## 🏁 Marcos do Projeto

```
28/03 ────── Sprint 0: Ambiente ────── 06/04
07/04 ────── Sprint 1: Backend Base ── 20/04
21/04 ────── Sprint 2: Dados Reais ─── 04/05
04/05 ──────────── ⭐ ENTREGA 2 ─────────────
05/05 ────── Sprint 3: IA + KPIs ───── 25/05
26/05 ────── Sprint 4: MVP Final ───── 08/06
08/06 ──────────── ⭐ ENTREGA 3 ─────────────
```

---

## 🔧 SPRINT 0 — Ambiente e Fundação
**Período:** 28/03 – 06/04 (fim de semana + dias úteis)  
**Objetivo:** Ter tudo rodando na máquina, zero código de negócio ainda.  
**Mentalidade:** Não pule essa etapa. Dev sem ambiente bom é sofrimento garantido.

---

### 📅 Semana 1 (28/03 – 30/03) — Sábado e Domingo

#### Sábado 28/03 — Setup Backend (3–4h)

- [ ] Instalar **Python 3.12** → https://python.org/downloads
- [ ] Instalar **VS Code** → https://code.visualstudio.com
  - Extensões: Python, Pylance, Docker, GitLens, REST Client
- [ ] Instalar **Docker Desktop para Windows** → https://docker.com/products/docker-desktop
- [ ] Criar pasta do projeto: `C:\projetos\horus`
- [ ] Abrir terminal no VS Code e rodar:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  pip install fastapi uvicorn sqlalchemy psycopg2-binary polars python-dotenv
  ```
- [ ] Criar estrutura de pastas:
  ```
  horus/
  ├── backend/
  │   ├── app/
  │   │   ├── main.py
  │   │   ├── database.py
  │   │   └── routers/
  │   ├── requirements.txt
  │   └── .env
  ├── frontend/
  ├── docker-compose.yml
  └── README.md
  ```
- [ ] Criar `backend/app/main.py` com Hello World FastAPI:
  ```python
  from fastapi import FastAPI

  app = FastAPI(title="Hórus API")

  @app.get("/")
  def root():
      return {"msg": "Hórus online 👁️"}
  ```
- [ ] Rodar: `uvicorn app.main:app --reload` e abrir `http://localhost:8000`
- [ ] ✅ Checkpoint: viu o JSON no navegador? Backend vivo.

---

#### Domingo 29/03 — Setup Frontend + Docker (3h)

- [ ] Criar o projeto Next.js:
  ```bash
  cd horus/frontend
  npx create-next-app@latest . --typescript --tailwind --app
  ```
- [ ] Rodar: `npm run dev` e abrir `http://localhost:3000`
- [ ] Criar `docker-compose.yml` na raiz:
  ```yaml
  version: '3.8'
  services:
    db:
      image: postgres:16
      environment:
        POSTGRES_DB: horus
        POSTGRES_USER: horus
        POSTGRES_PASSWORD: horus123
      ports:
        - "5432:5432"
      volumes:
        - pgdata:/var/lib/postgresql/data

    redis:
      image: redis:7-alpine
      ports:
        - "6379:6379"

  volumes:
    pgdata:
  ```
- [ ] Rodar: `docker compose up -d`
- [ ] Instalar DBeaver (client visual de banco): https://dbeaver.io
- [ ] Conectar DBeaver ao PostgreSQL local (host: localhost, porta: 5432, user: horus, pass: horus123)
- [ ] ✅ Checkpoint: banco rodando, frontend rodando, backend rodando. Os três de pé.

---

### 📅 Dias Úteis 31/03 – 04/04 (1h/dia, de manhã)

#### Segunda 31/03 — Git e GitHub (1h)
- [ ] Criar repositório no GitHub: `horus-fiscalizacao`
- [ ] Criar `.gitignore` (Python + Node)
- [ ] Commit inicial:
  ```bash
  git init
  git add .
  git commit -m "feat: estrutura inicial do projeto"
  git branch -M main
  git remote add origin https://github.com/SEU_USER/horus-fiscalizacao
  git push -u origin main
  ```
- [ ] Adicionar professor como colaborador: `howardroatti`

#### Terça 01/04 — SQLAlchemy: primeiro modelo (1h)
- [ ] Criar `backend/app/database.py`:
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker, DeclarativeBase
  import os

  DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://horus:horus123@localhost/horus")

  engine = create_engine(DATABASE_URL)
  SessionLocal = sessionmaker(bind=engine)

  class Base(DeclarativeBase):
      pass
  ```
- [ ] Criar `backend/app/models.py` com modelo `AgentePublico`:
  ```python
  from sqlalchemy import Column, String, Float, DateTime
  from .database import Base

  class AgentePublico(Base):
      __tablename__ = "agentes_publicos"
      cpf = Column(String, primary_key=True)
      nome = Column(String, nullable=False)
      orgao = Column(String)
      cargo = Column(String)
      remuneracao = Column(Float)
      score_risco = Column(Float, default=0.0)
  ```

#### Quarta 02/04 — Criar tabelas no banco (1h)
- [ ] Adicionar ao `main.py`:
  ```python
  from .database import Base, engine
  from . import models

  Base.metadata.create_all(bind=engine)
  ```
- [ ] Rodar o backend e verificar no DBeaver se a tabela foi criada
- [ ] Commit: `feat: modelo AgentePublico e conexão com banco`

#### Quinta 03/04 — Primeiro endpoint real (1h)
- [ ] Criar `backend/app/routers/agentes.py`:
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.orm import Session
  from ..database import SessionLocal
  from ..models import AgentePublico

  router = APIRouter(prefix="/agentes", tags=["Agentes"])

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()

  @router.get("/")
  def listar_agentes(db: Session = Depends(get_db)):
      return db.query(AgentePublico).limit(50).all()
  ```
- [ ] Registrar router no `main.py`
- [ ] Testar em `http://localhost:8000/docs` (Swagger automático do FastAPI)

#### Sexta 04/04 — Folga ou revisão (1h)
- [ ] Revisar o que foi feito na semana
- [ ] Anotar dúvidas aqui no Obsidian
- [ ] Commit geral com tudo que ficou pendente

---

### 📅 Fim de Semana 05–06/04

#### Sábado 05/04 — Primeira ingestão real de dados (4h)

> Esse é o momento em que o Hórus começa a ter dados de verdade.

- [ ] Criar `backend/app/ingestao/` (pasta)
- [ ] Criar `backend/app/ingestao/portal_transparencia.py`:
  ```python
  import httpx
  import polars as pl

  BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
  HEADERS = {"chave-api-dados": "SUA_CHAVE_AQUI"}
  # Cadastre-se em: https://portaldatransparencia.gov.br/api-de-dados/cadastrar

  def buscar_servidores(pagina: int = 1):
      url = f"{BASE_URL}/servidores"
      params = {"pagina": pagina}
      response = httpx.get(url, headers=HEADERS, params=params, timeout=30)
      response.raise_for_status()
      return response.json()

  def processar_servidores(dados: list) -> pl.DataFrame:
      return pl.DataFrame(dados).select([
          pl.col("cpf").alias("cpf"),
          pl.col("nome").alias("nome"),
          pl.col("orgaoExercicio").struct.field("nome").alias("orgao"),
          pl.col("cargo").alias("cargo"),
          pl.col("remuneracaoBasicaBruta").alias("remuneracao"),
      ])
  ```
- [ ] Cadastrar chave gratuita na API do Portal da Transparência
- [ ] Testar busca e ver os dados chegando
- [ ] ✅ Checkpoint: primeiros servidores públicos no terminal

#### Domingo 06/04 — Salvar dados no banco (3h)
- [ ] Criar função que salva o DataFrame Polars no PostgreSQL:
  ```python
  def salvar_servidores(df: pl.DataFrame, db: Session):
      for row in df.to_dicts():
          agente = AgentePublico(**row)
          db.merge(agente)  # upsert: atualiza se já existe
      db.commit()
  ```
- [ ] Criar endpoint POST `/ingestao/servidores` que dispara a coleta
- [ ] Testar e verificar no DBeaver os dados salvos
- [ ] Commit: `feat: ingestão de servidores do Portal da Transparência`

---

## 🔧 SPRINT 1 — Backend Base Completo
**Período:** 07/04 – 20/04  
**Objetivo:** API com os 5 cruzamentos principais funcionando, dados reais no banco.

---

### 📅 Semana 2 (07/04 – 11/04)

#### Segunda 07/04 — Modelo Empresa (1h)
- [ ] Criar modelo `Empresa` no `models.py`:
  ```python
  class Empresa(Base):
      __tablename__ = "empresas"
      cnpj = Column(String, primary_key=True)
      razao_social = Column(String)
      situacao = Column(String)
      data_abertura = Column(String)
      score_risco = Column(Float, default=0.0)

  class SocioEmpresa(Base):
      __tablename__ = "socios_empresa"
      id = Column(String, primary_key=True)
      cnpj_empresa = Column(String, ForeignKey("empresas.cnpj"))
      cpf_socio = Column(String)
      nome_socio = Column(String)
      qualificacao = Column(String)
  ```

#### Terça 08/04 — Ingestão CNPJ (1h)
> O dump da Receita Federal é enorme (~50GB). Vamos usar uma amostra.
- [ ] Baixar amostra dos dados CNPJ: https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj
- [ ] Criar `backend/app/ingestao/cnpj.py` para processar o CSV com Polars:
  ```python
  import polars as pl

  def carregar_empresas(caminho_csv: str) -> pl.DataFrame:
      return pl.read_csv(
          caminho_csv,
          separator=";",
          encoding="latin1",
          infer_schema_length=1000,
      ).select([
          pl.col("CNPJ_BASICO").alias("cnpj"),
          pl.col("RAZAO_SOCIAL").alias("razao_social"),
          pl.col("SITUACAO_CADASTRAL").alias("situacao"),
          pl.col("DATA_INICIO_ATIVIDADE").alias("data_abertura"),
      ])
  ```

#### Quarta 09/04 — Modelo Contrato (1h)
- [ ] Criar modelo `ContratoPublico`:
  ```python
  class ContratoPublico(Base):
      __tablename__ = "contratos_publicos"
      id = Column(String, primary_key=True)
      cnpj_fornecedor = Column(String, ForeignKey("empresas.cnpj"))
      orgao_contratante = Column(String)
      valor = Column(Float)
      data_inicio = Column(String)
      data_fim = Column(String)
      objeto = Column(String)
  ```

#### Quinta 10/04 — Ingestão contratos (1h)
- [ ] Criar `backend/app/ingestao/contratos.py` usando API do Portal:
  ```python
  def buscar_contratos(orgao: str, pagina: int = 1):
      url = f"{BASE_URL}/contratos"
      params = {"orgaoSuperior": orgao, "pagina": pagina}
      response = httpx.get(url, headers=HEADERS, params=params, timeout=30)
      return response.json()
  ```

#### Sexta 11/04 — Commit semanal (1h)
- [ ] Commit com modelos e ingestões da semana
- [ ] Atualizar README com instruções de como rodar o projeto

---

### 📅 Fim de Semana 12–13/04

#### Sábado 12/04 — CRUZAMENTO 1: Político → Empresa → Contrato (4h)

> Esse é o coração do Hórus. Quando funcionar, o projeto já tem valor real.

- [ ] Criar `backend/app/cruzamentos/conflito_interesse.py`:
  ```python
  import polars as pl
  from sqlalchemy.orm import Session

  def detectar_conflito_interesse(db: Session) -> pl.DataFrame:
      """
      Retorna agentes públicos que são sócios de empresas
      que possuem contratos com o mesmo órgão onde trabalham.
      """
      query = """
      SELECT
          a.nome AS agente,
          a.cpf,
          a.orgao,
          e.razao_social AS empresa,
          e.cnpj,
          c.valor,
          c.objeto,
          c.orgao_contratante
      FROM agentes_publicos a
      JOIN socios_empresa s ON s.cpf_socio = a.cpf
      JOIN empresas e ON e.cnpj = s.cnpj_empresa
      JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
      WHERE c.orgao_contratante ILIKE '%' || a.orgao || '%'
      ORDER BY c.valor DESC
      """
      import pandas as pd
      resultado = pd.read_sql(query, db.bind)
      return pl.from_pandas(resultado)
  ```
- [ ] Criar endpoint `GET /cruzamentos/conflito-interesse`
- [ ] Testar com dados reais — pode não ter resultado ainda, normal
- [ ] ✅ Checkpoint: primeiro cruzamento SQL funcionando

#### Domingo 13/04 — CRUZAMENTO 2: Doação → Contrato (3h)
- [ ] Criar modelo `DoacaoEleitoral`:
  ```python
  class DoacaoEleitoral(Base):
      __tablename__ = "doacoes_eleitorais"
      id = Column(String, primary_key=True)
      cnpj_doador = Column(String)
      cpf_candidato = Column(String)
      valor = Column(Float)
      ano_eleicao = Column(Integer)
  ```
- [ ] Criar `backend/app/cruzamentos/retorno_favor.py`:
  ```python
  def detectar_retorno_favor(db: Session) -> pl.DataFrame:
      """
      Empresas que doaram pra campanha e depois ganharam contratos.
      """
      query = """
      SELECT
          d.cnpj_doador,
          e.razao_social,
          d.valor AS valor_doacao,
          d.ano_eleicao,
          c.valor AS valor_contrato,
          c.data_inicio,
          c.orgao_contratante
      FROM doacoes_eleitorais d
      JOIN empresas e ON e.cnpj = d.cnpj_doador
      JOIN contratos_publicos c ON c.cnpj_fornecedor = d.cnpj_doador
      WHERE CAST(SUBSTR(c.data_inicio, 1, 4) AS INTEGER) >= d.ano_eleicao
      ORDER BY c.valor DESC
      """
      import pandas as pd
      return pl.from_pandas(pd.read_sql(query, db.bind))
  ```

---

### 📅 Semana 3 (14/04 – 18/04)

#### Segunda 14/04 — Score de risco (1h)
- [ ] Criar `backend/app/analytics/score.py`:
  ```python
  def calcular_score_agente(cpf: str, db: Session) -> float:
      score = 0.0
      # +40 pontos se é sócio de empresa com contrato público
      # +30 pontos se empresa recebeu doação e depois ganhou contrato
      # +20 pontos se empresa está no CEIS
      # +10 pontos por cada contrato acima de R$100k
      return min(score, 100.0)  # máximo 100
  ```
- [ ] Implementar a lógica de pontuação consultando o banco

#### Terça 15/04 — Endpoint de busca por CPF/CNPJ (1h)
- [ ] Criar endpoint `GET /busca/{identificador}`:
  - Se 11 dígitos → busca agente público
  - Se 14 dígitos → busca empresa
  - Retorna: dados + score + cruzamentos encontrados

#### Quarta 16/04 — CEIS Integration (1h)
- [ ] Criar ingestão da lista CEIS (empresas sancionadas):
  ```python
  def buscar_ceis(pagina: int = 1):
      url = f"{BASE_URL}/ceis"
      response = httpx.get(url, headers=HEADERS, params={"pagina": pagina})
      return response.json()
  ```
- [ ] Adicionar verificação CEIS ao score de risco

#### Quinta 17/04 — Testes dos endpoints (1h)
- [ ] Testar todos os endpoints no Swagger (`/docs`)
- [ ] Corrigir erros encontrados
- [ ] Documentar endpoints no README

#### Sexta 18/04 — Buffer e commit (1h)
- [ ] Resolver qualquer pendência da semana
- [ ] Commit: `feat: cruzamentos 1 e 2, score de risco, busca por CPF/CNPJ`

---

### 📅 Fim de Semana 19–20/04

#### Sábado 19/04 — Frontend: estrutura e dashboard (5h)

> Agora começa o que o professor vai ver na tela.

- [ ] Instalar dependências do frontend:
  ```bash
  cd frontend
  npm install recharts axios lucide-react
  npm install -D @types/node
  ```
- [ ] Criar estrutura de páginas:
  ```
  frontend/app/
  ├── page.tsx              ← Dashboard principal
  ├── busca/page.tsx        ← Busca por CPF/CNPJ
  ├── cruzamentos/page.tsx  ← Lista de irregularidades
  └── components/
      ├── KPICard.tsx
      ├── RiscoGauge.tsx
      └── TabelaIrregularidades.tsx
  ```
- [ ] Criar `KPICard.tsx`:
  ```tsx
  interface KPICardProps {
    titulo: string
    valor: string | number
    descricao: string
    cor?: string
  }

  export function KPICard({ titulo, valor, descricao, cor = "blue" }: KPICardProps) {
    return (
      <div className={`bg-white border-l-4 border-${cor}-600 rounded-lg p-6 shadow-sm`}>
        <p className="text-sm text-gray-500">{titulo}</p>
        <p className="text-3xl font-bold text-gray-800 mt-1">{valor}</p>
        <p className="text-xs text-gray-400 mt-1">{descricao}</p>
      </div>
    )
  }
  ```
- [ ] Criar página principal com 4 KPIs:
  - Total de agentes monitorados
  - Total de empresas analisadas
  - Irregularidades detectadas
  - Valor total em contratos suspeitos

#### Domingo 20/04 — Frontend: página de busca (3h)
- [ ] Criar `busca/page.tsx` com campo de busca CPF/CNPJ
- [ ] Conectar ao endpoint do backend
- [ ] Exibir resultado: nome, órgão, score de risco, cruzamentos encontrados
- [ ] Criar componente `RiscoGauge` — barra de 0 a 100 colorida (verde/amarelo/vermelho)
- [ ] ✅ Checkpoint: digitei um CPF e vi o score aparecer

---

## 🔧 SPRINT 2 — Dados Reais + Protótipo Entrega 2
**Período:** 21/04 – 04/05  
**Objetivo:** Sistema com dados reais, dashboard funcional, pronto pra gravar vídeo.

---

### 📅 Semana 4 (21/04 – 25/04)

#### Segunda 21/04 — Tabela de irregularidades (1h)
- [ ] Criar `TabelaIrregularidades.tsx` com colunas:
  - Agente | Empresa | Tipo de Irregularidade | Valor | Score
- [ ] Alimentar com dados dos cruzamentos reais
- [ ] Ordenar por score de risco (maior primeiro)

#### Terça 22/04 — Gráfico de distribuição de risco (1h)
- [ ] Usar Recharts pra criar gráfico de barras:
  - Eixo X: faixa de score (0-20, 21-40, 41-60, 61-80, 81-100)
  - Eixo Y: quantidade de agentes em cada faixa
  ```tsx
  import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
  ```

#### Quarta 23/04 — Página de cruzamentos (1h)
- [ ] Criar filtros na página de cruzamentos:
  - Por tipo (conflito de interesse, retorno de favor, CEIS)
  - Por valor mínimo de contrato
  - Por órgão

#### Quinta 24/04 — Polimento visual (1h)
- [ ] Adicionar header com logo e nome "Hórus"
- [ ] Adicionar loading states nas requisições
- [ ] Responsividade básica (mobile)

#### Sexta 25/04 — Buffer (1h)
- [ ] Resolver bugs pendentes
- [ ] Commit geral

---

### 📅 Fim de Semana 26–27/04

#### Sábado 26/04 — Dados reais em escala (4h)
- [ ] Rodar ingestão completa do Tier 1:
  - Portal da Transparência: 200+ servidores federais
  - CNPJ: amostra de 1000 empresas do ES
  - Contratos: últimos 12 meses
  - CEIS: lista completa (é menor, ~50k registros)
- [ ] Verificar quantas irregularidades o sistema detecta com dados reais
- [ ] Ajustar queries se necessário

#### Domingo 27/04 — Preparação do vídeo (3h)
- [ ] Criar roteiro do vídeo de demonstração (5–8 minutos):
  ```
  1. (30s) Apresentação: "Esse é o Hórus..."
  2. (1m)  Dashboard: KPIs com dados reais
  3. (2m)  Busca por CPF: mostrar score e cruzamentos
  4. (2m)  Tabela de irregularidades: filtrar, ordenar
  5. (1m)  Explicar a lógica dos cruzamentos
  6. (30s) Próximos passos
  ```
- [ ] Gravar rascunho pra ver como fica

---

### 📅 Semana 5 (28/04 – 02/05)

#### Segunda–Quarta (1h/dia) — Ajustes pós-rascunho
- [ ] Corrigir o que ficou feio no vídeo rascunho
- [ ] Melhorar mensagens de erro
- [ ] Adicionar tooltips explicativos nas telas

#### Quinta 01/05 — Feriado 🎉
- [ ] Se tiver ânimo: gravar o vídeo final
- [ ] Se não: descanso total, você merece

#### Sexta 02/05 — Vídeo final (2h)
- [ ] Gravar vídeo final (OBS Studio ou Loom)
- [ ] Subir no YouTube (unlisted) ou Google Drive
- [ ] Adicionar link no README do GitHub

---

### 📅 Fim de Semana 03–04/05

#### Sábado 03/05 — Documentação da Entrega 2 (3h)
- [ ] Atualizar README com:
  - Como instalar e rodar
  - Endpoints disponíveis
  - Screenshots do sistema
- [ ] Commit final: `entrega-2: protótipo funcional com análise preliminar`
- [ ] Tag no git: `git tag v0.2.0 && git push origin v0.2.0`

#### Domingo 04/05 — ⭐ ENTREGA 2
- [ ] Enviar link do repositório pro professor
- [ ] Enviar link do vídeo
- [ ] Respirar fundo. Você chegou na metade do projeto.

---

## 🔧 SPRINT 3 — IA e KPIs Avançados
**Período:** 05/05 – 25/05  
**Objetivo:** Isolation Forest pra detecção de anomalias, NLP básico no DOU, dashboard melhorado.

> Essa sprint você já tem mais fôlego pois a Entrega 2 passou.

### Tarefas principais (detalhar quando chegar aqui)

- [ ] **Isolation Forest:** detectar agentes com padrão financeiro anômalo
  ```python
  from sklearn.ensemble import IsolationForest
  # Features: remuneração, valor_contratos_empresa, num_contratos, score_ceis
  modelo = IsolationForest(contamination=0.05, random_state=42)
  ```
- [ ] **NLP com spaCy:** extrair nomes de agentes e empresas do Diário Oficial
- [ ] **Grafo de relacionamentos:** visualização com React Force Graph
- [ ] **Filtros avançados:** por estado, por órgão, por período
- [ ] **Exportar relatório:** PDF com as irregularidades encontradas

---

## 🔧 SPRINT 4 — MVP Final
**Período:** 26/05 – 08/06  
**Objetivo:** Sistema polido, documentado, pronto pra apresentar.

### Tarefas principais (detalhar quando chegar aqui)

- [ ] Polimento geral de UI
- [ ] Documentação técnica completa no GitHub
- [ ] Vídeo final de demonstração
- [ ] Deploy no Railway (backend) + Vercel (frontend)
- [ ] **Tag:** `git tag v1.0.0`

---

## 🆘 Quando Travar — O que Fazer

> Todo dev trava. A questão é quanto tempo você perde travado.

1. **Lê o erro com calma.** 90% das vezes a resposta está na mensagem de erro.
2. **Copia o erro e cola no ChatGPT ou Claude.** Sem vergonha.
3. **Procura no Stack Overflow.** Alguém já teve esse problema.
4. **30 minutos travado no mesmo problema = para, anota a dúvida, vai fazer outra task.**
5. **Me manda aqui no Claude com o código e o erro.** Resolvo junto com você.

---

## 📚 Recursos de Consulta Rápida

| Tecnologia | Link |
|-----------|------|
| FastAPI | https://fastapi.tiangolo.com |
| Polars | https://docs.pola.rs |
| SQLAlchemy | https://docs.sqlalchemy.org |
| Next.js | https://nextjs.org/docs |
| Recharts | https://recharts.org |
| Portal Transparência API | https://api.portaldatransparencia.gov.br |
| Dados CNPJ | https://dados.gov.br |
| Docker Compose | https://docs.docker.com/compose |

---

## 📝 Diário de Bordo

> Use essa seção pra anotar o que fez em cada dia. Ajuda a não perder o fio.

### 28/03
- [ ] O que fiz:
- [ ] O que travou:
- [ ] Próxima tarefa:

### 29/03
- [ ] O que fiz:
- [ ] O que travou:
- [ ] Próxima tarefa:

---

## 🏷️ Commits Padrão

Use esse padrão nos commits pra ficar profissional:

```
feat: nova funcionalidade
fix: correção de bug
docs: atualização de documentação
refactor: refatoração sem mudar comportamento
chore: configuração, dependências
```

Exemplos:
```bash
git commit -m "feat: endpoint de busca por CPF com score de risco"
git commit -m "fix: corrige cálculo de score quando não há contratos"
git commit -m "docs: adiciona instruções de instalação no README"
```

---

*Última atualização: 28/03/2026*  
*"O olho que tudo vê — um commit de cada vez."* 👁️

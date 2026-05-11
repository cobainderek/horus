# Roteiro — Vídeo demo Entrega 2

**Duração-alvo:** 3 a 5 minutos
**Formato:** Tela cheia gravando o navegador + terminal (OBS Studio, GNOME Screen Recorder, ou similar)
**Áudio:** Você narrando

---

## Antes de gravar (checklist 2 min)

```bash
# 1. confira que tudo tá no ar
docker ps          # horus-db + horus-redis healthy
curl http://localhost:8001/      # backend retorna JSON
curl http://localhost:3000/      # frontend HTTP 200

# 2. tenha as 3 abas abertas no navegador:
#    - http://localhost:3000           (dashboard principal)
#    - http://localhost:8001/docs      (swagger)
#    - https://portaldatransparencia.gov.br/sancoes/ceis   (fonte oficial)

# 3. terminal aberto em ~/Horus com o repo
```

---

## ROTEIRO — 5 cenas

### CENA 1 — Apresentação do problema (45s)

**Mostra:** página inicial http://localhost:3000

**Fala:**

> "Oi, sou o Derek Cobain, aluno do TADS na FAESA. Esse é o **Hórus** — meu Projeto Integrador III orientado pelo prof. Howard Cruz.
>
> O problema que ele resolve: o governo brasileiro **mantém uma lista pública de empresas punidas** — o CEIS, da CGU. Essas empresas, em tese, **não podem receber contrato federal novo**.
>
> Na prática, **muitas delas continuam contratando**. Os dados estão disponíveis em APIs públicas, mas **ninguém cruza**. O Hórus automatiza esse cruzamento."

**Foco visual:** os 4 KPIs no topo + frase "investigamos N empresas no CEIS, em X houve sobreposição..."

---

### CENA 2 — Os achados (60s)

**Mostra:** rola até a seção "🚨 sobreposição temporal comprovada"

**Fala:**

> "O sistema **investigou 190 empresas** que estão no CEIS e têm contrato federal registrado. Em **42 delas** consegui provar matematicamente que **sanção e contrato estavam vigentes ao mesmo tempo** — irregularidade evidente, isso é o que aparece aqui em cima.
>
> As outras 148... — *desce até a seção POTENCIAL* — ...essas o algoritmo investigou, mas os contratos detectados são **anteriores à sanção atual**. **Não há prova de irregularidade temporal**, então não acuso — mas reporto pra transparência do método."

**Foco visual:** mostrar as duas seções claramente separadas, badges GRAVE em vermelho vs POTENCIAL em amarelo.

---

### CENA 3 — Um caso concreto (90s)

**Mostra:** clica em um caso forte (recomendo **WELTSOLUTIONS** ou outro top GRAVE)

**Fala:**

> "Vou abrir um caso real. **WELTSOLUTIONS Suporte em TI** — empresa de Brasília.
>
> Olha aqui: ela **está suspensa pelo TCU**, sanção em vigor, vigência [diz as datas]. Mesmo assim, **figura como fornecedora em R$ 114 milhões em contrato federal** com o Ministério da Gestão. Esse contrato começou em **R$ 990 mil** e **virou R$ 114 milhões** — cresceu **11.475% por aditivos**. — *aponta pra alerta vermelho*
>
> Pra qualquer um conferir, eu coloco aqui — *clica em 'sanção CEIS'* — o link pro Portal da Transparência oficial mostrando a sanção. Aqui — *clica em 'página da empresa'* — a lista completa de contratos dela. E ainda o link pro Diário Oficial pra buscar o processo.
>
> **Eu não decreto nada. Aponto o indício e mando pra fonte primária.** É auditoria pública, sem suposição."

**Foco visual:** detalhes do card (situação Receita, capital social, contratos), e clicar nos 2-3 links de verificação.

---

### CENA 4 — Como o sistema funciona (60s)

**Mostra:** terminal `~/Horus`

**Fala:**

> "Por dentro: o sistema tem um **pipeline ETL em duas camadas**. — *roda* `ls data/raw/` — esses CSVs são o **dado bruto** baixado direto das APIs públicas. CEIS e contratos vêm da CGU, dados cadastrais da Receita Federal via BrasilAPI. Tudo reproduzível.
>
> — *roda* `python -m backend.ingestao --help` — *mostra* — os 6 comandos do pipeline. Eu chamo `tudo` e ele baixa, transforma, carrega no Postgres."

**Mostra:** rapidamente abre o Swagger em :8001/docs

**Fala:**

> "A API tem os endpoints organizados — busca, dashboard, cruzamentos, grafo, ML. Tudo documentado."

**Foco visual:** terminal limpo, `listar-csvs` mostrando os arquivos, Swagger UI aberto.

---

### CENA 5 — Stack e impacto (45s)

**Mostra:** volta pra http://localhost:3000 (rola até o footer)

**Fala:**

> "Stack: **Python com FastAPI** no back, **PostgreSQL** com **Apache AGE** pra grafo, **scikit-learn**, **spaCy**, **Celery + Redis** pra jobs agendados, e **Next.js + Tailwind** no front. **Tudo containerizado**, tudo no git.
>
> Impacto social: cidadão, jornalista ou MP pega esse sistema, identifica os casos comprovados, faz LAI no órgão contratante, e força a resposta. **R$ 2,69 bilhões** em contratos suspeitos detectados nessa primeira rodada. Esse é o tamanho do problema.
>
> Próximas entregas: relatório técnico e MVP final em junho. Obrigado!"

---

## Após gravar

1. Salva o vídeo em `.mp4`
2. Renomeia: `horus-entrega2-derek-cobain.mp4`
3. Sobe no repo:
   ```bash
   git lfs install   # se o vídeo for > 100 MB
   mkdir -p docs/videos
   mv ~/horus-entrega2-derek-cobain.mp4 docs/videos/
   git add docs/videos/horus-entrega2-derek-cobain.mp4
   git commit -m "video: entrega 2 - protótipo funcional"
   git push
   ```
4. Manda o link do repo + link do commit do vídeo pro Howard.

---

## Dicas de gravação

- **Não precisa estar perfeito.** Hesitar, errar e corrigir é HUMANO e mostra que vc tá no controle.
- **Fala alto e devagar.** Microfone do notebook capta tudo, mas devagar tu evita ruído.
- **Não leia.** Tenha esse roteiro do lado, mas fala como se tivesse explicando pra um amigo.
- **Tela cheia.** F11 no Chrome/Firefox.
- **Cursor visível.** Configure OBS pra destacar o cursor (Ferramentas → Source Record).

**Se errar uma cena, NÃO REGRAVA TUDO.** Pausa, respira, e refaz só aquela cena. Edita depois (CapCut, Davinci Resolve, ou simplesmente Shotcut — todos free).

**Se faltar tempo:** corta a CENA 4. Foca em CENA 1, 2, 3, 5.

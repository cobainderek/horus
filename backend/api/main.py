"""Hórus — FastAPI principal."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import busca, cruzamentos, dashboard, grafo, ml, nlp


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from .database import aplicar_migrations
    aplicar_migrations()
    yield


app = FastAPI(
    title="Hórus API",
    description="Sistema de fiscalização de dados públicos brasileiros.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cruzamentos.router)
app.include_router(dashboard.router)
app.include_router(busca.router)
app.include_router(ml.router)
app.include_router(grafo.router)
app.include_router(nlp.router)


@app.get("/", tags=["Root"])
def root():
    return {"projeto": "Hórus", "versao": "0.3.0", "docs": "/docs"}

"""Conexão SQLAlchemy com o Postgres."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://horus:horus123@localhost:5433/horus",
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


# Migrations idempotentes — rodam toda subida da API/CLI.
# Adicionar uma linha aqui equivale a "uma nova coluna no banco".
MIGRATIONS = [
    "ALTER TABLE contratos_publicos ADD COLUMN IF NOT EXISTS valor_inicial DOUBLE PRECISION",
    "ALTER TABLE contratos_publicos ADD COLUMN IF NOT EXISTS valor_final DOUBLE PRECISION",
    "ALTER TABLE contratos_publicos ADD COLUMN IF NOT EXISTS modalidade VARCHAR(100)",
    "ALTER TABLE contratos_publicos ADD COLUMN IF NOT EXISTS numero_processo VARCHAR(100)",
    "ALTER TABLE contratos_publicos ADD COLUMN IF NOT EXISTS data_assinatura VARCHAR(10)",
    "ALTER TABLE ceis ADD COLUMN IF NOT EXISTS fundamentacao TEXT",
    "ALTER TABLE ceis ADD COLUMN IF NOT EXISTS numero_processo VARCHAR(100)",
]


def aplicar_migrations() -> None:
    """Executa ALTER TABLEs idempotentes."""
    with engine.connect() as conn:
        for sql in MIGRATIONS:
            conn.execute(text(sql))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Schemas Pydantic — entrada/saída da API."""
from pydantic import BaseModel


class KPIs(BaseModel):
    total_agentes: int
    total_empresas: int
    total_contratos: int
    total_sancoes: int
    total_irregularidades: int
    valor_contratos_suspeitos: float


class ConflitoInteresse(BaseModel):
    agente_nome: str
    agente_cpf: str
    agente_orgao: str
    empresa_razao_social: str
    empresa_cnpj: str
    contrato_valor: float
    contrato_objeto: str | None = None
    orgao_contratante: str
    score_risco: float | None = None


class RetornoFavor(BaseModel):
    doador_cnpj: str
    doador_nome: str
    valor_doacao: float
    ano_eleicao: int | None = None
    candidato_nome: str | None = None
    contrato_valor: float
    contrato_orgao: str
    contrato_objeto: str | None = None


class EmpresaSancionadaContrato(BaseModel):
    cnpj: str
    razao_social: str
    tipo_sancao: str
    contrato_valor: float
    contrato_orgao: str
    contrato_objeto: str | None = None


class Busca(BaseModel):
    tipo: str
    dados: dict
    score_risco: float
    irregularidades: list[dict]

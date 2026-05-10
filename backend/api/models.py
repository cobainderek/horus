"""Entidades SQLAlchemy do Hórus — 6 tabelas que cobrem os 5 cruzamentos."""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class AgentePublico(Base):
    __tablename__ = "agentes_publicos"
    cpf = Column(String(14), primary_key=True)
    nome = Column(String(200), nullable=False, index=True)
    orgao = Column(String(200), nullable=False)
    cargo = Column(String(200))
    remuneracao = Column(Float, default=0.0)
    score_risco = Column(Float, default=0.0)


class Empresa(Base):
    __tablename__ = "empresas"
    cnpj = Column(String(18), primary_key=True)
    razao_social = Column(String(300), nullable=False, index=True)
    situacao = Column(String(50))
    data_abertura = Column(String(10))
    score_risco = Column(Float, default=0.0)

    socios = relationship("SocioEmpresa", back_populates="empresa", lazy="selectin")
    contratos = relationship("ContratoPublico", back_populates="empresa", lazy="selectin")
    sancoes = relationship("CEIS", back_populates="empresa", lazy="selectin")


class SocioEmpresa(Base):
    __tablename__ = "socios_empresa"
    id = Column(String(20), primary_key=True)
    cnpj_empresa = Column(String(18), ForeignKey("empresas.cnpj"), nullable=False)
    cpf_socio = Column(String(14), nullable=False, index=True)
    nome_socio = Column(String(200), nullable=False)
    qualificacao = Column(String(100))

    empresa = relationship("Empresa", back_populates="socios")


class ContratoPublico(Base):
    __tablename__ = "contratos_publicos"
    id = Column(String(20), primary_key=True)
    cnpj_fornecedor = Column(String(18), ForeignKey("empresas.cnpj"), nullable=False)
    orgao_contratante = Column(String(200), nullable=False)
    valor = Column(Float, nullable=False)
    data_inicio = Column(String(10))
    data_fim = Column(String(10))
    objeto = Column(Text)
    valor_inicial = Column(Float)
    valor_final = Column(Float)
    modalidade = Column(String(100))
    numero_processo = Column(String(100))
    data_assinatura = Column(String(10))

    empresa = relationship("Empresa", back_populates="contratos")


class CEIS(Base):
    __tablename__ = "ceis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(18), ForeignKey("empresas.cnpj"), nullable=False)
    razao_social = Column(String(300))
    tipo_sancao = Column(String(200))
    data_inicio_sancao = Column(String(10))
    data_fim_sancao = Column(String(10))
    orgao_sancionador = Column(String(200))
    fundamentacao = Column(Text)
    numero_processo = Column(String(100))

    empresa = relationship("Empresa", back_populates="sancoes")


class DadosCadastrais(Base):
    """Snapshot da Receita Federal (via BrasilAPI) para cada empresa."""
    __tablename__ = "dados_cadastrais"

    cnpj = Column(String(18), ForeignKey("empresas.cnpj"), primary_key=True)
    nome_fantasia = Column(String(300))
    situacao_cadastral = Column(String(50))
    data_inicio_atividade = Column(String(10))
    capital_social = Column(Float)
    porte = Column(String(100))
    natureza_juridica = Column(String(200))
    cnae_descricao = Column(String(300))
    cnae_codigo = Column(String(20))
    logradouro = Column(String(200))
    numero = Column(String(20))
    municipio = Column(String(100))
    uf = Column(String(2))
    telefone = Column(String(50))
    email = Column(String(200))
    opcao_simples = Column(Integer, default=0)
    atualizado_em = Column(String(10))


class DoacaoEleitoral(Base):
    __tablename__ = "doacoes_eleitorais"
    id = Column(String(20), primary_key=True)
    cnpj_doador = Column(String(18))
    nome_doador = Column(String(300))
    cpf_candidato = Column(String(14))
    nome_candidato = Column(String(200))
    valor = Column(Float)
    ano_eleicao = Column(Integer)
    cargo_candidato = Column(String(100))

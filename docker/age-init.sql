-- Habilita a extensão Apache AGE e cria o grafo do Hórus.
-- Executado automaticamente pelo postgres na 1ª subida do container.
-- Nome do grafo: horus_graph (evita conflito com schema $user=horus).

CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, public;

SELECT ag_catalog.create_graph('horus_graph');

-- Garante que tabelas comuns (CREATE TABLE sem schema) caem em "public".
ALTER ROLE horus SET search_path = public, ag_catalog;

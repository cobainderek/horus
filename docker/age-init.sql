-- Habilita a extensão Apache AGE e cria o grafo padrão do Hórus.
-- Executado automaticamente pelo postgres na 1ª subida do container.

CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path TO ag_catalog, "$user", public;

SELECT create_graph('horus');

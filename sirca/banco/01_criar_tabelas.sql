-- SIRCA Equipe E. PostgreSQL 16+. Banco vazio / esquema dedicado.
BEGIN;
CREATE TABLE familia (
 id_familia varchar(10) PRIMARY KEY,
 nome_responsavel varchar(160) NOT NULL,
 cpf_mascarado varchar(30), nascimento_responsavel date,
 endereco text, bairro varchar(100), telefone varchar(60),
 n_dependentes integer CHECK(n_dependentes>=0),
 renda_familiar numeric(12,2) CHECK(renda_familiar>=0),
 data_cadastro date NOT NULL,
 situacao varchar(20) NOT NULL CHECK(situacao IN('ativo','inativo','desligado')),
 observacao text
);
CREATE TABLE participante (
 id_participante varchar(10) PRIMARY KEY,
 nome varchar(160) NOT NULL,
 id_familia varchar(10) NOT NULL REFERENCES familia(id_familia),
 nascimento date NOT NULL,
 escola varchar(160), turma_ano varchar(50),
 data_entrada date NOT NULL CHECK(data_entrada>=nascimento),
 situacao varchar(20) NOT NULL CHECK(situacao IN('ativo','desligado','transferido')),
 data_desligamento date,
 CHECK(data_desligamento IS NULL OR data_desligamento>=data_entrada),
 CHECK(data_desligamento IS NULL OR situacao='desligado')
);
CREATE TABLE colaborador (
 id_colaborador varchar(10) PRIMARY KEY,
 nome varchar(160) NOT NULL,
 tipo_identificador varchar(30) NOT NULL CHECK(tipo_identificador IN('nome_fornecido','token_legado')),
 UNIQUE(nome,tipo_identificador)
);
CREATE TABLE oficina (
 id_oficina varchar(10) PRIMARY KEY,
 nome varchar(160) NOT NULL UNIQUE,
 id_oficineiro varchar(10) REFERENCES colaborador(id_colaborador),
 dia_semana varchar(10) NOT NULL CHECK(dia_semana IN('segunda','terca','quarta','quinta','sexta')),
 hora_inicio time NOT NULL, hora_fim time NOT NULL CHECK(hora_fim>hora_inicio),
 sala varchar(50), vagas integer NOT NULL CHECK(vagas>0),
 mes_inicio char(7), mes_fim char(7),
 CHECK(mes_inicio IS NULL OR mes_inicio ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
 CHECK(mes_fim IS NULL OR mes_fim ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
 CHECK(mes_fim IS NULL OR mes_inicio IS NULL OR mes_fim>=mes_inicio)
);
CREATE TABLE encontro (
 id_oficina varchar(10) NOT NULL REFERENCES oficina(id_oficina),
 data_encontro date NOT NULL,
 PRIMARY KEY(id_oficina,data_encontro)
);
CREATE TABLE frequencia (
 id_participante varchar(10) NOT NULL REFERENCES participante(id_participante),
 id_oficina varchar(10) NOT NULL,
 data_encontro date NOT NULL,
 presenca varchar(20) NOT NULL CHECK(presenca IN('presente','falta','falta justificada')),
 id_registrador varchar(10) NOT NULL REFERENCES colaborador(id_colaborador),
 registrado_em timestamptz,
 importado_em timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
 origem varchar(10) NOT NULL CHECK(origem IN('legado','sessao')),
 arquivo_origem text, linha_origem integer CHECK(linha_origem>0),
 PRIMARY KEY(id_participante,id_oficina,data_encontro),
 FOREIGN KEY(id_oficina,data_encontro) REFERENCES encontro(id_oficina,data_encontro),
 CHECK(origem<>'sessao' OR registrado_em IS NOT NULL),
 CHECK(origem<>'legado' OR (arquivo_origem IS NOT NULL AND linha_origem IS NOT NULL))
);
CREATE TABLE orgao (
 id_orgao varchar(10) PRIMARY KEY, nome varchar(160) NOT NULL UNIQUE
);
CREATE TABLE doacao (
 id_doacao varchar(10) PRIMARY KEY, data_doacao date NOT NULL,
 doador varchar(160) NOT NULL, tipo varchar(50) NOT NULL CHECK(tipo IN('alimento','brinquedo','dinheiro','higiene','material escolar','movel','vestuario')),
 item varchar(160) NOT NULL, quantidade numeric(12,2) CHECK(quantidade>=0),
 unidade varchar(30), destino text,
 valor_estimado numeric(12,2) CHECK(valor_estimado>=0),
 arquivo_origem text NOT NULL, linha_origem integer NOT NULL CHECK(linha_origem>0)
);
CREATE TABLE encaminhamento (
 id_encaminhamento varchar(10) PRIMARY KEY, data_encaminhamento date NOT NULL,
 id_participante varchar(10) NOT NULL REFERENCES participante(id_participante),
 servico varchar(160) NOT NULL, id_orgao varchar(10) NOT NULL REFERENCES orgao(id_orgao),
 situacao varchar(20) CHECK(situacao IN('sem retorno','encaminhado','aguardando','atendido')),
 retorno text,
 arquivo_origem text NOT NULL, linha_origem integer NOT NULL CHECK(linha_origem>0)
);
CREATE TABLE lacuna_frequencia (
 id_lacuna integer PRIMARY KEY, id_oficina varchar(10) NOT NULL REFERENCES oficina(id_oficina),
 inicio date NOT NULL, fim date NOT NULL CHECK(fim>=inicio), motivo text NOT NULL
);
CREATE FUNCTION verificar_desligamento() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p participante%ROWTYPE;
BEGIN
 SELECT * INTO p FROM participante WHERE id_participante=NEW.id_participante FOR SHARE;
 IF NOT FOUND THEN RETURN NEW; END IF; -- a FK emite a rejeicao do inexistente
 IF (p.data_desligamento IS NOT NULL AND NEW.data_encontro>=p.data_desligamento)
    OR (p.situacao='desligado' AND p.data_desligamento IS NULL) THEN
    RAISE EXCEPTION 'RN-04: desligado; data do desligamento ausente ou data do encontro bloqueada';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER tg_frequencia_desligamento BEFORE INSERT OR UPDATE ON frequencia
 FOR EACH ROW EXECUTE FUNCTION verificar_desligamento();
CREATE FUNCTION verificar_alteracao_desligamento() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.situacao='desligado' AND EXISTS (
  SELECT 1 FROM frequencia f WHERE f.id_participante=NEW.id_participante
  AND (NEW.data_desligamento IS NULL OR f.data_encontro>=NEW.data_desligamento)
 ) THEN RAISE EXCEPTION 'RN-04: frequencias existentes incompatíveis com o desligamento'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER tg_participante_desligamento BEFORE UPDATE ON participante
 FOR EACH ROW EXECUTE FUNCTION verificar_alteracao_desligamento();
COMMIT;

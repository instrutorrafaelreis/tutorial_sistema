-- ==========================================================
-- ENTREGA 3: SCRIPT DE CRIAÇÃO E POPULAÇÃO DO BANCO DE DADOS
-- Arquivo: oficina_db.sql
-- ==========================================================

CREATE DATABASE IF NOT EXISTS oficina_db;
USE oficina_db;

-- 1. Tabela CLIENTE (CPF e Senha armazenados criptografados em SHA-256 conforme LGPD)
CREATE TABLE IF NOT EXISTS cliente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    cpf VARCHAR(64) NOT NULL,
    login VARCHAR(50) NOT NULL,
    senha VARCHAR(64) NOT NULL
);

-- 2. Tabela VEICULO (Com Chave Estrangeira para CLIENTE)
CREATE TABLE IF NOT EXISTS veiculo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    modelo VARCHAR(100) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    cliente_id INT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES cliente(id) ON DELETE CASCADE
);

-- 3. Tabela AGENDAMENTO (Com Chave Estrangeira para VEICULO)
CREATE TABLE IF NOT EXISTS agendamento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_agendamento DATE NOT NULL,
    servico VARCHAR(100) NOT NULL,
    veiculo_id INT NOT NULL,
    FOREIGN KEY (veiculo_id) REFERENCES veiculo(id) ON DELETE CASCADE
);

-- ==========================================================
-- POPULAÇÃO INICIAL (Mínimo de 3 registros por tabela)
-- Obs: O hash SHA-256 abaixo para senha corresponde a '123'
-- ==========================================================

INSERT INTO cliente (nome, telefone, cpf, login, senha) VALUES
('Ana Silva', '11999990001', '2c624232cdd221771294dfbb310aca000a0df6ac8b66b696d90ef06fdefb64a3', 'ana', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'),
('Carlos Souza', '11999990002', '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b', 'carlos', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'),
('Mariana Costa', '11999990003', 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35', 'mariana', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3');

INSERT INTO veiculo (modelo, marca, cliente_id) VALUES
('Civic', 'Honda', 1),
('Corolla', 'Toyota', 2),
('Onix', 'Chevrolet', 3);

INSERT INTO agendamento (data_agendamento, servico, veiculo_id) VALUES
('2026-05-20', 'Troca de Óleo e Filtros', 1),
('2026-03-10', 'Alinhamento e Balanceamento', 2),
('2025-11-05', 'Revisão de Freios', 3);

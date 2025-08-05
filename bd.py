import sqlite3
from funcoes import gerenciar_conexao, hash_senha

#Cria todas as tabelas necessárias para o sistema financeiro
def inicializar_tabelas():
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            #TABELA USUARIOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    cargo TEXT NOT NULL CHECK (cargo IN ('Administrador', 'Gerente Financeiro', 'Vendedor'))
                );
            """)

            #TABELA FORNECEDORES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    cpf_cnpj TEXT UNIQUE,
                    email TEXT,
                    telefone TEXT,
                    ramo TEXT,
                    data_cadastro TEXT NOT NULL
                );
            """)

            #TABELA CLIENTES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    cpf_cnpj TEXT UNIQUE,
                    email TEXT,
                    telefone TEXT,
                    endereco TEXT,
                    data_cadastro TEXT NOT NULL
                );
            """)

            #TABELA CONTAS BANCÁRIAS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contas_bancarias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_conta TEXT UNIQUE NOT NULL,
                    saldo_inicial REAL NOT NULL DEFAULT 0,
                    tipo_conta TEXT,
                    instituicao TEXT
                );
            """)

            #TABELA CONTAS A PAGAR
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contas_a_pagar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento TEXT NOT NULL,
                    data_pagamento TEXT,
                    status TEXT NOT NULL CHECK(status IN ('Pendente', 'Pago', 'Atrasado', 'Parcial')),
                    fornecedor_id INTEGER NOT NULL,
                    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
                );
            """)

            #TABELA CONTAS A RECEBER
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contas_a_receber (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_vencimento TEXT NOT NULL,
                    data_recebimento TEXT,
                    status TEXT NOT NULL CHECK(status IN ('Pendente', 'Recebido', 'Atrasado', 'Parcial')),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                );
            """)


            #TABELA LANÇAMENTOS FINANCEIROS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_lancamento TEXT NOT NULL,
                    tipo TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa')),
                    conta_bancaria_id INTEGER NOT NULL,
                    conta_a_pagar_id INTEGER,
                    conta_a_receber_id INTEGER,
                    FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias(id),
                    FOREIGN KEY (conta_a_pagar_id) REFERENCES contas_a_pagar(id),
                    FOREIGN KEY (conta_a_receber_id) REFERENCES contas_a_receber(id)
                );
            """)

            print("Tabelas verificadas e criadas com sucesso!")

    except Exception as e:
        print(f"ERRO ao inicializar tabelas: {e}")


#CRIA O USUÁRIO PADRÃO QUE É O DO ADMINISTRADOR, SENDO O USUÁRIO ADM, E SENHA ADM123
def admin_padrao():
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM usuarios WHERE nome_usuario = ?", ('adm',))
            if not cursor.fetchone():
                senha_padrao_hasheada = hash_senha("adm123")
                cursor.execute("INSERT INTO usuarios (nome_usuario, senha, cargo) VALUES (?, ?, ?)",
                               ('adm', senha_padrao_hasheada, 'Administrador'))
                print("Usuário administrador padrão ('adm') criado com sucesso.")
            else:
                print("Usuário padrão 'adm' já existe.")
    except Exception as e:
        print(f"ERRO ao verificar/criar usuário padrão: {e}")


if __name__ == '__main__':
    inicializar_tabelas()
    admin_padrao()
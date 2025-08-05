import sqlite3
import contextlib
import hashlib
import datetime
import os
import sys

# Nome do arquivo do banco de dados SQLite.
banco_de_dados = "bd.db"

@contextlib.contextmanager
def gerenciar_conexao():
    """
    - ABRE a conexão.
    - Ativa o suporte a chaves estrangeiras (essencial para integridade).
    - SALVA a transação em caso de sucesso.
    - Faz backup em caso de erro.
    - Garante que a conexão seja fechada ao final.
    """
    conn = None
    try:
        conn = sqlite3.connect(banco_de_dados)
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"ERRO: Erro na transação do banco de dados: {e}")
        # Re-lança a exceção para que a função chamadora possa tratá-la, se necessário.
        raise
    finally:
        if conn:
            conn.close()

def hash_senha(senha: str) -> str:
    """
    Gera um hash da senha.
    """
    return hashlib.sha256(senha.encode()).hexdigest()

def exibir_menu_e_obter_opcao(titulo_menu: str, opcoes: list) -> int:
    """
    Exibe um menu de opções e garante que seja numero int
    """
    print(f"\n--- {titulo_menu} ---")
    for i, opcao in enumerate(opcoes, 1):
        print(f"{i}. {opcao}")
    while True:
        try:
            escolha = int(input("Escolha uma opção: "))
            if 1 <= escolha <= len(opcoes):
                return escolha
            else:
                print(f"Opção inválida. Por favor, digite um número entre 1 e {len(opcoes)}.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

def buscar_id(lista_itens: list, acao: str = "selecionar") -> int | None:
    """
    Solicita um ID ao usuário e verifica se ele existe em uma lista de itens fornecida.
    """
    if not lista_itens:
        print(f"Não há itens disponíveis para {acao}.")
        return None

    ids_existentes = {item[0] for item in lista_itens}

    while True:
        try:
            id_digitado = input(f"Digite o ID para {acao} (ou Enter para cancelar): ").strip()
            if not id_digitado:
                print("Operação cancelada.")
                return None
            crud_id = int(id_digitado)

            if crud_id in ids_existentes:
                return crud_id
            else:
                print(f"ID {crud_id} não encontrado na lista. Tente novamente.")
        except ValueError:
            print("ID inválido. Por favor, digite um número.")

def deletar(msg: str, lista_para_validacao: list):
    """
    Função genérica para deletar um item de uma tabela específica.
    'msg' é o nome da entidade (ex: 'cliente').
    'lista_para_validacao' é usada pela função buscar_id para validar a escolha.
    """
    TABLE_MAP = {
        "cliente": "clientes",
        "fornecedor": "fornecedores",
        "conta": "contas_bancarias",
        "conta a receber": "contas_a_receber",
        "conta a pagar": "contas_a_pagar",
        "lancamento": "lancamentos",
        "usuario": "usuarios"
    }
    table_name = TABLE_MAP.get(msg.lower())

    if not table_name:
        print(f"ERRO: Tipo '{msg}' não reconhecido para deleção.")
        return

    crud_id = buscar_id(lista_para_validacao, acao=f"deletar {msg}")
    if crud_id is None:
        return

    certeza = input(f"Tem certeza que deseja DELETAR o(a) {msg.upper()} com ID {crud_id}? Esta ação não pode ser desfeita. (s/n): ").lower().strip()
    if certeza == 's':
        try:
            with gerenciar_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (crud_id,))
                print(f"\n{msg.upper()} com ID {crud_id} deletado com sucesso!")
        except sqlite3.IntegrityError:
            print(f"\nERRO: Não foi possível deletar o(a) {msg.upper()} com ID {crud_id}.")
            print("Este item está sendo referenciado por outros registros no sistema (ex: um lançamento ou uma conta).")
            print("É necessário remover as dependências antes de poder deletar este item.")
        except Exception as e:
            print(f"Ocorreu um erro ao deletar o(a) {msg.upper()}: {e}")
    else:
        print("\nOperação de deleção cancelada.")

def buscar_entidade_por_id(table_name: str, entity_id: int) -> bool:
    """
    Verifica se uma entidade com um dado ID existe em uma tabela específica.
    """
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (entity_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"ERRO ao verificar {table_name} no banco de dados: {e}")
        return False

# Funções de verificação específicas que usam a função genérica
def buscar_cliente(cliente_id: int) -> bool:
    return buscar_entidade_por_id("clientes", cliente_id)

def buscar_fornecedor(fornecedor_id: int) -> bool:
    return buscar_entidade_por_id("fornecedores", fornecedor_id)

def buscar_conta_bancaria(conta_id: int) -> bool:
    return buscar_entidade_por_id("contas_bancarias", conta_id)

def id_conta_lancamento() -> int | None:
    """
    Exibe a lista de contas bancárias e pede ao usuário para selecionar uma para o lançamento
    """
    try:
        from crud_contas import exibir_lista_contas
        print("\n--- Seleção de Conta Bancária ---")
        lista_contas = exibir_lista_contas()
    except ImportError:
        print("ERRO: A função 'exibir_lista_contas' não foi encontrada.")
        return None
    except Exception as e:
        print(f"ERRO ao carregar lista de contas para seleção: {e}")
        return None

    if not lista_contas:
        print("Nenhuma conta bancária cadastrada. Cadastre uma conta primeiro.")
        return None

    return buscar_id(lista_contas, acao="selecionar a conta bancária")

def atualizar_status_contas():
    """
    Atualiza o status de contas pendentes para 'Atrasado' se a data de vencimento já passou.
    """
    hoje = datetime.date.today().isoformat()
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            # Atualiza contas a pagar
            cursor.execute("""
                UPDATE contas_a_pagar
                SET status = 'Atrasado'
                WHERE data_vencimento < ? AND status = 'Pendente'
            """, (hoje,))
            # Atualiza contas a receber
            cursor.execute("""
                UPDATE contas_a_receber
                SET status = 'Atrasado'
                WHERE data_vencimento < ? AND status = 'Pendente'
            """, (hoje,))
    except Exception as e:
        print(f"ERRO ao atualizar status de contas para 'Atrasado': {e}")


def limpar_tela():
    print("\n" * 100)

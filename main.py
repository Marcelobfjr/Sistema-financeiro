import sys
import time
# Funções dos módulos de CRUD
from crud_usuarios import menu_usuarios
from crud_clientes import menu_clientes
from crud_fornecedores import menu_fornecedores
from crud_contas import menu_contas
from crud_contas_a_pagar import menu_contas_a_pagar
from crud_contas_a_receber import menu_contas_a_receber
from crud_lancamentos import menu_lancamentos
# Funções de inicialização e utilidades
from bd import inicializar_tabelas, admin_padrao
from funcoes import gerenciar_conexao, hash_senha, exibir_menu_e_obter_opcao, limpar_tela, atualizar_status_contas

#DICIONÁRIOS DE MAPEAMENTO PARA O MENU E PERMISSÕES
# Mapeia as chaves internas para as funções de menu que serão chamadas.
MENU_FUNCTIONS_MAP = {
    "usuarios": menu_usuarios,
    "clientes": menu_clientes,
    "fornecedores": menu_fornecedores,
    "contas_bancarias": menu_contas,
    "contas_a_pagar": menu_contas_a_pagar,
    "contas_a_receber": menu_contas_a_receber,
    "lancamentos": menu_lancamentos
}

# Define as permissões de acesso para cada cargo do sistema.
PERMISSOES_CARGO = {
    "Administrador": [
        "usuarios", "clientes", "fornecedores", "contas_bancarias",
        "contas_a_pagar", "contas_a_receber", "lancamentos"
    ],
    "Gerente Financeiro": [
        "clientes", "fornecedores", "contas_bancarias",
        "contas_a_pagar", "contas_a_receber", "lancamentos"
    ],
    "Vendedor": ["clientes", "contas_a_receber"]
}

# Mapeia o texto de exibição no menu principal para as chaves de módulo internas.
MAIN_MENU_OPTIONS_MAP = {
    "Gerenciar Usuários": "usuarios",
    "Gerenciar Clientes": "clientes",
    "Gerenciar Fornecedores": "fornecedores",
    "Gerenciar Contas Bancárias": "contas_bancarias",
    "Gerenciar Contas a Pagar": "contas_a_pagar",
    "Gerenciar Contas a Receber": "contas_a_receber",
    "Gerenciar Lançamentos": "lancamentos"
}


#FUNÇÃO DE LOGIN
def login() -> tuple | None:
    """
    Realiza a autenticação do usuário, verificando suas credenciais no banco de dados.
    Retorna uma tupla com (id, nome_usuario, cargo) em caso de sucesso, ou None em caso de falha.
    """
    limpar_tela()
    print("--- TELA DE LOGIN ---")
    max_tentativas = 3
    for tentativas in range(max_tentativas):
        nome_usuario = input("Usuário: ").strip()
        senha_plana = input("Senha: ").strip()

        if not nome_usuario or not senha_plana:
            print("Usuário e senha não podem ser vazios.")
            continue

        senha_hasheada = hash_senha(senha_plana)

        try:
            with gerenciar_conexao() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, nome_usuario, cargo FROM usuarios WHERE nome_usuario = ? AND senha = ?",
                    (nome_usuario, senha_hasheada)
                )
                resultado = cursor.fetchone()

                if resultado:
                    print(f"\nLogin bem-sucedido! Bem-vindo, {resultado[1]} ({resultado[2]}).")
                    time.sleep(1)
                    return resultado
                else:
                    print(f"Usuário ou senha incorretos. ({max_tentativas - 1 - tentativas} tentativas restantes)")
        except Exception as e:
            print(f"ERRO: Problema ao conectar ao banco de dados para login: {e}")
            return None

    print(f"\nNúmero máximo de tentativas ({max_tentativas}) excedido. Encerrando.")
    return None


#FUNÇÃO DO MENU PRINCIPAL
def main_menu(info_usuario: tuple):
    """
    Exibe o menu principal com opçõe baseadas no cargo do usuário logado.
    """
    usuario_id, usuarioname, usuario_cargo = info_usuario

    # Obtém a lista de módulos permitidos para o cargo do usuário
    modulos_permitidos = PERMISSOES_CARGO.get(usuario_cargo, [])

    while True:
        limpar_tela()
        print(f"--- MENU PRINCIPAL - Logado como: {usuarioname} ({usuario_cargo}) ---")

        opcoes = []
        permissoes = []

        for texto, modulo in MAIN_MENU_OPTIONS_MAP.items():
            if modulo in modulos_permitidos:
                opcoes.append(texto)
                permissoes.append(MENU_FUNCTIONS_MAP[modulo])

        opcoes.append("Sair do Sistema")

        escolha = exibir_menu_e_obter_opcao("SELECIONE UMA OPÇÃO", opcoes)

        if escolha == len(opcoes):
            print("Saindo do sistema. Até mais!")
            sys.exit(0)

        funcao = permissoes[escolha - 1]
        funcao()

        input("\nPressione Enter para retornar ao Menu Principal...")



if __name__ == "__main__":
    print("Iniciando o sistema financeiro...")
    inicializar_tabelas()
    admin_padrao()
    time.sleep(1)

    usuario_autenticado = login()

    if usuario_autenticado is None:
        print("Falha na autenticação. O sistema será encerrado.")
        sys.exit(1)

    print("Verificando e atualizando status de contas...")
    atualizar_status_contas()
    time.sleep(1)

    main_menu(usuario_autenticado)
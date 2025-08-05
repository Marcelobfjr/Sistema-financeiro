from funcoes import gerenciar_conexao, hash_senha, exibir_menu_e_obter_opcao, buscar_id, deletar as deletar_item, \
    limpar_tela


LARGURA_ID_USUARIO = 5
LARGURA_NOME_USUARIO = 30
LARGURA_CARGO_USUARIO = 20


def definir_cargo() -> str:
    cargos = ['Administrador', 'Gerente Financeiro', 'Vendedor']
    escolha = exibir_menu_e_obter_opcao("SELECIONE O CARGO", cargos)
    return cargos[escolha - 1]


#ADICIONAR USUÁRIO
def adicionar_usuario():
    limpar_tela()
    print("--- ADICIONAR NOVO USUÁRIO ---")
    nome_usuario = input("Nome do novo usuário: ").strip()
    senha_plana = input("Senha do novo usuário: ").strip()
    if not nome_usuario or not senha_plana:
        print("\nERRO: Nome de usuário e senha não podem ser vazios.")
        return

    cargo = definir_cargo()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE nome_usuario = ?", (nome_usuario,))
            if cursor.fetchone():
                print(f"\nERRO: O nome de usuário '{nome_usuario}' já existe!")
                return

            senha_hasheada = hash_senha(senha_plana)
            cursor.execute(
                "INSERT INTO usuarios (nome_usuario, senha, cargo) VALUES (?, ?, ?)",
                (nome_usuario, senha_hasheada, cargo)
            )
            print("\nUsuário cadastrado com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar o usuário: {e}")


#LISTAR FUNCIONÁRIOS
def exibir_lista_usuarios():
    limpar_tela()
    print("--- LISTA DE USUÁRIOS ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome_usuario, cargo FROM usuarios ORDER BY id")
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhum usuário cadastrado.")
                return []

            header = (
                f"{'ID':<{LARGURA_ID_USUARIO}} | {'NOME DE USUÁRIO':<{LARGURA_NOME_USUARIO}} | {'CARGO':<{LARGURA_CARGO_USUARIO}}"
            )
            print(header)
            print("-" * len(header))
            for user in resultados:
                print(
                    f"{user[0]:<{LARGURA_ID_USUARIO}} | {user[1]:<{LARGURA_NOME_USUARIO}} | {user[2]:<{LARGURA_CARGO_USUARIO}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar os usuários: {e}")
        return []


#ATUALIZAR FUNCIONÁRIO
def atualizar_usuario():
    limpar_tela()
    print("--- ATUALIZAR INFORMAÇÕES DE USUÁRIO ---")
    lista_usuarios = exibir_lista_usuarios()
    if not lista_usuarios:
        return

    usuario_id = buscar_id(lista_usuarios, "atualizar")
    if not usuario_id:
        return

    if usuario_id == 1:
        print("\nERRO: O usuário administrador principal (ID 1) não pode ser modificado por esta função.")
        return

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT nome_usuario, cargo FROM usuarios WHERE id = ?", (usuario_id,))
            usuario = cursor.fetchone()
            if not usuario:
                print("ERRO: Usuário não encontrado.")
                return

            nome, cargo = usuario

            opcoes_update = ["Nome de usuário", "Senha", "Cargo"]
            escolha_campo = exibir_menu_e_obter_opcao(f"QUAL CAMPO DO USUÁRIO '{nome}' DESEJA ATUALIZAR?",
                                                      opcoes_update)

            coluna_db = ""
            novo_dado = ""

            if escolha_campo == 1:
                coluna_db = "nome_usuario"
                novo_dado = input(f"Digite o novo nome de usuário (atual: {nome}): ").strip()
                if not novo_dado:
                    print("\nERRO: O nome de usuário não pode ser vazio. Operação cancelada.")
                    return
                cursor.execute("SELECT id FROM usuarios WHERE nome_usuario = ? AND id != ?", (novo_dado, usuario_id))
                if cursor.fetchone():
                    print(f"\nERRO: O nome de usuário '{novo_dado}' já está em uso. A atualização foi cancelada.")
                    return

            elif escolha_campo == 2:
                coluna_db = "senha"
                nova_senha = input("Digite a nova senha: ").strip()
                if not nova_senha:
                    print("\nERRO: A senha não pode ser vazia. Operação cancelada.")
                    return
                novo_dado = hash_senha(nova_senha)

            elif escolha_campo == 3:
                coluna_db = "cargo"
                print(f"O cargo atual é: {cargo}")
                novo_dado = definir_cargo()

            query = f"UPDATE usuarios SET {coluna_db} = ? WHERE id = ?"
            cursor.execute(query, (novo_dado, usuario_id))
            print(f"\nO campo '{opcoes_update[escolha_campo - 1]}' foi atualizado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro durante a atualização: {e}")


#DELETAR USUÁRIO
def deletar_usuario():
    limpar_tela()
    print("--- DELETAR USUÁRIO ---")
    lista_usuarios = exibir_lista_usuarios()
    if not lista_usuarios:
        return

    usuario_id_deletar = buscar_id(lista_usuarios, "deletar")
    if usuario_id_deletar == 1:
        print("\nERRO: O usuário administrador padrão (ID 1) não pode ser deletado.")
        return

    item_a_deletar = [user for user in lista_usuarios if user[0] == usuario_id_deletar]
    if item_a_deletar:
        deletar_item("usuario", item_a_deletar)


#MENU USUÁRIOS
def menu_usuarios():
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Usuário",
            "Ver Lista de Usuários",
            "Atualizar Usuário",
            "Deletar Usuário",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE USUÁRIOS", opcoes)

        if escolha == 1:
            adicionar_usuario()
        elif escolha == 2:
            exibir_lista_usuarios()
        elif escolha == 3:
            atualizar_usuario()
        elif escolha == 4:
            deletar_usuario()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")
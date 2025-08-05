import datetime
from funcoes import gerenciar_conexao, buscar_id, deletar as deletar_item, exibir_menu_e_obter_opcao, limpar_tela


LARGURA_ID_FORN = 4
LARGURA_NOME_FORN = 25
LARGURA_CPF_CNPJ_FORN = 18
LARGURA_EMAIL_FORN = 30
LARGURA_RAMO_FORN = 20
LARGURA_DATA_CADASTRO_FORN = 18


#ADICIONAR FORNECEDOR
def adicionar_fornecedor():
    limpar_tela()
    print("--- ADICIONAR NOVO FORNECEDOR ---")
    nome = input("Nome do Fornecedor: ").strip()
    while not nome:
        nome = input("O nome é obrigatório. Digite o nome do fornecedor: ").strip()

    cpf_cnpj = input("CPF/CNPJ (opcional): ").strip()
    email = input("Email (opcional): ").strip()
    telefone = input("Telefone (opcional): ").strip()
    ramo = input("Ramo de Atividade (opcional): ").strip()
    data_cadastro = datetime.date.today().isoformat()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            #VERIFICAÇÃO DE CPF E CNPJ DUPLICADOS
            cursor.execute("SELECT id FROM fornecedores WHERE nome = ?", (nome,))
            if cursor.fetchone():
                print(f"\nERRO: Já existe um fornecedor com o nome '{nome}'.")
                return

            if cpf_cnpj:
                cursor.execute("SELECT id FROM fornecedores WHERE cpf_cnpj = ?", (cpf_cnpj,))
                if cursor.fetchone():
                    print(f"\nERRO: Já existe um fornecedor com o CPF/CNPJ '{cpf_cnpj}'.")
                    return

            cursor.execute(
                "INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, ramo, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
                (nome, cpf_cnpj or None, email or None, telefone or None, ramo or None, data_cadastro)
            )
            print("\nFornecedor cadastrado com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar o fornecedor: {e}")


#LISTAR FORNECEDORES
def exibir_lista_fornecedores():
    limpar_tela()
    print("--- LISTA DE FORNECEDORES ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, cpf_cnpj, email, ramo, data_cadastro FROM fornecedores ORDER BY id")
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhum fornecedor cadastrado.")
                return []

            header = (
                f"{'ID':<{LARGURA_ID_FORN}} | {'NOME':<{LARGURA_NOME_FORN}} | {'CPF/CNPJ':<{LARGURA_CPF_CNPJ_FORN}} | "
                f"{'EMAIL':<{LARGURA_EMAIL_FORN}} | {'RAMO':<{LARGURA_RAMO_FORN}} | {'DATA CADASTRO':<{LARGURA_DATA_CADASTRO_FORN}}"
            )
            print(header)
            print("-" * len(header))

            for forn in resultados:
                print(
                    f"{forn[0]:<{LARGURA_ID_FORN}} | {forn[1]:<{LARGURA_NOME_FORN}} | "
                    f"{forn[2] or 'N/A':<{LARGURA_CPF_CNPJ_FORN}} | {forn[3] or 'N/A':<{LARGURA_EMAIL_FORN}} | "
                    f"{forn[4] or 'N/A':<{LARGURA_RAMO_FORN}} | {forn[5]:<{LARGURA_DATA_CADASTRO_FORN}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar os fornecedores: {e}")
        return []


#ATUALIZAR FORNECEDOR
def atualizar_fornecedor():
    limpar_tela()
    print("--- ATUALIZAR INFORMAÇÕES DE FORNECEDOR ---")
    lista_fornecedores = exibir_lista_fornecedores()
    if not lista_fornecedores:
        return

    fornecedor_id = buscar_id(lista_fornecedores, "atualizar")
    if not fornecedor_id:
        return

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome, cpf_cnpj, email, telefone, ramo FROM fornecedores WHERE id = ?",
                (fornecedor_id,)
            )
            data = cursor.fetchone()
            if not data:
                print("ERRO: Fornecedor não encontrado.")
                return

            nome, cpf, email, telefone, ramo = data

            opcoes_update = ["Nome", "CPF/CNPJ", "Email", "Telefone", "Ramo de Atividade"]
            escolha_campo = exibir_menu_e_obter_opcao(f"QUAL CAMPO DO FORNECEDOR '{nome}' DESEJA ATUALIZAR?",
                                                      opcoes_update)

            coluna_db = ""
            novo_dado = ""

            if escolha_campo == 1:
                coluna_db = "nome"
                novo_dado = input(f"Novo nome (atual: {nome}): ").strip()
            elif escolha_campo == 2:
                coluna_db = "cpf_cnpj"
                novo_dado = input(f"Novo CPF/CNPJ (atual: {cpf or 'N/A'}): ").strip()
            elif escolha_campo == 3:
                coluna_db = "email"
                novo_dado = input(f"Novo email (atual: {email or 'N/A'}): ").strip()
            elif escolha_campo == 4:
                coluna_db = "telefone"
                novo_dado = input(f"Novo telefone (atual: {telefone or 'N/A'}): ").strip()
            elif escolha_campo == 5:
                coluna_db = "ramo"
                novo_dado = input(f"Novo ramo (atual: {ramo or 'N/A'}): ").strip()

            if not novo_dado and coluna_db == "nome":
                print("\nERRO: O nome não pode ser vazio. Operação cancelada.")
                return

            if coluna_db in ["nome", "cpf_cnpj"] and novo_dado:
                cursor.execute(
                    f"SELECT id FROM fornecedores WHERE {coluna_db} = ? AND id != ?",
                    (novo_dado, fornecedor_id)
                )
                if cursor.fetchone():
                    print(
                        f"\nERRO: Já existe outro fornecedor com este {coluna_db.upper()}. A atualização foi cancelada.")
                    return

            dado_final = novo_dado or None

            query = f"UPDATE fornecedores SET {coluna_db} = ? WHERE id = ?"
            cursor.execute(query, (dado_final, fornecedor_id))
            print(f"\nO campo '{opcoes_update[escolha_campo - 1]}' foi atualizado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro durante a atualização: {e}")

#DELETAR FORNECEDOR
def deletar_fornecedor():
    limpar_tela()
    print("--- DELETAR FORNECEDOR ---")
    lista_fornecedores = exibir_lista_fornecedores()
    if not lista_fornecedores:
        return
    deletar_item("fornecedor", lista_fornecedores)


#MENU DE FORNECEDORES
def menu_fornecedores():
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Fornecedor",
            "Ver Lista de Fornecedores",
            "Atualizar Fornecedor",
            "Deletar Fornecedor",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE FORNECEDORES", opcoes)

        if escolha == 1:
            adicionar_fornecedor()
        elif escolha == 2:
            exibir_lista_fornecedores()
        elif escolha == 3:
            atualizar_fornecedor()
        elif escolha == 4:
            deletar_fornecedor()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")
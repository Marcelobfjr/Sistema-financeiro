import datetime
from funcoes import gerenciar_conexao, buscar_id, deletar as deletar_item, exibir_menu_e_obter_opcao, limpar_tela

#VARIÁVEIS PARA A CRIAÇÃO DAS TABELAS NA HORA DE PRINTAR
LARGURA_ID_CLIENTE = 4
LARGURA_NOME_CLIENTE = 25
LARGURA_CPF_CNPJ_CLIENTE = 18
LARGURA_EMAIL_CLIENTE = 30
LARGURA_TELEFONE_CLIENTE = 15
LARGURA_DATA_CADASTRO_CLIENTE = 18


#ADICIONAR O CLIENTE
def adicionar_cliente():
    limpar_tela()
    print("--- ADICIONAR NOVO CLIENTE ---")
    nome = input("Nome do Cliente: ").strip()
    while not nome:
        nome = input("O nome é obrigatório. Digite o nome do cliente: ").strip()

    cpf_cnpj = input("CPF/CNPJ (opcional): ").strip()
    email = input("Email (opcional): ").strip()
    telefone = input("Telefone (opcional): ").strip()
    endereco = input("Endereço (opcional): ").strip()
    data_cadastro = datetime.date.today().isoformat()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            #VALIDAÇÃO PARA VER SE O CLIENTE JÁ EXISTE
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (nome,))
            if cursor.fetchone():
                print(f"\nERRO: Já existe um cliente com o nome '{nome}'.")
                return
            #VALIDAÇÃO PARA VER SE O CPF/CNPJ JÁ EXISTE, ISSO EVITA CLIENTES DUPLICADOS
            if cpf_cnpj:
                cursor.execute("SELECT id FROM clientes WHERE cpf_cnpj = ?", (cpf_cnpj,))
                if cursor.fetchone():
                    print(f"\nERRO: Já existe um cliente com o CPF/CNPJ '{cpf_cnpj}'.")
                    return

            cursor.execute(
                "INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
                (nome, cpf_cnpj or None, email or None, telefone or None, endereco or None, data_cadastro)
            )
            print("\nCliente cadastrado com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar o cliente: {e}")


#LISTAR CLIENTES
def exibir_lista_clientes():
    limpar_tela()
    print("--- LISTA DE CLIENTES ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, cpf_cnpj, email, telefone, data_cadastro FROM clientes ORDER BY id")
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhum cliente cadastrado.")
                return []

            #FORMATAÇÃO DA TABELA
            header = (
                f"{'ID':<{LARGURA_ID_CLIENTE}} | {'NOME':<{LARGURA_NOME_CLIENTE}} | {'CPF/CNPJ':<{LARGURA_CPF_CNPJ_CLIENTE}} | "
                f"{'EMAIL':<{LARGURA_EMAIL_CLIENTE}} | {'TELEFONE':<{LARGURA_TELEFONE_CLIENTE}} | {'DATA CADASTRO':<{LARGURA_DATA_CADASTRO_CLIENTE}}"
            )
            print(header)
            print("-" * len(header))

            for cliente in resultados:
                print(
                    f"{cliente[0]:<{LARGURA_ID_CLIENTE}} | {cliente[1]:<{LARGURA_NOME_CLIENTE}} | "
                    f"{cliente[2] or 'N/A':<{LARGURA_CPF_CNPJ_CLIENTE}} | {cliente[3] or 'N/A':<{LARGURA_EMAIL_CLIENTE}} | "
                    f"{cliente[4] or 'N/A':<{LARGURA_TELEFONE_CLIENTE}} | {cliente[5]:<{LARGURA_DATA_CADASTRO_CLIENTE}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar os clientes: {e}")
        return []


#ATUALIZAR CLIENTE
def atualizar_cliente():
    limpar_tela()
    print("--- ATUALIZAR CLIENTE ---")
    lista_clientes = exibir_lista_clientes()
    if not lista_clientes:
        return

    cliente_id = buscar_id(lista_clientes, "atualizar")
    if not cliente_id:
        return

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            #BUSCA OS DADOS DO CLIENTE, SE EXISTE
            cursor.execute("SELECT nome, cpf_cnpj, email, telefone, endereco FROM clientes WHERE id = ?", (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                print("ERRO: Cliente não encontrado.")
                return

            nome, cpf, email, telefone, endereco = cliente

            #INPUT PARA SABER O QUE VAI SER ATUALIZADO
            opcoes_update = ["Nome", "CPF/CNPJ", "Email", "Telefone", "Endereço"]
            escolha_campo = exibir_menu_e_obter_opcao(f"QUAL CAMPO DO CLIENTE '{nome}' DESEJA ATUALIZAR?",
                                                      opcoes_update)

            coluna_db = ""
            novo_dado = ""

            if escolha_campo == 1:
                coluna_db = "nome"
                novo_dado = input(f"Digite o novo nome (atual: {nome}): ").strip()
            elif escolha_campo == 2:
                coluna_db = "cpf_cnpj"
                novo_dado = input(f"Digite o novo CPF/CNPJ (atual: {cpf or 'N/A'}): ").strip()
            elif escolha_campo == 3:
                coluna_db = "email"
                novo_dado = input(f"Digite o novo email (atual: {email or 'N/A'}): ").strip()
            elif escolha_campo == 4:
                coluna_db = "telefone"
                novo_dado = input(f"Digite o novo telefone (atual: {telefone or 'N/A'}): ").strip()
            elif escolha_campo == 5:
                coluna_db = "endereco"
                novo_dado = input(f"Digite o novo endereço (atual: {endereco or 'N/A'}): ").strip()

            if not novo_dado and coluna_db in ["nome"]:
                print("\nERRO: O nome não pode ser vazio. Operação cancelada.")
                return

            #VALIDA OS DADOS E VERIFICA SE ELES EXISTEM.
            if coluna_db in ["nome", "cpf_cnpj"] and novo_dado:
                cursor.execute(f"SELECT id FROM clientes WHERE {coluna_db} = ? AND id != ?", (novo_dado, cliente_id))
                if cursor.fetchone():
                    print(f"\nERRO: Já existe outro cliente com este {coluna_db.upper()}. A atualização foi cancelada.")
                    return

            #ATUALIZA
            dado_final = novo_dado or None
            query = f"UPDATE clientes SET {coluna_db} = ? WHERE id = ?"
            cursor.execute(query, (dado_final, cliente_id))

            print(f"\nO campo '{opcoes_update[escolha_campo - 1]}' foi atualizado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro durante a atualização: {e}")


#DELETAR CLIENTE
def deletar_cliente():
    limpar_tela()
    print("--- DELETAR CLIENTE ---")
    lista_clientes = exibir_lista_clientes()
    if not lista_clientes:
        return
    deletar_item("cliente", lista_clientes)


#MENU DE CLIENTES
def menu_clientes():
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Cliente",
            "Ver Lista de Clientes",
            "Atualizar Cliente",
            "Deletar Cliente",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE CLIENTES", opcoes)

        if escolha == 1:
            adicionar_cliente()
        elif escolha == 2:
            exibir_lista_clientes()
        elif escolha == 3:
            atualizar_cliente()
        elif escolha == 4:
            deletar_cliente()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")
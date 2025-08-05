from funcoes import gerenciar_conexao, buscar_id, deletar as deletar_item, exibir_menu_e_obter_opcao, limpar_tela

#VARIÁVEIS PARA A TABELA
LARGURA_ID_CB = 4
LARGURA_NOME_CONTA_CB = 25
LARGURA_TIPO_CB = 20
LARGURA_INSTITUICAO_CB = 20
LARGURA_SALDO_CB = 18


#ADICIONAR CONTA BANCÁRIA
def adicionar_conta():
    limpar_tela()
    print("--- ADICIONAR NOVA CONTA BANCÁRIA / CAIXA ---")
    nome_conta = input("Nome da Conta (ex: Banco do Brasil, Caixa Interno): ").strip()
    while not nome_conta:
        nome_conta = input("O nome da conta é obrigatório. Tente novamente: ").strip()

    while True:
        try:
            saldo_inicial_str = input("Saldo Inicial (pressione Enter para 0): ").replace(',', '.').strip()
            saldo_inicial = float(saldo_inicial_str) if saldo_inicial_str else 0.0
            break
        except ValueError:
            print("Valor inválido. Digite um número para o saldo.")

    tipo_conta = input("Tipo de Conta (ex: Corrente, Poupança, Caixa Físico): ").strip()
    instituicao = input("Instituição Financeira (opcional): ").strip()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM contas_bancarias WHERE nome_conta = ?", (nome_conta,))
            if cursor.fetchone():
                print(f"\nERRO: Já existe uma conta com o nome '{nome_conta}'.")
                return

            cursor.execute(
                "INSERT INTO contas_bancarias (nome_conta, saldo_inicial, tipo_conta, instituicao) VALUES (?, ?, ?, ?)",
                (nome_conta, saldo_inicial, tipo_conta or None, instituicao or None)
            )
            print("\nConta cadastrada com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar a conta: {e}")


#LISTAR CONTAS
def exibir_lista_contas():
    limpar_tela()
    print("--- LISTA DE CONTAS BANCÁRIAS / CAIXAS ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            # Aqui calcula o saldo atual de cada conta somando o saldo inicial
            # com todas as receitas e subtraindo todas as despesas da tabela de lançamentos.
            # cb = contas bancárias \ coalesce = retorna o primeiro numero nao nulo da operacao, evita se n tiver nada em lancamentos
            # l = lancamentos
            # SE L.VALOR FOR RECEITA SOMA, SE -L NO ELSE, É DESPESA SUBTRAI
            #LEFT JOIN UNE AS DUAS TABELAS, ID, NOME DA CONTA, TIPO, INSTITUICAO E SALDO ATUAL SAO AS COLUNAS
            cursor.execute("""
                SELECT
                    cb.id,
                    cb.nome_conta,
                    cb.tipo_conta,
                    cb.instituicao,
                    (cb.saldo_inicial + 
                     COALESCE(SUM(CASE WHEN l.tipo = 'Receita' THEN l.valor ELSE -l.valor END), 0)
                    ) AS saldo_atual
                FROM
                    contas_bancarias cb
                LEFT JOIN
                    lancamentos l ON cb.id = l.conta_bancaria_id
                GROUP BY
                    cb.id
                ORDER BY
                    cb.id;
            """)
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhuma conta cadastrada.")
                return []

            header = (
                f"{'ID':<{LARGURA_ID_CB}} | {'NOME DA CONTA':<{LARGURA_NOME_CONTA_CB}} | {'TIPO':<{LARGURA_TIPO_CB}} | "
                f"{'INSTITUIÇÃO':<{LARGURA_INSTITUICAO_CB}} | {'SALDO ATUAL':<{LARGURA_SALDO_CB}}"
            )
            print(header)
            print("-" * len(header))
            for conta in resultados:
                print(
                    f"{conta[0]:<{LARGURA_ID_CB}} | {conta[1]:<{LARGURA_NOME_CONTA_CB}} | "
                    f"{conta[2] or 'N/A':<{LARGURA_TIPO_CB}} | {conta[3] or 'N/A':<{LARGURA_INSTITUICAO_CB}} | "
                    f"R${conta[4]:<{LARGURA_SALDO_CB - 2}.2f}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar as contas: {e}")
        return []


#ATUALIZAR CONTA
def atualizar_conta():
    limpar_tela()
    print("--- ATUALIZAR CONTA BANCÁRIA ---")
    lista_contas = exibir_lista_contas()
    if not lista_contas:
        return

    conta_id = buscar_id(lista_contas, "atualizar")
    if not conta_id:
        return

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome_conta, saldo_inicial, tipo_conta, instituicao FROM contas_bancarias WHERE id = ?",
                (conta_id,)
            )
            conta = cursor.fetchone()
            if not conta:
                print("ERRO: Conta não encontrada.")
                return

        nome, saldo, tipo, instituicao = conta


        opcoes_update = ["Nome da Conta", "Saldo Inicial", "Tipo de Conta", "Instituição"]
        escolha_campo = exibir_menu_e_obter_opcao(f"QUAL CAMPO DA CONTA '{nome}' DESEJA ATUALIZAR?",
                                                  opcoes_update)

        coluna_db = ""
        novo_dado = None

        if escolha_campo == 1:
            coluna_db = "nome_conta"
            novo_dado = input(f"Novo nome da conta (atual: {nome}): ").strip()
            if not novo_dado:
                print("\nERRO: Nome da conta não pode ser vazio. Operação cancelada.")
                return
        elif escolha_campo == 2:
            coluna_db = "saldo_inicial"
            print(
                "\nATENÇÃO: Alterar o SALDO INICIAL pode causar inconsistências no saldo atual se já existirem lançamentos.")
            print("É recomendado fazer um lançamento de ajuste em vez desta alteração.")
            while True:
                try:
                    novo_dado_str = input(f"Novo saldo inicial (atual: {saldo:.2f}): ").replace(',','.').strip()
                    novo_dado = float(novo_dado_str)
                    break
                except ValueError:
                    print("Valor inválido. Digite um número.")
        elif escolha_campo == 3:
            coluna_db = "tipo_conta"
            novo_dado = input(f"Novo tipo de conta (atual: {tipo or 'N/A'}): ").strip()
        elif escolha_campo == 4:
            coluna_db = "instituicao"
            novo_dado = input(f"Nova instituição (atual: {instituicao or 'N/A'}): ").strip()


        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            #NOVO NOME DA CONTA TEM QUE SER ÚNICO
            if coluna_db == "nome_conta":
                cursor.execute(
                    "SELECT id FROM contas_bancarias WHERE nome_conta = ? AND id != ?",
                    (novo_dado, conta_id)
                )
                if cursor.fetchone():
                    print(f"\nERRO: Já existe outra conta com o nome '{novo_dado}'. A atualização foi cancelada.")
                    return

            #'isinstance' FAZ COM QUE 0.0 NÃO VIRE NULO
            dado_final = novo_dado if novo_dado or isinstance(novo_dado, (int, float)) else None

            query = f"UPDATE contas_bancarias SET {coluna_db} = ? WHERE id = ?"
            cursor.execute(query, (dado_final, conta_id))
            print(f"\nA conta foi atualizado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro durante a atualização: {e}")


#DELETAR CONTA
def deletar_conta():
    limpar_tela()
    print("--- DELETAR CONTA BANCÁRIA ---")
    lista_contas = exibir_lista_contas()
    if not lista_contas:
        return
    deletar_item("conta", lista_contas)


#MENU DE CONTAS
def menu_contas():
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Conta",
            "Ver Lista de Contas",
            "Atualizar Conta",
            "Deletar Conta",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE CONTAS", opcoes)

        if escolha == 1:
            adicionar_conta()
        elif escolha == 2:
            exibir_lista_contas()
        elif escolha == 3:
            atualizar_conta()
        elif escolha == 4:
            deletar_conta()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")
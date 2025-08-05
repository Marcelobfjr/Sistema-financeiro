import datetime
from funcoes import (
    gerenciar_conexao, buscar_id, deletar as deletar_item,
    exibir_menu_e_obter_opcao, buscar_cliente, limpar_tela, id_conta_lancamento
)

#Formatação
LARGURA_ID_CR = 4
LARGURA_CLIENTE_CR = 20
LARGURA_DESCRICAO_CR = 25
LARGURA_VALOR_TOTAL_CR = 12
LARGURA_VALOR_RECEBIDO_CR = 12
LARGURA_SALDO_CR = 12
LARGURA_VENCIMENTO_CR = 12
LARGURA_STATUS_CR = 10


#Função 1
def adicionar_conta_a_receber():
    """
    Coleta os dados do usuário para registrar uma nova conta a receber no banco de dados.
    """
    limpar_tela()
    print("--- ADICIONAR NOVA CONTA A RECEBER ---")

    # Loop para garantir que o ID do cliente seja válido
    while True:
        try:
            id_cliente_str = input("ID do Cliente (Consulte a lista de clientes) (Enter para sair): ").strip()
            if not id_cliente_str:
                return
            cliente_id = int(id_cliente_str)
            # verificar se o cliente realmente existe no banco.
            if buscar_cliente(cliente_id):
                break
            else:
                print("ERRO: ID de Cliente não encontrado. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número para o ID do cliente.")

    # Laço para que a descrição não fique em branco
    descricao = input("Descrição da Receita: ").strip()
    while not descricao:
        descricao = input("Descrição não pode ser vazia. Tente novamente: ").strip()

    # Laço para validar a entrada do valor
    while True:
        try:
            valor = float(input("Valor Total a Receber: ").replace(',', '.'))
            if valor > 0:
                break
            else:
                print("O valor deve ser um número positivo.")
        except ValueError:
            print("Valor inválido. Use números (ex: 100.50).")

    # laço para validar o formato da data de vencimento
    while True:
        data_vencimento_str = input("Data de Vencimento (AAAA-MM-DD): ").strip()
        try:
            # Data no formato correto para ser salva no banco
            data_vencimento = datetime.datetime.strptime(data_vencimento_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            break
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD (ex: 2025-12-31).")

    # inserir os dados validados no banco
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contas_a_receber (cliente_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'Pendente')",
                (cliente_id, descricao, valor, data_vencimento)
            )
            print("\nConta a Receber cadastrada com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar a conta a receber: {e}")


# Função 2
def exibir_lista_contas_a_receber():
    """
    busca calcula e mostra todas as contas a receber com seus saldos atualizados.
    """
    limpar_tela()
    print("--- LISTA DE CONTAS A RECEBER ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    car.id,
                    c.nome AS nome_cliente,
                    car.descricao,
                    car.valor,
                    COALESCE(SUM(l.valor), 0) AS valor_recebido,
                    (car.valor - COALESCE(SUM(l.valor), 0)) AS saldo_a_receber,
                    car.data_vencimento,
                    car.status
                FROM
                    contas_a_receber car
                JOIN
                    clientes c ON car.cliente_id = c.id
                LEFT JOIN
                    lancamentos l ON car.id = l.conta_a_receber_id AND l.tipo = 'Receita'
                GROUP BY
                    car.id
                ORDER BY
                    car.id;
            """)
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhuma conta a receber encontrada.")
                return []

            # Montar a tabela usando as dimensões de formatação
            header = (
                f"{'ID':<{LARGURA_ID_CR}} | {'CLIENTE':<{LARGURA_CLIENTE_CR}} | {'DESCRIÇÃO':<{LARGURA_DESCRICAO_CR}} | "
                f"{'VALOR TOTAL':<{LARGURA_VALOR_TOTAL_CR}} | {'RECEBIDO':<{LARGURA_VALOR_RECEBIDO_CR}} | "
                f"{'SALDO':<{LARGURA_SALDO_CR}} | {'VENCIMENTO':<{LARGURA_VENCIMENTO_CR}} | {'STATUS':<{LARGURA_STATUS_CR}}"
            )
            print(header)
            print("-" * len(header))

            for conta in resultados:
                print(
                    f"{conta[0]:<{LARGURA_ID_CR}} | {conta[1]:<{LARGURA_CLIENTE_CR}} | {conta[2]:<{LARGURA_DESCRICAO_CR}} | "
                    f"R${conta[3]:<{LARGURA_VALOR_TOTAL_CR - 2}.2f} | R${conta[4]:<{LARGURA_VALOR_RECEBIDO_CR - 2}.2f} | "
                    f"R${conta[5]:<{LARGURA_SALDO_CR - 2}.2f} | {conta[6]:<{LARGURA_VENCIMENTO_CR}} | {conta[7]:<{LARGURA_STATUS_CR}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar as contas a receber: {e}")
        return []


# função 3
def registrar_recebimento():
    """
     registrar um pagamento (parcial ou total) para uma conta a receber
    """
    limpar_tela()
    print("--- REGISTRAR RECEBIMENTO DE CONTA ---")
    lista_contas = exibir_lista_contas_a_receber()
    if not lista_contas:
        return

    #Selecionar a conta a receber que terá um pagamento registrado
    conta_id = buscar_id(lista_contas, "registrar recebimento para a conta")
    if not conta_id:
        return

    # Saldo pendente da conta selecionada
    saldo_a_receber = 0
    valor_total = 0
    descricao_conta = ""
    for conta in lista_contas:
        if conta[0] == conta_id:
            valor_total = conta[3]
            saldo_a_receber = conta[5]
            descricao_conta = conta[2]
            break

    if saldo_a_receber <= 0:
        print(f"\nA conta ID {conta_id} já foi totalmente recebida. Nenhuma ação necessária.")
        return

    print(f"\nSaldo a receber da conta ID {conta_id}: R${saldo_a_receber:.2f}")

    # Validar o valor do pagamento
    while True:
        try:
            valor_recebimento = float(input("Digite o valor recebido: ").replace(',', '.'))
            # Pagamento não seja maior que a dívida.
            if 0 < valor_recebimento <= saldo_a_receber:
                break
            else:
                print(f"Valor inválido. Deve ser um número positivo e no máximo R${saldo_a_receber:.2f}.")
        except ValueError:
            print("Entrada inválida. Digite um número.")

    # Selecionar a conta bancária que o dinheiro vai entrar
    conta_bancaria_id = id_conta_lancamento()
    if not conta_bancaria_id:
        print("Registro de recebimento cancelado.")
        return

    data_recebimento = datetime.date.today().isoformat()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            #inserir o novo pagamento na tabela de lançamentos
            cursor.execute(
                """
                INSERT INTO lancamentos (descricao, valor, data_lancamento, tipo, conta_bancaria_id, conta_a_receber_id)
                VALUES (?, ?, ?, 'Receita', ?, ?)
                """,
                (f"Receb. ref. conta ID {conta_id}: {descricao_conta}", valor_recebimento, data_recebimento,
                 conta_bancaria_id, conta_id)
            )
            novo_lancamento_id = cursor.lastrowid
            print(f"\nLançamento de receita ID {novo_lancamento_id} criado com sucesso.")

            # Atualizar o status da conta a receber
            cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE conta_a_receber_id = ?", (conta_id,))
            total_recebido_atualizado = cursor.fetchone()[0]

            # Novo status da conta
            novo_status = 'Parcial'
            # Se o total recebido for maior ou igual ao valor original da conta ela ta quitada
            if total_recebido_atualizado >= valor_total:
                novo_status = 'Recebido'

            # atualizar tabela
            cursor.execute(
                "UPDATE contas_a_receber SET status = ?, data_recebimento = ? WHERE id = ?",
                (novo_status, data_recebimento, conta_id)
            )
            print(f"Status da conta ID {conta_id} atualizado para '{novo_status}'.")

    except Exception as e:
        print(f"\nERRO ao registrar recebimento: {e}")


# Função 4
def deletar_conta_a_receber():
    """
    Deleta uma conta a receber
    """
    limpar_tela()
    print("--- DELETAR CONTA A RECEBER ---")
    lista_contas = exibir_lista_contas_a_receber()
    if not lista_contas:
        return
    deletar_item("conta a receber", lista_contas)


# Função do menu
def menu_contas_a_receber():
    """
    menu de opções
    """
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Conta a Receber",
            "Registrar Recebimento de Conta",
            "Ver Lista de Contas a Receber",
            "Deletar Conta a Receber",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE CONTAS A RECEBER", opcoes)

        # chamar a função que corresponda com a escolha
        if escolha == 1:
            adicionar_conta_a_receber()
        elif escolha == 2:
            registrar_recebimento()
        elif escolha == 3:
            exibir_lista_contas_a_receber()
        elif escolha == 4:
            deletar_conta_a_receber()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")

if __name__ == '__main__':
    menu_contas_a_receber()
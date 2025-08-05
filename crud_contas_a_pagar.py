import datetime
from funcoes import (
    gerenciar_conexao, buscar_id, deletar as deletar_item,
    exibir_menu_e_obter_opcao, buscar_fornecedor, limpar_tela, id_conta_lancamento
)

# formatação
LARGURA_ID_CP = 4
LARGURA_FORNECEDOR_CP = 20
LARGURA_DESCRICAO_CP = 25
LARGURA_VALOR_TOTAL_CP = 12
LARGURA_VALOR_PAGO_CP = 12
LARGURA_SALDO_CP = 12
LARGURA_VENCIMENTO_CP = 12
LARGURA_STATUS_CP = 10


# Função 1
def adicionar_conta_a_pagar():
    """
    Dados do usuário para criar e registrar uma nova conta a pagar no sistema
    """
    limpar_tela()
    print("--- ADICIONAR NOVA CONTA A PAGAR ---")

    # loop para garantir que o ID exista
    while True:
        try:
            id_fornecedor_str = input("ID do Fornecedor (Consulte a lista de fornecedores) (Enter para sair): ").strip()
            if not id_fornecedor_str:
                return
            fornecedor_id = int(id_fornecedor_str)
            if buscar_fornecedor(fornecedor_id):
                break
            else:
                print("ERRO: ID de Fornecedor não encontrado. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número para o ID do fornecedor.")

    # loop para não deixar que a descrição seja salva em branco
    descricao = input("Descrição da Despesa: ").strip()
    while not descricao:
        descricao = input("Descrição não pode ser vazia. Tente novamente: ").strip()

    # loop para validar a entrada
    while True:
        try:
            valor = float(input("Valor Total a Pagar: ").replace(',', '.'))
            if valor > 0:
                break
            else:
                print("O valor deve ser um número positivo.")
        except ValueError:
            print("Valor inválido. Use números (ex: 100.50).")

    # Loop para validar o formato da data
    while True:
        data_vencimento_str = input("Data de Vencimento (AAAA-MM-DD): ").strip()
        try:
            data_vencimento = datetime.datetime.strptime(data_vencimento_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            break
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD (ex: 2025-12-31).")

    # Inserir no banco de dados
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contas_a_pagar (fornecedor_id, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, 'Pendente')",
                (fornecedor_id, descricao, valor, data_vencimento)
            )
            print("\nConta a Pagar cadastrada com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar a conta a pagar: {e}")


# Função 2
def exibir_lista_contas_a_pagar():
    """
    Busca no banco de dados todas as contas a pagar e calcula os saldos em tempo real
    """
    limpar_tela()
    print("--- LISTA DE CONTAS A PAGAR ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    cap.id,
                    f.nome AS nome_fornecedor,
                    cap.descricao,
                    cap.valor,
                    COALESCE(SUM(l.valor), 0) AS valor_pago,
                    (cap.valor - COALESCE(SUM(l.valor), 0)) AS saldo_devedor,
                    cap.data_vencimento,
                    cap.status
                FROM
                    contas_a_pagar cap
                JOIN
                    fornecedores f ON cap.fornecedor_id = f.id
                LEFT JOIN
                    lancamentos l ON cap.id = l.conta_a_pagar_id AND l.tipo = 'Despesa'
                GROUP BY
                    cap.id
                ORDER BY
                    cap.id;
            """)
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhuma conta a pagar encontrada.")
                return []

            # Monta o cabeçalho
            header = (
                f"{'ID':<{LARGURA_ID_CP}} | {'FORNECEDOR':<{LARGURA_FORNECEDOR_CP}} | {'DESCRIÇÃO':<{LARGURA_DESCRICAO_CP}} | "
                f"{'VALOR TOTAL':<{LARGURA_VALOR_TOTAL_CP}} | {'VALOR PAGO':<{LARGURA_VALOR_PAGO_CP}} | "
                f"{'SALDO':<{LARGURA_SALDO_CP}} | {'VENCIMENTO':<{LARGURA_VENCIMENTO_CP}} | {'STATUS':<{LARGURA_STATUS_CP}}"
            )
            print(header)
            print("-" * len(header))

            #imprime cada linha da tabela
            for conta in resultados:
                print(
                    f"{conta[0]:<{LARGURA_ID_CP}} | {conta[1]:<{LARGURA_FORNECEDOR_CP}} | {conta[2]:<{LARGURA_DESCRICAO_CP}} | "
                    f"R${conta[3]:<{LARGURA_VALOR_TOTAL_CP - 2}.2f} | R${conta[4]:<{LARGURA_VALOR_PAGO_CP - 2}.2f} | "
                    f"R${conta[5]:<{LARGURA_SALDO_CP - 2}.2f} | {conta[6]:<{LARGURA_VENCIMENTO_CP}} | {conta[7]:<{LARGURA_STATUS_CP}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar as contas a pagar: {e}")
        return []


#Função 3
def registrar_pagamento():
    """
    Registra um pagamento para uma conta a pagar
    """
    limpar_tela()
    print("--- REGISTRAR PAGAMENTO DE CONTA ---")
    lista_contas = exibir_lista_contas_a_pagar()
    if not lista_contas:
        return

    # conta para registrar um pagamento
    conta_id = buscar_id(lista_contas, "registrar pagamento para a conta")
    if not conta_id:
        return

    # o sistema busca na lista o saldo devedor atual da conta
    saldo_devedor = 0
    valor_total = 0
    descricao_conta = ""
    for conta in lista_contas:
        if conta[0] == conta_id:
            valor_total = conta[3]      # valor total
            saldo_devedor = conta[5]    # Pega o saldo devedor
            descricao_conta = conta[2]  # Pega a descrição
            break

    # pagamentos não sejam feitos para contas já quitadas
    if saldo_devedor <= 0:
        print(f"\nA conta ID {conta_id} já está totalmente paga. Nenhuma ação necessária.")
        return

    print(f"\nSaldo devedor da conta ID {conta_id}: R${saldo_devedor:.2f}")

    # O usuário informa o valor do pagamento
    while True:
        try:
            valor_pagamento = float(input("Digite o valor a ser pago: ").replace(',', '.'))
            # pagamento não seja negativo ou maior que a dívida
            if 0 < valor_pagamento <= saldo_devedor:
                break
            else:
                print(f"Valor inválido. Deve ser um número positivo e no máximo R${saldo_devedor:.2f}.")
        except ValueError:
            print("Entrada inválida. Digite um número.")

    # qual conta bancária da empresa o dinheiro vai sair
    conta_bancaria_id = id_conta_lancamento()
    if not conta_bancaria_id:
        print("Registro de pagamento cancelado.")
        return

    data_pagamento = datetime.date.today().isoformat()

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()

            # novo registro na tabela lançamentos
            cursor.execute(
                """
                INSERT INTO lancamentos (descricao, valor, data_lancamento, tipo, conta_bancaria_id, conta_a_pagar_id)
                VALUES (?, ?, ?, 'Despesa', ?, ?)
                """,
                (f"Pagamento ref. conta ID {conta_id}: {descricao_conta}", valor_pagamento, data_pagamento,
                 conta_bancaria_id, conta_id)
            )
            novo_lancamento_id = cursor.lastrowid
            print(f"\nLançamento de despesa ID {novo_lancamento_id} criado com sucesso.")

            # atualiza o status da conta a paga
            cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE conta_a_pagar_id = ?", (conta_id,))
            total_pago_atualizado = cursor.fetchone()[0]

            # parcial ou pago
            novo_status = 'Parcial'
            if total_pago_atualizado >= valor_total:
                novo_status = 'Pago'

            # atualiza a tabela
            cursor.execute(
                "UPDATE contas_a_pagar SET status = ?, data_pagamento = ? WHERE id = ?",
                (novo_status, data_pagamento, conta_id)
            )
            print(f"Status da conta ID {conta_id} atualizado para '{novo_status}'.")

    except Exception as e:
        print(f"\nERRO ao registrar pagamento: {e}")


# Função 4
def deletar_conta_a_pagar():
    """
    Deleta uma conta a pagar
    """
    limpar_tela()
    print("--- DELETAR CONTA A PAGAR ---")
    lista_contas = exibir_lista_contas_a_pagar()
    if not lista_contas:
        return
    deletar_item("conta a pagar", lista_contas)


# menu
def menu_contas_a_pagar():
    """
    Exibe o menu
    """
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Conta a Pagar",
            "Registrar Pagamento de Conta",
            "Ver Lista de Contas a Pagar",
            "Deletar Conta a Pagar",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE CONTAS A PAGAR", opcoes)

        if escolha == 1:
            adicionar_conta_a_pagar()
        elif escolha == 2:
            registrar_pagamento()
        elif escolha == 3:
            exibir_lista_contas_a_pagar()
        elif escolha == 4:
            deletar_conta_a_pagar()
        elif escolha == 5:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")

if __name__ == '__main__':
    menu_contas_a_pagar()
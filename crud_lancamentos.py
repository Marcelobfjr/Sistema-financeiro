import datetime
from funcoes import (
    gerenciar_conexao, buscar_id, deletar as deletar_item,
    exibir_menu_e_obter_opcao, id_conta_lancamento, limpar_tela
)
from crud_contas_a_pagar import exibir_lista_contas_a_pagar
from crud_contas_a_receber import exibir_lista_contas_a_receber

LARGURA_ID_LANC = 5
LARGURA_DESCRICAO_LANC = 35
LARGURA_VALOR_LANC = 12
LARGURA_DATA_LANC = 12
LARGURA_TIPO_LANC = 10
LARGURA_CONTA_BANC_LANC = 25
LARGURA_VINCULO_LANC = 20  # Para o ID e tipo de vínculo


def definir_tipo_lancamento() -> str:
    #DECIDIR ENTRE RECEITA E DESPESA
    tipos = ["Receita", "Despesa"]
    escolha = exibir_menu_e_obter_opcao("SELECIONE O TIPO DE LANÇAMENTO", tipos)
    return tipos[escolha - 1]


#ADICIONAR LANÇAMENTO
def adicionar_lancamento():
    limpar_tela()
    print("--- ADICIONAR NOVO LANÇAMENTO AVULSO ---")
    print("Nota: Para pagar ou receber uma conta, use os menus específicos.")

    descricao = input("Descrição do Lançamento: ").strip()
    while not descricao:
        descricao = input("Descrição não pode ser vazia. Tente novamente: ").strip()

    while True:
        try:
            valor = float(input("Valor do Lançamento: ").replace(',', '.'))
            if valor > 0:
                break
            else:
                print("O valor deve ser positivo.")
        except ValueError:
            print("Valor inválido. Use números (ex: 100.50).")

    data_lancamento_str = input(
        f"Data do Lançamento (padrão: hoje - {datetime.date.today().isoformat()}) [AAAA-MM-DD]: ").strip()
    if not data_lancamento_str:
        data_lancamento = datetime.date.today().isoformat()
    else:
        while True:
            try:
                data_lancamento = datetime.datetime.strptime(data_lancamento_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                break
            except ValueError:
                data_lancamento_str = input("Formato inválido. Use AAAA-MM-DD: ").strip()

    tipo = definir_tipo_lancamento()

    conta_bancaria_id = id_conta_lancamento()
    if conta_bancaria_id is None:
        print("Lançamento cancelado.")
        return

    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO lancamentos (descricao, valor, data_lancamento, tipo, conta_bancaria_id) VALUES (?, ?, ?, ?, ?)",
                (descricao, valor, data_lancamento, tipo, conta_bancaria_id)
            )
            print("\nLançamento avulso cadastrado com sucesso!")
    except Exception as e:
        print(f"\nERRO ao adicionar o lançamento: {e}")


#LISTA DE LANÇAMENTOS
def exibir_lista_lancamentos():
    limpar_tela()
    print("--- LISTA DE TODOS OS LANÇAMENTOS ---")
    try:
        with gerenciar_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    l.id,
                    l.descricao,
                    l.valor,
                    l.data_lancamento,
                    l.tipo,
                    cb.nome_conta,
                    l.conta_a_pagar_id,
                    l.conta_a_receber_id
                FROM
                    lancamentos l
                JOIN
                    contas_bancarias cb ON l.conta_bancaria_id = cb.id
                ORDER BY
                    l.id;
            """)
            resultados = cursor.fetchall()

            if not resultados:
                print("Nenhum lançamento encontrado.")
                return []

            header = (
                f"{'ID':<{LARGURA_ID_LANC}} | {'DESCRIÇÃO':<{LARGURA_DESCRICAO_LANC}} | {'VALOR':<{LARGURA_VALOR_LANC}} | "
                f"{'DATA':<{LARGURA_DATA_LANC}} | {'TIPO':<{LARGURA_TIPO_LANC}} | {'CONTA':<{LARGURA_CONTA_BANC_LANC}} | "
                f"{'VÍNCULO':<{LARGURA_VINCULO_LANC}}"
            )
            print(header)
            print("-" * len(header))

            for lanc in resultados:
                vinculo = "Nenhum"
                if lanc[6]:
                    vinculo = f"Pagamento (ID {lanc[6]})"
                elif lanc[7]:
                    vinculo = f"Recebimento (ID {lanc[7]})"

                print(
                    f"{lanc[0]:<{LARGURA_ID_LANC}} | {lanc[1]:<{LARGURA_DESCRICAO_LANC}} | R${lanc[2]:<{LARGURA_VALOR_LANC - 2}.2f} | "
                    f"{lanc[3]:<{LARGURA_DATA_LANC}} | {lanc[4]:<{LARGURA_TIPO_LANC}} | {lanc[5]:<{LARGURA_CONTA_BANC_LANC}} | "
                    f"{vinculo:<{LARGURA_VINCULO_LANC}}"
                )
            print("-" * len(header))
            return resultados
    except Exception as e:
        print(f"\nERRO ao listar os lançamentos: {e}")
        return []


#DELETAR LANÇAMENTO
def deletar_lancamento():
    limpar_tela()
    print("--- DELETAR LANÇAMENTO ---")
    print("ATENÇÃO: Deletar um lançamento vinculado a uma conta a pagar/receber")
    print("pode causar inconsistências no saldo dessa conta. O status da conta NÃO será revertido.")

    lista_lancamentos = exibir_lista_lancamentos()
    if not lista_lancamentos:
        return

    deletar_item("lancamento", lista_lancamentos)


#MENU
def menu_lancamentos():
    while True:
        limpar_tela()
        opcoes = [
            "Adicionar Lançamento Avulso",
            "Ver Lista de Lançamentos",
            "Deletar Lançamento",
            "Voltar ao Menu Principal"
        ]
        escolha = exibir_menu_e_obter_opcao("MENU DE LANÇAMENTOS", opcoes)

        if escolha == 1:
            adicionar_lancamento()
        elif escolha == 2:
            exibir_lista_lancamentos()
        elif escolha == 3:
            deletar_lancamento()
        elif escolha == 4:
            print("Retornando ao menu principal...")
            break
        else:
            print("Opção inválida.")

        input("\nPressione Enter para continuar...")
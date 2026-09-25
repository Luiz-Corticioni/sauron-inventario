"""CRUD dos ativos de TI.

O dicionário principal usa o ID inteiro como chave. Assim, uma busca conhecida
por ID pode usar ``ativos.get(id)`` diretamente, sem percorrer todos os itens.
"""

import vulnerabilidades
from utilitarios import (
    cabecalho,
    confirmar,
    escolher_localizacao,
    escolher_tipo_ativo,
    ler_inteiro,
    ler_opcao,
    ler_texto_obrigatorio,
)


def buscar_por_id(ativos, id_ativo):
    """Busca direta pela chave do dicionário."""

    return ativos.get(id_ativo)


def buscar_por_nome(ativos, termo):
    """Busca sequencial e sem diferença entre maiúsculas e minúsculas."""

    termo = termo.casefold().strip()
    if not termo:
        return []
    return [
        ativo
        for ativo in ativos.values()
        if termo in ativo["nome"].casefold()
    ]


def cadastrar(ativos):
    """Cria um ativo e permite inserir sua lista inicial de vulnerabilidades."""

    cabecalho("CADASTRO GUIADO DE ATIVO")
    while True:
        id_ativo = ler_inteiro("ID inteiro do ativo: ", minimo=1)
        if id_ativo not in ativos:
            break
        print(f"[ERRO] O ID {id_ativo} já pertence a outro ativo.")

    nome = ler_texto_obrigatorio("Nome/hostname: ")
    responsavel = ler_texto_obrigatorio("Responsável: ")
    setor = ler_texto_obrigatorio("Setor responsável: ")
    descricao = input("Descrição (opcional): ").strip()
    tipo = escolher_tipo_ativo()
    localizacao = escolher_localizacao(tipo)

    ativo = {
        "id": id_ativo,
        "nome": nome,
        "tipo": tipo,
        "responsavel": responsavel,
        "setor": setor,
        "localizacao": localizacao,
        "descricao": descricao,
        "vulnerabilidades": {},
    }

    # O registro entra antes das vulnerabilidades para o gerador de IDs poder
    # examinar a base inteira, inclusive este novo ativo.
    ativos[id_ativo] = ativo
    print(f"\n[SUCESSO] Ativo '{nome}' [ID {id_ativo}] cadastrado.")

    if confirmar("Deseja cadastrar uma vulnerabilidade inicial? [S/N]: "):
        while True:
            cadastrada = vulnerabilidades.cadastrar(ativos, ativo)
            if not cadastrada:
                break
            if not confirmar("Cadastrar outra vulnerabilidade neste ativo? [S/N]: "):
                break
    return True


def imprimir_ficha(ativo):
    """Exibe o registro em formato semelhante a uma ficha de inventário."""

    cabecalho("FICHA DO ATIVO")
    print(f"ID:                    {ativo['id']}")
    print(f"Nome/hostname:         {ativo['nome']}")
    print(f"Tipo:                  {ativo['tipo'].rotulo}")
    print(f"Código do tipo:        {ativo['tipo'].value}")
    print(f"Responsável:           {ativo['responsavel']}")
    print(f"Setor:                 {ativo['setor']}")
    print(f"Localização:           {ativo['localizacao']}")
    print(f"Descrição:             {ativo['descricao'] or 'Não informada'}")
    quantidade = len(ativo["vulnerabilidades"])
    print(f"Vulnerabilidades:      {quantidade}")

    if not quantidade:
        print("\n[INFO] Ativo sem vulnerabilidades registradas.")
        return

    print("\nRESUMO DE SEGURANÇA")
    print("-" * 64)
    for identificador, item in sorted(ativo["vulnerabilidades"].items()):
        print(
            f"{identificador} | {item['severidade'].value:<7} | "
            f"{item['status'].value:<14} | {item['categoria']}"
        )


def consultar(ativos):
    """Consulta por ID ou por parte do nome, conforme exige o trabalho."""

    if not ativos:
        print("\n[INFO] Nenhum ativo cadastrado.")
        return

    cabecalho("CONSULTAR ATIVO")
    print("1 - Buscar pelo ID")
    print("2 - Buscar pelo nome/hostname")
    print("0 - Voltar")
    escolha = ler_opcao("Opção: ", range(0, 3))

    if escolha == "0":
        return
    if escolha == "1":
        id_ativo = ler_inteiro("ID: ", minimo=1)
        ativo = buscar_por_id(ativos, id_ativo)
        if ativo is None:
            print(f"[INFO] Nenhum ativo possui o ID {id_ativo}.")
            return
        imprimir_ficha(ativo)
        return

    termo = ler_texto_obrigatorio("Nome ou parte do hostname: ")
    encontrados = buscar_por_nome(ativos, termo)
    if not encontrados:
        print(f"[INFO] Nenhum ativo encontrado para '{termo}'.")
        return
    for ativo in sorted(encontrados, key=lambda item: item["id"]):
        imprimir_ficha(ativo)


def listar(ativos):
    """Mostra uma visão compacta de todos os ativos, ordenada por ID."""

    cabecalho("LISTA DE ATIVOS")
    if not ativos:
        print("[INFO] Nenhum ativo cadastrado.")
        return

    print(f"{'ID':<7}{'NOME/HOSTNAME':<23}{'TIPO':<23}{'LOCALIZAÇÃO'}")
    print("-" * 80)
    for ativo in sorted(ativos.values(), key=lambda item: item["id"]):
        print(
            f"{ativo['id']:<7}"
            f"{ativo['nome'][:21]:<23}"
            f"{ativo['tipo'].rotulo[:21]:<23}"
            f"{ativo['localizacao']}"
        )


def selecionar(ativos, finalidade="selecionar"):
    """Seleciona um ativo por ID para as operações que exigem registro único."""

    if not ativos:
        print("[INFO] Nenhum ativo cadastrado.")
        return None
    id_ativo = ler_inteiro(f"ID do ativo a {finalidade}: ", minimo=1)
    ativo = buscar_por_id(ativos, id_ativo)
    if ativo is None:
        print(f"[ERRO] Nenhum ativo foi encontrado com o ID {id_ativo}.")
    return ativo


def atualizar(ativos):
    """Atualiza somente o campo escolhido, evitando redigitar todo o registro."""

    cabecalho("ATUALIZAR ATIVO")
    ativo = selecionar(ativos, "atualizar")
    if ativo is None:
        return False

    print(f"\nAtivo: {ativo['nome']} [ID {ativo['id']}]")
    print("1 - Nome/hostname")
    print("2 - Responsável")
    print("3 - Setor")
    print("4 - Localização")
    print("5 - Tipo")
    print("6 - Descrição")
    print("0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 7))

    if escolha == "0":
        print("[INFO] Atualização cancelada.")
        return False
    if escolha == "1":
        ativo["nome"] = ler_texto_obrigatorio("Novo nome/hostname: ")
    elif escolha == "2":
        ativo["responsavel"] = ler_texto_obrigatorio("Novo responsável: ")
    elif escolha == "3":
        ativo["setor"] = ler_texto_obrigatorio("Novo setor: ")
    elif escolha == "4":
        ativo["localizacao"] = escolher_localizacao(ativo["tipo"])
    elif escolha == "5":
        ativo["tipo"] = escolher_tipo_ativo()
        print("A localização será revisada para o novo tipo.")
        ativo["localizacao"] = escolher_localizacao(ativo["tipo"])
    elif escolha == "6":
        ativo["descricao"] = input("Nova descrição (pode ficar vazia): ").strip()

    print("[SUCESSO] Ativo atualizado.")
    return True


def remover(ativos):
    """Remove o ativo; as vulnerabilidades somem junto por estarem aninhadas nele."""

    cabecalho("REMOVER ATIVO")
    ativo = selecionar(ativos, "remover")
    if ativo is None:
        return False

    print(f"\nID: {ativo['id']}")
    print(f"Nome: {ativo['nome']}")
    print(f"Vulnerabilidades associadas: {len(ativo['vulnerabilidades'])}")
    print("As vulnerabilidades associadas também serão removidas.")
    if not confirmar("Confirmar remoção? [S/N]: "):
        print("[INFO] Remoção cancelada.")
        return False

    del ativos[ativo["id"]]
    print(f"[SUCESSO] Ativo '{ativo['nome']}' e seus dados foram removidos.")
    return True

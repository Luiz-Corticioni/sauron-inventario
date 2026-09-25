"""Operações relacionadas às vulnerabilidades dos ativos."""

import re

from utilitarios import (
    CATALOGO_VULNERABILIDADES,
    cabecalho,
    confirmar,
    escolher_severidade,
    escolher_status_vulnerabilidade,
    exibir_item_catalogo,
    ler_opcao,
    ler_texto_obrigatorio,
)


def gerar_id(ativos):
    """Gera VUL-001, VUL-002... sem reutilizar um identificador existente."""

    maior_numero = 0
    for ativo in ativos.values():
        for identificador in ativo["vulnerabilidades"]:
            correspondencia = re.fullmatch(r"VUL-(\d+)", identificador)
            if correspondencia:
                maior_numero = max(maior_numero, int(correspondencia.group(1)))
    return f"VUL-{maior_numero + 1:03d}"


def _escolher_categoria(permitir_cancelar=True):
    """Explica a categoria escolhida e devolve seus dados para o cadastro."""

    while True:
        cabecalho("ESCOLHA DA CATEGORIA")
        for codigo, item in CATALOGO_VULNERABILIDADES.items():
            print(f"{codigo} - {item['nome']}")
        print("7 - Vulnerabilidade personalizada")
        if permitir_cancelar:
            print("0 - Cancelar")

        validas = [*CATALOGO_VULNERABILIDADES.keys(), "7"]
        if permitir_cancelar:
            validas.append("0")
        escolha = ler_opcao("Opção: ", validas)

        if escolha == "0":
            return None

        if escolha == "7":
            nome = ler_texto_obrigatorio("Nome da categoria personalizada: ")
            orientacao = input("Tratamento sugerido (opcional): ").strip()
            return {"nome": nome, "tratamento": orientacao}

        item = CATALOGO_VULNERABILIDADES[escolha]
        exibir_item_catalogo(item)
        if confirmar("\nUsar esta categoria? [S/N]: "):
            return {"nome": item["nome"], "tratamento": item["tratamento"]}


def cadastrar(ativos, ativo):
    """Cadastra uma vulnerabilidade e devolve True quando houve alteração."""

    cabecalho("CADASTRAR VULNERABILIDADE")
    print(f"Ativo: {ativo['nome']} [ID {ativo['id']}]")

    categoria = _escolher_categoria()
    if categoria is None:
        print("[INFO] Cadastro cancelado.")
        return False

    descricao = ler_texto_obrigatorio("Descreva o problema encontrado: ")
    severidade = escolher_severidade()
    status = escolher_status_vulnerabilidade()
    identificador = gerar_id(ativos)

    ativo["vulnerabilidades"][identificador] = {
        "categoria": categoria["nome"],
        "descricao": descricao,
        "severidade": severidade,
        "status": status,
        "tratamento_sugerido": categoria["tratamento"],
    }
    print(f"\n[SUCESSO] {identificador} cadastrada em '{ativo['nome']}'.")
    return True


def listar(ativo):
    """Exibe todos os campos importantes ou informa que a lista está vazia."""

    cabecalho(f"VULNERABILIDADES DE {ativo['nome'].upper()}")
    vulnerabilidades = ativo["vulnerabilidades"]
    if not vulnerabilidades:
        print("[INFO] Este ativo está sem vulnerabilidades registradas.")
        return

    for identificador, item in sorted(vulnerabilidades.items()):
        print(f"\n[{item['severidade'].value.upper()}] {identificador}")
        print(f"Categoria:  {item['categoria']}")
        print(f"Descrição:  {item['descricao']}")
        print(f"Status:     {item['status'].value}")
        if item.get("tratamento_sugerido"):
            print(f"Orientação: {item['tratamento_sugerido']}")
        print("-" * 64)


def _selecionar(ativo, acao):
    """Localiza uma vulnerabilidade pelo ID antes de atualizar ou remover."""

    if not ativo["vulnerabilidades"]:
        print("[INFO] Este ativo está sem vulnerabilidades registradas.")
        return None, None

    print("Vulnerabilidades disponíveis:")
    for identificador, item in sorted(ativo["vulnerabilidades"].items()):
        print(f"  {identificador} - {item['categoria']} ({item['status'].value})")

    identificador = input(f"ID da vulnerabilidade a {acao}: ").strip().upper()
    vulnerabilidade = ativo["vulnerabilidades"].get(identificador)
    if vulnerabilidade is None:
        print(f"[ERRO] A vulnerabilidade '{identificador}' não foi encontrada neste ativo.")
        return None, None
    return identificador, vulnerabilidade


def atualizar(ativo):
    """Permite alterar um campo por vez, preservando os demais valores."""

    cabecalho("ATUALIZAR VULNERABILIDADE")
    identificador, vulnerabilidade = _selecionar(ativo, "atualizar")
    if vulnerabilidade is None:
        return False

    print("\n1 - Descrição")
    print("2 - Categoria")
    print("3 - Severidade")
    print("4 - Status de tratamento")
    print("0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 5))

    if escolha == "0":
        print("[INFO] Atualização cancelada.")
        return False
    if escolha == "1":
        vulnerabilidade["descricao"] = ler_texto_obrigatorio("Nova descrição: ")
    elif escolha == "2":
        categoria = _escolher_categoria(permitir_cancelar=False)
        vulnerabilidade["categoria"] = categoria["nome"]
        vulnerabilidade["tratamento_sugerido"] = categoria["tratamento"]
    elif escolha == "3":
        vulnerabilidade["severidade"] = escolher_severidade()
    elif escolha == "4":
        vulnerabilidade["status"] = escolher_status_vulnerabilidade()

    print(f"[SUCESSO] {identificador} atualizada.")
    return True


def remover(ativo):
    """Remove somente a vulnerabilidade selecionada após confirmação."""

    cabecalho("REMOVER VULNERABILIDADE")
    identificador, vulnerabilidade = _selecionar(ativo, "remover")
    if vulnerabilidade is None:
        return False

    print(f"\nCategoria: {vulnerabilidade['categoria']}")
    print(f"Descrição: {vulnerabilidade['descricao']}")
    if not confirmar(f"Remover definitivamente {identificador}? [S/N]: "):
        print("[INFO] Remoção cancelada.")
        return False

    del ativo["vulnerabilidades"][identificador]
    print(f"[SUCESSO] {identificador} removida.")
    return True

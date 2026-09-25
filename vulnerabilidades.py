"""CRUD de vulnerabilidades vinculadas a ativos identificados."""

import re

from utilitarios import (
    CATALOGO_VULNERABILIDADES, cabecalho, confirmar, escolher_severidade,
    escolher_status_vulnerabilidade, exibir_item_catalogo, ler_opcao,
    ler_texto_obrigatorio,
)


CODIGO_PERSONALIZADA = 99


def gerar_id(ativos, codigo_categoria):
    """Gera ``VUL-TT-NNN``; TT identifica a categoria da vulnerabilidade."""

    codigo = int(codigo_categoria)
    maior = 0
    padrao = re.compile(rf"VUL-{codigo:02d}-(\d{{3}})$")
    for ativo in ativos.values():
        for identificador in ativo["vulnerabilidades"]:
            correspondencia = padrao.fullmatch(identificador)
            if correspondencia:
                maior = max(maior, int(correspondencia.group(1)))
    return f"VUL-{codigo:02d}-{maior + 1:03d}"


def _escolher_categoria(permitir_cancelar=True):
    while True:
        cabecalho("ESCOLHA DA CATEGORIA")
        print("O ID usará VUL-TT-NNN, onde TT é o código abaixo.")
        for codigo, item in CATALOGO_VULNERABILIDADES.items():
            print(f"{int(codigo):02d} - {item['nome']}")
        print(f"{CODIGO_PERSONALIZADA:02d} - Vulnerabilidade personalizada")
        if permitir_cancelar:
            print("00 - Cancelar")
        validas = [*CATALOGO_VULNERABILIDADES.keys(), str(CODIGO_PERSONALIZADA)]
        validas.extend(f"{int(codigo):02d}" for codigo in CATALOGO_VULNERABILIDADES)
        if permitir_cancelar:
            validas.extend(["0", "00"])
        escolha = ler_opcao("Opção: ", validas)
        if escolha in ("0", "00"):
            return None
        if escolha == str(CODIGO_PERSONALIZADA):
            return {
                "codigo": CODIGO_PERSONALIZADA,
                "nome": ler_texto_obrigatorio("Nome da categoria personalizada: "),
                "tratamento": input("Tratamento sugerido (opcional): ").strip(),
            }
        escolha = str(int(escolha))
        item = CATALOGO_VULNERABILIDADES[escolha]
        exibir_item_catalogo(item)
        if confirmar("\nUsar esta categoria? [S/N]: "):
            return {
                "codigo": int(escolha), "nome": item["nome"],
                "tratamento": item["tratamento"],
            }


def cadastrar(ativos, ativo):
    """Cadastra uma vulnerabilidade no ativo já selecionado."""

    cabecalho("CADASTRAR VULNERABILIDADE")
    print(f"Ativo selecionado: {ativo['hostname']} [ID {ativo['id']}]")
    categoria = _escolher_categoria()
    if categoria is None:
        print("[INFO] Cadastro cancelado.")
        return False
    descricao = ler_texto_obrigatorio("Descreva o problema encontrado: ")
    severidade = escolher_severidade()
    status = escolher_status_vulnerabilidade()
    identificador = gerar_id(ativos, categoria["codigo"])
    ativo["vulnerabilidades"][identificador] = {
        "codigo_categoria": categoria["codigo"],
        "categoria": categoria["nome"], "descricao": descricao,
        "severidade": severidade, "status": status,
        "tratamento_sugerido": categoria["tratamento"],
    }
    print(
        f"\n[SUCESSO] {identificador} cadastrada. "
        f"O código {categoria['codigo']:02d} representa '{categoria['nome']}'."
    )
    return True


def listar(ativo):
    cabecalho(f"VULNERABILIDADES DE {ativo['hostname'].upper()}")
    if not ativo["vulnerabilidades"]:
        print("[INFO] Este ativo está sem vulnerabilidades registradas.")
        return
    for identificador, item in sorted(ativo["vulnerabilidades"].items()):
        print(f"\n[{item['severidade'].value.upper()}] {identificador}")
        print(f"Tipo {item['codigo_categoria']:02d}: {item['categoria']}")
        print(f"Descrição:  {item['descricao']}")
        print(f"Status:     {item['status'].value}")
        if item.get("tratamento_sugerido"):
            print(f"Orientação: {item['tratamento_sugerido']}")


def _selecionar(ativo, acao):
    if not ativo["vulnerabilidades"]:
        print("[INFO] Este ativo está sem vulnerabilidades registradas.")
        return None, None
    for identificador, item in sorted(ativo["vulnerabilidades"].items()):
        print(f"  {identificador} - {item['categoria']} ({item['status'].value})")
    identificador = input(f"ID da vulnerabilidade a {acao}: ").strip().upper()
    vulnerabilidade = ativo["vulnerabilidades"].get(identificador)
    if vulnerabilidade is None:
        print(f"[ERRO] A vulnerabilidade '{identificador}' não foi encontrada neste ativo.")
        return None, None
    return identificador, vulnerabilidade


def atualizar(ativos, ativo):
    """Atualiza um campo; se a categoria mudar, recalcula o ID coerente."""

    cabecalho("ATUALIZAR VULNERABILIDADE")
    identificador, vulnerabilidade = _selecionar(ativo, "atualizar")
    if vulnerabilidade is None:
        return False
    print("\n1 - Descrição\n2 - Categoria\n3 - Severidade")
    print("4 - Status de tratamento\n0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 5))
    if escolha == "0":
        return False
    if escolha == "1":
        vulnerabilidade["descricao"] = ler_texto_obrigatorio("Nova descrição: ")
    elif escolha == "2":
        categoria = _escolher_categoria(permitir_cancelar=False)
        novo_id = gerar_id(ativos, categoria["codigo"])
        vulnerabilidade.update({
            "codigo_categoria": categoria["codigo"],
            "categoria": categoria["nome"],
            "tratamento_sugerido": categoria["tratamento"],
        })
        del ativo["vulnerabilidades"][identificador]
        ativo["vulnerabilidades"][novo_id] = vulnerabilidade
        print(f"[INFO] O ID foi alterado para {novo_id} para refletir a categoria.")
        identificador = novo_id
    elif escolha == "3":
        vulnerabilidade["severidade"] = escolher_severidade()
    else:
        vulnerabilidade["status"] = escolher_status_vulnerabilidade()
    print(f"[SUCESSO] {identificador} atualizada.")
    return True


def remover(ativo):
    cabecalho("REMOVER VULNERABILIDADE")
    identificador, vulnerabilidade = _selecionar(ativo, "remover")
    if vulnerabilidade is None:
        return False
    print(f"\nCategoria: {vulnerabilidade['categoria']}")
    print(f"Descrição: {vulnerabilidade['descricao']}")
    if not confirmar(f"Remover definitivamente {identificador}? [S/N]: "):
        return False
    del ativo["vulnerabilidades"][identificador]
    print(f"[SUCESSO] {identificador} removida.")
    return True

"""CRUD de ativos com identificação automática e localização controlada."""

import estrutura
import vulnerabilidades
from identificacao import (
    gerar_hostname,
    gerar_id_ativo,
    sugerir_codigo_fabricante,
    validar_codigo_fabricante,
    validar_numero_serie,
)
from utilitarios import cabecalho, confirmar, escolher_tipo_ativo, ler_opcao, ler_texto_obrigatorio


def buscar_por_id(ativos, id_ativo):
    """Busca por uma chave estruturada, ignorando letras minúsculas."""

    return ativos.get(str(id_ativo).strip().upper())


def buscar_por_nome(ativos, termo):
    """Pesquisa em hostname, usuário, responsável e fabricante."""

    termo = termo.casefold().strip()
    if not termo:
        return []
    campos = ("hostname", "usuario", "responsavel", "fabricante")
    return [
        ativo for ativo in ativos.values()
        if any(termo in ativo[campo].casefold() for campo in campos)
    ]


def _ler_codigo_fabricante(fabricante):
    sugestao = sugerir_codigo_fabricante(fabricante)
    while True:
        entrada = input(
            f"Código do fabricante [ENTER usa {sugestao}; 1 a 3 letras]: "
        ).strip().upper()
        codigo = entrada or sugestao
        if validar_codigo_fabricante(codigo):
            return codigo
        print("[ERRO] Informe somente de uma a três letras.")


def _ler_numero_serie():
    while True:
        serie = input("Número de série patrimonial (3 a 12 algarismos): ").strip()
        if validar_numero_serie(serie):
            return serie
        print("[ERRO] Use somente de 3 a 12 algarismos.")


def _ler_identidade(ativos, tipo=None, id_atual=None):
    """Obtém os dados mínimos e devolve ID e hostname calculados."""

    tipo = tipo or escolher_tipo_ativo()
    fabricante = ler_texto_obrigatorio("Fabricante: ")
    codigo = _ler_codigo_fabricante(fabricante)
    serie = _ler_numero_serie()
    usuario = ler_texto_obrigatorio("Nome do usuário associado ao ativo: ")
    identificador = gerar_id_ativo(tipo, codigo, serie)
    hostname = gerar_hostname(tipo, usuario, serie)
    if identificador in ativos and identificador != id_atual:
        print(f"[ERRO] O ID automático {identificador} já pertence a outro ativo.")
        return None
    if any(
        outro["hostname"] == hostname and outro["id"] != id_atual
        for outro in ativos.values()
    ):
        print(f"[ERRO] O hostname automático {hostname} já está em uso.")
        return None
    print("\nIdentificação calculada pelo sistema:")
    print(f"  ID do ativo: {identificador} = tipo {tipo.value} + fabricante {codigo} + série {serie}")
    print(f"  Hostname:    {hostname} = prefixo {tipo.name} + usuário + série")
    return {
        "id": identificador, "hostname": hostname, "nome": hostname,
        "tipo": tipo, "fabricante": fabricante,
        "codigo_fabricante": codigo, "numero_serie": serie, "usuario": usuario,
    }


def _escolher_posicao(base, tipo):
    if not base["setores"]:
        print("[ERRO] Cadastre um setor antes de cadastrar ativos.")
        return None, None
    setor_id = estrutura.selecionar_setor(base)
    if setor_id is None:
        return None, None
    sala_id = estrutura.selecionar_sala(base, setor_id, tipo=tipo)
    return (setor_id, sala_id) if sala_id is not None else (None, None)


def cadastrar(base):
    """Cria ID/hostname automaticamente e valida a sala escolhida."""

    ativos = base["ativos"]
    cabecalho("CADASTRO GUIADO DE ATIVO")
    print("O ID e o hostname não são digitados livremente: o Sauron irá gerá-los.")
    identidade = _ler_identidade(ativos)
    if identidade is None:
        return False
    responsavel = ler_texto_obrigatorio("Responsável técnico: ")
    descricao = input("Descrição (opcional): ").strip()
    print("\nDefina a posição do ativo na estrutura da empresa.")
    setor_id, sala_id = _escolher_posicao(base, identidade["tipo"])
    if setor_id is None:
        print("[INFO] Cadastro cancelado porque a posição não foi definida.")
        return False
    ativo = {
        **identidade, "responsavel": responsavel, "setor_id": setor_id,
        "sala_id": sala_id, "descricao": descricao, "vulnerabilidades": {},
    }
    ativos[ativo["id"]] = ativo
    print(f"\n[SUCESSO] {ativo['hostname']} [ID {ativo['id']}] cadastrado.")
    if confirmar("Deseja cadastrar uma vulnerabilidade inicial? [S/N]: "):
        while vulnerabilidades.cadastrar(ativos, ativo):
            if not confirmar("Cadastrar outra vulnerabilidade neste ativo? [S/N]: "):
                break
    return True


def imprimir_ficha(base, ativo):
    cabecalho("FICHA DO ATIVO")
    print(f"ID estruturado:         {ativo['id']}")
    print(f"Hostname automático:    {ativo['hostname']}")
    print(f"Tipo/código:            {ativo['tipo'].rotulo} / {ativo['tipo'].value}")
    print(f"Fabricante/código:      {ativo['fabricante']} / {ativo['codigo_fabricante']}")
    print(f"Número de série:        {ativo['numero_serie']}")
    print(f"Usuário associado:      {ativo['usuario']}")
    print(f"Responsável técnico:    {ativo['responsavel']}")
    print(f"Setor:                  {estrutura.caminho_setor(base, ativo['setor_id'])}")
    print(f"Sala:                   {ativo['sala_id']} — {estrutura.nome_sala(base, ativo['sala_id'])}")
    print(f"Descrição:              {ativo['descricao'] or 'Não informada'}")
    print(f"Vulnerabilidades:       {len(ativo['vulnerabilidades'])}")
    for identificador, item in sorted(ativo["vulnerabilidades"].items()):
        print(
            f"  {identificador} | {item['severidade'].value:<7} | "
            f"{item['status'].value:<14} | {item['categoria']}"
        )


def consultar(base):
    if not base["ativos"]:
        print("\n[INFO] Nenhum ativo cadastrado.")
        return
    cabecalho("CONSULTAR ATIVO")
    print("1 - Buscar pelo ID estruturado")
    print("2 - Buscar por hostname, usuário, responsável ou fabricante")
    print("0 - Voltar")
    escolha = ler_opcao("Opção: ", range(0, 3))
    if escolha == "0":
        return
    if escolha == "1":
        id_ativo = input("ID (ex.: 4H21444): ").strip().upper()
        ativo = buscar_por_id(base["ativos"], id_ativo)
        if ativo is None:
            print(f"[INFO] Nenhum ativo possui o ID {id_ativo}.")
        else:
            imprimir_ficha(base, ativo)
        return
    termo = ler_texto_obrigatorio("Termo da busca: ")
    encontrados = buscar_por_nome(base["ativos"], termo)
    if not encontrados:
        print(f"[INFO] Nenhum ativo encontrado para '{termo}'.")
    for ativo in sorted(encontrados, key=lambda item: item["id"]):
        imprimir_ficha(base, ativo)


def listar(base):
    cabecalho("LISTA DE ATIVOS")
    if not base["ativos"]:
        print("[INFO] Nenhum ativo cadastrado.")
        return
    print(f"{'ID':<17}{'HOSTNAME':<32}{'TIPO':<22}{'SALA':<10}SETOR")
    print("-" * 110)
    for ativo in sorted(base["ativos"].values(), key=lambda item: item["id"]):
        print(
            f"{ativo['id']:<17}{ativo['hostname'][:30]:<32}"
            f"{ativo['tipo'].rotulo[:20]:<22}{ativo['sala_id']:<10}"
            f"{estrutura.caminho_setor(base, ativo['setor_id'])}"
        )


def selecionar(base, finalidade="selecionar"):
    if not base["ativos"]:
        print("[INFO] Nenhum ativo cadastrado.")
        return None
    listar(base)
    id_ativo = input(f"ID estruturado do ativo a {finalidade}: ").strip().upper()
    ativo = buscar_por_id(base["ativos"], id_ativo)
    if ativo is None:
        print(f"[ERRO] Nenhum ativo foi encontrado com o ID {id_ativo}.")
    return ativo


def _atualizar_identidade(base, ativo):
    antiga_chave = ativo["id"]
    identidade = _ler_identidade(base["ativos"], id_atual=antiga_chave)
    if identidade is None:
        return False
    ativo.update(identidade)
    if ativo["id"] != antiga_chave:
        del base["ativos"][antiga_chave]
        base["ativos"][ativo["id"]] = ativo
    return True


def atualizar(base):
    cabecalho("ATUALIZAR ATIVO")
    ativo = selecionar(base, "atualizar")
    if ativo is None:
        return False
    print(f"\nAtivo: {ativo['hostname']} [ID {ativo['id']}]")
    print("1 - Identificação (tipo, fabricante, série, usuário, ID e hostname)")
    print("2 - Responsável técnico")
    print("3 - Setor e sala")
    print("4 - Sala dentro do setor atual")
    print("5 - Descrição\n0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 6))
    if escolha == "0":
        return False
    if escolha == "1":
        return _atualizar_identidade(base, ativo)
    if escolha == "2":
        ativo["responsavel"] = ler_texto_obrigatorio("Novo responsável técnico: ")
    elif escolha == "3":
        setor_id, sala_id = _escolher_posicao(base, ativo["tipo"])
        if setor_id is None:
            return False
        ativo["setor_id"], ativo["sala_id"] = setor_id, sala_id
    elif escolha == "4":
        sala_id = estrutura.selecionar_sala(base, ativo["setor_id"], tipo=ativo["tipo"])
        if sala_id is None:
            return False
        ativo["sala_id"] = sala_id
    elif escolha == "5":
        ativo["descricao"] = input("Nova descrição (pode ficar vazia): ").strip()
    print("[SUCESSO] Ativo atualizado.")
    return True


def remover(base):
    cabecalho("REMOVER ATIVO")
    ativo = selecionar(base, "remover")
    if ativo is None:
        return False
    print(f"\n{ativo['id']} — {ativo['hostname']}")
    print(f"Vulnerabilidades que também serão removidas: {len(ativo['vulnerabilidades'])}")
    if not confirmar("Confirmar remoção? [S/N]: "):
        return False
    del base["ativos"][ativo["id"]]
    print(f"[SUCESSO] Ativo '{ativo['hostname']}' removido.")
    return True

"""Gestão hierárquica de setores, subsetores e salas controladas."""

import auditoria
import autenticacao
from utilitarios import TipoAtivo, cabecalho, confirmar, ler_inteiro, ler_opcao, ler_texto_obrigatorio


CATEGORIAS_SALA = {
    "1": ("SERVIDORES", "Sala de Servidores"),
    "2": ("TELECOM", "Armário de Telecomunicações"),
    "3": ("ESCRITORIO", "Escritório ou sala de usuários"),
    "4": ("DATACENTER_NUVEM", "Datacenter ou ambiente em nuvem"),
    "5": ("LABORATORIO", "Laboratório técnico"),
    "6": ("OUTRO", "Outro local controlado"),
}

LOCAIS_RECOMENDADOS = {
    TipoAtivo.SERVIDOR: {"SERVIDORES", "DATACENTER_NUVEM"},
    TipoAtivo.NOTEBOOK: {"ESCRITORIO", "LABORATORIO"},
    TipoAtivo.ESTACAO_DE_TRABALHO: {"ESCRITORIO", "LABORATORIO"},
    TipoAtivo.SWITCH: {"SERVIDORES", "TELECOM", "LABORATORIO"},
    TipoAtivo.ROTEADOR: {"SERVIDORES", "TELECOM", "LABORATORIO"},
    TipoAtivo.IMPRESSORA_DE_REDE: {"ESCRITORIO", "LABORATORIO"},
    TipoAtivo.APLICACAO_WEB: {"SERVIDORES", "DATACENTER_NUVEM"},
    TipoAtivo.BANCO_DE_DADOS: {"SERVIDORES", "DATACENTER_NUVEM"},
    TipoAtivo.SOFTWARE_LICENCIADO: {"ESCRITORIO", "DATACENTER_NUVEM"},
}


def proximo_id_setor(registros):
    return max(registros, default=0) + 1


def proximo_id_sala(registros):
    """Gera SAL-001, SAL-002... a partir das chaves existentes."""

    numeros = [int(i[4:]) for i in registros if i.startswith("SAL-") and i[4:].isdigit()]
    return f"SAL-{max(numeros, default=0) + 1:03d}"


def caminho_setor(base, setor_id):
    nomes, atual, visitados = [], setor_id, set()
    while atual is not None and atual in base["setores"] and atual not in visitados:
        visitados.add(atual)
        setor = base["setores"][atual]
        nomes.append(setor["nome"])
        atual = setor["setor_pai_id"]
    return " > ".join(reversed(nomes)) or "Setor não encontrado"


def nome_sala(base, sala_id):
    sala = base["salas"].get(sala_id)
    return sala["nome"] if sala else "Sala não encontrada"


def _filhos(base, setor_id):
    return sorted(
        (s for s in base["setores"].values() if s["setor_pai_id"] == setor_id),
        key=lambda item: item["nome"].casefold(),
    )


def _descendentes(base, setor_id):
    resultado, pilha = set(), [setor_id]
    while pilha:
        atual = pilha.pop()
        for filho in _filhos(base, atual):
            if filho["id"] not in resultado:
                resultado.add(filho["id"])
                pilha.append(filho["id"])
    return resultado


def rotulo_categoria(categoria):
    for _, (codigo, rotulo) in CATEGORIAS_SALA.items():
        if codigo == categoria:
            return rotulo
    return categoria


def listar_tabela_salas(base, setor_id=None):
    """Explica os IDs tabelados e mostra os locais cadastrados."""

    print("\nFormato do ID de sala: SAL-NNN (ex.: SAL-007).")
    print(f"{'ID':<10}{'CATEGORIA':<24}{'SALA':<30}SETOR")
    print("-" * 92)
    salas = base["salas"].values()
    if setor_id is not None:
        salas = (sala for sala in salas if sala["setor_id"] == setor_id)
    for sala in sorted(salas, key=lambda item: item["id"]):
        print(
            f"{sala['id']:<10}{rotulo_categoria(sala['categoria'])[:22]:<24}"
            f"{sala['nome'][:28]:<30}{caminho_setor(base, sala['setor_id'])}"
        )


def listar(base):
    cabecalho("ESTRUTURA DA EMPRESA")
    if not base["setores"]:
        print("[INFO] Nenhum setor cadastrado.")
        return

    def imprimir_no(setor, nivel):
        prefixo = "    " * nivel
        print(f"{prefixo}|-- [{setor['id']}] {setor['nome']}")
        salas = sorted(
            (s for s in base["salas"].values() if s["setor_id"] == setor["id"]),
            key=lambda item: item["id"],
        )
        for sala in salas:
            print(
                f"{prefixo}    |-- {sala['id']} | {sala['nome']} "
                f"({rotulo_categoria(sala['categoria'])})"
            )
        for filho in _filhos(base, setor["id"]):
            imprimir_no(filho, nivel + 1)

    raizes = sorted(
        (s for s in base["setores"].values() if s["setor_pai_id"] is None),
        key=lambda item: item["nome"].casefold(),
    )
    for raiz in raizes:
        imprimir_no(raiz, 0)
    listar_tabela_salas(base)


def selecionar_setor(base, permitir_raiz=False, mensagem="ID do setor: "):
    if not base["setores"] and not permitir_raiz:
        print("[INFO] Nenhum setor cadastrado.")
        return None
    for setor in sorted(base["setores"].values(), key=lambda item: item["id"]):
        print(f"  {setor['id']} - {caminho_setor(base, setor['id'])}")
    if permitir_raiz:
        print("  0 - Sem setor-pai (nível principal)")
    while True:
        identificador = ler_inteiro(mensagem, minimo=0 if permitir_raiz else 1)
        if permitir_raiz and identificador == 0:
            return None
        if identificador in base["setores"]:
            return identificador
        print(f"[ERRO] O setor {identificador} não existe.")


def sala_adequada(tipo, sala):
    return sala["categoria"] in LOCAIS_RECOMENDADOS[tipo]


def _autorizar_local_inadequado(base, tipo, sala):
    recomendadas = ", ".join(sorted(LOCAIS_RECOMENDADOS[tipo]))
    print(
        f"\n[AVISO] {tipo.rotulo} não é normalmente instalado em "
        f"'{rotulo_categoria(sala['categoria'])}'."
    )
    print(f"Categorias recomendadas: {recomendadas}.")
    if not autenticacao.autorizar_admin(base, "Autorizar ativo em local não recomendado"):
        return False
    auditoria.registrar(
        base, "EXCECAO_LOCALIZACAO", sala["id"],
        f"{tipo.rotulo} autorizado em {sala['nome']} ({sala['categoria']}).",
    )
    return True


def selecionar_sala(base, setor_id, tipo=None, permitir_cadastro=True):
    """Seleciona SAL-NNN, validando a adequação ao tipo quando informado."""

    while True:
        salas = sorted(
            (s for s in base["salas"].values() if s["setor_id"] == setor_id),
            key=lambda item: item["id"],
        )
        listar_tabela_salas(base, setor_id)
        if permitir_cadastro:
            print("  NOVA - Cadastrar uma sala neste setor (exige PIN)")
        if not salas and not permitir_cadastro:
            print("[INFO] Este setor ainda não possui salas.")
            return None
        identificador = input("ID da sala: ").strip().upper()
        if permitir_cadastro and identificador == "NOVA":
            criada = cadastrar_sala(base, setor_id=setor_id, devolver_id=True)
            if criada is None:
                return None
            sala_criada = base["salas"][criada]
            if tipo is not None and not sala_adequada(tipo, sala_criada):
                if not _autorizar_local_inadequado(base, tipo, sala_criada):
                    print("[INFO] A sala foi criada, mas não foi selecionada para este ativo.")
                    continue
            return criada
        sala = base["salas"].get(identificador)
        if sala is None or sala["setor_id"] != setor_id:
            print("[ERRO] A sala informada não pertence ao setor selecionado.")
            continue
        if tipo is not None and not sala_adequada(tipo, sala):
            if not _autorizar_local_inadequado(base, tipo, sala):
                print("[INFO] Escolha outra sala.")
                continue
        return identificador


def cadastrar_setor(base):
    cabecalho("CADASTRAR SETOR OU SUBSETOR")
    nome = ler_texto_obrigatorio("Nome: ")
    print("\nEscolha o setor-pai. Use zero para criar um setor principal.")
    setor_pai_id = selecionar_setor(base, permitir_raiz=True)
    descricao = input("Descrição (opcional): ").strip()
    if any(
        s["setor_pai_id"] == setor_pai_id and s["nome"].casefold() == nome.casefold()
        for s in base["setores"].values()
    ):
        print("[ERRO] Já existe um setor com esse nome no mesmo nível.")
        return False
    identificador = proximo_id_setor(base["setores"])
    base["setores"][identificador] = {
        "id": identificador, "nome": nome,
        "setor_pai_id": setor_pai_id, "descricao": descricao,
    }
    print(f"[SUCESSO] Setor '{caminho_setor(base, identificador)}' cadastrado.")
    return True


def _escolher_categoria_sala():
    print("\nCategorias tabeladas de sala:")
    for opcao, (codigo, rotulo) in CATEGORIAS_SALA.items():
        print(f"  {opcao} - {rotulo} [{codigo}]")
    return CATEGORIAS_SALA[ler_opcao("Categoria: ", CATEGORIAS_SALA)][0]


def cadastrar_sala(base, setor_id=None, devolver_id=False):
    """Cria sala SAL-NNN somente após autorização administrativa."""

    cabecalho("CADASTRAR SALA — OPERAÇÃO ADMINISTRATIVA")
    if not autenticacao.autorizar_admin(base, "Criar uma nova sala física ou lógica"):
        return None if devolver_id else False
    if setor_id is None:
        setor_id = selecionar_setor(base)
        if setor_id is None:
            return None if devolver_id else False
    nome = ler_texto_obrigatorio("Nome da sala: ")
    categoria = _escolher_categoria_sala()
    descricao = input("Descrição (opcional): ").strip()
    if any(
        s["setor_id"] == setor_id and s["nome"].casefold() == nome.casefold()
        for s in base["salas"].values()
    ):
        print("[ERRO] Já existe uma sala com esse nome neste setor.")
        return None if devolver_id else False
    identificador = proximo_id_sala(base["salas"])
    base["salas"][identificador] = {
        "id": identificador, "nome": nome, "setor_id": setor_id,
        "categoria": categoria, "descricao": descricao,
    }
    auditoria.registrar(
        base, "CRIAR_SALA", identificador,
        f"Sala '{nome}' [{categoria}] criada em {caminho_setor(base, setor_id)}.",
    )
    print(f"[SUCESSO] {identificador} — '{nome}' cadastrada.")
    return identificador if devolver_id else True


def atualizar_setor(base):
    cabecalho("ATUALIZAR SETOR")
    identificador = selecionar_setor(base)
    if identificador is None:
        return False
    setor = base["setores"][identificador]
    print("1 - Nome\n2 - Descrição\n3 - Setor-pai\n0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 4))
    if escolha == "0":
        return False
    if escolha == "1":
        novo_nome = ler_texto_obrigatorio("Novo nome: ")
        if any(
            outro["id"] != identificador
            and outro["setor_pai_id"] == setor["setor_pai_id"]
            and outro["nome"].casefold() == novo_nome.casefold()
            for outro in base["setores"].values()
        ):
            print("[ERRO] Já existe um setor com esse nome no mesmo nível.")
            return False
        setor["nome"] = novo_nome
    elif escolha == "2":
        setor["descricao"] = input("Nova descrição: ").strip()
    else:
        print("Escolha o novo setor-pai ou zero para o nível principal.")
        novo_pai = selecionar_setor(base, permitir_raiz=True)
        if novo_pai in (_descendentes(base, identificador) | {identificador}):
            print("[ERRO] Um setor não pode ficar dentro de si ou de seus descendentes.")
            return False
        setor["setor_pai_id"] = novo_pai
    print("[SUCESSO] Setor atualizado.")
    return True


def _selecionar_sala_global(base):
    if not base["salas"]:
        print("[INFO] Nenhuma sala cadastrada.")
        return None
    listar_tabela_salas(base)
    identificador = input("ID da sala: ").strip().upper()
    if identificador not in base["salas"]:
        print("[ERRO] Sala não encontrada.")
        return None
    return identificador


def atualizar_sala(base):
    cabecalho("ATUALIZAR SALA")
    identificador = _selecionar_sala_global(base)
    if identificador is None:
        return False
    sala = base["salas"][identificador]
    print("1 - Nome\n2 - Descrição\n3 - Setor responsável\n4 - Categoria\n0 - Cancelar")
    escolha = ler_opcao("Opção: ", range(0, 5))
    if escolha == "0":
        return False
    if escolha == "1":
        sala["nome"] = ler_texto_obrigatorio("Novo nome: ")
    elif escolha == "2":
        sala["descricao"] = input("Nova descrição: ").strip()
    elif escolha == "3":
        novo_setor = selecionar_setor(base)
        if novo_setor is None:
            return False
        sala["setor_id"] = novo_setor
        for ativo in base["ativos"].values():
            if ativo["sala_id"] == identificador:
                ativo["setor_id"] = novo_setor
    else:
        sala["categoria"] = _escolher_categoria_sala()
    print("[SUCESSO] Sala atualizada.")
    return True


def remover_setor(base):
    cabecalho("REMOVER SETOR")
    identificador = selecionar_setor(base)
    if identificador is None:
        return False
    if _filhos(base, identificador) or any(s["setor_id"] == identificador for s in base["salas"].values()):
        print("[ERRO] Remova ou transfira primeiro os subsetores e salas associados.")
        return False
    if not confirmar("Confirmar remoção do setor? [S/N]: "):
        return False
    del base["setores"][identificador]
    print("[SUCESSO] Setor removido.")
    return True


def remover_sala(base):
    cabecalho("REMOVER SALA")
    identificador = _selecionar_sala_global(base)
    if identificador is None:
        return False
    sala = base["salas"][identificador]
    if any(a["sala_id"] == identificador for a in base["ativos"].values()):
        print("[ERRO] Transfira ou remova os ativos desta sala primeiro.")
        return False
    if not confirmar(f"Remover a sala '{sala['nome']}'? [S/N]: "):
        return False
    del base["salas"][identificador]
    print("[SUCESSO] Sala removida.")
    return True


def menu(base, salvar_se_alterado):
    while True:
        cabecalho("ESTRUTURA ORGANIZACIONAL")
        print("IDs de sala seguem SAL-NNN; criação de sala exige PIN e gera auditoria.")
        print("1 - Visualizar setores, subsetores e salas")
        print("2 - Cadastrar setor ou subsetor")
        print("3 - Cadastrar sala (PIN administrativo)")
        print("4 - Atualizar setor\n5 - Atualizar sala")
        print("6 - Remover setor\n7 - Remover sala\n0 - Voltar")
        escolha = ler_opcao("Opção: ", range(0, 8))
        if escolha == "0":
            return
        operacoes = {
            "2": cadastrar_setor, "3": cadastrar_sala, "4": atualizar_setor,
            "5": atualizar_sala, "6": remover_setor, "7": remover_sala,
        }
        if escolha == "1":
            listar(base)
        else:
            salvar_se_alterado(base, operacoes[escolha](base))

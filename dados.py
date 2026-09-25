"""Persistência do Sauron em tabelas TXT relacionadas por chaves."""

import csv
import json
from pathlib import Path

from identificacao import gerar_hostname, gerar_id_ativo, validar_hostname, validar_id_ativo
from utilitarios import CATALOGO_VULNERABILIDADES, Severidade, StatusVulnerabilidade, TipoAtivo


PASTA_DADOS = Path(__file__).resolve().parent / "dados"
CAMINHO_JSON_LEGADO = PASTA_DADOS / "inventario.json"

COLUNAS = {
    "setores": ("id", "nome", "setor_pai_id", "descricao"),
    "salas": ("id", "nome", "setor_id", "categoria", "descricao"),
    "ativos": (
        "id", "hostname", "tipo", "fabricante", "codigo_fabricante",
        "numero_serie", "usuario", "responsavel", "setor_id", "sala_id",
        "descricao",
    ),
    "vulnerabilidades": (
        "id", "ativo_id", "codigo_categoria", "categoria", "descricao",
        "severidade", "status", "tratamento_sugerido",
    ),
    "seguranca": ("id", "salt", "pin_hash", "iteracoes"),
    "auditoria": ("id", "data_hora", "ator", "acao", "entidade", "detalhes"),
}


class ErroDeDados(Exception):
    """Indica falha controlada de leitura, estrutura ou gravação."""


def criar_base_vazia(com_estrutura_padrao=True):
    """Cria as seis tabelas internas e, opcionalmente, a estrutura inicial."""

    base = {
        "ativos": {}, "setores": {}, "salas": {},
        "seguranca": {}, "auditoria": {},
    }
    if not com_estrutura_padrao:
        return base

    nomes = ("Administração", "Financeiro", "TI", "Recursos Humanos")
    for identificador, nome in enumerate(nomes, start=1):
        base["setores"][identificador] = {
            "id": identificador, "nome": nome,
            "setor_pai_id": None, "descricao": "",
        }

    salas = (
        ("SAL-001", "Sala de Servidores", 3, "SERVIDORES", "Infraestrutura central"),
        ("SAL-002", "Armário de Telecomunicações", 3, "TELECOM", "Equipamentos de rede"),
        ("SAL-003", "Sala Administrativa", 1, "ESCRITORIO", ""),
        ("SAL-004", "Sala Financeira", 2, "ESCRITORIO", ""),
        ("SAL-005", "Sala de TI", 3, "ESCRITORIO", ""),
        ("SAL-006", "Sala de RH", 4, "ESCRITORIO", ""),
    )
    for identificador, nome, setor_id, categoria, descricao in salas:
        base["salas"][identificador] = {
            "id": identificador, "nome": nome, "setor_id": setor_id,
            "categoria": categoria, "descricao": descricao,
        }
    return base


def _ler_tabela(pasta, nome):
    caminho = pasta / f"{nome}.txt"
    if not caminho.exists():
        raise ErroDeDados(f"A tabela obrigatória '{caminho.name}' não foi encontrada.")
    try:
        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter="\t")
            if tuple(leitor.fieldnames or ()) != COLUNAS[nome]:
                raise ErroDeDados(
                    f"O cabeçalho de '{caminho.name}' não corresponde ao esquema esperado. "
                    "Use as tabelas desta versão ou restaure um backup compatível."
                )
            return list(leitor)
    except UnicodeError as erro:
        raise ErroDeDados(f"A tabela '{caminho.name}' não está em UTF-8.") from erro
    except OSError as erro:
        raise ErroDeDados(f"Não foi possível ler '{caminho}'.") from erro


def _inteiro(texto, campo, tabela, permitir_vazio=False):
    if permitir_vazio and texto == "":
        return None
    try:
        return int(texto)
    except (TypeError, ValueError) as erro:
        raise ErroDeDados(
            f"O campo '{campo}' da tabela '{tabela}.txt' precisa ser inteiro."
        ) from erro


def _validar_integridade(base):
    """Valida chaves, formatos e relações antes de ler ou gravar."""

    setores, salas = base["setores"], base["salas"]
    for setor in setores.values():
        if not setor["nome"].strip():
            raise ErroDeDados(f"O setor {setor['id']} está sem nome.")
        pai = setor["setor_pai_id"]
        if pai is not None and pai not in setores:
            raise ErroDeDados(f"O setor {setor['id']} referencia o setor-pai {pai} inexistente.")
        visitados, atual = {setor["id"]}, pai
        while atual is not None:
            if atual in visitados:
                raise ErroDeDados("A tabela setores.txt contém uma relação cíclica.")
            visitados.add(atual)
            atual = setores[atual]["setor_pai_id"]

    for sala in salas.values():
        if not sala["id"].startswith("SAL-") or not sala["id"][4:].isdigit():
            raise ErroDeDados(f"ID de sala inválido: {sala['id']}.")
        if not sala["nome"].strip() or sala["setor_id"] not in setores:
            raise ErroDeDados(f"A sala {sala['id']} está incompleta ou referencia setor inexistente.")

    ids_vulnerabilidades = set()
    for chave, ativo in base["ativos"].items():
        if chave != ativo["id"] or not validar_id_ativo(ativo["id"]):
            raise ErroDeDados(f"ID de ativo inválido: {ativo['id']}.")
        if not validar_hostname(ativo["hostname"]):
            raise ErroDeDados(f"Hostname inválido no ativo {ativo['id']}.")
        if not ativo["responsavel"].strip() or not ativo["usuario"].strip():
            raise ErroDeDados(f"O ativo {ativo['id']} possui campo obrigatório vazio.")
        if ativo["setor_id"] not in setores or ativo["sala_id"] not in salas:
            raise ErroDeDados(f"O ativo {ativo['id']} referencia uma posição inexistente.")
        if salas[ativo["sala_id"]]["setor_id"] != ativo["setor_id"]:
            raise ErroDeDados(f"O ativo {ativo['id']} está em setor diferente de sua sala.")
        for identificador, vuln in ativo["vulnerabilidades"].items():
            if identificador in ids_vulnerabilidades:
                raise ErroDeDados(f"ID de vulnerabilidade duplicado: {identificador}.")
            codigo = int(vuln["codigo_categoria"])
            if not identificador.startswith(f"VUL-{codigo:02d}-"):
                raise ErroDeDados(f"ID de vulnerabilidade incompatível: {identificador}.")
            ids_vulnerabilidades.add(identificador)


def _desserializar(tabelas):
    base = criar_base_vazia(com_estrutura_padrao=False)
    try:
        for linha in tabelas["setores"]:
            identificador = _inteiro(linha["id"], "id", "setores")
            if identificador in base["setores"]:
                raise ErroDeDados(f"ID de setor duplicado: {identificador}.")
            base["setores"][identificador] = {
                "id": identificador, "nome": linha["nome"],
                "setor_pai_id": _inteiro(linha["setor_pai_id"], "setor_pai_id", "setores", True),
                "descricao": linha["descricao"],
            }
        for linha in tabelas["salas"]:
            identificador = linha["id"].upper()
            if identificador in base["salas"]:
                raise ErroDeDados(f"ID de sala duplicado: {identificador}.")
            base["salas"][identificador] = {
                "id": identificador, "nome": linha["nome"],
                "setor_id": _inteiro(linha["setor_id"], "setor_id", "salas"),
                "categoria": linha["categoria"], "descricao": linha["descricao"],
            }
        for linha in tabelas["ativos"]:
            identificador = linha["id"].upper()
            if identificador in base["ativos"]:
                raise ErroDeDados(f"ID de ativo duplicado: {identificador}.")
            base["ativos"][identificador] = {
                "id": identificador, "hostname": linha["hostname"].upper(),
                "nome": linha["hostname"].upper(), "tipo": TipoAtivo[linha["tipo"]],
                "fabricante": linha["fabricante"],
                "codigo_fabricante": linha["codigo_fabricante"],
                "numero_serie": linha["numero_serie"], "usuario": linha["usuario"],
                "responsavel": linha["responsavel"],
                "setor_id": _inteiro(linha["setor_id"], "setor_id", "ativos"),
                "sala_id": linha["sala_id"].upper(), "descricao": linha["descricao"],
                "vulnerabilidades": {},
            }
        ids_vulnerabilidades = set()
        for linha in tabelas["vulnerabilidades"]:
            ativo_id = linha["ativo_id"].upper()
            if ativo_id not in base["ativos"]:
                raise ErroDeDados(f"A vulnerabilidade {linha['id']} referencia ativo inexistente.")
            if linha["id"] in ids_vulnerabilidades:
                raise ErroDeDados(f"ID de vulnerabilidade duplicado: {linha['id']}.")
            ids_vulnerabilidades.add(linha["id"])
            base["ativos"][ativo_id]["vulnerabilidades"][linha["id"]] = {
                "codigo_categoria": _inteiro(linha["codigo_categoria"], "codigo_categoria", "vulnerabilidades"),
                "categoria": linha["categoria"], "descricao": linha["descricao"],
                "severidade": Severidade[linha["severidade"]],
                "status": StatusVulnerabilidade[linha["status"]],
                "tratamento_sugerido": linha["tratamento_sugerido"],
            }
        for linha in tabelas["seguranca"]:
            base["seguranca"][linha["id"]] = {
                "id": linha["id"], "salt": linha["salt"],
                "pin_hash": linha["pin_hash"],
                "iteracoes": _inteiro(linha["iteracoes"], "iteracoes", "seguranca"),
            }
        for linha in tabelas["auditoria"]:
            base["auditoria"][linha["id"]] = dict(linha)
    except KeyError as erro:
        raise ErroDeDados(f"Valor ausente ou Enum inválido: {erro}.") from erro
    _validar_integridade(base)
    return base


def _obter_ou_criar_setor(base, nome):
    for setor in base["setores"].values():
        if setor["nome"].casefold() == nome.casefold():
            return setor["id"]
    identificador = max(base["setores"], default=0) + 1
    base["setores"][identificador] = {
        "id": identificador, "nome": nome, "setor_pai_id": None,
        "descricao": "Importado do inventário JSON anterior",
    }
    return identificador


def _proximo_id_sala(salas):
    numeros = [int(i[4:]) for i in salas if i.startswith("SAL-") and i[4:].isdigit()]
    return f"SAL-{max(numeros, default=0) + 1:03d}"


def _obter_ou_criar_sala(base, nome, setor_id):
    for sala in base["salas"].values():
        if sala["setor_id"] == setor_id and sala["nome"].casefold() == nome.casefold():
            return sala["id"]
    identificador = _proximo_id_sala(base["salas"])
    base["salas"][identificador] = {
        "id": identificador, "nome": nome, "setor_id": setor_id,
        "categoria": "OUTRO", "descricao": "Importada do inventário JSON anterior",
    }
    return identificador


def _migrar_json_legado(caminho):
    """Converte a antiga base JSON para o esquema atual com IDs válidos."""

    base = criar_base_vazia()
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
        if not isinstance(conteudo, dict):
            raise ValueError
        sequencias_vulnerabilidade = {}
        codigos_por_nome = {
            item["nome"].casefold(): int(codigo)
            for codigo, item in CATALOGO_VULNERABILIDADES.items()
        }
        for indice, (id_texto, item) in enumerate(conteudo.items(), start=1):
            tipo = TipoAtivo[item["tipo"]]
            serie = str(id_texto) if str(id_texto).isdigit() and len(str(id_texto)) >= 3 else f"{indice:03d}"
            serie = serie[:12].zfill(3)
            identificador = gerar_id_ativo(tipo, "L", serie)
            usuario = item.get("responsavel", "LEGADO")
            hostname = gerar_hostname(tipo, usuario, serie)
            setor_id = _obter_ou_criar_setor(base, item.get("setor", "Sem setor"))
            sala_id = _obter_ou_criar_sala(base, item.get("localizacao", "Sem sala"), setor_id)
            vulnerabilidades = {}
            for vulnerabilidade in item.get("vulnerabilidades", {}).values():
                categoria = vulnerabilidade.get("categoria", "Importada")
                codigo = codigos_por_nome.get(categoria.casefold(), 99)
                sequencias_vulnerabilidade[codigo] = sequencias_vulnerabilidade.get(codigo, 0) + 1
                id_vulnerabilidade = f"VUL-{codigo:02d}-{sequencias_vulnerabilidade[codigo]:03d}"
                vulnerabilidades[id_vulnerabilidade] = {
                    "codigo_categoria": codigo,
                    "categoria": categoria,
                    "descricao": vulnerabilidade.get("descricao", "Importada da base anterior"),
                    "severidade": Severidade[vulnerabilidade.get("severidade", "MEDIA")],
                    "status": StatusVulnerabilidade[vulnerabilidade.get("status", "ABERTA")],
                    "tratamento_sugerido": vulnerabilidade.get("tratamento_sugerido", ""),
                }
            base["ativos"][identificador] = {
                "id": identificador, "hostname": hostname, "nome": hostname,
                "tipo": tipo, "fabricante": "Legado", "codigo_fabricante": "L",
                "numero_serie": serie, "usuario": usuario,
                "responsavel": item["responsavel"], "setor_id": setor_id,
                "sala_id": sala_id, "descricao": item.get("descricao", ""),
                "vulnerabilidades": vulnerabilidades,
            }
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as erro:
        raise ErroDeDados("Não foi possível migrar inventario.json.") from erro
    return base


def carregar(pasta=PASTA_DADOS):
    """Carrega todas as tabelas ou cria uma base inicial na primeira execução."""

    pasta = Path(pasta)
    caminhos = [pasta / f"{nome}.txt" for nome in COLUNAS]
    existentes = [caminho.exists() for caminho in caminhos]
    if any(existentes) and not all(existentes):
        ausentes = [caminho.name for caminho in caminhos if not caminho.exists()]
        raise ErroDeDados("Base incompleta. Tabelas ausentes: " + ", ".join(ausentes))
    if not any(existentes):
        legado = pasta / CAMINHO_JSON_LEGADO.name
        base = _migrar_json_legado(legado) if legado.exists() else criar_base_vazia()
        salvar(base, pasta)
        return base
    return _desserializar({nome: _ler_tabela(pasta, nome) for nome in COLUNAS})


def _linhas_para_salvar(base):
    linhas = {nome: [] for nome in COLUNAS}
    for setor in sorted(base["setores"].values(), key=lambda item: item["id"]):
        linhas["setores"].append({**setor, "setor_pai_id": setor["setor_pai_id"] or ""})
    for sala in sorted(base["salas"].values(), key=lambda item: item["id"]):
        linhas["salas"].append(dict(sala))
    for ativo in sorted(base["ativos"].values(), key=lambda item: item["id"]):
        linhas["ativos"].append({
            "id": ativo["id"], "hostname": ativo["hostname"],
            "tipo": ativo["tipo"].name, "fabricante": ativo["fabricante"],
            "codigo_fabricante": ativo["codigo_fabricante"],
            "numero_serie": ativo["numero_serie"], "usuario": ativo["usuario"],
            "responsavel": ativo["responsavel"], "setor_id": ativo["setor_id"],
            "sala_id": ativo["sala_id"], "descricao": ativo["descricao"],
        })
        for identificador, vulnerabilidade in sorted(ativo["vulnerabilidades"].items()):
            linhas["vulnerabilidades"].append({
                "id": identificador, "ativo_id": ativo["id"],
                "codigo_categoria": vulnerabilidade["codigo_categoria"],
                "categoria": vulnerabilidade["categoria"],
                "descricao": vulnerabilidade["descricao"],
                "severidade": vulnerabilidade["severidade"].name,
                "status": vulnerabilidade["status"].name,
                "tratamento_sugerido": vulnerabilidade.get("tratamento_sugerido", ""),
            })
    linhas["seguranca"] = [dict(item) for item in base["seguranca"].values()]
    linhas["auditoria"] = [dict(item) for item in base["auditoria"].values()]
    return linhas


def salvar(base, pasta=PASTA_DADOS):
    """Grava temporários e só então substitui as tabelas oficiais."""

    pasta = Path(pasta)
    _validar_integridade(base)
    linhas, temporarios = _linhas_para_salvar(base), {}
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, colunas in COLUNAS.items():
            temporario = pasta / f"{nome}.tmp"
            temporarios[nome] = temporario
            with temporario.open("w", encoding="utf-8", newline="") as arquivo:
                escritor = csv.DictWriter(
                    arquivo, fieldnames=colunas, delimiter="\t", lineterminator="\n"
                )
                escritor.writeheader()
                escritor.writerows(linhas[nome])
        for nome, temporario in temporarios.items():
            temporario.replace(pasta / f"{nome}.txt")
    except OSError as erro:
        raise ErroDeDados(f"Não foi possível gravar as tabelas em '{pasta}'.") from erro

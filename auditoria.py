"""Registro de ações administrativas relevantes em tabela TXT."""

from datetime import datetime, timezone

from utilitarios import cabecalho


def proximo_id(registros):
    """Gera uma chave sequencial legível sem reutilizar registros removidos."""

    numeros = []
    for identificador in registros:
        if identificador.startswith("AUD-") and identificador[4:].isdigit():
            numeros.append(int(identificador[4:]))
    return f"AUD-{max(numeros, default=0) + 1:06d}"


def registrar(base, acao, entidade, detalhes, ator="ADMIN_PIN"):
    """Acrescenta um evento com horário UTC e devolve seu ID."""

    identificador = proximo_id(base["auditoria"])
    base["auditoria"][identificador] = {
        "id": identificador,
        "data_hora": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ator": ator,
        "acao": acao,
        "entidade": entidade,
        "detalhes": detalhes,
    }
    return identificador


def listar(base):
    """Mostra o histórico administrativo do mais recente ao mais antigo."""

    cabecalho("REGISTRO DE AUDITORIA")
    if not base["auditoria"]:
        print("[INFO] Nenhuma ação administrativa foi registrada.")
        return
    for evento in reversed(list(base["auditoria"].values())):
        print(
            f"{evento['id']} | {evento['data_hora']} | {evento['ator']} | "
            f"{evento['acao']}"
        )
        print(f"  Entidade: {evento['entidade']}")
        print(f"  Detalhes: {evento['detalhes']}")

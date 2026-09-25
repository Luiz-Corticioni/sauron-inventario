"""Leitura e gravação da base do Sentinela em um arquivo JSON.

JSON é texto estruturado. Portanto, atende ao requisito de persistir os dados
em arquivo de texto e continua legível fora do programa.
"""

import json
from pathlib import Path

from utilitarios import Severidade, StatusVulnerabilidade, TipoAtivo


# O caminho parte deste arquivo, não da pasta em que o comando foi executado.
# Isso permite iniciar o sistema tanto pela raiz quanto por outro diretório.
CAMINHO_DADOS = Path(__file__).resolve().parent / "dados" / "inventario.json"


class ErroDeDados(Exception):
    """Indica uma falha controlada ao ler ou gravar o arquivo da aplicação."""


def _serializar(ativos):
    """Converte Enums e chaves inteiras para valores aceitos pelo JSON."""

    saida = {}
    for id_ativo, ativo in ativos.items():
        vulnerabilidades = {}
        for id_vulnerabilidade, vulnerabilidade in ativo["vulnerabilidades"].items():
            vulnerabilidades[id_vulnerabilidade] = {
                **vulnerabilidade,
                "severidade": vulnerabilidade["severidade"].name,
                "status": vulnerabilidade["status"].name,
            }

        saida[str(id_ativo)] = {
            **ativo,
            "tipo": ativo["tipo"].name,
            "vulnerabilidades": vulnerabilidades,
        }
    return saida


def _desserializar(conteudo):
    """Reconstrói as chaves inteiras e os membros dos Enums após a leitura."""

    if not isinstance(conteudo, dict):
        raise ErroDeDados("A raiz de inventario.json precisa ser um objeto JSON.")

    ativos = {}
    try:
        for id_texto, item in conteudo.items():
            id_ativo = int(id_texto)
            vulnerabilidades = {}

            for id_vulnerabilidade, vulnerabilidade in item.get(
                "vulnerabilidades", {}
            ).items():
                vulnerabilidades[id_vulnerabilidade] = {
                    **vulnerabilidade,
                    "severidade": Severidade[vulnerabilidade["severidade"]],
                    "status": StatusVulnerabilidade[vulnerabilidade["status"]],
                }

            ativos[id_ativo] = {
                **item,
                "id": id_ativo,
                "tipo": TipoAtivo[item["tipo"]],
                "vulnerabilidades": vulnerabilidades,
            }
    except (KeyError, TypeError, ValueError) as erro:
        raise ErroDeDados(
            "O arquivo inventario.json possui campos ausentes ou inválidos."
        ) from erro

    return ativos


def carregar(caminho=CAMINHO_DADOS):
    """Lê a base. Na primeira execução, um arquivo ausente equivale a base vazia."""

    caminho = Path(caminho)
    if not caminho.exists():
        return {}

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ErroDeDados(
            f"O arquivo '{caminho.name}' não contém um JSON válido."
        ) from erro
    except OSError as erro:
        raise ErroDeDados(f"Não foi possível ler '{caminho}'.") from erro

    return _desserializar(conteudo)


def salvar(ativos, caminho=CAMINHO_DADOS):
    """Grava toda a base usando um arquivo temporário para reduzir corrupção."""

    caminho = Path(caminho)
    temporario = caminho.with_suffix(".tmp")

    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(_serializar(ativos), arquivo, ensure_ascii=False, indent=2)
        # replace troca o arquivo somente depois que a escrita terminou.
        temporario.replace(caminho)
    except OSError as erro:
        raise ErroDeDados(f"Não foi possível gravar '{caminho}'.") from erro


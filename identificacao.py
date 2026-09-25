"""Regras centralizadas para IDs de ativos e hostnames do Sauron."""

import re
import unicodedata

from utilitarios import TipoAtivo


PREFIXOS_HOSTNAME = {
    TipoAtivo.SERVIDOR: "SRV",
    TipoAtivo.NOTEBOOK: "NB",
    TipoAtivo.ESTACAO_DE_TRABALHO: "EST",
    TipoAtivo.SWITCH: "SW",
    TipoAtivo.ROTEADOR: "RTR",
    TipoAtivo.IMPRESSORA_DE_REDE: "IMP",
    TipoAtivo.APLICACAO_WEB: "WEB",
    TipoAtivo.BANCO_DE_DADOS: "DB",
    TipoAtivo.SOFTWARE_LICENCIADO: "SWL",
}

PADRAO_ID_ATIVO = re.compile(r"^[1-9][A-Z]{1,3}\d{3,12}$")
PADRAO_HOSTNAME = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+){2}$")


def _sem_acentos(texto):
    """Remove acentos para produzir códigos portáveis entre sistemas."""

    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(letra for letra in normalizado if not unicodedata.combining(letra))


def normalizar_codigo(texto, limite=3):
    """Mantém somente letras maiúsculas para um código curto."""

    return re.sub(r"[^A-Z]", "", _sem_acentos(texto).upper())[:limite]


def sugerir_codigo_fabricante(fabricante):
    """Sugere o primeiro caractere alfabético; Huawei, por exemplo, vira H."""

    codigo = normalizar_codigo(fabricante, 1)
    if not codigo:
        raise ValueError("O fabricante precisa conter ao menos uma letra.")
    return codigo


def validar_codigo_fabricante(codigo):
    """Aceita de uma a três letras, sem números ou sinais."""

    return bool(re.fullmatch(r"[A-Z]{1,3}", codigo.strip().upper()))


def validar_numero_serie(numero_serie):
    """Exige de três a doze algarismos para evitar identificadores vagos."""

    return bool(re.fullmatch(r"\d{3,12}", str(numero_serie).strip()))


def gerar_id_ativo(tipo, codigo_fabricante, numero_serie):
    """Monta ``tipo + fabricante + série``, como ``4H21444``."""

    codigo = codigo_fabricante.strip().upper()
    serie = str(numero_serie).strip()
    if not isinstance(tipo, TipoAtivo):
        raise ValueError("Tipo de ativo inválido.")
    if not validar_codigo_fabricante(codigo):
        raise ValueError("O código do fabricante deve ter de uma a três letras.")
    if not validar_numero_serie(serie):
        raise ValueError("O número de série deve ter de três a doze algarismos.")
    return f"{tipo.value}{codigo}{serie}"


def validar_id_ativo(identificador):
    """Confere o formato e se o primeiro dígito representa um tipo conhecido."""

    texto = str(identificador).strip().upper()
    if not PADRAO_ID_ATIVO.fullmatch(texto):
        return False
    return int(texto[0]) in {tipo.value for tipo in TipoAtivo}


def normalizar_usuario(usuario):
    """Transforma um nome em segmento seguro de hostname."""

    partes = re.findall(r"[A-Z0-9]+", _sem_acentos(usuario).upper())
    segmento = "".join(partes)[:18]
    if not segmento:
        raise ValueError("O usuário precisa conter letras ou números.")
    return segmento


def gerar_hostname(tipo, usuario, numero_serie):
    """Gera hostname derivado do tipo, usuário e série do ativo."""

    if not validar_numero_serie(numero_serie):
        raise ValueError("Número de série inválido para gerar hostname.")
    return f"{PREFIXOS_HOSTNAME[tipo]}-{normalizar_usuario(usuario)}-{numero_serie}"


def validar_hostname(hostname):
    """Aceita somente o formato produzido por :func:`gerar_hostname`."""

    return bool(PADRAO_HOSTNAME.fullmatch(str(hostname).strip().upper()))

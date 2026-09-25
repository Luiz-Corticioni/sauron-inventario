"""Autenticação local por PIN sem armazenar o segredo em texto puro."""

import getpass
import hashlib
import hmac
import secrets


ITERACOES_PADRAO = 240_000


def validar_formato_pin(pin):
    """Um PIN administrativo deve ter entre seis e doze algarismos."""

    return pin.isdigit() and 6 <= len(pin) <= 12


def criar_credencial(pin, salt=None, iteracoes=ITERACOES_PADRAO):
    """Produz salt e hash PBKDF2; o PIN original não é persistido."""

    if not validar_formato_pin(pin):
        raise ValueError("O PIN deve conter de 6 a 12 algarismos.")
    salt = salt or secrets.token_hex(16)
    resumo = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), bytes.fromhex(salt), iteracoes
    ).hex()
    return {"id": "ADMIN", "salt": salt, "pin_hash": resumo, "iteracoes": iteracoes}


def verificar_pin(pin, credencial):
    """Compara hashes em tempo constante para reduzir vazamentos laterais."""

    if not validar_formato_pin(pin):
        return False
    candidata = criar_credencial(
        pin, salt=credencial["salt"], iteracoes=int(credencial["iteracoes"])
    )
    return hmac.compare_digest(candidata["pin_hash"], credencial["pin_hash"])


def _configurar_pin(base):
    print("\n[SEGURANÇA] Nenhum PIN administrativo foi configurado.")
    print("Crie um PIN de 6 a 12 números. Ele será salvo apenas como hash.")
    for _ in range(3):
        primeiro = getpass.getpass("Novo PIN: ").strip()
        segundo = getpass.getpass("Confirme o PIN: ").strip()
        if primeiro != segundo:
            print("[ERRO] Os PINs não coincidem.")
        elif not validar_formato_pin(primeiro):
            print("[ERRO] Use somente 6 a 12 algarismos.")
        else:
            base["seguranca"]["ADMIN"] = criar_credencial(primeiro)
            print("[SUCESSO] PIN administrativo configurado.")
            return True
    print("[ERRO] Não foi possível configurar o PIN.")
    return False


def autorizar_admin(base, motivo):
    """Configura ou solicita o PIN e limita a três tentativas."""

    print(f"\n[AUTORIZAÇÃO ADMINISTRATIVA] {motivo}")
    credencial = base["seguranca"].get("ADMIN")
    if credencial is None:
        if not _configurar_pin(base):
            return False
        credencial = base["seguranca"]["ADMIN"]
        print("Confirme o novo PIN para concluir esta operação.")
    for tentativa in range(1, 4):
        pin = getpass.getpass("PIN administrativo: ").strip()
        if verificar_pin(pin, credencial):
            return True
        print(f"[ERRO] PIN incorreto ({tentativa}/3).")
    print("[BLOQUEADO] Operação cancelada após três tentativas.")
    return False

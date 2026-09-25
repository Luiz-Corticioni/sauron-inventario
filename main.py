"""Ponto de entrada e menus do sistema Sentinela.

Este arquivo coordena os módulos. As regras dos ativos ficam em ``ativos.py``,
as vulnerabilidades em ``vulnerabilidades.py`` e o arquivo JSON em ``dados.py``.
"""

import ativos
import dados
import vulnerabilidades
from utilitarios import (
    cabecalho,
    ler_opcao,
    menu_catalogo,
    mostrar_mapa,
    mostrar_painel,
)


def salvar_se_alterado(base, alterado):
    """Persiste a base somente quando alguma operação realmente a modificou."""

    if alterado:
        dados.salvar(base)


def menu_ativos(base):
    """Apresenta explicitamente as quatro operações do CRUD de ativos."""

    while True:
        cabecalho("GESTÃO DE ATIVOS")
        print("1 - Cadastrar ativo          (Create)")
        print("2 - Consultar ativo          (Read)")
        print("3 - Atualizar ativo          (Update)")
        print("4 - Remover ativo            (Delete)")
        print("5 - Listar todos os ativos")
        print("0 - Voltar")
        escolha = ler_opcao("Opção: ", range(0, 6))

        if escolha == "0":
            return
        if escolha == "1":
            salvar_se_alterado(base, ativos.cadastrar(base))
        elif escolha == "2":
            ativos.consultar(base)
        elif escolha == "3":
            salvar_se_alterado(base, ativos.atualizar(base))
        elif escolha == "4":
            salvar_se_alterado(base, ativos.remover(base))
        elif escolha == "5":
            ativos.listar(base)


def menu_vulnerabilidades(base):
    """Gerencia vulnerabilidades sempre vinculadas a um ativo existente."""

    while True:
        cabecalho("GESTÃO DE VULNERABILIDADES")
        print("1 - Cadastrar vulnerabilidade")
        print("2 - Visualizar vulnerabilidades")
        print("3 - Atualizar vulnerabilidade")
        print("4 - Remover vulnerabilidade")
        print("0 - Voltar")
        escolha = ler_opcao("Opção: ", range(0, 5))

        if escolha == "0":
            return

        ativo = ativos.selecionar(base, "usar")
        if ativo is None:
            continue

        if escolha == "1":
            salvar_se_alterado(base, vulnerabilidades.cadastrar(base, ativo))
        elif escolha == "2":
            vulnerabilidades.listar(ativo)
        elif escolha == "3":
            salvar_se_alterado(base, vulnerabilidades.atualizar(ativo))
        elif escolha == "4":
            salvar_se_alterado(base, vulnerabilidades.remover(ativo))


def executar():
    """Carrega a base uma vez e mantém o programa ativo até a opção de saída."""

    try:
        base = dados.carregar()
    except dados.ErroDeDados as erro:
        print(f"[ERRO DE DADOS] {erro}")
        print("O sistema foi encerrado para não sobrescrever a base com defeito.")
        return

    while True:
        cabecalho("SENTINELA - INVENTÁRIO DE SEGURANÇA DE TI")
        print("1 - Gestão de ativos")
        print("2 - Gestão de vulnerabilidades")
        print("3 - Mapa da infraestrutura")
        print("4 - Catálogo educativo de vulnerabilidades")
        print("5 - Painel de segurança")
        print("0 - Sair")
        escolha = ler_opcao("Opção: ", range(0, 6))

        try:
            if escolha == "0":
                print("\nDados preservados. Encerrando o Sentinela.")
                return
            if escolha == "1":
                menu_ativos(base)
            elif escolha == "2":
                menu_vulnerabilidades(base)
            elif escolha == "3":
                mostrar_mapa(base)
            elif escolha == "4":
                menu_catalogo()
            elif escolha == "5":
                mostrar_painel(base)
        except dados.ErroDeDados as erro:
            # Erros de arquivo são informados sem derrubar o menu inteiro.
            print(f"[ERRO DE DADOS] {erro}")


if __name__ == "__main__":
    try:
        executar()
    except (KeyboardInterrupt, EOFError):
        print("\nExecução interrompida pelo usuário.")


"""Ponto de entrada e menus do sistema Sauron.

Arquivo central, "O cérebro do sistema" As regras dos ativos ficam em ``ativos.py``,
as vulnerabilidades em ``vulnerabilidades.py`` e as tabelas TXT em ``dados.py``.
"""

import ativos
import auditoria
import dados
import estrutura
import modo_euler
import vulnerabilidades
from utilitarios import (
    cabecalho,
    exibir_banner,
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
        print("IDs: VUL-TT-NNN (TT identifica o tipo da vulnerabilidade)")
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
            salvar_se_alterado(
                base, vulnerabilidades.cadastrar(base["ativos"], ativo)
            )
        elif escolha == "2":
            vulnerabilidades.listar(ativo)
        elif escolha == "3":
            salvar_se_alterado(base, vulnerabilidades.atualizar(base["ativos"], ativo))
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

    exibir_banner()
    while True:
        cabecalho("SAURON — INVENTÁRIO E INTELIGÊNCIA DE INFRAESTRUTURA")
        print("1 - Gestão de ativos")
        print("2 - Gestão de vulnerabilidades")
        print("3 - Estrutura da empresa: setores, subsetores e salas")
        print("4 - Mapa dinâmico da infraestrutura")
        print("5 - Catálogo educativo de vulnerabilidades")
        print("6 - Painel de segurança")
        print("7 - Modo Euler — laboratório matemático")
        print("8 - Registro de auditoria administrativa")
        print("0 - Sair")
        escolha = ler_opcao("Opção: ", range(0, 9))

        try:
            if escolha == "0":
                print("\nDados preservados. O Olho de Sauron foi encerrado.")
                return
            if escolha == "1":
                menu_ativos(base)
            elif escolha == "2":
                menu_vulnerabilidades(base)
            elif escolha == "3":
                estrutura.menu(base, salvar_se_alterado)
            elif escolha == "4":
                mostrar_mapa(base)
            elif escolha == "5":
                menu_catalogo()
            elif escolha == "6":
                mostrar_painel(base["ativos"])
            elif escolha == "7":
                modo_euler.menu_modo_euler()
            elif escolha == "8":
                auditoria.listar(base)
        except dados.ErroDeDados as erro:
            # Adição bacana que fiz, erros agora não fodem o código inteiro :).
            print(f"[ERRO DE DADOS] {erro}")


if __name__ == "__main__":
    try:
        executar()
    except (KeyboardInterrupt, EOFError):
        print("\nExecução interrompida pelo usuário.")

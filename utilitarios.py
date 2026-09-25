"""Funções e constantes compartilhadas pelo sistema Sentinela.

Este módulo concentra validações, enumerações, textos educativos e o mapa.
Assim, os módulos de ativos e vulnerabilidades não repetem a mesma lógica.
"""

from enum import Enum
import unicodedata


class TipoAtivo(Enum):
    """Tipos de ativo com o código inteiro exigido pelo enunciado."""

    SERVIDOR = 1
    NOTEBOOK = 2
    ESTACAO_DE_TRABALHO = 3
    SWITCH = 4
    ROTEADOR = 5
    IMPRESSORA_DE_REDE = 6
    APLICACAO_WEB = 7
    BANCO_DE_DADOS = 8
    SOFTWARE_LICENCIADO = 9

    @property
    def rotulo(self):
        return ROTULOS_TIPO_ATIVO[self.name]


ROTULOS_TIPO_ATIVO = {
    "SERVIDOR": "Servidor",
    "NOTEBOOK": "Notebook",
    "ESTACAO_DE_TRABALHO": "Estação de Trabalho",
    "SWITCH": "Switch",
    "ROTEADOR": "Roteador",
    "IMPRESSORA_DE_REDE": "Impressora de Rede",
    "APLICACAO_WEB": "Aplicação Web",
    "BANCO_DE_DADOS": "Banco de Dados",
    "SOFTWARE_LICENCIADO": "Software Licenciado",
}


class Severidade(Enum):
    """Impacto estimado de uma vulnerabilidade."""

    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"


class StatusVulnerabilidade(Enum):
    """Etapa atual do tratamento da vulnerabilidade."""

    ABERTA = "Aberta"
    EM_TRATAMENTO = "Em tratamento"
    CORRIGIDA = "Corrigida"
    RISCO_ACEITO = "Risco aceito"


# Locais padronizados deixam o mapa organizado, mas a opção "Outro" permite
# representar situações reais que não foram previstas pelos autores.
LOCALIZACOES = [
    "Sala de Servidores",
    "Armário de Telecomunicações",
    "Nuvem / Datacenter",
    "Administração",
    "Financeiro",
    "TI",
    "Recursos Humanos",
    "Recepção",
    "Outro",
]


# O valor é uma tupla porque alguns tipos podem ficar corretamente em mais de
# um local. A recomendação apenas orienta: ela nunca bloqueia o cadastro.
LOCAIS_RECOMENDADOS = {
    TipoAtivo.SERVIDOR: ("Sala de Servidores", "Nuvem / Datacenter"),
    TipoAtivo.NOTEBOOK: ("Administração", "Financeiro", "TI", "Recursos Humanos"),
    TipoAtivo.ESTACAO_DE_TRABALHO: (
        "Administração",
        "Financeiro",
        "TI",
        "Recursos Humanos",
    ),
    TipoAtivo.SWITCH: ("Sala de Servidores", "Armário de Telecomunicações"),
    TipoAtivo.ROTEADOR: ("Sala de Servidores", "Armário de Telecomunicações"),
    TipoAtivo.IMPRESSORA_DE_REDE: ("Administração", "Financeiro", "TI"),
    TipoAtivo.APLICACAO_WEB: ("Nuvem / Datacenter", "Sala de Servidores"),
    TipoAtivo.BANCO_DE_DADOS: ("Nuvem / Datacenter", "Sala de Servidores"),
    TipoAtivo.SOFTWARE_LICENCIADO: ("Nuvem / Datacenter", "TI"),
}


# Catálogo local: não consulta CVE nem depende de internet. Além de educar o
# usuário, este dicionário demonstra uma aplicação clara da estrutura dict.
CATALOGO_VULNERABILIDADES = {
    "1": {
        "nome": "Senha fraca",
        "explicacao": "Credencial curta, previsível, reutilizada ou fácil de descobrir.",
        "exemplo": "Conta administrativa protegida por uma senha muito simples.",
        "risco": "Uma pessoa não autorizada pode conseguir acesso ao ativo.",
        "tratamento": "Criar uma senha forte, exclusiva e ativar autenticação multifator.",
        "severidade_tipica": "Média ou Alta",
    },
    "2": {
        "nome": "Software desatualizado",
        "explicacao": "Programa ou sistema executando uma versão antiga e sem correções recentes.",
        "exemplo": "Servidor que não recebeu as atualizações de segurança disponíveis.",
        "risco": "Falhas já conhecidas podem continuar exploráveis.",
        "tratamento": "Planejar a atualização, testar e instalar uma versão suportada.",
        "severidade_tipica": "Média, Alta ou Crítica",
    },
    "3": {
        "nome": "Serviço exposto",
        "explicacao": "Serviço acessível por uma rede ou por usuários que não precisam utilizá-lo.",
        "exemplo": "Painel administrativo acessível diretamente pela internet.",
        "risco": "A superfície de ataque aumenta desnecessariamente.",
        "tratamento": "Restringir acessos e revisar regras de firewall e autenticação.",
        "severidade_tipica": "Alta ou Crítica",
    },
    "4": {
        "nome": "Configuração incorreta",
        "explicacao": "Parâmetro do sistema configurado de forma insegura ou diferente do padrão adotado.",
        "exemplo": "Compartilhamento de arquivos liberado para todos os usuários.",
        "risco": "Dados e funções podem ficar disponíveis indevidamente.",
        "tratamento": "Revisar a configuração e aplicar uma referência segura.",
        "severidade_tipica": "Média ou Alta",
    },
    "5": {
        "nome": "Permissão excessiva",
        "explicacao": "Usuário ou programa possui mais privilégios do que precisa.",
        "exemplo": "Conta comum com permissão de administrador.",
        "risco": "Um erro ou acesso indevido pode causar impacto maior.",
        "tratamento": "Aplicar o princípio do menor privilégio e revisar os acessos.",
        "severidade_tipica": "Média ou Alta",
    },
    "6": {
        "nome": "Ausência de criptografia",
        "explicacao": "Dados sensíveis são armazenados ou transmitidos sem proteção criptográfica.",
        "exemplo": "Informação confidencial enviada por uma conexão sem proteção.",
        "risco": "Terceiros podem ler ou alterar os dados durante o armazenamento ou trânsito.",
        "tratamento": "Usar protocolos seguros e criptografia adequada aos dados.",
        "severidade_tipica": "Alta",
    },
}


DESCRICOES_SEVERIDADE = {
    Severidade.BAIXA: "Impacto pequeno e limitado.",
    Severidade.MEDIA: "Pode comprometer parcialmente o ativo.",
    Severidade.ALTA: "Pode causar comprometimento significativo.",
    Severidade.CRITICA: "Pode comprometer seriamente um ativo essencial.",
}


DESCRICOES_STATUS = {
    StatusVulnerabilidade.ABERTA: "Foi identificada, mas o tratamento ainda não começou.",
    StatusVulnerabilidade.EM_TRATAMENTO: "A correção ou mitigação está em andamento.",
    StatusVulnerabilidade.CORRIGIDA: "A causa foi tratada e a correção foi concluída.",
    StatusVulnerabilidade.RISCO_ACEITO: "A organização decidiu aceitar conscientemente o risco.",
}


def cabecalho(titulo):
    """Exibe um título padronizado para deixar os menus consistentes."""

    print("\n" + "=" * 64)
    print(titulo.center(64))
    print("=" * 64)


def ler_texto_obrigatorio(mensagem):
    """Repete a pergunta até receber algum texto não vazio."""

    while True:
        texto = input(mensagem).strip()
        if texto:
            return texto
        print("[ERRO] Este campo é obrigatório e não pode ficar vazio.")


def ler_inteiro(mensagem, minimo=None):
    """Converte a entrada para int e trata texto, decimal e campo vazio."""

    while True:
        entrada = input(mensagem).strip()
        try:
            numero = int(entrada)
        except ValueError:
            print("[ERRO] Digite um número inteiro válido.")
            continue

        if minimo is not None and numero < minimo:
            print(f"[ERRO] Digite um número maior ou igual a {minimo}.")
            continue
        return numero


def ler_opcao(mensagem, opcoes_validas):
    """Aceita apenas uma das opções textuais informadas."""

    opcoes = {str(opcao) for opcao in opcoes_validas}
    while True:
        escolha = input(mensagem).strip()
        if escolha in opcoes:
            return escolha
        print(f"[ERRO] Opção inválida. Escolha entre: {', '.join(sorted(opcoes))}.")


def confirmar(mensagem="Confirmar? [S/N]: "):
    """Transforma S/N em True/False sem deixar uma resposta inválida passar."""

    while True:
        resposta = input(mensagem).strip().upper()
        if resposta in ("S", "N"):
            return resposta == "S"
        print("[ERRO] Digite S para sim ou N para não.")


def escolher_tipo_ativo():
    """Mostra os códigos inteiros do Enum e devolve o membro escolhido."""

    print("\nTipos de ativo:")
    for tipo in TipoAtivo:
        print(f"  {tipo.value} - {tipo.rotulo}")

    codigos = [tipo.value for tipo in TipoAtivo]
    codigo = int(ler_opcao("Opção: ", codigos))
    return TipoAtivo(codigo)


def escolher_severidade():
    """Explica o significado de cada nível antes de pedir a escolha."""

    cabecalho("SEVERIDADE")
    membros = list(Severidade)
    for indice, severidade in enumerate(membros, start=1):
        print(f"{indice} - {severidade.value}")
        print(f"    {DESCRICOES_SEVERIDADE[severidade]}")
    indice = int(ler_opcao("Opção: ", range(1, len(membros) + 1)))
    return membros[indice - 1]


def escolher_status_vulnerabilidade():
    """Explica os estados do fluxo de tratamento antes da escolha."""

    cabecalho("STATUS DE TRATAMENTO")
    membros = list(StatusVulnerabilidade)
    for indice, status in enumerate(membros, start=1):
        print(f"{indice} - {status.value}")
        print(f"    {DESCRICOES_STATUS[status]}")
    indice = int(ler_opcao("Opção: ", range(1, len(membros) + 1)))
    return membros[indice - 1]


def _sem_acentos(texto):
    """Cria uma versão comparável do texto sem alterar o valor exibido."""

    normalizado = unicodedata.normalize("NFD", texto.casefold())
    return "".join(letra for letra in normalizado if unicodedata.category(letra) != "Mn")


def escolher_localizacao(tipo):
    """Oferece locais padronizados e avisa quando a escolha foge da recomendação."""

    recomendados = LOCAIS_RECOMENDADOS[tipo]
    while True:
        print(f"\nLocalizações recomendadas para {tipo.rotulo}:")
        print("  " + " ou ".join(recomendados))
        print("\nLocalizações disponíveis:")
        for indice, local in enumerate(LOCALIZACOES, start=1):
            print(f"  {indice} - {local}")

        indice = int(ler_opcao("Opção: ", range(1, len(LOCALIZACOES) + 1)))
        local = LOCALIZACOES[indice - 1]
        if local == "Outro":
            local = ler_texto_obrigatorio("Informe a localização: ")

        locais_normalizados = {_sem_acentos(item) for item in recomendados}
        if _sem_acentos(local) in locais_normalizados:
            return local

        print("\n[AVISO DE INFRAESTRUTURA]")
        print(f"Um ativo do tipo {tipo.rotulo} costuma ficar em:")
        print("  " + " ou ".join(recomendados))
        print(f"Local escolhido: {local}")
        if confirmar("Deseja manter a localização escolhida? [S/N]: "):
            return local
        print("Escolha uma nova localização.")


def exibir_item_catalogo(item):
    """Exibe uma explicação completa de um item do catálogo."""

    cabecalho(item["nome"].upper())
    print(f"O que é:              {item['explicacao']}")
    print(f"Exemplo:               {item['exemplo']}")
    print(f"Possível consequência: {item['risco']}")
    print(f"Tratamento sugerido:   {item['tratamento']}")
    print(f"Severidade típica:     {item['severidade_tipica']}")


def menu_catalogo():
    """Permite estudar as categorias sem cadastrar nenhum registro."""

    while True:
        cabecalho("CATÁLOGO EDUCATIVO DE VULNERABILIDADES")
        for codigo, item in CATALOGO_VULNERABILIDADES.items():
            print(f"{codigo} - {item['nome']}")
        print("0 - Voltar")

        escolha = ler_opcao("Opção: ", ["0", *CATALOGO_VULNERABILIDADES.keys()])
        if escolha == "0":
            return
        exibir_item_catalogo(CATALOGO_VULNERABILIDADES[escolha])
        input("\nPressione ENTER para voltar ao catálogo...")


def mostrar_mapa(ativos):
    """Mostra a topologia conceitual e agrupa os ativos pelo local cadastrado."""

    cabecalho("MAPA LÓGICO DA INFRAESTRUTURA")
    print(
        """
                         INTERNET
                            |
                       [ FIREWALL ]
                            |
                +-----------+-----------+
                |                       |
        [ NUVEM / DATACENTER ]    [ REDE INTERNA ]
                |                       |
       Aplicações e Bancos       [SALA DE SERVIDORES]
                                        |
                           Servidores - Switches - Roteadores
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
              ADMINISTRAÇÃO         FINANCEIRO             TI
                    |                   |                   |
           Notebooks/Impressoras  Notebooks/Impressoras  Estações
"""
    )

    if not ativos:
        print("[INFO] Ainda não há ativos cadastrados para posicionar no mapa.")
        return

    # Um segundo dicionário agrupa vários ativos sob a mesma localização.
    por_localizacao = {}
    for ativo in ativos.values():
        local = ativo["localizacao"]
        por_localizacao.setdefault(local, []).append(ativo)

    print("\nATIVOS CADASTRADOS POR LOCALIZAÇÃO")
    print("-" * 64)
    for local in sorted(por_localizacao, key=str.casefold):
        print(f"\n[{local.upper()}]")
        lista = sorted(por_localizacao[local], key=lambda item: item["id"])
        for ativo in lista:
            print(f"  |-- {ativo['nome']} [ID {ativo['id']}] - {ativo['tipo'].rotulo}")


def calcular_painel(ativos):
    """Calcula os números do painel e também pode ser testada sem usar input."""

    tipos = {tipo: 0 for tipo in TipoAtivo}
    severidades_abertas = {severidade: 0 for severidade in Severidade}
    total_vulnerabilidades = 0
    ativos_sem_vulnerabilidades = 0

    for ativo in ativos.values():
        tipos[ativo["tipo"]] += 1
        vulnerabilidades = ativo["vulnerabilidades"]
        if not vulnerabilidades:
            ativos_sem_vulnerabilidades += 1

        for vulnerabilidade in vulnerabilidades.values():
            total_vulnerabilidades += 1
            if vulnerabilidade["status"] != StatusVulnerabilidade.CORRIGIDA:
                severidades_abertas[vulnerabilidade["severidade"]] += 1

    return {
        "total_ativos": len(ativos),
        "tipos": tipos,
        "total_vulnerabilidades": total_vulnerabilidades,
        "severidades_abertas": severidades_abertas,
        "ativos_sem_vulnerabilidades": ativos_sem_vulnerabilidades,
    }


def mostrar_painel(ativos):
    """Apresenta um resumo simples sem usar bibliotecas externas."""

    resumo = calcular_painel(ativos)
    cabecalho("PAINEL DE SEGURANÇA")
    print(f"Ativos cadastrados:              {resumo['total_ativos']:>4}")
    for tipo, quantidade in resumo["tipos"].items():
        if quantidade:
            print(f"  {tipo.rotulo + ':':30} {quantidade:>4}")

    print(f"\nVulnerabilidades cadastradas:    {resumo['total_vulnerabilidades']:>4}")
    print("Vulnerabilidades não corrigidas por severidade:")
    for severidade, quantidade in resumo["severidades_abertas"].items():
        print(f"  {severidade.value + ':':30} {quantidade:>4}")
    print(
        f"\nAtivos sem vulnerabilidades:      "
        f"{resumo['ativos_sem_vulnerabilidades']:>4}"
    )

    criticas = resumo["severidades_abertas"][Severidade.CRITICA]
    if criticas:
        print(f"\n[ATENÇÃO] Existem {criticas} vulnerabilidade(s) crítica(s) não corrigida(s).")

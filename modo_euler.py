"""Laboratório matemático seguro e sem dependências externas do Sauron."""
#Importante ressaltar que aqui me inspirei em trabalhos de outras pessoas em repositórios
#públicos do github e utilizei abertamente recursos de IA Generativa. 
#Necessito estudar mais sobre como implementar esse solução e principalmente como
#otimiza-la com maestria, sinto me envergonhado por não conseguir ter implementado tal solução 
#de maneira assertiva e honesta, contudo, prometo melhorar as operações e fornecer uma explicação
#digna de aplausos em alguns dias, preciso de um tempinho para me aprimorar hehehe

import ast
import math
import re

from utilitarios import cabecalho, ler_inteiro, ler_opcao, ler_real


FUNCOES = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "exp": math.exp,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "abs": abs,
}
CONSTANTES = {"pi": math.pi, "e": math.e}
NOMES_PERMITIDOS = {"x", *CONSTANTES}


class ErroExpressao(ValueError):
    """Indica sintaxe ou operação não permitida no Modo Euler."""


def normalizar_expressao(expressao):
    """Aceita ``^`` como potência e vírgula decimal entre algarismos."""

    expressao = expressao.strip().replace("^", "**")
    return re.sub(r"(?<=\d),(?=\d)", ".", expressao)


def _validar_no(no):
    """Valida recursivamente a árvore para impedir execução arbitrária."""

    if isinstance(no, ast.Expression):
        _validar_no(no.body)
        return
    if isinstance(no, ast.Constant):
        if not isinstance(no.value, (int, float)) or isinstance(no.value, bool):
            raise ErroExpressao("Somente constantes numéricas são permitidas.")
        if not math.isfinite(float(no.value)) or abs(float(no.value)) > 1e12:
            raise ErroExpressao("A constante numérica é grande demais.")
        return
    if isinstance(no, ast.Name):
        if no.id not in NOMES_PERMITIDOS:
            raise ErroExpressao(f"O nome '{no.id}' não é permitido.")
        return
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.UAdd, ast.USub)):
        _validar_no(no.operand)
        return
    if isinstance(no, ast.BinOp) and isinstance(
        no.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
    ):
        _validar_no(no.left)
        _validar_no(no.right)
        if isinstance(no.op, ast.Pow) and isinstance(no.right, ast.Constant):
            if abs(float(no.right.value)) > 50:
                raise ErroExpressao("Expoentes constantes devem estar entre -50 e 50.")
        return
    if isinstance(no, ast.Call):
        if not isinstance(no.func, ast.Name) or no.func.id not in FUNCOES:
            raise ErroExpressao("A chamada de função não é permitida.")
        if len(no.args) != 1 or no.keywords:
            raise ErroExpressao("Cada função matemática deve receber um argumento.")
        _validar_no(no.args[0])
        return
    raise ErroExpressao(f"Construção não permitida: {type(no).__name__}.")


def compilar_funcao(expressao):
    """Compila uma expressão validada e devolve ``f(x)`` e sua árvore AST."""

    expressao = normalizar_expressao(expressao)
    if not expressao or len(expressao) > 200:
        raise ErroExpressao("A expressão deve ter entre 1 e 200 caracteres.")
    try:
        arvore = ast.parse(expressao, mode="eval")
    except SyntaxError as erro:
        raise ErroExpressao("Sintaxe inválida. Exemplo: x^2 + 2*x - 3.") from erro
    _validar_no(arvore)
    codigo = compile(arvore, "<modo-euler>", "eval")

    def funcao(x):
        ambiente = {"x": float(x), **FUNCOES, **CONSTANTES}
        try:
            resultado = eval(codigo, {"__builtins__": {}}, ambiente)
            resultado = float(resultado)
        except (ArithmeticError, TypeError, ValueError, OverflowError) as erro:
            raise ErroExpressao(f"A função não está definida em x = {x:g}.") from erro
        if not math.isfinite(resultado):
            raise ErroExpressao(f"O resultado não é finito em x = {x:g}.")
        return resultado

    return funcao, arvore.body, expressao


def _somar_polinomios(primeiro, segundo, fator=1.0):
    resultado = dict(primeiro)
    for grau, coeficiente in segundo.items():
        resultado[grau] = resultado.get(grau, 0.0) + fator * coeficiente
    return {grau: valor for grau, valor in resultado.items() if abs(valor) > 1e-12}


def _multiplicar_polinomios(primeiro, segundo):
    resultado = {}
    for grau_a, coef_a in primeiro.items():
        for grau_b, coef_b in segundo.items():
            grau = grau_a + grau_b
            if grau > 50:
                return None
            resultado[grau] = resultado.get(grau, 0.0) + coef_a * coef_b
    return resultado


def extrair_polinomio(no):
    """Tenta converter uma AST em ``{grau: coeficiente}``; senão, devolve None."""

    if isinstance(no, ast.Constant):
        return {0: float(no.value)}
    if isinstance(no, ast.Name):
        if no.id == "x":
            return {1: 1.0}
        if no.id in CONSTANTES:
            return {0: CONSTANTES[no.id]}
        return None
    if isinstance(no, ast.UnaryOp):
        polinomio = extrair_polinomio(no.operand)
        if polinomio is None:
            return None
        fator = -1.0 if isinstance(no.op, ast.USub) else 1.0
        return {grau: fator * coef for grau, coef in polinomio.items()}
    if isinstance(no, ast.BinOp):
        esquerda = extrair_polinomio(no.left)
        direita = extrair_polinomio(no.right)
        if isinstance(no.op, (ast.Add, ast.Sub)) and esquerda is not None and direita is not None:
            return _somar_polinomios(
                esquerda, direita, -1.0 if isinstance(no.op, ast.Sub) else 1.0
            )
        if isinstance(no.op, ast.Mult) and esquerda is not None and direita is not None:
            return _multiplicar_polinomios(esquerda, direita)
        if isinstance(no.op, ast.Div) and esquerda is not None and direita is not None:
            if set(direita) == {0} and abs(direita[0]) > 1e-12:
                return {grau: coef / direita[0] for grau, coef in esquerda.items()}
        if isinstance(no.op, ast.Pow) and esquerda is not None:
            if isinstance(no.right, ast.Constant):
                expoente = no.right.value
                if isinstance(expoente, int) and 0 <= expoente <= 50:
                    resultado = {0: 1.0}
                    for _ in range(expoente):
                        resultado = _multiplicar_polinomios(resultado, esquerda)
                    return resultado
    return None


def _contem_x(no):
    return any(isinstance(item, ast.Name) and item.id == "x" for item in ast.walk(no))


def identificar_tipo(no):
    """Classifica a família predominante da expressão informada."""

    polinomio = extrair_polinomio(no)
    if polinomio is not None:
        grau = max(polinomio, default=0)
        return {
            0: "Constante",
            1: "Afim (linear)",
            2: "Quadrática",
            3: "Cúbica",
        }.get(grau, f"Polinomial de grau {grau}")

    categorias = []
    chamadas = {
        item.func.id
        for item in ast.walk(no)
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
    }
    if chamadas & {"sin", "cos", "tan", "asin", "acos", "atan"}:
        categorias.append("trigonométrica")
    if chamadas & {"log", "ln", "log10"}:
        categorias.append("logarítmica")
    if "exp" in chamadas or any(
        isinstance(item, ast.BinOp)
        and isinstance(item.op, ast.Pow)
        and _contem_x(item.right)
        for item in ast.walk(no)
    ):
        categorias.append("exponencial")
    if "sqrt" in chamadas:
        categorias.append("radical")
    if any(
        isinstance(item, ast.BinOp)
        and isinstance(item.op, ast.Pow)
        and _contem_x(item.left)
        and isinstance(item.right, ast.Constant)
        and isinstance(item.right.value, (int, float))
        and not float(item.right.value).is_integer()
        for item in ast.walk(no)
    ):
        categorias.append("radical")
    if any(
        isinstance(item, ast.BinOp)
        and isinstance(item.op, ast.Div)
        and _contem_x(item.right)
        for item in ast.walk(no)
    ):
        categorias.append("racional")
    categorias = list(dict.fromkeys(categorias))
    if not categorias:
        return "Algébrica ou composta"
    if len(categorias) == 1:
        return categorias[0].capitalize()
    return "Composta: " + ", ".join(categorias)


def derivar_polinomio(coeficientes):
    """Calcula simbolicamente os coeficientes da derivada polinomial."""

    return {
        grau - 1: grau * coeficiente
        for grau, coeficiente in coeficientes.items()
        if grau > 0 and abs(coeficiente) > 1e-12
    }


def integrar_polinomio(coeficientes):
    """Calcula simbolicamente uma primitiva polinomial sem a constante C."""

    return {
        grau + 1: coeficiente / (grau + 1)
        for grau, coeficiente in coeficientes.items()
        if abs(coeficiente) > 1e-12
    }


def formatar_polinomio(coeficientes, incluir_constante=False):
    """Transforma coeficientes em uma expressão matemática legível."""

    termos = []
    for grau in sorted(coeficientes, reverse=True):
        coeficiente = coeficientes[grau]
        if abs(coeficiente) <= 1e-12:
            continue
        sinal = "-" if coeficiente < 0 else "+"
        modulo = abs(coeficiente)
        numero = f"{modulo:.8g}"
        if grau == 0:
            corpo = numero
        elif grau == 1:
            corpo = "x" if abs(modulo - 1.0) <= 1e-12 else f"{numero}*x"
        else:
            corpo = f"x^{grau}" if abs(modulo - 1.0) <= 1e-12 else f"{numero}*x^{grau}"
        if not termos:
            termos.append(("-" if sinal == "-" else "") + corpo)
        else:
            termos.append(f" {sinal} {corpo}")
    resultado = "".join(termos) or "0"
    if incluir_constante:
        resultado += " + C"
    return resultado


def derivada_numerica(funcao, x, passo=None):
    """Aproxima f'(x) por diferença central."""

    h = passo or 1e-5 * max(1.0, abs(x))
    return (funcao(x + h) - funcao(x - h)) / (2.0 * h)


def integrar_simpson(funcao, inicio, fim, subdivisoes=1000):
    """Aproxima a integral definida pela regra composta de Simpson."""

    if subdivisoes < 2:
        raise ValueError("São necessárias ao menos duas subdivisões.")
    if subdivisoes % 2:
        subdivisoes += 1
    if inicio == fim:
        return 0.0
    h = (fim - inicio) / subdivisoes
    soma = funcao(inicio) + funcao(fim)
    for indice in range(1, subdivisoes):
        peso = 4 if indice % 2 else 2
        soma += peso * funcao(inicio + indice * h)
    return soma * h / 3.0


def _bissecao(funcao, esquerda, direita, iteracoes=60):
    fe = funcao(esquerda)
    fd = funcao(direita)
    if abs(fe) < 1e-10:
        return esquerda
    if abs(fd) < 1e-10:
        return direita
    for _ in range(iteracoes):
        meio = (esquerda + direita) / 2.0
        fm = funcao(meio)
        if abs(fm) < 1e-10:
            return meio
        if fe * fm <= 0:
            direita = meio
        else:
            esquerda, fe = meio, fm
    return (esquerda + direita) / 2.0


def encontrar_raizes(funcao, inicio, fim, amostras=1000):
    """Procura raízes por amostragem e bisseção em mudanças de sinal."""

    if inicio > fim:
        inicio, fim = fim, inicio
    passo = (fim - inicio) / amostras
    raizes = []
    anterior_x = inicio
    try:
        anterior_y = funcao(anterior_x)
    except ErroExpressao:
        anterior_y = None

    if anterior_y is not None and abs(anterior_y) < 1e-8:
        raizes.append(anterior_x)

    for indice in range(1, amostras + 1):
        atual_x = inicio + indice * passo
        try:
            atual_y = funcao(atual_x)
        except ErroExpressao:
            anterior_x, anterior_y = atual_x, None
            continue
        candidata = None
        if abs(atual_y) < 1e-8:
            candidata = atual_x
        elif anterior_y is not None and anterior_y * atual_y < 0:
            candidata = _bissecao(funcao, anterior_x, atual_x)
        if candidata is not None and all(abs(candidata - raiz) > max(passo, 1e-6) for raiz in raizes):
            raizes.append(candidata)
        anterior_x, anterior_y = atual_x, atual_y
    return raizes


def _ler_intervalo():
    inicio = ler_real("Início do intervalo: ")
    fim = ler_real("Fim do intervalo: ")
    if inicio > fim:
        inicio, fim = fim, inicio
        print("[INFO] Os limites foram reorganizados em ordem crescente.")
    return inicio, fim


def _mostrar_tabela(funcao):
    inicio, fim = _ler_intervalo()
    pontos = ler_inteiro("Quantidade de pontos (2 a 30): ", minimo=2)
    pontos = min(pontos, 30)
    passo = (fim - inicio) / (pontos - 1)
    print(
        "\n{:>16} | {:>16} | {:>20}".format(
            "x", "f(x)", "f'(x) aproximada"
        )
    )
    print("-" * 58)
    for indice in range(pontos):
        x = inicio + indice * passo
        try:
            y = funcao(x)
            derivada = derivada_numerica(funcao, x)
            print(f"{x:>16.8g} | {y:>16.8g} | {derivada:>20.8g}")
        except ErroExpressao:
            print(f"{x:>16.8g} | {'fora do domínio':>39}")


def mostrar_guia_euler():
    """Ensina a notação aceita e resume os métodos de cálculo usados."""

    cabecalho("GUIA DE NOTAÇÃO E MÉTODOS DO MODO EULER")
    print("VARIÁVEL E OPERADORES")
    print("  Use x como variável e +, -, *, /, ^ ou ** como operadores.")
    print("  Multiplicação precisa do asterisco: escreva 2*x, nunca 2x.")
    print("  Potência pode ser x^2 ou x**2. Decimais aceitam 2.5 ou 2,5.")
    print("\nFUNÇÕES E CONSTANTES")
    print("  sin(x), cos(x), tan(x), asin(x), acos(x), atan(x)")
    print("  exp(x), log(x) ou ln(x), log10(x), sqrt(x), abs(x)")
    print("  Constantes: pi e e. Exemplos: sin(pi*x), exp(-x), log(x)/x")
    print("\nEXEMPLOS PRINCIPAIS")
    print("  Afim:         2*x + 3")
    print("  Quadrática:   x^2 + 2*x - 3")
    print("  Racional:     (x + 1)/(x - 2)")
    print("  Trigonométrica: sin(x) + cos(2*x)")
    print("  Exponencial:  exp(-x)")
    print("  Logarítmica:  log(x)   (exige x > 0)")
    print("  Radical:      sqrt(x + 4)   (exige x >= -4)")
    print("\nCOMO O SAURON CHEGA AOS RESULTADOS")
    print("  Classificação: inspeciona a árvore sintática já validada.")
    print("  Polinômios: aplica as regras de potência em coeficientes e graus.")
    print("  Derivada numérica: diferença central [f(x+h)-f(x-h)]/(2h).")
    print("  Integral: regra composta de Simpson, com pesos 1, 4, 2, ..., 4, 1.")
    print("  Raízes: amostra o intervalo e refina mudanças de sinal por bisseção.")
    print("  Os resultados numéricos são aproximações e dependem do intervalo/passo.")


def menu_modo_euler():
    """Executa o laboratório interativo de análise de funções."""

    mostrar_guia_euler()
    while True:
        cabecalho("MODO EULER — LABORATÓRIO MATEMÁTICO")
        print("Use x como variável. Operadores: +, -, *, /, ^ ou **.")
        print("Funções: sin, cos, tan, exp, log/ln, log10, sqrt e abs.")
        print("Constantes: pi e e. Digite 0 para voltar.")
        entrada = input("\nf(x) = ").strip()
        if entrada == "0":
            return
        try:
            funcao, arvore, expressao = compilar_funcao(entrada)
        except ErroExpressao as erro:
            print(f"[ERRO MATEMÁTICO] {erro}")
            continue

        tipo = identificar_tipo(arvore)
        cabecalho("ANÁLISE DA FUNÇÃO")
        print(f"Expressão normalizada: f(x) = {expressao}")
        print(f"Classificação:         {tipo}")
        print("Método: árvore sintática validada; nenhuma chamada externa é permitida.")
        polinomio = extrair_polinomio(arvore)
        if polinomio is not None:
            print(f"Grau:                  {max(polinomio, default=0)}")
            print(f"Derivada simbólica:    f'(x) = {formatar_polinomio(derivar_polinomio(polinomio))}")
            print(
                "Primitiva simbólica:   F(x) = "
                + formatar_polinomio(integrar_polinomio(polinomio), True)
            )

        while True:
            print("\n1 - Calcular f(x)")
            print("2 - Calcular derivada aproximada em um ponto")
            print("3 - Calcular integral definida e valor médio")
            print("4 - Procurar raízes em um intervalo")
            print("5 - Gerar tabela de valores e derivadas")
            print("6 - Informar outra função")
            print("7 - Rever guia de notação e métodos")
            print("0 - Voltar ao menu principal")
            escolha = ler_opcao("Opção: ", range(0, 8))
            if escolha == "0":
                return
            if escolha == "6":
                break
            if escolha == "7":
                mostrar_guia_euler()
                continue
            try:
                if escolha == "1":
                    x = ler_real("x = ")
                    print(f"f({x:g}) = {funcao(x):.12g}")
                    print("Método: substituição direta de x na expressão validada.")
                elif escolha == "2":
                    x = ler_real("Ponto x = ")
                    print(f"f'({x:g}) ≈ {derivada_numerica(funcao, x):.12g}")
                    print("Método: diferença central com valores em x-h e x+h.")
                elif escolha == "3":
                    inicio, fim = _ler_intervalo()
                    subdivisoes = ler_inteiro(
                        "Subdivisões de Simpson (mínimo 2; sugerido 1000): ", minimo=2
                    )
                    integral = integrar_simpson(funcao, inicio, fim, subdivisoes)
                    print(f"Integral ≈ {integral:.12g}")
                    print("Método: regra composta de Simpson sobre subdivisões pares.")
                    if fim != inicio:
                        print(f"Valor médio ≈ {integral / (fim - inicio):.12g}")
                elif escolha == "4":
                    inicio, fim = _ler_intervalo()
                    raizes = encontrar_raizes(funcao, inicio, fim)
                    if raizes:
                        print("Raízes aproximadas: " + ", ".join(f"{raiz:.10g}" for raiz in raizes))
                    else:
                        print("[INFO] Nenhuma mudança de sinal foi encontrada no intervalo.")
                    print("Método: amostragem seguida de bisseção nas mudanças de sinal.")
                elif escolha == "5":
                    _mostrar_tabela(funcao)
                    print("Método: amostragem uniforme e derivada central em cada ponto.")
            except (ErroExpressao, ValueError) as erro:
                print(f"[ERRO MATEMÁTICO] {erro}")

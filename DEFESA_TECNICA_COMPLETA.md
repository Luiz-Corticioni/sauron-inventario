# Defesa técnica completa do sistema Sentinela

## Finalidade deste material

Este documento serve como roteiro de apresentação e como material de estudo
para a arguição do projeto. Ele explica a arquitetura, o fluxo dos dados, cada
classe e cada função da versão final. Também compara essa versão com a solução
anterior e examina alternativas compatíveis com a ementa.

A ideia central do Sentinela é manter o CRUD explícito e didático, enquanto a
experiência do usuário apresenta elementos próprios de um inventário de
segurança: catálogo educativo, orientação de localização, mapa lógico e painel
de riscos. O programa continua baseado em fundamentos da disciplina: variáveis,
funções, condicionais, laços, listas, dicionários, Enum, arquivos, módulos e
tratamento de exceções.

## Apresentação oral em cinco minutos

### Primeiro minuto

Apresente o problema e a arquitetura.

> O Sentinela é um inventário textual de segurança. Ele cadastra ativos de TI,
> associa vulnerabilidades, acompanha o tratamento e grava tudo em JSON. Separei
> o sistema em cinco módulos: `main.py` coordena os menus, `ativos.py` contém o
> CRUD, `vulnerabilidades.py` trata os riscos, `dados.py` cuida do arquivo e
> `utilitarios.py` reúne os tipos enumerados, validações, catálogo, mapa e painel.

Em seguida, mostre o dicionário principal e explique que o ID inteiro funciona
como chave. Uma consulta conhecida por ID usa `ativos.get(id_ativo)`. A busca por
nome percorre os valores porque permite encontrar trechos do hostname.

### Segundo minuto

Cadastre um ativo do tipo Switch. Mostre que o Enum associa o tipo a um código
inteiro. Escolha primeiro uma localização incomum para acionar o aviso e depois
selecione Sala de Servidores. Explique que a recomendação orienta, mas não
bloqueia uma exceção real.

Cadastre uma vulnerabilidade inicial. Abra uma categoria do catálogo, mostre a
explicação, selecione severidade e status e destaque o ID automático `VUL-001`.

### Terceiro minuto

Consulte o ativo pelo hostname. Na ficha, mostre os dados de inventário e o
resumo das vulnerabilidades. Atualize o responsável ou setor sem redigitar o
registro inteiro. Explique que a função altera somente a chave escolhida no
dicionário.

### Quarto minuto

Abra o mapa. Explique que ele primeiro mostra a topologia conceitual e depois
agrupa os ativos reais pelo campo `localizacao`. Abra o painel e mostre que as
contagens são calculadas a partir da mesma base em memória, sem duplicar dados.

### Quinto minuto

Mostre `inventario.json` e explique a conversão dos Enums para texto. Finalize
com a remoção de um ativo, destacando que as vulnerabilidades são eliminadas
junto porque estão aninhadas no registro. Mostre no repositório as branches e
os merges reais usados durante o desenvolvimento.

## Visão geral da arquitetura

O fluxo principal é o seguinte:

```text
Usuário
  |
  v
main.py
  |-- ativos.py
  |-- vulnerabilidades.py
  |-- utilitarios.py
  `-- dados.py
         |
         v
dados/inventario.json
```

`main.py` não implementa regras detalhadas. Ele recebe escolhas e encaminha o
controle. Os módulos de domínio alteram o dicionário em memória. Quando uma
função informa que houve alteração, `main.py` chama `dados.salvar`. Essa divisão
evita que o menu saiba como serializar JSON e evita que a persistência saiba
como cadastrar um ativo.

O objeto central possui esta forma conceitual:

```python
ativos = {
    101: {
        "id": 101,
        "nome": "SW-CORE-01",
        "tipo": TipoAtivo.SWITCH,
        "responsavel": "Equipe de Redes",
        "setor": "TI",
        "localizacao": "Sala de Servidores",
        "descricao": "Switch principal",
        "vulnerabilidades": {
            "VUL-001": {
                "categoria": "Software desatualizado",
                "descricao": "Firmware antigo",
                "severidade": Severidade.ALTA,
                "status": StatusVulnerabilidade.EM_TRATAMENTO,
                "tratamento_sugerido": "Atualizar o firmware"
            }
        }
    }
}
```

O ID do ativo é uma chave inteira. As vulnerabilidades formam outro dicionário
dentro do ativo. Essa composição cria uma relação de pertencimento simples: a
vulnerabilidade existe no contexto do ativo. A exclusão do ativo elimina toda a
estrutura associada sem uma segunda busca.

## Módulo main

### Papel do módulo

`main.py` é o ponto de entrada. Ele carrega a base, exibe menus, encaminha cada
opção ao módulo adequado e solicita a gravação quando uma operação modifica os
dados. Essa função de coordenação costuma ser chamada de camada de apresentação
ou controlador, embora o trabalho não exija arquitetura formal.

### Função salvar se alterado

Assinatura:

```python
def salvar_se_alterado(base, alterado):
```

`base` é o dicionário completo de ativos. `alterado` é um valor booleano
devolvido pelas operações de cadastro, atualização ou remoção. Se ele for
`True`, a função chama `dados.salvar(base)`. Se for `False`, nenhuma escrita é
feita.

Essa decisão evita gravar o arquivo quando o usuário apenas consultou dados ou
cancelou uma operação. Também padroniza a persistência: os menus não precisam
repetir blocos `if alterado` em toda opção. A função não retorna valor porque
seu efeito esperado é a gravação.

Uma alternativa seria salvar dentro de cada função de domínio. Isso reduziria
uma linha no menu, mas criaria dependência direta de `ativos.py` e
`vulnerabilidades.py` em relação a `dados.py`. Outra alternativa seria salvar
apenas ao sair. Ela faria menos operações de disco, mas perderia todo o trabalho
se o programa fosse interrompido antes do encerramento.

### Função menu ativos

Assinatura:

```python
def menu_ativos(base):
```

A função executa um laço `while True`. Em cada repetição, mostra as operações
Create, Read, Update e Delete, além da listagem. `ler_opcao` só permite valores
entre zero e cinco. A opção zero usa `return`, encerrando o submenu e devolvendo
o controle ao menu principal.

Cada opção chama uma função de `ativos.py`. Operações de escrita são envolvidas
por `salvar_se_alterado`. Consulta e listagem não alteram a base e, portanto,
não gravam o arquivo. O CRUD permanece visível no menu, o que facilita a
verificação do requisito pelo avaliador.

Ponto importante para a defesa: o menu não conhece a estrutura interna do
registro. Ele sabe apenas qual ação deve solicitar. Se o campo de um ativo
mudar, a maior parte do menu permanece intacta.

### Função menu vulnerabilidades

Assinatura:

```python
def menu_vulnerabilidades(base):
```

Também usa um laço contínuo e apresenta cadastrar, visualizar, atualizar e
remover. Antes de executar a operação, chama `ativos.selecionar(base, "usar")`.
Isso garante que toda vulnerabilidade fique vinculada a um ativo existente.

Se a seleção devolver `None`, o comando `continue` inicia a próxima repetição
do menu. Se um ativo for encontrado, a função correspondente recebe o próprio
dicionário do ativo. Como dicionários são objetos mutáveis, alterar esse objeto
altera a estrutura contida em `base`. Depois, as operações de escrita são
persistidas.

Esse fluxo evita o uso de um identificador de ativo solto dentro do módulo de
vulnerabilidades. O módulo recebe o registro que deve manipular, reduzindo
buscas duplicadas.

### Função executar

Assinatura:

```python
def executar():
```

É a função principal do sistema. Primeiro chama `dados.carregar()`. Caso o JSON
esteja inválido ou não possa ser lido, captura `dados.ErroDeDados`, informa o
problema e encerra. Essa interrupção é deliberada: iniciar com uma base vazia e
salvá-la poderia sobrescrever um arquivo corrompido que ainda contém dados
recuperáveis.

Após o carregamento, o menu principal permanece em um `while True`. Ele oferece
gestão de ativos, vulnerabilidades, mapa, catálogo e painel. A opção zero encerra
com `return`. Um segundo `try` captura falhas de gravação durante a sessão sem
transformar uma exceção de arquivo em um fechamento abrupto do programa.

No bloco final do arquivo, `if __name__ == "__main__"` garante que `executar`
só seja iniciado automaticamente quando `main.py` é executado diretamente. Se
o módulo for importado por um teste, o menu não começa. `KeyboardInterrupt` e
`EOFError` tratam interrupções do terminal de forma legível.

## Módulo ativos

### Papel do módulo

`ativos.py` implementa o CRUD e as formas de visualização dos ativos. Todas as
funções recebem `ativos` explicitamente, em vez de depender de uma variável
global. Isso permite testar funções com uma base pequena e isolada.

### Função buscar por id

Assinatura:

```python
def buscar_por_id(ativos, id_ativo):
```

Ela executa `ativos.get(id_ativo)`. Se a chave existir, devolve o dicionário do
ativo. Caso contrário, devolve `None`. O método `get` evita `KeyError` e expressa
claramente que a ausência é uma possibilidade prevista.

Em um dicionário, a busca por chave tem complexidade média O(1). Isso significa
que o tempo médio não cresce na mesma proporção que a quantidade de registros.
Essa é a justificativa técnica do requisito que pede `dict` como índice.

### Função buscar por nome

Assinatura:

```python
def buscar_por_nome(ativos, termo):
```

O termo passa por `casefold()` e `strip()`. `strip` remove espaços nas pontas.
`casefold` cria uma forma apropriada para comparação sem diferença entre
maiúsculas e minúsculas. Se o termo ficar vazio, a função devolve uma lista
vazia.

Depois, uma compreensão de lista percorre `ativos.values()` e mantém os
registros cujo nome contém o termo. O resultado é uma lista porque diferentes
hostnames podem conter o mesmo fragmento. A complexidade é O(n), pois a busca
parcial não usa um índice separado.

Um índice por hostname poderia tornar a busca exata mais rápida, mas exigiria
sincronizar dois dicionários sempre que um nome fosse atualizado. Para uma base
didática pequena e uma pesquisa por fragmento, a varredura é mais simples e
menos sujeita a inconsistências.

### Função cadastrar

Assinatura:

```python
def cadastrar(ativos):
```

A função começa exibindo um cabeçalho e lê o ID em um laço. `ler_inteiro`
garante o tipo e o limite mínimo. A condição `id_ativo not in ativos` garante
unicidade. Se a chave já existir, o usuário é informado e a pergunta se repete.

Depois são lidos nome, responsável e setor. A descrição é opcional. O tipo vem
de `escolher_tipo_ativo`, que retorna um membro de `TipoAtivo`. A localização
vem de `escolher_localizacao(tipo)`, de modo que as recomendações dependem do
tipo já selecionado.

O registro é construído como dicionário e inserido com
`ativos[id_ativo] = ativo`. A lista inicial de vulnerabilidades é representada
por um dicionário vazio. A inserção ocorre antes do cadastro das
vulnerabilidades porque o gerador de IDs examina a base completa.

Se o usuário desejar uma vulnerabilidade inicial, um laço chama
`vulnerabilidades.cadastrar`. Se o cadastro for cancelado, o laço termina. Se
for concluído, o usuário pode adicionar outra. Ao final, a função devolve
`True`, informando ao menu que a base mudou.

Pontos da ementa presentes nessa única função: entrada de dados, conversão de
tipo, laço, condição, função, dicionário, Enum, composição de estruturas e
interação entre módulos.

### Função imprimir ficha

Assinatura:

```python
def imprimir_ficha(ativo):
```

Esta função é responsável somente pela apresentação. Ela lê as chaves do ativo
e imprime os campos em formato organizado. O operador `or` em
`ativo['descricao'] or 'Não informada'` substitui uma string vazia por um texto
mais claro para o usuário.

`len(ativo["vulnerabilidades"])` calcula a quantidade de riscos. Se for zero,
a função informa a ausência e retorna antecipadamente. Caso existam registros,
percorre os pares com `items()` e imprime ID, severidade, status e categoria.
`sorted` torna a ordem previsível.

Separar a exibição da busca permite reutilizar a ficha tanto em uma pesquisa
por ID quanto em vários resultados por nome.

### Função consultar

Assinatura:

```python
def consultar(ativos):
```

Primeiro verifica se a base está vazia. Depois oferece busca por ID ou nome. Na
busca por ID, chama `buscar_por_id`. Na busca por nome, chama
`buscar_por_nome`. O resultado direto é impresso uma vez; a lista de resultados
é ordenada e percorrida.

Essa função demonstra duas estratégias de consulta no mesmo sistema. O ID é
uma chave exata e eficiente. O nome é um atributo textual, pode ser parcial e
pode gerar múltiplos resultados.

### Função listar

Assinatura:

```python
def listar(ativos):
```

Mostra uma visão compacta de todos os ativos. `ativos.values()` fornece os
registros sem as chaves externas. `sorted` usa uma função `lambda` para ordenar
pelo campo `id`. As f-strings definem larguras de coluna para alinhar ID, nome,
tipo e localização.

Os cortes `[:21]` impedem que nomes muito longos destruam a tabela textual. A
ficha completa continua disponível na consulta. Essa é uma escolha de interface,
não uma perda no dado armazenado.

### Função selecionar

Assinatura:

```python
def selecionar(ativos, finalidade="selecionar"):
```

Centraliza a seleção por ID usada em atualização, remoção e vulnerabilidades.
O parâmetro `finalidade` muda a frase mostrada ao usuário, sem duplicar a lógica.
Se a base estiver vazia ou o ID não existir, devolve `None`. Caso contrário,
devolve o dicionário do ativo.

Essa função reduz repetição e mantém mensagens consistentes. O valor padrão
permite chamá-la sem sempre informar uma finalidade.

### Função atualizar

Assinatura:

```python
def atualizar(ativos):
```

Seleciona o ativo e apresenta campos editáveis. A opção zero cancela e devolve
`False`. Cada outra opção altera uma chave específica do dicionário. Como o
registro é mutável e pertence à base, não é necessário reinseri-lo.

Ao mudar o tipo, a função também revisa a localização. Isso preserva a coerência
entre o novo tipo e as recomendações de infraestrutura. A descrição pode ficar
vazia porque é opcional. Ao final, devolve `True` para solicitar persistência.

Outra implementação possível seria pedir todos os campos novamente. Ela seria
menor, mas aumentaria o risco de apagar informações corretas durante uma
alteração simples.

### Função remover

Assinatura:

```python
def remover(ativos):
```

Seleciona o registro, mostra nome, ID e quantidade de vulnerabilidades e pede
confirmação. Se o usuário responder não, devolve `False`. Se confirmar, executa
`del ativos[ativo["id"]]` e devolve `True`.

As vulnerabilidades desaparecem porque fazem parte do dicionário removido. Isso
atende ao requisito de exclusão em cascata sem manter uma segunda coleção
global. Em um banco relacional, o mesmo comportamento exigiria uma chave
estrangeira com cascata ou duas operações coordenadas.

## Módulo vulnerabilidades

### Papel do módulo

`vulnerabilidades.py` manipula os riscos contidos em um ativo. Ele conhece o
formato da vulnerabilidade, mas não carrega nem salva arquivos. O menu entrega o
ativo já selecionado e decide quando persistir.

### Função gerar id

Assinatura:

```python
def gerar_id(ativos):
```

A função percorre todos os ativos e todos os identificadores de
vulnerabilidade. A expressão regular `VUL-(\d+)` reconhece o padrão e captura a
parte numérica. `max` mantém o maior valor. O próximo ID é formatado com três
dígitos por `f"VUL-{maior_numero + 1:03d}"`.

O uso da base completa torna o identificador único entre ativos, e não apenas
dentro de um ativo. IDs fora do padrão são ignorados de forma segura. A
complexidade é O(v), sendo v o total de vulnerabilidades. Para o volume do
trabalho, essa varredura é adequada. Em uma base grande, seria melhor persistir
um contador ou usar UUID.

### Função escolher categoria

Assinatura:

```python
def _escolher_categoria(permitir_cancelar=True):
```

O sublinhado inicial indica que a função é interna ao módulo. Ela lista o
catálogo, oferece categoria personalizada e, quando permitido, cancelamento.
Uma categoria predefinida é explicada por `exibir_item_catalogo`. O usuário
confirma antes de usá-la.

O retorno é um pequeno dicionário com `nome` e `tratamento`. Na opção
personalizada, esses valores são digitados. No cancelamento, o retorno é
`None`. Essa padronização permite que `cadastrar` e `atualizar` usem o mesmo
resultado, independentemente da origem da categoria.

### Função cadastrar vulnerabilidade

Assinatura:

```python
def cadastrar(ativos, ativo):
```

A função mostra qual ativo receberá o risco e chama `_escolher_categoria`. Se o
retorno for `None`, informa o cancelamento e devolve `False`. Depois lê a
descrição, a severidade e o status. O ID é obtido por `gerar_id(ativos)`.

O registro possui os quatro campos mínimos do enunciado: categoria, descrição,
severidade e status. `tratamento_sugerido` é um acréscimo educativo. A inserção
usa `ativo["vulnerabilidades"][identificador] = {...}`. A função devolve `True`
para indicar alteração.

### Função listar vulnerabilidades

Assinatura:

```python
def listar(ativo):
```

Se o dicionário interno estiver vazio, informa explicitamente que não há
registros. Caso contrário, percorre os itens ordenados e apresenta os campos
exigidos. A orientação só é mostrada se existir, usando `item.get` para tolerar
registros antigos que não possuam essa chave.

Essa tolerância é útil em evolução de dados. O acesso direto
`item['tratamento_sugerido']` produziria `KeyError` em um JSON criado antes da
adição do campo.

### Função selecionar vulnerabilidade

Assinatura:

```python
def _selecionar(ativo, acao):
```

É outra função interna. Ela lista os IDs disponíveis, lê a escolha, normaliza
com `strip().upper()` e usa `get`. O parâmetro `acao` personaliza a mensagem.

O retorno possui dois valores: identificador e dicionário da vulnerabilidade.
Em uma falha, devolve `(None, None)`. Essa tupla permite que atualização e
remoção usem tanto a chave quanto o valor sem realizar nova busca.

### Função atualizar vulnerabilidade

Assinatura:

```python
def atualizar(ativo):
```

Seleciona o risco e oferece quatro campos. Descrição usa texto obrigatório.
Categoria reutiliza o catálogo. Severidade e status reutilizam menus
explicativos. A opção zero devolve `False`; uma alteração concluída devolve
`True`.

Permitir atualizar o status é essencial ao sentido de acompanhamento. Uma
vulnerabilidade pode começar aberta, passar para em tratamento e terminar
corrigida. O dado representa um processo, não apenas uma anotação estática.

### Função remover vulnerabilidade

Assinatura:

```python
def remover(ativo):
```

Seleciona, mostra os dados e solicita confirmação. A exclusão usa
`del ativo["vulnerabilidades"][identificador]`. O ativo continua existindo.
A função diferencia a remoção de um risco da remoção completa do ativo.

O enunciado não exige explicitamente Delete separado para vulnerabilidades,
mas essa função completa a gestão e torna a aplicação mais coerente.

## Módulo dados

### Papel do módulo

`dados.py` é a única parte que conhece o caminho e o formato físico da base. O
restante do sistema trabalha com objetos Python. Essa separação permite trocar
JSON por outro mecanismo no futuro com poucas alterações externas.

### Constante caminho dados

`CAMINHO_DADOS` usa `Path(__file__).resolve().parent`. O caminho parte da pasta
do próprio módulo, e não do diretório atual do terminal. Portanto, o programa
localiza `dados/inventario.json` mesmo quando é iniciado por um caminho externo.

### Classe erro de dados

Assinatura:

```python
class ErroDeDados(Exception):
```

É uma exceção específica para problemas de leitura, estrutura e gravação. Ela
permite que `main.py` capture falhas esperadas de persistência sem esconder
erros de programação não relacionados.

Uma classe vazia já é útil porque seu tipo comunica a categoria do problema.
Não foi necessário criar atributos adicionais.

### Função serializar

Assinatura:

```python
def _serializar(ativos):
```

JSON aceita strings, números, booleanos, listas, objetos e `null`, mas não sabe
gravar membros de Enum. A função cria uma nova estrutura. Converte a chave
inteira do ativo para string e substitui `tipo`, `severidade` e `status` pelos
nomes dos membros, como `SWITCH`, `ALTA` e `EM_TRATAMENTO`.

Os operadores `**ativo` e `**vulnerabilidade` copiam os pares existentes. As
chaves especiais são escritas depois e substituem os objetos Enum pelas formas
serializáveis. A estrutura em memória não é modificada.

### Função desserializar

Assinatura:

```python
def _desserializar(conteudo):
```

Realiza o caminho inverso. Primeiro garante que a raiz do JSON seja um objeto.
Converte a chave textual para `int` e reconstrói os Enums por acesso como
`TipoAtivo[item["tipo"]]`.

`item.get("vulnerabilidades", {})` permite carregar um registro sem a chave
interna como coleção vazia. Falhas de chave, tipo ou conversão são reunidas em
`ErroDeDados` com uma mensagem compreensível. A causa original é preservada por
`raise ... from erro`, o que ajuda durante depuração.

### Função carregar

Assinatura:

```python
def carregar(caminho=CAMINHO_DADOS):
```

O parâmetro possui um caminho padrão, mas pode receber outro caminho nos testes.
Se o arquivo ainda não existir, devolve `{}`, comportamento esperado na primeira
execução. Caso exista, abre em modo de leitura com UTF-8 e chama `json.load`.

Um JSON sintaticamente inválido gera `JSONDecodeError`, convertido para
`ErroDeDados`. Falhas do sistema de arquivos geram `OSError`, também convertido.
Após a leitura, `_desserializar` devolve a base pronta para uso.

### Função salvar

Assinatura:

```python
def salvar(ativos, caminho=CAMINHO_DADOS):
```

Cria a pasta necessária e grava primeiro em um arquivo `.tmp`. `json.dump` usa
UTF-8, mantém acentos por `ensure_ascii=False` e aplica indentação para leitura
humana. Somente depois da escrita completa, `temporario.replace(caminho)` troca
o arquivo principal.

Essa gravação reduz o risco de deixar o JSON pela metade se houver falha durante
a escrita. Não é uma transação completa como a de um banco de dados, mas é uma
melhoria simples e explicável dentro do escopo do projeto.

## Módulo utilitarios

### Papel do módulo

`utilitarios.py` concentra elementos usados por vários módulos. Ele contém os
Enums, os dicionários de conhecimento, os validadores e as visualizações
derivadas. A centralização evita mensagens e regras divergentes.

### Enum tipo ativo

`TipoAtivo` possui nove membros, todos associados a inteiros. A propriedade
`rotulo` consulta `ROTULOS_TIPO_ATIVO` para mostrar um nome amigável sem mudar o
valor numérico exigido. `TipoAtivo.SWITCH.value` é `4`, enquanto
`TipoAtivo.SWITCH.rotulo` é `Switch`.

Separar código e rótulo evita usar strings livres para classificação. Uma
entrada inválida não se torna um tipo reconhecido por acidente.

### Enum severidade

`Severidade` limita a escala a Baixa, Média, Alta e Crítica. Seus valores são
textos amigáveis. O Enum evita variações como `alta`, `ALTO` ou `grave`, que
dificultariam contagens no painel.

### Enum status vulnerabilidade

`StatusVulnerabilidade` representa Aberta, Em tratamento, Corrigida e Risco
aceito. O painel considera corrigida como encerrada. Os demais estados são
contados como não corrigidos, inclusive risco aceito, pois o problema continua
existindo mesmo quando a organização decide conviver com ele.

### Constantes de localização e catálogo

`LOCALIZACOES` é uma lista porque representa uma sequência de escolhas.
`LOCAIS_RECOMENDADOS` é um dicionário que mapeia cada `TipoAtivo` para uma tupla
de locais. A tupla expressa um conjunto fixo de recomendações.

`CATALOGO_VULNERABILIDADES` é um dicionário de dicionários. Cada código aponta
para nome, explicação, exemplo, risco, tratamento e severidade típica. O catálogo
é local e não depende de internet ou CVE real, conforme permitido pelo
enunciado.

`DESCRICOES_SEVERIDADE` e `DESCRICOES_STATUS` transformam membros de Enum em
explicações. O sistema ensina o significado da escolha antes de armazená-la.

### Função cabecalho

Assinatura:

```python
def cabecalho(titulo):
```

Imprime uma linha, o título centralizado em 64 caracteres e outra linha. Não
altera dados. A função mantém identidade visual e elimina repetição de vários
`print` em cada menu.

### Função ler texto obrigatorio

Assinatura:

```python
def ler_texto_obrigatorio(mensagem):
```

Usa um laço até receber uma string não vazia. `strip` impede que apenas espaços
sejam aceitos. Diferentemente da solução anterior, números puros não são
rejeitados: um hostname, setor ou nome pode legitimamente conter números.

### Função ler inteiro

Assinatura:

```python
def ler_inteiro(mensagem, minimo=None):
```

Tenta converter a entrada com `int`. Se ocorrer `ValueError`, informa o erro e
repete. Se `minimo` foi fornecido, também valida o limite. Essa função demonstra
conversão de tipos e tratamento de exceções sem encerrar o programa.

O valor padrão `None` significa que não há limite. Para IDs, o sistema usa
`minimo=1`.

### Função ler opcao

Assinatura:

```python
def ler_opcao(mensagem, opcoes_validas):
```

Converte todas as opções válidas para strings e verifica se a entrada pertence
ao conjunto. Por isso, funciona com `range`, listas de inteiros ou chaves
textuais do catálogo. A função devolve uma string, e os chamadores comparam com
`"1"`, `"2"` e assim por diante.

O uso de `set` torna o teste de pertencimento direto e elimina opções repetidas.

### Função confirmar

Assinatura:

```python
def confirmar(mensagem="Confirmar? [S/N]: "):
```

Normaliza a resposta com `strip().upper()`. Retorna `True` para S e `False` para
N. Qualquer outro valor repete a pergunta. O parâmetro padrão fornece uma
mensagem genérica, mas cada operação pode enviar um texto específico.

### Função escolher tipo ativo

Assinatura:

```python
def escolher_tipo_ativo():
```

Percorre `TipoAtivo`, imprime `value` e `rotulo`, cria a lista de códigos válidos
e lê a opção. `TipoAtivo(codigo)` converte o inteiro no membro correspondente.
O retorno não é uma string, mas um objeto Enum.

### Função escolher severidade

Assinatura:

```python
def escolher_severidade():
```

Transforma o Enum em lista para associar posições de um a quatro. Mostra o
rótulo e sua explicação, valida o índice e devolve `membros[indice - 1]`. A
subtração existe porque listas começam em zero, enquanto o menu começa em um.

### Função escolher status vulnerabilidade

Assinatura:

```python
def escolher_status_vulnerabilidade():
```

Segue o mesmo padrão da severidade, mas usa `DESCRICOES_STATUS`. A repetição do
formato é intencional porque mantém cada função pequena e fácil de explicar.
Uma função genérica para todos os Enums reduziria linhas, mas exigiria parâmetros
e abstrações adicionais.

### Função sem acentos

Assinatura:

```python
def _sem_acentos(texto):
```

`casefold` normaliza maiúsculas. `unicodedata.normalize("NFD", ...)` separa
letras e sinais diacríticos. A compreensão remove caracteres cuja categoria é
`Mn`, como o acento separado. Assim, `Armário` e `armario` podem ser comparados.

A função não altera o texto armazenado ou exibido. Ela cria apenas uma forma de
comparação.

### Função escolher localizacao

Assinatura:

```python
def escolher_localizacao(tipo):
```

Consulta `LOCAIS_RECOMENDADOS[tipo]`, mostra recomendações e lista opções. A
opção Outro solicita texto livre. Depois, compara a escolha com as recomendações
normalizadas.

Se a localização for recomendada, retorna imediatamente. Caso contrário,
exibe um aviso e pergunta se o usuário deseja manter a exceção. Responder sim
retorna o local; responder não reinicia o laço.

Essa é uma regra orientativa, não uma validação absoluta. Um switch pode estar
temporariamente em laboratório, e bloquear o cadastro transformaria uma boa
prática geral em uma regra falsa.

### Função exibir item catalogo

Assinatura:

```python
def exibir_item_catalogo(item):
```

Recebe um dos dicionários internos do catálogo e imprime cada campo com um
rótulo. Separar essa apresentação permite usá-la tanto no menu de estudo quanto
durante o cadastro.

### Função menu catalogo

Assinatura:

```python
def menu_catalogo():
```

Mantém um laço próprio, lista as categorias e permite abrir cada explicação sem
modificar a base. A opção zero retorna ao menu principal. O `input` final pausa
a tela para que o usuário leia antes de voltar ao índice.

### Função mostrar mapa

Assinatura:

```python
def mostrar_mapa(ativos):
```

Primeiro imprime uma topologia conceitual. Depois verifica se há ativos reais.
Para agrupá-los, cria `por_localizacao = {}` e usa
`setdefault(local, []).append(ativo)`. Se a chave ainda não existe, `setdefault`
cria uma lista; em seguida, o ativo é adicionado.

O laço final ordena as localizações e os ativos por ID. O mapa não tenta
descobrir conexões físicas reais. Ele representa a organização lógica com base
no campo cadastrado, o que é compatível com o nível da atividade.

### Função calcular painel

Assinatura:

```python
def calcular_painel(ativos):
```

Cria contadores de tipos e severidades por compreensões de dicionário. Percorre
cada ativo, incrementa seu tipo, verifica ausência de vulnerabilidades e
percorre os riscos. Vulnerabilidades corrigidas não entram nos contadores de
pendências.

O retorno é um dicionário de resumo. A função não imprime e não lê entradas.
Por isso, pode ser testada automaticamente e reutilizada por outra interface.
Essa separação entre cálculo e exibição é uma das decisões mais importantes da
versão final.

### Função mostrar painel

Assinatura:

```python
def mostrar_painel(ativos):
```

Chama `calcular_painel` e formata os resultados. Tipos com quantidade zero não
são impressos, enquanto todas as severidades aparecem para deixar a escala
completa. Se houver risco crítico não corrigido, mostra um alerta.

A função não mantém contadores próprios permanentes. O painel sempre deriva os
números da base atual, evitando divergência entre um contador salvo e os
registros reais.

## Testes automatizados

### Função criar base exemplo

Monta dois ativos previsíveis. Um possui uma vulnerabilidade alta em tratamento
e o outro não possui riscos. Essa função evita repetir a mesma estrutura em
cada teste.

### Teste busca direta por id

Confirma que o ID 101 devolve o switch e que um ID inexistente devolve `None`.
Ele valida o comportamento de `dict.get` usado pela aplicação.

### Teste busca parcial por nome

Pesquisa `fin` em minúsculas e espera encontrar `NOTE-FIN-01`. Isso verifica a
busca parcial e a normalização de caixa.

### Teste id da vulnerabilidade

Com `VUL-001` já presente, espera `VUL-002`. O teste protege a regra de geração
sequencial.

### Teste painel

Confirma dois ativos, uma vulnerabilidade, um ativo sem riscos e uma pendência
alta. Ele verifica a lógica sem depender do texto impresso.

### Teste persistencia

Usa `TemporaryDirectory`, grava o JSON fora da base real e o carrega novamente.
Depois verifica chaves inteiras e membros Enum. Esse teste comprova a ida e a
volta da serialização sem deixar arquivos de teste no projeto.

## Comparação com a solução anterior

### O que a solução anterior fazia bem

A solução anterior já possuía uma separação válida entre menu, ativo,
vulnerabilidades, enumerações, validadores, persistência e exceções. Ela usava
o ID como chave do dicionário, persistia em JSON, consultava por ID ou nome e
mantinha as vulnerabilidades dentro do ativo. Tecnicamente, já atendia grande
parte do enunciado.

Também havia escolhas maduras: `EnumSelecionavel` evitava repetir menus,
exceções personalizadas distinguiam dados inválidos de erro de arquivo e a
serialização reconstruía objetos Enum.

### Por que a arquitetura foi alterada

A versão anterior tinha sete módulos e uma classe base abstrata para tornar
Enums selecionáveis. Isso é elegante, mas aumenta a quantidade de conceitos que
precisam ser defendidos em uma apresentação curta. A versão final usa cinco
módulos e funções explícitas para cada tipo de escolha.

O objetivo não foi tornar a solução anterior errada. A mudança priorizou a
proximidade com a ementa, a leitura por iniciantes e a explicação oral.

### Diferenças nos dados do ativo

Antes, o cadastro exigia IP e sistema operacional e reunia setor e localização
em um campo. A versão final separa setor, que indica responsabilidade
organizacional, de localização, que indica posição física ou lógica. IP e
sistema operacional foram removidos porque não são requisitos mínimos e
desviavam atenção para validação de rede.

Essa remoção é uma escolha de escopo. IP e sistema operacional poderiam ser
reintroduzidos como campos opcionais sem alterar o núcleo do CRUD.

### Diferenças nas vulnerabilidades

Antes, o usuário digitava um identificador semelhante a CVE. O enunciado não
exige vulnerabilidades reais. A versão final gera IDs internos para evitar
duplicidade e não exigir conhecimento prévio.

A categoria antes era texto livre. Agora existe um catálogo explicativo, com
opção personalizada. Severidade e status continuam controlados por Enum, mas os
menus explicam o significado de cada escolha.

### Diferenças na localização

Antes, localização era apenas texto obrigatório. Agora há locais padronizados,
recomendações por tipo, confirmação de exceções e agrupamento no mapa. O dado
passou a alimentar uma funcionalidade posterior, em vez de ser apenas
armazenado.

### Diferenças na persistencia

Na solução anterior, `ativo.py` mantinha uma variável global e oferecia funções
próprias para carregar e salvar. Na versão final, a base é carregada por
`main.py` e passada como argumento. Isso reduz estado global e facilita testes.

A versão final também grava em arquivo temporário antes de substituir o JSON.
As exceções foram concentradas em `ErroDeDados`, pois o projeto não precisava de
uma hierarquia maior para cumprir seu objetivo.

### Diferenças na demonstracao do dicionario

A solução anterior possuía uma opção artificial para imprimir chaves, valores e
pares de um dicionário de exemplo. A versão final demonstra dicionários em
funcionalidades reais: busca por ID, catálogo, agrupamento do mapa, contagem do
painel e armazenamento de vulnerabilidades. Isso dá uma justificativa funcional
ao requisito.

### Diferenças na experiencia do usuario

A versão anterior era um CRUD direto. A versão final mantém o CRUD, mas oferece
ficha do ativo, catálogo, orientação de infraestrutura, mapa e painel. Esses
recursos aumentam o capricho sem exigir bibliotecas externas ou conceitos fora
do curso.

## Caminhos alternativos compatíveis com a ementa

### Solucao em um unico arquivo

Todo o programa poderia ficar em `main.py`, com um dicionário global e funções
em sequência. Seria o caminho mais fácil para um primeiro contato com Python.
Ele atenderia os requisitos se preservasse Enum, arquivo, validações e CRUD.

A desvantagem seria a mistura de menus, regras e persistência. Com o crescimento
do código, revisar uma parte exigiria navegar por um arquivo muito longo.

### Solucao com listas em vez de dicionario principal

Uma lista de ativos seria simples para cadastrar e percorrer. Entretanto, a
busca por ID precisaria examinar os elementos até encontrar o alvo. Além disso,
o requisito pede uso relevante de dicionário. A lista poderia continuar útil
como resultado de uma pesquisa, mas não seria a melhor estrutura principal.

### Dois arquivos JSON

Ativos e vulnerabilidades poderiam ser armazenados em arquivos separados. Cada
vulnerabilidade teria `id_ativo` para representar o vínculo. Essa organização
aproxima o projeto de tabelas relacionais e facilita consultas globais de
vulnerabilidades.

Em compensação, remover um ativo exigiria filtrar o segundo arquivo, e seria
possível criar uma vulnerabilidade órfã por erro. Para o escopo atual, aninhar
os riscos simplifica a integridade.

### Arquivos CSV

CSV é texto e poderia atender à persistência. O problema é representar a lista
de vulnerabilidades dentro de cada ativo. Seriam necessários dois CSVs ou uma
codificação manual. JSON expressa estruturas aninhadas de modo mais natural.

### Programacao orientada a objetos

Poderiam existir classes `Ativo`, `Vulnerabilidade` e `Repositorio`. Métodos
como `ativo.adicionar_vulnerabilidade` encapsulariam regras. Essa solução é
adequada quando orientação a objetos faz parte do conteúdo estudado.

Para esta avaliação, classes de domínio aumentariam a carga conceitual sem
resolver um requisito adicional. O uso de dicionários torna o requisito nove
imediatamente visível.

### Banco de dados SQLite

SQLite forneceria tabelas, chaves primárias, consultas e integridade
referencial. Seria tecnicamente forte para uma aplicação maior. Contudo, o
enunciado pede arquivos de texto como base e avalia fundamentos. SQL poderia
desviar a apresentação para conteúdo não central das sprints.

### Interface grafica

Tkinter poderia criar formulários e botões. Uma interface gráfica melhoraria a
navegação, mas adicionaria estados de tela, callbacks e validação de widgets. O
menu textual é suficiente para o requisito e deixa o algoritmo visível ao
avaliador.

### Indice secundario por hostname

Um segundo dicionário como `id_por_hostname` permitiria busca exata rápida. Ele
seria útil com muitos ativos. Toda alteração de nome, porém, precisaria remover
a chave antiga e criar a nova. Como a pesquisa atual aceita fragmentos, ainda
seria necessário percorrer nomes para esse caso.

### Geracao de ids com contador persistido

O sistema poderia manter `proximo_id_vulnerabilidade` no JSON. A geração seria
O(1) e nunca reutilizaria um número removido. O custo seria ampliar o formato da
base e garantir a atualização do contador em toda inserção. UUID seria outra
opção, mas produziria identificadores menos amigáveis para a apresentação.

### Validacao com expressoes regulares

Hostnames, IPs e códigos poderiam ser verificados por regex. A solução anterior
fazia isso com IPv4. É um caminho válido se esses campos forem necessários. Na
versão final, evitou-se uma restrição rígida porque o enunciado permite ativos
como aplicações e bancos, que não possuem necessariamente um único IP.

### Salvamento apenas no encerramento

Manter tudo em memória e gravar ao sair reduziria operações de disco. O risco é
perder a sessão em uma interrupção. Salvar após cada alteração oferece uma
garantia prática melhor para um programa interativo pequeno.

### Camada de servicos

Uma arquitetura maior poderia incluir `servicos.py` entre menus e dados. Essa
camada coordenaria regras e persistência. No projeto atual, seria uma abstração
com pouco benefício, pois as funções de domínio já são pequenas.

## Relação entre a ementa e a implementação

| Conteúdo | Aplicação no Sentinela |
| --- | --- |
| Variáveis e tipos | IDs inteiros, textos, booleanos e objetos Enum |
| Entrada e saída | `input`, `print` e f-strings em todos os menus |
| Conversão | `int` em `ler_inteiro` e conversão de código para Enum |
| Condicionais | Validação, decisões de menu, alertas e estados vazios |
| Laços | Menus, repetição de entradas e travessia dos registros |
| Funções | Separação de cada responsabilidade em operações reutilizáveis |
| Listas e tuplas | Localizações, resultados de busca e locais recomendados |
| Dicionários | Base indexada, registros, catálogo, agrupamento e painel |
| Enumeração | Tipo, severidade e status com valores controlados |
| Arquivos | Persistência em JSON textual |
| Exceções | Conversão de inteiro, leitura, JSON inválido e gravação |
| Módulos | Divisão entre menu, domínio, utilidades e persistência |
| Git | Branches e merges reais no repositório do estudante |

## Perguntas técnicas prováveis

### Por que o dicionario e melhor para o ID

Porque o ID é único e funciona naturalmente como chave. A busca direta tem
complexidade média O(1), enquanto uma lista exigiria busca O(n).

### Por que a busca por nome nao e O 1

Porque ela aceita fragmentos. O programa precisa comparar o termo com cada
hostname. Um dicionário por nome ajudaria apenas na igualdade exata.

### O que significa um objeto mutavel

Um dicionário pode ser alterado depois de criado. Quando `selecionar` devolve o
dicionário de um ativo, `atualizar` modifica o mesmo objeto que está dentro da
base.

### Por que Enum e melhor que texto livre

Enum limita os valores possíveis, evita grafias inconsistentes e associa
códigos definidos aos tipos. Isso simplifica comparação, painel e persistência.

### Por que serializar

Objetos Enum existem em Python, mas JSON não os reconhece. Serializar converte
esses objetos para strings. Desserializar reconstrói os tipos ao carregar.

### Por que usar get

`get` devolve `None` ou um valor padrão quando a chave não existe. O acesso com
colchetes geraria `KeyError`, que precisaria ser capturado.

### Por que setdefault no mapa

Ele cria uma lista somente na primeira ocorrência de uma localização e devolve
a lista existente nas ocorrências seguintes. Assim, todos os ativos do mesmo
local ficam agrupados.

### Por que calcular e mostrar painel sao funcoes separadas

O cálculo pode ser testado e reutilizado sem capturar texto do terminal. A
função de exibição cuida apenas da formatação.

### O que acontece se o JSON estiver corrompido

`json.load` gera `JSONDecodeError`. `dados.carregar` converte a falha para
`ErroDeDados`, e `executar` encerra antes de sobrescrever a base.

### A recomendacao de localizacao garante seguranca

Não. Ela representa uma orientação didática. Segurança real depende de
controles físicos, rede, acesso, redundância e políticas que estão fora do
escopo desta atividade.

### Qual limitacao voce reconhece

O programa é monousuário, grava o arquivo inteiro a cada alteração e não possui
autenticação. Essas limitações são aceitáveis para uma aplicação textual de
aprendizagem, mas seriam revistas em um sistema corporativo.

## Conclusão para a defesa

O Sentinela atende ao CRUD e aos campos exigidos, usa Enum com códigos inteiros,
indexa ativos por ID em um dicionário, persiste a base em arquivo textual e
trata entradas incorretas. Os elementos adicionais não substituem os requisitos.
O catálogo explica o risco, a recomendação relaciona tipo e localização, o mapa
reorganiza os ativos cadastrados e o painel deriva indicadores da mesma base.

A principal justificativa da arquitetura é a separação de responsabilidades
sem esconder os fundamentos avaliados. Cada módulo tem um papel identificável,
as funções recebem dados explicitamente e as decisões técnicas podem ser
explicadas com conceitos presentes na ementa.

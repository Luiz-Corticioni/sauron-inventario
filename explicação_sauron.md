# Explicação do código — Sauron

## 1. Visão da solução

O Sauron é uma aplicação modular de terminal. `main.py` coordena o fluxo, os
módulos de domínio executam regras e `dados.py` converte os objetos em seis
tabelas TXT. Durante a execução, os registros são dicionários indexados por ID;
no disco, são linhas tabuladas relacionadas por chaves.

O desenho separa quatro responsabilidades:

1. interface e validação de entrada;
2. regras de negócio de ativos, salas e vulnerabilidades;
3. persistência e integridade;
4. cálculo matemático seguro.

Essa divisão evita uma função principal enorme e permite testar regras sem
simular toda a digitação do usuário.

## 2. Histórico de evolução do sauron

| Antes | Problema | Solução atual |
|---|---|---|
| ID inteiro digitado livremente | qualquer número era aceito | ID calculado por tipo, fabricante e série |
| hostname digitado livremente | nomes inconsistentes e duplicados | hostname calculado a partir do tipo, usuário e série |
| sala com ID inteiro | o código não explicava a entidade | `SAL-NNN`, exibido em tabela no menu |
| vulnerabilidade `VUL-NNN` | o ID não informava o tipo | `VUL-TT-NNN`, com categoria incorporada |
| cadastro de sala sem controle | qualquer pessoa alterava a topologia | PIN administrativo, hash e auditoria |
| aviso de local apenas informativo | exceção sem rastreabilidade | aviso + autorização + registro persistente |
| mapa somente hierárquico | perdeu-se a visão da rede | topologia tradicional + expansão dinâmica |
| Euler com sintaxe resumida | usuário não sabia escrever funções | guia no menu e explicação dos métodos |

## 3. Modelo de dados

`base` contém cinco índices principais; vulnerabilidades ficam aninhadas nos
ativos enquanto o programa está aberto:

```text
base
|-- setores: {int: setor}
|-- salas: {"SAL-NNN": sala}
|-- ativos: {"TFFFNNN": ativo com vulnerabilidades}
|-- seguranca: {"ADMIN": credencial com hash}
`-- auditoria: {"AUD-NNNNNN": evento}
```

Ao salvar, vulnerabilidades são desaninhadas para sua própria tabela. Isso dá
uma navegação simples em memória e um modelo relacional legível no disco. 
em outras palavras significa algo mais simplório e begginer friendly
para stakeholders mais leigos na área, não necessitando de uma 
alta capacidade intelectiva para realizar operações dentro do espaço.

## 4. Explicação de todas as funções

### `main.py`

| Função | Entrada/saída e responsabilidade |
|---|---|
| `salvar_se_alterado(base, alterado)` | recebe o resultado booleano de um CRUD e só chama `dados.salvar` quando houver mudança |
| `menu_ativos(base)` | laço do CRUD de ativos; despacha cadastrar, consultar, atualizar, remover e listar |
| `menu_vulnerabilidades(base)` | escolhe primeiro um ativo alfanumérico e depois executa o CRUD da vulnerabilidade vinculada |
| `executar()` | carrega as tabelas uma vez, mostra o menu principal, trata falhas de dados e encerra sem perder registros |

### `identificacao.py`

| Função | Explicação completa |
|---|---|
| `_sem_acentos(texto)` | aplica normalização Unicode NFKD e remove marcas combinantes; torna códigos portáveis |
| `normalizar_codigo(texto, limite)` | mantém apenas A–Z, converte para maiúsculas e limita o tamanho |
| `sugerir_codigo_fabricante(fabricante)` | usa a primeira letra normalizada; “Huawei” resulta em `H` |
| `validar_codigo_fabricante(codigo)` | regex que exige de uma a três letras |
| `validar_numero_serie(numero_serie)` | regex que exige de três a doze algarismos |
| `gerar_id_ativo(tipo, codigo, serie)` | valida os componentes e concatena `tipo.value + código + série` |
| `validar_id_ativo(id)` | verifica a regex e confirma se o primeiro dígito pertence ao Enum de tipos |
| `normalizar_usuario(usuario)` | remove acentos e sinais, junta os segmentos e limita a 18 caracteres |
| `gerar_hostname(tipo, usuario, serie)` | consulta o prefixo do tipo e monta `PREFIXO-USUARIO-SERIE` |
| `validar_hostname(hostname)` | garante três segmentos alfanuméricos separados por hífen |

O ID e o hostname não são o mesmo dado. O primeiro representa patrimônio e o
segundo, identificação operacional na rede.

### `ativos.py`

| Função | Explicação completa |
|---|---|
| `buscar_por_id(ativos, id)` | acesso direto O(1) ao dicionário após normalizar para maiúsculas |
| `buscar_por_nome(ativos, termo)` | busca sequencial em hostname, usuário, responsável e fabricante usando `casefold` |
| `_ler_codigo_fabricante(fabricante)` | mostra a sugestão e repete até receber um código válido |
| `_ler_numero_serie()` | impede letras, campos curtos e séries longas demais |
| `_ler_identidade(...)` | reúne tipo, fabricante, série e usuário; calcula ID/hostname e verifica duplicidades |
| `_escolher_posicao(base, tipo)` | escolhe setor e chama a seleção de sala já levando o tipo para validação |
| `cadastrar(base)` | monta o ativo, posiciona-o, insere no índice e oferece vulnerabilidade inicial |
| `imprimir_ficha(base, ativo)` | resolve relações e mostra todos os componentes da identidade e o resumo de riscos |
| `consultar(base)` | permite consulta exata pelo ID ou textual por quatro campos |
| `listar(base)` | tabela compacta usada também antes de selecionar um ativo |
| `selecionar(base, finalidade)` | lê o ID alfanumérico e devolve exatamente um registro ou `None` |
| `_atualizar_identidade(base, ativo)` | recalcula a identidade e troca a chave do dicionário quando o ID muda |
| `atualizar(base)` | altera um grupo coerente de campos; localização continua validada |
| `remover(base)` | confirma e remove o ativo; vulnerabilidades aninhadas saem em cascata |

### `estrutura.py`

| Função | Explicação completa |
|---|---|
| `proximo_id_setor(registros)` | calcula o próximo inteiro dos setores |
| `proximo_id_sala(registros)` | extrai números dos IDs `SAL-` e gera o próximo com três casas |
| `caminho_setor(base, id)` | sobe por `setor_pai_id` e produz `TI > Redes > Infraestrutura` |
| `nome_sala(base, id)` | resolve ID para nome sem causar exceção quando ausente |
| `_filhos(base, id)` | filtra e ordena filhos diretos de um setor |
| `_descendentes(base, id)` | percorre a árvore com uma pilha para impedir ciclos em atualizações |
| `rotulo_categoria(categoria)` | converte código interno da sala em texto explicativo |
| `listar_tabela_salas(base, setor_id)` | mostra formato, ID, categoria, nome e caminho do setor |
| `listar(base)` | usa recursão para imprimir setores, subsetores e salas em níveis |
| `selecionar_setor(...)` | repete a leitura até receber setor existente; zero pode significar raiz |
| `sala_adequada(tipo, sala)` | testa se a categoria pertence ao conjunto recomendado daquele tipo |
| `_autorizar_local_inadequado(...)` | explica o conflito, solicita PIN e cria evento de auditoria |
| `selecionar_sala(...)` | aceita `SAL-NNN`, permite `NOVA` e valida a compatibilidade do local |
| `cadastrar_setor(base)` | cria raiz ou subsetor e bloqueia nomes duplicados no mesmo nível |
| `_escolher_categoria_sala()` | converte o menu de categorias no código persistido |
| `cadastrar_sala(...)` | exige PIN, gera `SAL-NNN`, insere a sala e registra auditoria |
| `atualizar_setor(base)` | altera nome, descrição ou pai sem permitir autorreferência/ciclo |
| `_selecionar_sala_global(base)` | reutiliza a tabela e localiza uma sala em qualquer setor |
| `atualizar_sala(base)` | altera nome, descrição, setor ou categoria e mantém ativos no mesmo setor da sala |
| `remover_setor(base)` | bloqueia remoção enquanto existirem filhos ou salas |
| `remover_sala(base)` | bloqueia remoção enquanto houver ativos na sala |
| `menu(base, salvar_se_alterado)` | laço que organiza o CRUD da estrutura e solicita persistência |

### `autenticacao.py`

| Função | Explicação completa |
|---|---|
| `validar_formato_pin(pin)` | exige 6 a 12 algarismos |
| `criar_credencial(pin, salt, iteracoes)` | gera salt aleatório quando necessário e calcula PBKDF2-HMAC-SHA256 |
| `verificar_pin(pin, credencial)` | recalcula o hash e usa `compare_digest` para comparação constante |
| `_configurar_pin(base)` | pede e confirma o primeiro PIN; salva somente a credencial derivada |
| `autorizar_admin(base, motivo)` | mostra o motivo, configura se necessário e limita a três tentativas |

PBKDF2 torna cada tentativa computacionalmente mais cara e o salt impede que
PINs iguais produzam hashes iguais. Para produção, seria necessário também
controle de usuários, expiração, recuperação e armazenamento externo de segredo.

### `auditoria.py`

| Função | Explicação completa |
|---|---|
| `proximo_id(registros)` | encontra o maior sufixo e gera `AUD-NNNNNN` |
| `registrar(...)` | inclui horário UTC, ator, ação, entidade e detalhes |
| `listar(base)` | exibe eventos do mais recente para o mais antigo |

### `vulnerabilidades.py`

| Função | Explicação completa |
|---|---|
| `gerar_id(ativos, codigo)` | varre todos os ativos, encontra a maior sequência da categoria e gera `VUL-TT-NNN` |
| `_escolher_categoria(...)` | mostra códigos, abre explicação educativa e devolve código/nome/tratamento |
| `cadastrar(ativos, ativo)` | recebe descrição, Enum de severidade/status, gera ID e aninha no ativo |
| `listar(ativo)` | exibe todos os campos e tratamento sugerido |
| `_selecionar(ativo, acao)` | restringe a busca às vulnerabilidades do ativo escolhido |
| `atualizar(ativos, ativo)` | altera campo; ao mudar categoria, troca o ID para manter a semântica |
| `remover(ativo)` | mostra o registro, confirma e o exclui |

### `dados.py`

| Função | Explicação completa |
|---|---|
| `criar_base_vazia(com_estrutura_padrao)` | cria todos os índices e as salas iniciais categorizadas |
| `_ler_tabela(pasta, nome)` | lê UTF-8 com `csv.DictReader` e exige o cabeçalho exato |
| `_inteiro(...)` | converte célula com mensagem que identifica campo e tabela |
| `_validar_integridade(base)` | verifica formatos, chaves, ciclos, setor/sala e unicidade das vulnerabilidades |
| `_desserializar(tabelas)` | reconstrói Enums, inteiros, índices e vulnerabilidades aninhadas |
| `_obter_ou_criar_setor(...)` | apoio à migração: reutiliza nome ou cria setor legado |
| `_proximo_id_sala(salas)` | versão interna do gerador usada pela migração |
| `_obter_ou_criar_sala(...)` | apoio à migração: cria sala `OUTRO` quando necessário |
| `_migrar_json_legado(caminho)` | transforma a estrutura JSON anterior em IDs/hostnames válidos |
| `carregar(pasta)` | exige o conjunto completo das tabelas e inicializa no primeiro uso |
| `_linhas_para_salvar(base)` | achata objetos e converte Enums para nomes persistíveis |
| `salvar(base, pasta)` | valida, escreve temporários e só depois substitui os arquivos oficiais |

### `modo_euler.py`

| Função | Explicação completa |
|---|---|
| `normalizar_expressao(expr)` | troca `^` por `**` e vírgula decimal por ponto |
| `_validar_no(no)` | percorre a AST e permite somente números, `x`, operadores e funções autorizadas |
| `compilar_funcao(expr)` | valida, compila com ambiente sem built-ins e devolve função, AST e texto normalizado |
| `_somar_polinomios(a, b, fator)` | combina coeficientes de graus iguais; fator -1 implementa subtração |
| `_multiplicar_polinomios(a, b)` | distribui termos somando graus e limita o grau a 50 |
| `extrair_polinomio(no)` | tenta representar a AST como `{grau: coeficiente}`; devolve `None` se não for polinômio |
| `_contem_x(no)` | informa se uma subárvore depende de `x` |
| `identificar_tipo(no)` | usa polinômio e chamadas AST para classificar a família matemática |
| `derivar_polinomio(coeficientes)` | aplica `a*x^n -> n*a*x^(n-1)` |
| `integrar_polinomio(coeficientes)` | aplica `a*x^n -> a*x^(n+1)/(n+1)` |
| `formatar_polinomio(...)` | converte o dicionário de coeficientes em expressão legível |
| `derivada_numerica(funcao, x, passo)` | usa diferença central `[f(x+h)-f(x-h)]/(2h)` |
| `integrar_simpson(...)` | soma extremos e pesos alternados 4/2; força subdivisão par |
| `_bissecao(...)` | reduz repetidamente um intervalo com mudança de sinal |
| `encontrar_raizes(...)` | amostra o domínio, detecta mudanças de sinal e chama bisseção |
| `_ler_intervalo()` | lê limites reais e corrige a ordem |
| `_mostrar_tabela(funcao)` | amostra até 30 pontos e trata valores fora do domínio |
| `mostrar_guia_euler()` | ensina notação, exemplos, domínio e métodos usados |
| `menu_modo_euler()` | coordena expressão, análise e operações até o usuário sair |

Limitações matemáticas importantes: a busca por raízes pode não detectar raízes
que apenas tocam o eixo; Simpson e diferença central são aproximações; derivada
simbólica e primitiva simbólica estão limitadas a polinômios reconhecidos.

### `utilitarios.py`

| Função | Explicação completa |
|---|---|
| `cabecalho` e `exibir_banner` | padronizam a interface sem biblioteca externa |
| `ler_texto_obrigatorio` | rejeita vazio |
| `ler_inteiro` e `ler_real` | convertem e repetem em erro; real rejeita infinito/NaN |
| `ler_opcao` | aceita apenas valores de um conjunto |
| `confirmar` | transforma S/N em booleano |
| `escolher_tipo_ativo` | converte menu numérico em `TipoAtivo` |
| `escolher_severidade` | explica e devolve `Severidade` |
| `escolher_status_vulnerabilidade` | explica e devolve `StatusVulnerabilidade` |
| `exibir_item_catalogo` | apresenta conceito, exemplo, risco e tratamento |
| `menu_catalogo` | navegação educativa sem modificar dados |
| `mostrar_mapa` | imprime a topologia fixa e injeta a expansão dinâmica cadastrada |
| `calcular_painel` | agrega quantidades e pode ser testado sem entrada |
| `mostrar_painel` | transforma o resumo em saída legível e destaca riscos críticos |

## 5. Outros caminhos possíveis

| Alternativa | Vantagem | Por que não foi a escolha principal agora |
|---|---|---|
| SQLite | transações, consultas e integridade nativas | esconderia parte do exercício didático com arquivos TXT |
| JSON único | simples de serializar | menos próximo da ideia “um arquivo por tabela” |
| UUID para ativo | praticamente elimina colisões | não carrega significado didático de tipo/fabricante |
| hostname digitado | flexível para padrões empresariais existentes | não atende ao requisito de completar automaticamente |
| login completo | múltiplos papéis e atribuição individual | ampliaria muito o escopo; PIN local é suficiente para o protótipo |
| SymPy | derivação e integração simbólicas amplas | adiciona dependência e reduz a implementação própria dos algoritmos |
| parser escrito do zero | controle absoluto da gramática | a AST do Python é menor, segura após validação e adequada à ementa |

## 6. Relação com a ementa

- variáveis e conversão: IDs, séries, limites e células TXT;
- condicionais: autorização, compatibilidade e escolhas dos menus;
- laços: CRUD, travessia de árvore, Simpson, bisseção e testes de entrada;
- funções: responsabilidades pequenas, parâmetros e retornos reutilizáveis;
- listas, tuplas e dicionários: catálogos, tabelas e índices em memória;
- Enum: tipos de ativo, severidade e status;
- arquivos: seis tabelas UTF-8;
- exceções: entrada, domínio matemático e corrupção de dados;
- módulos: interface, domínio, segurança, persistência e matemática.

## 7. Limites e melhorias futuras

O protótipo é monousuário e local. Múltiplos processos podem disputar arquivos;
a substituição das seis tabelas não é uma transação indivisível; o PIN não
identifica uma pessoa específica; e o catálogo não consulta CVE. Uma evolução
natural seria migrar para SQLite/PostgreSQL, criar usuários e papéis, armazenar
segredos fora da base, adicionar backup/versionamento e integrar fontes de
vulnerabilidade. Essas limitações são conhecidas e não anulam o objetivo
didático da versão atual.

# Sentinela - Inventário de Segurança de TI

Aplicação textual em Python para cadastrar, consultar, atualizar e remover
ativos de TI e suas vulnerabilidades. A solução foi construída para a atividade
avaliativa das Sprints 1 e 2 de Cibersegurança da UFU.

## Como executar

Requisito: Python 3.10 ou mais recente. O projeto não usa pacotes externos.

```bash
python main.py
```

Execute o comando dentro da pasta `sentinela_inventario`.

## Estrutura

```text
sentinela_inventario/
|-- main.py                 # menus e coordenação do programa
|-- ativos.py               # CRUD dos ativos
|-- vulnerabilidades.py     # cadastro e manutenção das vulnerabilidades
|-- dados.py                # leitura e gravação do JSON
|-- utilitarios.py          # Enum, validações, catálogo, mapa e painel
|-- dados/
|   `-- inventario.json     # base de dados textual
|-- tests/
|   `-- test_sistema.py     # testes automatizados
|-- GUIA_DE_APRESENTACAO.md # roteiro curto para apresentação
`-- DEFESA_TECNICA_COMPLETA.md # explicação integral e alternativas
```

## Diferenciais implementados

- catálogo que explica cada vulnerabilidade, seu risco e tratamento;
- IDs automáticos no formato `VUL-001`;
- mapa lógico da empresa com ativos agrupados por localização;
- sugestão de local conforme o tipo, sem impedir exceções reais;
- ficha organizada do ativo e painel de segurança;
- campos separados para setor e localização;
- persistência JSON e tratamento de entradas incorretas;
- funções pequenas e comentários voltados à intenção do código.

## Relação com os dez requisitos

| Nº | Atendimento |
|---:|---|
| 1 | Menus textuais claros e validadores de texto, inteiro, opções e confirmações. |
| 2 | `TipoAtivo` é um `Enum` com nove categorias e códigos inteiros. |
| 3 | Cadastro exige ID, nome, responsável, setor, localização e tipo; aceita vulnerabilidades iniciais e grava em JSON. |
| 4 | Consulta por ID ou por parte do nome/hostname. |
| 5 | Atualização individual de nome, responsável, setor, localização, tipo ou descrição. |
| 6 | Remoção do ativo elimina suas vulnerabilidades aninhadas. |
| 7 | Vulnerabilidade registra descrição, categoria, severidade e status. |
| 8 | Listagem mostra os campos e informa quando não há registros. |
| 9 | O dicionário `ativos` é indexado pelo ID inteiro. |
| 10 | Deve ser demonstrado pelo histórico real do repositório do estudante. |

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes verificam busca, geração de IDs, painel e ida/volta da persistência.

## Material para apresentação e defesa

- `GUIA_DE_APRESENTACAO.md`: roteiro resumido para uma apresentação rápida;
- `DEFESA_TECNICA_COMPLETA.md`: explicação de cada função, comparação com a
  solução anterior, decisões de arquitetura, caminhos alternativos compatíveis
  com a ementa e respostas para perguntas técnicas prováveis.

## Observação sobre Git

O arquivo `.zip` não pode fabricar o histórico exigido no requisito 10. Crie as
branches durante seu próprio desenvolvimento e faça merges reais. Um fluxo
possível é:

```bash
git switch -c feature/crud-ativos
# faça e confirme mudanças relacionadas aos ativos
git switch main
git merge feature/crud-ativos

git switch -c feature/vulnerabilidades
# faça e confirme mudanças relacionadas às vulnerabilidades
git switch main
git merge feature/vulnerabilidades

git switch -c feature/mapa-painel
# faça e confirme mudanças relacionadas ao mapa e painel
git switch main
git merge feature/mapa-painel
```

Não execute todos os comandos apenas para produzir aparência de histórico:
os commits e merges devem corresponder às etapas que você realmente revisar.

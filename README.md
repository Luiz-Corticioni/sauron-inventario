# Sauron — explicações breves sobre o projeto.
para melhores explicações, consulte explicação_sauron.md 

Aplicação de terminal em Python para inventário de ativos, gestão de
vulnerabilidades, estrutura física/organizacional, auditoria e análise
matemática. Usa somente a biblioteca padrão do Python.

## Execução

Requisito: Python 3.10 ou mais recente.

```powershell
cd "C:\Users\Luiz Fabiano\Desktop\cibersegurança ufu\sprint 1\prototipo mapa\Sentinela_Inventario_Final\sentinela_inventario"
python main.py
```

## Identificadores

| Registro | Formato | Exemplo | Formação |
|---|---|---|---|
| Ativo | `TFFFNNN...` | `4H21444` | tipo 4 (switch) + fabricante H (Huawei) + série 21444 |
| Hostname | `PREFIXO-USUARIO-SERIE` | `SW-LUIZFABIANO-21444` | calculado; não aceita valor livre |
| Sala | `SAL-NNN` | `SAL-007` | sequência da tabela de salas |
| Vulnerabilidade | `VUL-TT-NNN` | `VUL-02-001` | tipo 02 (software desatualizado) + sequência |
| Auditoria | `AUD-NNNNNN` | `AUD-000001` | sequência de eventos administrativos |

Tipos de ativo: 1 servidor, 2 notebook, 3 estação, 4 switch, 5 roteador,
6 impressora, 7 aplicação web, 8 banco de dados e 9 software licenciado.

O ID e o hostname são campos distintos. O usuário informa tipo, fabricante,
série e usuário associado; o sistema calcula ambos e rejeita duplicidade.

## Banco de dados TXT

Cada arquivo em `dados/` representa uma tabela tabulada em UTF-8:

| Tabela | Responsabilidade |
|---|---|
| `setores.txt` | setores e subsetores recursivos |
| `salas.txt` | salas `SAL-NNN`, categoria e setor responsável |
| `ativos.txt` | identificação, hostname, fabricante, usuário e localização |
| `vulnerabilidades.txt` | riscos `VUL-TT-NNN` vinculados ao ativo |
| `seguranca.txt` | salt e hash PBKDF2 do PIN, nunca o PIN em texto puro |
| `auditoria.txt` | data, ator, ação, entidade e detalhes das autorizações |

As tabelas são carregadas para dicionários durante a execução. Antes de salvar,
o sistema valida chaves estrangeiras, formatos, IDs duplicados e ciclos entre
setores. A gravação usa arquivos temporários para reduzir o risco de corrupção.

## Salas, localização e autorização

As categorias tabeladas são: servidores, telecomunicações, escritório,
datacenter/nuvem, laboratório e outro local controlado. Cada tipo de ativo tem
categorias recomendadas. Quando o usuário tenta colocar um ativo em um local
inadequado, o Sauron mostra o aviso e exige o PIN administrativo.

A criação de uma sala também exige PIN. No primeiro uso, o administrador cria
um PIN de 6 a 12 números. Só o hash PBKDF2 e um salt aleatório são salvos. A
criação e as exceções de localização entram em `auditoria.txt`.

## Gestão de vulnerabilidades

O menu lista os ativos antes de solicitar seu ID, aceita os novos IDs
alfanuméricos e permite cadastrar, consultar, atualizar e remover riscos. Os
códigos de tipo são:

| Código | Categoria |
|---:|---|
| 01 | Senha fraca |
| 02 | Software desatualizado |
| 03 | Serviço exposto |
| 04 | Configuração incorreta |
| 05 | Permissão excessiva |
| 06 | Ausência de criptografia |
| 99 | Categoria personalizada |

## Mapa da infraestrutura

O mapa conserva a visão anterior de rede — internet, firewall, nuvem/datacenter,
rede interna e sala de servidores. Logo abaixo, uma expansão dinâmica encaixa
setores, subsetores, salas e ativos cadastrados na árvore da rede interna.

## Modo Euler

O próprio menu apresenta o guia. Regras principais:

- use `x` como variável;
- escreva `2*x`, e não `2x`;
- potência aceita `x^2` ou `x**2`;
- funções: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `exp`, `log`, `ln`,
  `log10`, `sqrt` e `abs`;
- constantes: `pi` e `e`;
- exemplos: `x^2 + 2*x - 3`, `sin(pi*x)`, `exp(-x)` e `log(x)/x`.

O menu também explica, de forma resumida, como chegou aos resultados: árvore
sintática para classificação, regra da potência para polinômios, diferença
central para derivadas, Simpson para integrais e bisseção para raízes.

## Estrutura de módulos

| Arquivo | Papel |
|---|---|
| `main.py` | coordenação dos menus |
| `ativos.py` | CRUD e fluxo de identidade dos ativos |
| `identificacao.py` | geração e validação de ID/hostname |
| `vulnerabilidades.py` | CRUD e IDs por categoria |
| `estrutura.py` | setores, salas, compatibilidade de local e PIN |
| `autenticacao.py` | hash e verificação do PIN administrativo |
| `auditoria.py` | histórico de ações privilegiadas |
| `dados.py` | seis tabelas TXT e integridade referencial |
| `modo_euler.py` | análise segura de funções |
| `utilitarios.py` | Enums, leitura, mapa, catálogo e painel |

## Testes

```powershell
python -m unittest discover -s tests -v
```


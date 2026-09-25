# Roteiro sugerido para a apresentação de 5 minutos

## 0:00-0:40 - Ideia e estrutura

Explique que o Sentinela é um inventário de segurança. Mostre rapidamente os
cinco módulos e diga que o ID inteiro é a chave do dicionário principal.

Frase útil: "Quando conheço o ID, uso `ativos.get(id)`; para nome, percorro os
valores porque a busca aceita partes do hostname."

## 0:40-2:20 - Cadastro completo

1. Cadastre um `Switch`.
2. Escolha uma localização incoerente para exibir o aviso.
3. Volte e escolha `Sala de Servidores`.
4. Cadastre uma vulnerabilidade inicial pelo catálogo.
5. Mostre que o ID `VUL-001` foi gerado automaticamente.

Esse fluxo demonstra Enum, validação, cadastro, catálogo, recomendação e lista
inicial de vulnerabilidades de uma só vez.

## 2:20-3:10 - Consulta e atualização

Busque o ativo pelo nome, abra sua ficha e atualize responsável ou setor.
Explique que apenas o campo escolhido é alterado.

## 3:10-4:10 - Mapa e painel

Mostre o mapa lógico e o agrupamento do ativo cadastrado. Depois abra o painel
para exibir as contagens derivadas do mesmo dicionário.

## 4:10-4:40 - Persistência e exclusão

Explique que `dados.py` transforma Enums em texto para gravar o JSON. Mostre a
confirmação da exclusão e diga que as vulnerabilidades estão dentro do ativo,
portanto são removidas junto com ele.

## 4:40-5:00 - Git

Mostre no repositório as branches e os merges reais usados no desenvolvimento.

## Perguntas prováveis

**Por que usar dicionário?**

Porque o ID único funciona como chave e permite acesso direto ao registro.

**Por que JSON?**

Porque é um arquivo de texto estruturado, legível e compatível com dicionários.

**Por que Enum?**

Porque limita os tipos a opções válidas e associa cada tipo a um código inteiro.

**Por que a localização inadequada não é bloqueada?**

Porque a recomendação ajuda o usuário, mas uma organização real pode possuir
uma exceção legítima. O sistema avisa e pede confirmação.

**Qual a diferença entre setor e localização?**

Setor indica quem responde pelo ativo; localização indica onde ele está.


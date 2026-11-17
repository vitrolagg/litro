# Exploração dos dados brutos da ANP

Relatório gerado por `explorer.py` a partir dos arquivos em `raw/`, baixados pelo coletor da série histórica de preços de combustíveis da ANP.

O objetivo da exploração é entender a fonte antes de escrever o pipeline: o que existe, em que formato e com que qualidade. 

Para gerar o relatório novamente: `python explorer.py`.

## Inventário

Os arquivos ficam organizados em uma subpasta por categoria de produto. O período de cada arquivo foi extraído do nome, que segue um de dois padrões: semestral (`1º semestre de 2004.csv`) ou mensal (`Abril de 2023.csv`).

- Total de arquivos: 182
- Tamanho total: 5.59 GB

### Resumo por categoria

`primeiro` é o início do período mais antigo e `ultimo` é o fim do mais recente. As datas são o período que o nome do arquivo **declara** cobrir; a comparação com as datas reais de coleta fica para as validações de qualidade da Fase 2. Os tamanhos usam base binária (1 MB = 1024² bytes).

| categoria                        |   arquivos | tamanho   | primeiro   | ultimo     |
|:---------------------------------|-----------:|:----------|:-----------|:-----------|
| Combustíveis automotivos         |         45 | 4.11 GB   | 2004-01-01 | 2026-06-30 |
| Etanol Hidratado + Gasolina C    |         46 | 370.77 MB | 2023-01-01 | 2026-10-31 |
| GLP P13                          |         45 | 969.64 MB | 2004-01-01 | 2026-06-30 |
| Óleo Diesel (S-500 e S-10) + GNV |         46 | 170.62 MB | 2023-01-01 | 2026-10-31 |

### Tipo de período por categoria

Cada categoria usa um único tipo de período. Essa é a premissa da verificação de lacunas, que gera a sequência esperada a partir desse tipo.

| categoria                        |   Mensal |   Semestral |
|:---------------------------------|---------:|------------:|
| Combustíveis automotivos         |        0 |          45 |
| Etanol Hidratado + Gasolina C    |       46 |           0 |
| GLP P13                          |        0 |          45 |
| Óleo Diesel (S-500 e S-10) + GNV |       46 |           0 |

## Verificação de lacunas

Para cada categoria, foi gerada a sequência de períodos que deveria existir entre o primeiro e o último arquivo (mês a mês ou semestre a semestre), que depois foi comparada com os períodos encontrados.

Limitações: as pontas não são verificadas (se faltar o primeiro ou o último arquivo, a lacuna não aparece) e períodos repetidos não são detectados.

Nenhuma lacuna encontrada: todas as categorias têm a sequência completa entre o primeiro e o último período.

## Verificação dos nomes dos arquivos

Cada nome de arquivo foi comparado com o formato exato esperado: `1º semestre de 2004.csv` para os semestrais e `Abril de 2023.csv` para os mensais. O objetivo é encontrar nomes que parecem iguais, mas usam caracteres diferentes.

Arquivos fora do formato: 1

| categoria                | arquivo                 |
|:-------------------------|:------------------------|
| Combustíveis automotivos | 2° semestre de 2023.csv |

Arquivos que usam o símbolo de grau (°) no lugar do indicador ordinal (º): 1. Os dois são visualmente iguais, mas são caracteres diferentes. A extração do período não é afetada, porque o padrão usado no inventário aceita qualquer símbolo entre o número e a palavra "semestre".

## Formato físico

### Delimitador

| categoria                        |   ; |   total |
|:---------------------------------|----:|--------:|
| Combustíveis automotivos         |  45 |      45 |
| Etanol Hidratado + Gasolina C    |  46 |      46 |
| GLP P13                          |  45 |      45 |
| Óleo Diesel (S-500 e S-10) + GNV |  46 |      46 |
| total                            | 182 |     182 |

### Cabeçalho

Todos os 182 arquivos têm o mesmo cabeçalho, com 16 colunas na mesma ordem:

1. `Regiao - Sigla`
2. `Estado - Sigla`
3. `Municipio`
4. `Revenda`
5. `CNPJ da Revenda`
6. `Nome da Rua`
7. `Numero Rua`
8. `Complemento`
9. `Bairro`
10. `Cep`
11. `Produto`
12. `Data da Coleta`
13. `Valor de Venda`
14. `Valor de Compra`
15. `Unidade de Medida`
16. `Bandeira`

## Leitura completa

Cada arquivo foi lido inteiro com a regra de leitura definida no formato físico (`sep=';'`, `encoding='utf-8'`, todas as colunas como texto), registrando o número de linhas, o tempo de leitura e a memória ocupada pelo DataFrame. O objetivo é confirmar que a regra funciona para todos os arquivos e conhecer o tamanho real dos dados.

Os 182 arquivos foram lidos sem erro: a regra de leitura funciona para todos.

### Tamanho dos dados

`memoria` é a memória que os arquivos ocupam depois de lidos pelo pandas e `segundos` é o tempo de leitura. Os totais somam todos os arquivos da categoria.

| categoria                        |   arquivos |   linhas | memoria   |   segundos |
|:---------------------------------|-----------:|---------:|:----------|-----------:|
| Combustíveis automotivos         |         45 | 25464380 | 21.85 GB  |       71.1 |
| Etanol Hidratado + Gasolina C    |         46 |  2269530 | 1.92 GB   |        8.2 |
| GLP P13                          |         45 |  6345989 | 5.37 GB   |       19.5 |
| Óleo Diesel (S-500 e S-10) + GNV |         46 |  1054801 | 914.00 MB |        5.9 |
| total                            |        182 | 35134700 | 30.04 GB  |      104.7 |

- Total de linhas: 35.134.700
- Tempo total de leitura: 104.7 segundos
- Em memória, cada arquivo ocupa em média 5.4 vezes o seu tamanho em disco (de 5.2 a 5.8 vezes).
- Maior arquivo em memória: `2º semestre de 2004.csv` (Combustíveis automotivos), com 150.79 MB em disco e 810.24 MB em memória.

Carregar o histórico inteiro de uma vez ocuparia cerca de 30.04 GB de memória, enquanto o maior arquivo sozinho ocupa 810.24 MB. Por isso a leitura, aqui e no pipeline da Fase 1, é feita um arquivo por vez.

Limitação: uma linha com campos a mais faz a leitura do arquivo falhar, e o arquivo apareceria na lista de falhas. Uma linha com campos a menos não gera erro: o pandas completa os campos que faltam com nulos. Esses casos aparecem na análise de nulos.

## Perfil das colunas

Para cada coluna, foi contada a quantidade de valores ausentes em todos os arquivos. Conta como ausente o campo vazio e o campo que só tem espaços: o pandas reconhece só o primeiro como nulo, então o segundo foi contado à parte. O objetivo é decidir quais colunas o pipeline da Fase 1 vai usar.

Os valores são a porcentagem de linhas sem valor, por categoria e no histórico inteiro (`total`).

| coluna            |   Combustíveis automotivos |   Etanol Hidratado + Gasolina C |   GLP P13 |   Óleo Diesel (S-500 e S-10) + GNV |   total |
|:------------------|---------------------------:|--------------------------------:|----------:|-----------------------------------:|--------:|
| Regiao - Sigla    |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Estado - Sigla    |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Municipio         |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Revenda           |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| CNPJ da Revenda   |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Nome da Rua       |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Numero Rua        |                        0.1 |                             0.0 |       0.0 |                                0.2 |     0.1 |
| Complemento       |                       74.7 |                            78.0 |      80.0 |                               75.4 |    75.9 |
| Bairro            |                        0.4 |                             0.2 |       1.9 |                                0.3 |     0.6 |
| Cep               |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Produto           |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Data da Coleta    |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Valor de Venda    |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Valor de Compra   |                       58.8 |                           100.0 |      72.6 |                              100.0 |    65.2 |
| Unidade de Medida |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |
| Bandeira          |                        0.0 |                             0.0 |       0.0 |                                0.1 |     0.0 |

- Colunas quase sempre preenchidas (menos de 1% ausente): `Regiao - Sigla`, `Estado - Sigla`, `Municipio`, `Revenda`, `CNPJ da Revenda`, `Nome da Rua`, `Numero Rua`, `Bairro`, `Cep`, `Produto`, `Data da Coleta`, `Valor de Venda`, `Unidade de Medida`, `Bandeira`
- Colunas vazias em mais da metade das linhas: `Complemento`, `Valor de Compra`

Limitação: a porcentagem do histórico inteiro pode esconder uma coluna que só passou a ser preenchida a partir de certo ano. A divisão por categoria mostra parte disso, porque as categorias mensais só existem a partir de 2023.

### Decisão por coluna

Cada coluna foi avaliada por dois critérios: se está vazia na maior parte das linhas e se tem uso nas consultas do projeto. O endereço não é usado nessas consultas, mas fica porque é um dado do posto, que vai para uma tabela própria no banco.

| coluna            | decisao   | motivo                                                                                             |
|:------------------|:----------|:---------------------------------------------------------------------------------------------------|
| Regiao - Sigla    | fica      | Agrupa as médias por região                                                                        |
| Estado - Sigla    | fica      | Filtro por estado (ex.: estado com o etanol mais barato)                                           |
| Municipio         | fica      | Filtro por cidade (ex.: preço da gasolina em Goiânia)                                              |
| Revenda           | fica      | Nome do posto                                                                                      |
| CNPJ da Revenda   | fica      | Identifica o posto e faz parte da chave do registro                                                |
| Nome da Rua       | fica      | Endereço do posto, para a tabela de postos                                                         |
| Numero Rua        | fica      | Endereço do posto, para a tabela de postos                                                         |
| Complemento       | sai       | Vazia na maior parte das linhas e sem uso nas consultas do projeto                                 |
| Bairro            | fica      | Endereço do posto, para a tabela de postos                                                         |
| Cep               | fica      | Endereço do posto, para a tabela de postos                                                         |
| Produto           | fica      | Todas as consultas filtram por produto                                                             |
| Data da Coleta    | fica      | Base de toda análise no tempo                                                                      |
| Valor de Venda    | fica      | É o preço, o centro do projeto                                                                     |
| Valor de Compra   | sai       | Vazia na maior parte das linhas, e em todas as categorias mensais; nenhuma consulta do projeto usa |
| Unidade de Medida | fica      | Diferencia as unidades dos produtos (ex.: o GLP é vendido por botijão de 13 kg)                    |
| Bandeira          | fica      | Permite comparar preços por bandeira do posto                                                      |

O pipeline da Fase 1 vai ler 14 das 16 colunas: `Regiao - Sigla`, `Estado - Sigla`, `Municipio`, `Revenda`, `CNPJ da Revenda`, `Nome da Rua`, `Numero Rua`, `Bairro`, `Cep`, `Produto`, `Data da Coleta`, `Valor de Venda`, `Unidade de Medida`, `Bandeira`.
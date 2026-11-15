# Exploração dos dados brutos da ANP

Relatório gerado por `explorer.py` a partir dos arquivos em `raw/`, baixados pelo coletor da série histórica de preços de combustíveis da ANP.

O objetivo da exploração é entender a fonte antes de escrever o pipeline: o que existe, em que formato e com que qualidade. 

Para gerar o relatório novamente: `python explorer.py`.

## Inventário

Os arquivos ficam organizados em uma subpasta por categoria de produto. O período de cada arquivo foi extraído do nome, que segue um de dois padrões: semestral (`1º semestre de 2004.csv`) ou mensal (`Abril de 2023.csv`).

- Total de arquivos: 182
- Tamanho total: 5.59 GB

### Resumo por categoria

`primeiro` é o início do período mais antigo e `ultimo` é o fim do mais recente. As datas são o período que o nome do arquivo **declara** cobrir; a comparação com as datas reais de coleta fica para a etapa de anomalias. Os tamanhos usam base binária (1 MB = 1024² bytes).

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

| categoria                        | faltando   |
|:---------------------------------|:-----------|
| Combustíveis automotivos         | []         |
| Etanol Hidratado + Gasolina C    | []         |
| GLP P13                          | []         |
| Óleo Diesel (S-500 e S-10) + GNV | []         |

## Verificação dos nomes dos arquivos

Cada nome de arquivo foi comparado com o formato exato esperado: `1º semestre de 2004.csv` para os semestrais e `Abril de 2023.csv` para os mensais. O objetivo é encontrar nomes que parecem iguais, mas usam caracteres diferentes.

Arquivos fora do formato: 1

| categoria                | arquivo                 |
|:-------------------------|:------------------------|
| Combustíveis automotivos | 2° semestre de 2023.csv |

Na análise feita, o caso encontrado é o uso do símbolo de grau (°) no lugar do indicador ordinal (º). Os dois são visualmente iguais, mas são caracteres diferentes. A extração do período não é afetada, porque o padrão usado no inventário aceita qualquer símbolo entre o número e a palavra "semestre".

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
| Combustíveis automotivos         |         45 | 25464380 | 21.85 GB  |       58.6 |
| Etanol Hidratado + Gasolina C    |         46 |  2269530 | 1.92 GB   |        6   |
| GLP P13                          |         45 |  6345989 | 5.37 GB   |       20.8 |
| Óleo Diesel (S-500 e S-10) + GNV |         46 |  1054801 | 914.00 MB |        3   |
| total                            |        182 | 35134700 | 30.04 GB  |       88.4 |

- Total de linhas: 35.134.700
- Tempo total de leitura: 88.4 segundos
- Em memória, cada arquivo ocupa em média 5.4 vezes o seu tamanho em disco (de 5.2 a 5.8 vezes).
- Maior arquivo em memória: `2º semestre de 2004.csv` (Combustíveis automotivos), com 150.79 MB em disco e 810.24 MB em memória.

Carregar o histórico inteiro de uma vez ocuparia cerca de 30.04 GB de memória, enquanto o maior arquivo sozinho ocupa 810.24 MB. Por isso a leitura, aqui e no pipeline da Fase 1, é feita um arquivo por vez.

Limitação: uma linha com campos a mais faz a leitura do arquivo falhar, e o arquivo apareceria na lista de falhas. Uma linha com campos a menos não gera erro: o pandas completa os campos que faltam com nulos. Esses casos aparecem na análise de nulos.
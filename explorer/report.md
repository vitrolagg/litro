## ================================== INVENTÁRIO ==================================

Arquivos: 182

Tamanho em disco: 5.59 GB

Resumo por categoria (datas que o nome do arquivo declara cobrir):

| categoria                        |   arquivos | tamanho   | periodo   | primeiro   | ultimo     |
|:---------------------------------|-----------:|:----------|:----------|:-----------|:-----------|
| Combustíveis automotivos         |         45 | 4.11 GB   | Semestral | 2004-01-01 | 2026-06-30 |
| Etanol Hidratado + Gasolina C    |         46 | 370.77 MB | Mensal    | 2023-01-01 | 2026-10-31 |
| GLP P13                          |         45 | 969.64 MB | Semestral | 2004-01-01 | 2026-06-30 |
| Óleo Diesel (S-500 e S-10) + GNV |         46 | 170.62 MB | Mensal    | 2023-01-01 | 2026-10-31 |

Lacunas na sequência de períodos: nenhuma

Nomes de arquivo fora do formato esperado: 1

| categoria                | arquivo                 |
|:-------------------------|:------------------------|
| Combustíveis automotivos | 2° semestre de 2023.csv |

Usam o símbolo de grau (°) no lugar do ordinal (º): 1

## ================================ FORMATO FÍSICO ================================

Delimitador detectado (número de arquivos):

| categoria                        |   ; |   total |
|:---------------------------------|----:|--------:|
| Combustíveis automotivos         |  45 |      45 |
| Etanol Hidratado + Gasolina C    |  46 |      46 |
| GLP P13                          |  45 |      45 |
| Óleo Diesel (S-500 e S-10) + GNV |  46 |      46 |
| total                            | 182 |     182 |

Cabeçalho: igual nos 182 arquivos, com 16 colunas:

   1. Regiao - Sigla

   2. Estado - Sigla

   3. Municipio

   4. Revenda

   5. CNPJ da Revenda

   6. Nome da Rua

   7. Numero Rua

   8. Complemento

   9. Bairro

  10. Cep

  11. Produto

  12. Data da Coleta

  13. Valor de Venda

  14. Valor de Compra

  15. Unidade de Medida

  16. Bandeira

## =============================== LEITURA COMPLETA ===============================

Arquivos lidos sem erro: 182 de 182

Totais por categoria (memoria = ocupada pelo pandas depois da leitura):

| categoria                        |   arquivos |   linhas |   linhas_vazias | memoria   |   segundos |
|:---------------------------------|-----------:|---------:|----------------:|:----------|-----------:|
| Combustíveis automotivos         |         45 | 25464380 |            9114 | 21.85 GB  |       65.9 |
| Etanol Hidratado + Gasolina C    |         46 |  2269530 |               0 | 1.92 GB   |        5.9 |
| GLP P13                          |         45 |  6345989 |               0 | 5.37 GB   |       28.8 |
| Óleo Diesel (S-500 e S-10) + GNV |         46 |  1054801 |            1477 | 914.00 MB |        3.4 |
| total                            |        182 | 35134700 |           10591 | 30.04 GB  |      104.1 |

Total de linhas: 35,134,700

Linhas totalmente vazias: 10,591 nos arquivos:

| categoria                        | arquivo                 |   linhas_vazias |
|:---------------------------------|:------------------------|----------------:|
| Combustíveis automotivos         | 1º semestre de 2025.csv |            9114 |
| Óleo Diesel (S-500 e S-10) + GNV | Janeiro de 2023.csv     |            1477 |

Memória / tamanho em disco: média de 5.4x (de 5.2x a 5.8x)

Maior arquivo em memória: Combustíveis automotivos / 2º semestre de 2004.csv (150.79 MB em disco, 810.24 MB em memória)

Histórico inteiro em memória: 30.04 GB

## ============================== PERFIL DAS COLUNAS ==============================

Porcentagem de valores ausentes (campo vazio ou só com espaços), por categoria e no total:

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

Menos de 1% ausente: Regiao - Sigla, Estado - Sigla, Municipio, Revenda, CNPJ da Revenda, Nome da Rua, Numero Rua, Bairro, Cep, Produto, Data da Coleta, Valor de Venda, Unidade de Medida, Bandeira

Mais de 50% ausente: Complemento, Valor de Compra

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
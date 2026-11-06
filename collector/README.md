# Coleta dos dados — Série histórica de preços de combustíveis (ANP)

Pipeline de ingestão que faz o download automático da [série histórica de preços de combustíveis](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis) publicada pela ANP como dado aberto, e entrega os arquivos padronizados para a etapa de exploração (`../explorer`).

## Dados coletados

| Categoria | Granularidade | Período |
|---|---|---|
| Combustíveis automotivos | semestral | 2004 – 2026 |
| GLP P13 | semestral | 2004 – 2026 |
| Etanol Hidratado + Gasolina C | mensal | 2023 – 2026 |
| Óleo Diesel (S-500 e S-10) + GNV | mensal | 2023 – 2026 |

Total: **182 arquivos, ~5,6 GB**. Os dados não são versionados no repositório (`raw/` está no `.gitignore`); basta rodar o coletor para gerá-los.

## Como funciona

1. **Scraping:** faz a requisição da página da ANP e, com BeautifulSoup, percorre cada categoria (`<h3>`) e seus links (`<ul>` → `<li>` → `<a>`).
2. **Download:** baixa cada arquivo em streaming para um arquivo temporário `.part`.
3. **Extração:** se o arquivo baixado for um ZIP, extrai o CSV de dentro.
4. **Padronização de encoding:** detecta o encoding do arquivo e regrava em UTF-8.
5. **Finalização:** o CSV final só é criado depois que todas as etapas terminam; o `.part` é removido.

## Desafios encontrados

- **Arquivos ZIP disfarçados de CSV:** 10 links entregam um ZIP, e em um deles o link termina em `.csv`. A detecção é feita pelo conteúdo do arquivo (`zipfile.is_zipfile`), não pela extensão.
- **Encoding:** a detecção testa os candidatos `utf-8-sig` → `cp1252` → `latin-1`, do mais restritivo para o mais permissivo, e a saída é sempre UTF-8 sem BOM. A ordem importa: o latin-1 aceita qualquer byte, então testá-lo primeiro classificaria todo arquivo como latin-1.
- **Instabilidade do servidor:** durante a coleta, o servidor passava a recusar conexões por alguns segundos após muitas requisições seguidas, além da instabilidade da minha própria rede. Cada arquivo tem até 15 tentativas, com espera inicial de 10 s que aumenta 5 s a cada falha, para que a coleta completa termine em uma única execução.
- **Integridade:** como o download vai para um `.part`, uma falha no meio nunca deixa um CSV truncado com o nome final.
- **Memória:** todos os arquivos são processados em blocos de 1 MB, então o consumo de RAM não depende do tamanho do arquivo (o maior tem ~158 MB).

## Como executar

Requer Python 3.8+ (testado no 3.14).

```bash
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Os arquivos são salvos em `raw/`, **relativo à pasta de onde o script é executado**.

## Saída

```
raw/
├── Combustíveis automotivos/
│   ├── 1º semestre de 2004.csv
│   └── ...
├── Etanol Hidratado + Gasolina C/
├── GLP P13/
└── Óleo Diesel (S-500 e S-10) + GNV/
```

- Encoding: **UTF-8** (sem BOM)
- Separador: `;`
- Decimal: `,` (ex.: `5,89`)
- Alguns campos de texto vêm entre aspas e contêm `;`, como em `"KM: 1350;"`. Leitores de CSV padrão, como o `pandas.read_csv`, tratam isso corretamente.

## Limitações

- A coleta é sempre completa: não há carga incremental que baixe só os arquivos novos.
- O caminho de saída é relativo à pasta de execução.
- O scraping depende da estrutura atual do HTML da página da ANP.

"""Exploração dos arquivos da ANP"""

# region Imports

# Biblioteca padrão
from pathlib import Path
import re

# Biblioteca de terceiros
import pandas as pd

# Módulos do projeto
import utils

# endregion

# region Constantes

# Mapeamento dos meses do ano para números
MONTHS_DICT = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
               'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}

# Dicionário para mapear o período para o pandas
FREQ = {'Mensal':'MS', 'Semestral':'6MS'}

# Caminho do arquivo relatório
REPORT_PATH = Path('report.md')

# Formato esperado de meses do ano
MONTHS = 'Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro'

# Padrões estritos esperados nos nomes dos arquivos
STRICT_PATTERNS = [
    r'^[12]º semestre de \d{4}\.csv$',
    rf'^({MONTHS}) de \d{{4}}\.csv$'
]

# endregion

# region Inventário

def build_inventory(path):
    """Monta o inventário dos arquivos CSV brutos, uma linha por arquivo.
    
    A categoria é o nome da subpasta onde o arquivo está. 
    O período é extraído do nome do arquivo, que segue os padrões semestral ou mensal.
    As datas de início e fim são o período que o nome declara cobrir, 
    não são datas coletadas de dentro do arquivo.
    
    Args:
        path: Pasta raiz dos arquivos
    
    Returns:
        DataFrame do pandas com as colunas:
            'categoria': Nome da subpasta onde o arquivo está
            'arquivo': Nome do arquivo
            'caminho': Caminho completo do arquivo
            'tamanho': Tamanho do arquivo em MB
            'periodo': Tipo do período
            'inicio': Data de início
            'fim': Data de fim
    
    Raises:
        FileNotFoundError: Se `path` não existir ou não for uma pasta.
        ValueError: Se o nome do arquivo não seguir os padrões semestral ou mensal.
    """

    # Caminho para a pasta raiz dos arquivos
    path = Path(path)

    # Se o caminho passado não existe ou não é uma pasta
    if not path.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {path}")

    # Lista com as informações por arquivo
    info_list = []

    # Todos os csv encontrados
    all_csvs = list(path.rglob('*.csv'))
    
    # Para cada arquivo encontrado
    for csv in all_csvs:

        # Nome do arquivo csv
        archive_name = csv.name

        # Categoria do arquivo
        category = csv.parent.name

        # Busca regex no primeiro padrão
        m = re.search(r'(\d)\D+ semestre de (\d{4})', archive_name)

        # Se a busca encontrar o padrão
        if m is not None:

            # Semestre coberto pelo arquivo
            semester = int(m.group(1))

            # Ano dos dados do arquivo
            year = int(m.group(2))

            # Tipo do período
            period = 'Semestral'

            # Mês inicial do intervalo do arquivo
            initial_month = 1 if semester == 1 else 7

            # Data de início da cobertura
            start_period = pd.Timestamp(year=year, month=initial_month, day=1)

            # Data de fim da cobertura
            finish_period = start_period + pd.DateOffset(months=6) - pd.Timedelta(days=1)

        else:

            # Faz a busca no segundo padrão
            m = re.search(r'(\w+) de (\d{4})', archive_name)

            # Se falhar no segundo padrão
            if m is None:
                raise ValueError(f"Nome do arquivo fora dos padrões esperados: {csv}")

            # Mês de referência do arquivo
            month = m.group(1).lower()

            # Ano de referência do arquivo
            year = int(m.group(2))

            # Tipo do período
            period = 'Mensal'

            # Normaliza o mês para o número equivalente
            month_number = MONTHS_DICT.get(month)

            # Se o mês no nome do arquivo falhar
            if month_number is None:
                raise ValueError(f"Mês no arquivo não reconhecido: {csv}")

            # Data de início da cobertura
            start_period = pd.Timestamp(year=year, month=month_number, day=1)

            # Data de fim da cobertura
            finish_period = start_period + pd.DateOffset(months=1) - pd.Timedelta(days=1)

        # Tamanho do arquivo
        archive_size = csv.stat().st_size / 1024 ** 2

        info_list.append(
            {
                'categoria':category,
                'arquivo':archive_name,
                'caminho':csv,
                'tamanho':archive_size,
                'periodo': period,
                'inicio':start_period,
                'fim':finish_period
            }
        )

    return pd.DataFrame(info_list)

def inventory_section(inventory:pd.DataFrame) -> str:
    """Monta a seção de inventário no relatório de resultados."""

    total_files = len(inventory)
    total_size = utils.format_mb(inventory['tamanho'].sum())

    summary = inventory.groupby('categoria').agg(
       arquivos=('arquivo', 'count'),
        tamanho=('tamanho', 'sum'),
        primeiro=('inicio', 'min'),
        ultimo=('fim', 'max'),
    )

    # Formata o sumário para exibição
    summary['tamanho'] = summary['tamanho'].map(utils.format_mb)
    summary['primeiro'] = summary['primeiro'].dt.strftime('%Y-%m-%d')
    summary['ultimo'] = summary['ultimo'].dt.strftime('%Y-%m-%d')

    # Quantidade de tipos de período por categoria
    type_category = pd.crosstab(inventory['categoria'], inventory['periodo'])

    lines = [
        '## Inventário',
        '',
        'Os arquivos ficam organizados em uma subpasta por categoria de produto. '
        'O período de cada arquivo foi extraído do nome, que segue um de dois padrões: '
        'semestral (`1º semestre de 2004.csv`) ou mensal (`Abril de 2023.csv`).',
        '',
        f'- Total de arquivos: {total_files}',
        f'- Tamanho total: {total_size}',
        '',
        '### Resumo por categoria',
        '',
        '`primeiro` é o início do período mais antigo e `ultimo` é o fim do mais recente. '
        'As datas são o período que o nome do arquivo **declara** cobrir; a comparação '
        'com as datas reais de coleta fica para as validações de qualidade da Fase 2. '
        'Os tamanhos usam base binária (1 MB = 1024² bytes).',
        '',
        summary.to_markdown(),
        '',
        '### Tipo de período por categoria',
        '',
        'Cada categoria usa um único tipo de período. Essa é a premissa da '
        'verificação de lacunas, que gera a sequência esperada a partir desse tipo.',
        '',
        type_category.to_markdown(),
    ]

    return '\n'.join(lines)

def identify_gaps(inventory: pd.DataFrame) -> pd.DataFrame:
    """Identifica lacunas no inventário.
    
    Checa períodos faltando em cada categoria.
    Não cobre períodos repetidos. As pontas não são verificadas então,
    se faltar o primeiro ou o último período nada acontece.
    Presume que cada categoria tem o mesmo tipo em todos os arquivos.
    
    Args:
        inventory: DataFrame do inventário
    
    Returns:
        DataFrame das lacunas, com as colunas:
            'categoria': Categoria do arquivo
            'faltando': lista com as datas de inicio dos períodos ausentes na categoria
    
    """

    # Lista com o resultado da verificação
    gaps_list = []

    # Itera sobre as categorias
    for category, group in inventory.groupby('categoria'):
        
        # Pega o período usado na categoria
        period_type = group['periodo'].iloc[0]

        # Lista do intervalo de datas esperado
        expected = pd.date_range(group['inicio'].min(), group['inicio'].max(), freq=FREQ[period_type])

        # Diferença entre o esperado e o intervalo real
        missing = sorted(set(expected) - set(group['inicio']))

        gaps_list.append(
            {
                'categoria': category,
                'faltando': missing
            }
        )

    return pd.DataFrame(gaps_list)

def gaps_section(gaps:pd.DataFrame) -> str:
    """Monta a seção de lacunas no relatório de resultados."""

    gaps_quantity = gaps['faltando'].str.len().sum()

    # Só as categorias que têm lacunas
    gaps_table = gaps[gaps['faltando'].str.len() > 0].copy()

    # Troca a lista de Timestamps por um texto com as datas no formato ano-mês.
    gaps_table['faltando'] = gaps_table['faltando'].map(
    
        # Para cada lista, formata cada data e junta tudo separado por vírgula
        lambda dates: ', '.join(date.strftime('%Y-%m') for date in dates)
    )

    lines = [
        '## Verificação de lacunas',
        '',
        'Para cada categoria, foi gerada a sequência de períodos que deveria existir '
        'entre o primeiro e o último arquivo (mês a mês ou semestre a semestre), '
        'que depois foi comparada com os períodos encontrados.',
        '',
        'Limitações: as pontas não são verificadas (se faltar o primeiro ou o último '
        'arquivo, a lacuna não aparece) e períodos repetidos não são detectados.',
        '',
    ]

    if gaps_quantity > 0:
        lines.append(f'Lacunas encontradas: {gaps_quantity}')
        lines.append('')
        lines.append(gaps_table.to_markdown(index=False))
    else:
        lines.append('Nenhuma lacuna encontrada: todas as categorias têm a sequência '
                     'completa entre o primeiro e o último período.')

    return '\n'.join(lines)

def find_names_inconsistencies(inventory:pd.DataFrame) -> pd.DataFrame:
    """Encontra inconsistências nos nomes dos arquivos do inventário
    
    Compara o nome do arquivo com o padrão estrito esperado em STRICT_PATTERNS.
    Encontra caracteres fora do padrão, mesmo que visualmente sejam iguais

    Args:
        inventory: DataFrame do inventário gerado em build_inventory
    
    Returns:
        DataFrame com os arquivos de nome fora do padrão esperado. Colunas:
            categoria: A categoria do arquivo encontrado
            arquivo: O nome do arquivo
    """

    # Lista para montar o DataFrame com os arquivos de nome inconsistente
    lines = []

    # Percorre cada linha do DataFrame
    for row in inventory.itertuples():

        # Se não estiver dentro do padrão esperado
        if not any(re.match(pattern, row.arquivo) for pattern in STRICT_PATTERNS):

            lines.append(
                {
                    "categoria":row.categoria,
                    "arquivo":row.arquivo
                }
            )

    return pd.DataFrame(lines)

def names_section(names_inconsistencies: pd.DataFrame) -> str:
    """Monta a seção do relatório com a verificação dos nomes dos arquivos."""

    lines = [
        '## Verificação dos nomes dos arquivos',
        '',
        'Cada nome de arquivo foi comparado com o formato exato esperado: '
        '`1º semestre de 2004.csv` para os semestrais e `Abril de 2023.csv` para os mensais. '
        'O objetivo é encontrar nomes que parecem iguais, mas usam caracteres diferentes.',
        '',
    ]

    if names_inconsistencies.empty:
        lines.append('Todos os nomes seguem o formato esperado.')
    else:
        lines.append(f'Arquivos fora do formato: {len(names_inconsistencies)}')
        lines.append('')
        lines.append(names_inconsistencies.to_markdown(index=False))

        # Quantos dos nomes fora do formato usam o símbolo de grau no lugar do ordinal
        degree_count = names_inconsistencies['arquivo'].str.contains('°').sum()

        # Só explica o caso do símbolo de grau se ele realmente aparecer
        if degree_count > 0:
            lines.append('')
            lines.append(
                f'Arquivos que usam o símbolo de grau (°) no lugar do indicador ordinal (º): '
                f'{degree_count}. Os dois são visualmente iguais, mas são caracteres '
                'diferentes. A extração do período não é afetada, porque o padrão usado no '
                'inventário aceita qualquer símbolo entre o número e a palavra "semestre".'
            )

    return '\n'.join(lines)

# endregion

# region Formato físico

def check_delimiter(inventory:pd.DataFrame) -> pd.DataFrame:
    """Cria um DataFrame com a relação arquivo e delimitador.

    Detecta o delimitador de cada arquivo do inventário.    
    
    Args:
        inventory: DataFrame do inventário de arquivos (precisa da coluna 'caminho')
    
    Returns:
        DataFrame com as colunas:
            'categoria': Categoria do arquivo.
            'arquivo': Nome do arquivo.
            'delimitador': Delimitador usado pelo arquivo. Ou None caso não tenha sido possível decidir
    """

    # Cria um DataFrame result que copia duas colunas do inventory
    result = inventory[['categoria', 'arquivo']].copy()

    # Cria no result a coluna delimitador e encontra o delimitador para cada linha passando o caminho correspondente.
    result['delimitador'] = inventory['caminho'].map(utils.find_delimiter)

    return result

def delimiter_section(delimiters:pd.DataFrame) -> str:
    """Monta a seção dos delimitadores para o relatório.
    
    Mostra uma tabela com a contagem de arquivos por categoria e delimitador.
    Se houver mais de um delimitador, lista os arquivos que não usam o predominante.
    
    Args:
        delimiters: O DataFrame com os delimitadores identificados por arquivo
    
    Returns:
        A string da seção para o relatório
    """
    
    summary = pd.crosstab(
        delimiters['categoria'],

        # Substitui o None por 'não detectado'
        delimiters['delimitador'].fillna('não detectado'),

        # Adiciona uma linha e uma coluna com a soma
        margins=True,

        # Nome dessa linha e dessa coluna
        margins_name='total'
    )

    # Lista de textos para o relatório
    lines = [
        '## Formato físico',
        '',
        '### Delimitador',
        '',
        summary.to_markdown(),
    ]

    # Se houver mais de um valor diferente
    if delimiters['delimitador'].nunique(dropna=False) > 1:

        # Encontra o delimitador principal
        main_delim = delimiters['delimitador'].mode()[0]

        # Separa as exceções
        exceptions = delimiters[delimiters['delimitador'] != main_delim]

        # Adiciona à lista de textos
        lines += ['', 'Arquivos fora do delimitador predominante: ', 
                  '',
                  exceptions.to_markdown(index= False)
                ]

    return '\n'.join(lines)

def check_headers(inventory:pd.DataFrame) -> pd.DataFrame:
    """Cria um DataFrame com o cabeçalho de cada arquivo.
    
    Args:
        inventory: Inventário de arquivos
    
    Returns:
        DataFrame com o cabeçalho dos arquivos. Colunas:
            'categoria': Categoria do arquivo.
            'arquivo': Nome do arquivo.
            'cabecalho': Cabeçalho do arquivo.
            'inicio': Data de inicio da cobertura do arquivo.
    """
    

    # Copia as colunas 'categoria' e 'arquivo' para o DataFrame result
    result = inventory[['categoria','arquivo', 'inicio']].copy()

    # Cria a coluna 'cabecalho' e preenche usando a função read_header
    result['cabecalho'] = inventory['caminho'].map(utils.read_header)

    return result

def archive_header_section(headers:pd.DataFrame) -> str:
    """Monta a seção de verificação dos cabeçalhos no relatório.

    Se todos os arquivos tiverem o mesmo cabeçalho, lista as colunas.
    Se houver mais de um padrão, mostra uma tabela com cada padrão.

    Args:
        headers: DataFrame gerado por check_headers

    Returns:
        A string da seção para o relatório
    """

    # Agrupa os arquivos pelo cabeçalho. A coluna 'cabecalho' vira o índice
    patterns = headers.groupby('cabecalho').agg(
        arquivos = ('arquivo', 'count'),
        primeiro= ('inicio', 'min'),
        ultimo=('inicio', 'max')
    )

    # Lista de textos para o relatório
    lines = [
        '### Cabeçalho',
        '',
    ]

    # Se existe um único padrão de cabeçalho
    if len(patterns) == 1:

        # Pega a tupla do único padrão, que está no índice
        columns = patterns.index[0]

        lines.append(f'Todos os {len(headers)} arquivos têm o mesmo cabeçalho, '
                     f'com {len(columns)} colunas na mesma ordem:')
        lines.append('')

        # Uma linha de lista numerada para cada coluna
        for number, name in enumerate(columns, start=1):
            lines.append(f'{number}. `{name}`')

    else:
        lines.append(f'Foram encontrados {len(patterns)} cabeçalhos diferentes.')
        lines.append('')

        # Traz o cabeçalho do índice de volta para uma coluna, para ele aparecer na tabela
        table = patterns.reset_index()

        # Formata as datas e transforma a tupla de colunas em texto
        table['colunas'] = table['cabecalho'].str.len()
        table['primeiro'] = table['primeiro'].dt.strftime('%Y-%m')
        table['ultimo'] = table['ultimo'].dt.strftime('%Y-%m')
        table['cabecalho'] = table['cabecalho'].map(', '.join)

        # O cabeçalho vai por último porque é a coluna mais longa
        table = table[['arquivos', 'primeiro', 'ultimo', 'colunas', 'cabecalho']]

        lines.append(table.to_markdown(index=False))

    return '\n'.join(lines)

# endregion

# region Leitura completa

def check_reading(inventory:pd.DataFrame) -> pd.DataFrame:

    rows = []

    # Total de arquivos, para mostrar o progresso
    total = len(inventory)

    # enumerate numera as voltas do loop a partir de 1, para o print do progresso
    for number, row in enumerate(inventory.itertuples(), start=1):

        # Obtém as estatísticas para o arquivo da linha atual
        stats = utils.read_file_stats(row.caminho)

        # Mostra o progresso: o tempo de leitura ou o erro, se a leitura falhou
        result = 'ERRO' if stats['erro'] is not None else f'{stats["segundos"]:.2f} s'
        print(f'    [{number}/{total}] {row.categoria} / {row.arquivo}: {result}')

        # Obtém categoria
        stats['categoria'] = row.categoria

        # Obtém nome do arquivo
        stats['arquivo'] = row.arquivo

        # Tamanho em disco, para comparar com a memória ocupada
        stats['tamanho'] = row.tamanho

        # Adiciona à lista
        rows.append(stats)

    return pd.DataFrame(rows, columns=['categoria', 'arquivo', 'tamanho', 'linhas', 'segundos', 'memoria_mb', 'erro'])

def reading_section(reading:pd.DataFrame) -> str:
    """Monta a seção de leitura completa do relatório.

    Mostra os totais de linhas, memória e tempo por categoria e no geral,
    os arquivos que falharam na leitura e a relação entre memória e tamanho em disco.

    Args:
        reading: DataFrame gerado por check_reading

    Returns:
        A string da seção para o relatório
    """

    # Arquivos em que a leitura falhou
    failures = reading[reading['erro'].notna()]

    # Totais por categoria. O sum ignora os valores vazios dos arquivos que falharam
    summary = reading.groupby('categoria').agg(
        arquivos=('arquivo', 'count'),
        linhas=('linhas', 'sum'),
        memoria=('memoria_mb', 'sum'),
        segundos=('segundos', 'sum'),
    )

    # Linha com o total geral, somando as categorias
    summary.loc['total'] = summary.sum()

    # Guarda os totais gerais antes de formatar a tabela
    total_lines = int(summary.loc['total', 'linhas'])
    total_memory = summary.loc['total', 'memoria']
    total_seconds = summary.loc['total', 'segundos']

    # Formata a tabela para exibição
    summary['arquivos'] = summary['arquivos'].astype(int)
    summary['linhas'] = summary['linhas'].astype(int)
    summary['memoria'] = summary['memoria'].map(utils.format_mb)
    summary['segundos'] = summary['segundos'].round(1)

    # Quantas vezes o DataFrame é maior que o arquivo em disco
    ratio = reading['memoria_mb'] / reading['tamanho']

    # Arquivo que ocupou mais memória
    largest = reading.loc[reading['memoria_mb'].idxmax()]

    lines = [
        '## Leitura completa',
        '',
        'Cada arquivo foi lido inteiro com a regra de leitura definida no formato físico '
        "(`sep=';'`, `encoding='utf-8'`, todas as colunas como texto), registrando o número "
        'de linhas, o tempo de leitura e a memória ocupada pelo DataFrame. O objetivo é '
        'confirmar que a regra funciona para todos os arquivos e conhecer o tamanho real dos dados.',
        '',
    ]

    # Resultado da leitura: todos leram ou lista dos que falharam
    if failures.empty:
        lines.append(f'Os {len(reading)} arquivos foram lidos sem erro: a regra de leitura funciona para todos.')
    else:
        lines.append(f'Arquivos que falharam na leitura: {len(failures)} de {len(reading)}')
        lines.append('')

        # Tira a quebra de linha que o pandas coloca no fim da mensagem de erro
        failures_table = failures[['categoria', 'arquivo', 'erro']].copy()
        failures_table['erro'] = failures_table['erro'].str.strip()

        lines.append(failures_table.to_markdown(index=False))

    lines += [
        '',
        '### Tamanho dos dados',
        '',
        '`memoria` é a memória que os arquivos ocupam depois de lidos pelo pandas e '
        '`segundos` é o tempo de leitura. Os totais somam todos os arquivos da categoria.',
        '',
        summary.to_markdown(),
        '',
        f'- Total de linhas: {total_lines:,}'.replace(',', '.'),
        f'- Tempo total de leitura: {total_seconds:.1f} segundos',
        f'- Em memória, cada arquivo ocupa em média {ratio.mean():.1f} vezes o seu tamanho em disco '
        f'(de {ratio.min():.1f} a {ratio.max():.1f} vezes).',
        f'- Maior arquivo em memória: `{largest["arquivo"]}` ({largest["categoria"]}), '
        f'com {utils.format_mb(largest["tamanho"])} em disco e {utils.format_mb(largest["memoria_mb"])} em memória.',
        '',
        f'Carregar o histórico inteiro de uma vez ocuparia cerca de {utils.format_mb(total_memory)} de memória, '
        f'enquanto o maior arquivo sozinho ocupa {utils.format_mb(largest["memoria_mb"])}. Por isso a leitura, '
        'aqui e no pipeline da Fase 1, é feita um arquivo por vez.',
        '',
        'Limitação: uma linha com campos a mais faz a leitura do arquivo falhar, e o arquivo '
        'apareceria na lista de falhas. Uma linha com campos a menos não gera erro: o pandas '
        'completa os campos que faltam com nulos. Esses casos aparecem na análise de nulos.',
    ]

    return '\n'.join(lines)

# endregion

# region Perfil das colunas

def check_nulls(inventory:pd.DataFrame) -> pd.DataFrame:
    """Conta os valores ausentes de cada coluna, em cada arquivo.

    Args:
        inventory: Inventário de arquivos

    Returns:
        DataFrame com uma linha por arquivo. Colunas:
            'categoria': Categoria do arquivo.
            'arquivo': Nome do arquivo.
            Uma coluna para cada coluna do CSV, com a quantidade de valores ausentes.
    """

    rows = []

    # Total de arquivos, para mostrar o progresso
    total = len(inventory)

    for number, row in enumerate(inventory.itertuples(), start=1):

        print(f'    [{number}/{total}] {row.categoria} / {row.arquivo}')

        # Ausentes do arquivo, como dicionário: nome da coluna do CSV -> quantidade
        nulls = utils.count_nulls(row.caminho).to_dict()

        # Identifica de qual categoria e arquivo vieram as contagens
        nulls['categoria'] = row.categoria
        nulls['arquivo'] = row.arquivo

        rows.append(nulls)

    return pd.DataFrame(rows)

def nulls_section(nulls:pd.DataFrame, reading:pd.DataFrame) -> str:
    """Monta a seção do perfil das colunas no relatório.

    Mostra a porcentagem de valores ausentes de cada coluna do CSV,
    por categoria e no histórico inteiro.

    Args:
        nulls: DataFrame gerado por check_nulls
        reading: DataFrame gerado por check_reading, de onde vem o total de linhas

    Returns:
        A string da seção para o relatório
    """

    # Colunas do CSV: todas, menos as que identificam o arquivo
    csv_columns = nulls.columns.drop(['categoria', 'arquivo'])

    # Ausentes por categoria: uma linha por categoria, uma coluna por coluna do CSV
    nulls_by_category = nulls.groupby('categoria')[csv_columns].sum()

    # Total de linhas de cada categoria, medido na leitura completa
    rows_by_category = reading.groupby('categoria')['linhas'].sum()

    # Porcentagem de ausentes. axis=0 divide cada linha (categoria) pelo total de linhas dela
    percent = nulls_by_category.div(rows_by_category, axis=0) * 100

    # Inverte a tabela: as colunas do CSV viram as linhas e as categorias viram as colunas
    percent = percent.T
    percent.index.name = 'coluna'

    # Porcentagem no histórico inteiro, somando todas as categorias
    percent['total'] = nulls_by_category.sum() / rows_by_category.sum() * 100

    # Colunas sem nenhum valor ausente e colunas vazias em mais da metade das linhas
    always_filled = [f'`{name}`' for name in percent.index[percent['total'] == 0]]
    mostly_empty = [f'`{name}`' for name in percent.index[percent['total'] > 50]]

    lines = [
        '## Perfil das colunas',
        '',
        'Para cada coluna, foi contada a quantidade de valores ausentes em todos os arquivos. '
        'Conta como ausente o campo vazio e o campo que só tem espaços: o pandas reconhece '
        'só o primeiro como nulo, então o segundo foi contado à parte. O objetivo é decidir '
        'quais colunas o pipeline da Fase 1 vai usar.',
        '',
        'Os valores são a porcentagem de linhas sem valor, por categoria e no histórico inteiro (`total`).',
        '',
        percent.to_markdown(floatfmt='.1f'),
        '',
        f'- Colunas sempre preenchidas: {", ".join(always_filled) or "nenhuma"}',
        f'- Colunas vazias em mais da metade das linhas: {", ".join(mostly_empty) or "nenhuma"}',
        '',
        'Limitação: a porcentagem do histórico inteiro pode esconder uma coluna que só passou '
        'a ser preenchida a partir de certo ano. A divisão por categoria mostra parte disso, '
        'porque as categorias mensais só existem a partir de 2023.',
    ]

    return '\n'.join(lines)

# endregion

# region Relatório

def header_section() -> str:
    """Monta a seção de cabeçalho do relatório de resultados."""

    lines = [
        '# Exploração dos dados brutos da ANP',
        '',
        'Relatório gerado por `explorer.py` a partir dos arquivos em `raw/`, '
        'baixados pelo coletor da série histórica de preços de combustíveis da ANP.',
        '',
        'O objetivo da exploração é entender a fonte antes de escrever o pipeline: '
        'o que existe, em que formato e com que qualidade. ',
        '',
        'Para gerar o relatório novamente: `python explorer.py`.',
    ]

    return '\n'.join(lines)

def write_report(sections:list[str], path:Path) -> None:
    """Junta as seções e escreve o relatório em markdown.
       
    Args:
        sections: Seções do relatório, já em markdown, 
        na ordem em que devem aparecer
        path: Arquivo de saída. É sobrescrito se já existir
    """

    # Junta as seções, com uma linha em branco de espaço entre elas
    report = '\n\n'.join(sections)

    # Escreve o arquivo
    path.write_text(report, encoding='utf-8')
    
# endregion

# region Função principal

def main():
    print('Montando o inventário...')
    inventory = build_inventory('raw')
    print(f'    {len(inventory)} arquivos encontrados')

    print('Verificando lacunas...')
    gaps = identify_gaps(inventory)

    print('Verificando os nomes dos arquivos...')
    name_inconsistencies = find_names_inconsistencies(inventory)

    print('Detectando os delimitadores...')
    delimiters = check_delimiter(inventory)

    print('Lendo os cabeçalhos...')
    headers = check_headers(inventory)

    print('Lendo todos os arquivos inteiros...')
    reading = check_reading(inventory)

    print('Contando os valores ausentes de cada coluna...')
    nulls = check_nulls(inventory)

    print('Montando o relatório...')
    sections = [
        header_section(),
        inventory_section(inventory),
        gaps_section(gaps),
        names_section(name_inconsistencies),
        delimiter_section(delimiters),
        archive_header_section(headers),
        reading_section(reading),
        nulls_section(nulls, reading),
    ]

    write_report(sections, path=REPORT_PATH)
    print(f'Relatório salvo em {REPORT_PATH}')

# endregion

if __name__ == '__main__':
    main()
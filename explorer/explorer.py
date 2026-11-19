"""Exploração dos arquivos da ANP

Roda todas as etapas da exploração, imprime os resultados no terminal
e grava os mesmos resultados em report.md:

    python explorer.py
"""

# region Imports

# Biblioteca padrão
from pathlib import Path
import re

# Biblioteca de terceiros
import pandas as pd

# Módulos do projeto
import utils
from utils import Report

# endregion

# region Constantes

# Pasta raiz dos arquivos brutos
RAW_PATH = Path('raw')

# Arquivo onde o resultado da exploração é gravado
REPORT_PATH = Path('report.md')

# Mapeamento dos meses do ano para números
MONTHS_DICT = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12
}

# Dicionário para mapear o período para o pandas
FREQ = {
    'Mensal':'MS',
    'Semestral':'6MS'
}

# Formato esperado de meses do ano
MONTHS = 'Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro'

# Padrões estritos esperados nos nomes dos arquivos
STRICT_PATTERNS = [
    r'^[12]º semestre de \d{4}\.csv$',
    rf'^({MONTHS}) de \d{{4}}\.csv$'
]

# Relatório da exploração, usado em todas as etapas
REPORT = Report()

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

            # Semestre de refência do arquivo
            semester = int(m.group(1))

            # Ano de referência do arquivo
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

def show_inventory(inventory: pd.DataFrame) -> None:
    """Imprime arquivos por categoria, lacunas e nomes fora do padrão."""

    REPORT.title('INVENTÁRIO')

    # Totais gerais do inventário
    REPORT.line(f'Arquivos: {len(inventory)}')
    REPORT.line(f'Tamanho em disco: {utils.format_mb(inventory["tamanho"].sum())}')
    REPORT.line()

    # Resumo por categoria: quantidade, tamanho, tipo de período e cobertura
    summary = inventory.groupby('categoria').agg(
        arquivos=('arquivo', 'count'),
        tamanho=('tamanho', 'sum'),
        periodo=('periodo', 'first'),
        primeiro=('inicio', 'min'),
        ultimo=('fim', 'max'),
    )

    # Formata o tamanho e as datas para exibição
    summary['tamanho'] = summary['tamanho'].map(utils.format_mb)
    summary['primeiro'] = summary['primeiro'].dt.strftime('%Y-%m-%d')
    summary['ultimo'] = summary['ultimo'].dt.strftime('%Y-%m-%d')

    REPORT.line('Resumo por categoria (datas que o nome do arquivo declara cobrir):')
    REPORT.table(summary)

    # Quantos tipos de período cada categoria usa. A verificação de lacunas presume um só
    period_types = inventory.groupby('categoria')['periodo'].nunique()

    # Avisa se alguma categoria mistura arquivos mensais e semestrais
    if (period_types > 1).any():
        REPORT.line('Categorias com mais de um tipo de período:')
        REPORT.line(', '.join(period_types[period_types > 1].index))
        REPORT.line()

    # Lacunas: períodos que faltam entre o primeiro e o último arquivo de cada categoria
    gaps = identify_gaps(inventory)

    # Só as categorias que têm lacunas
    gaps = gaps[gaps['faltando'].str.len() > 0].copy()

    if gaps.empty:
        REPORT.line('Lacunas na sequência de períodos: nenhuma')
        REPORT.line()
    else:
        # Troca a lista de Timestamps por um texto com as datas no formato ano-mês
        gaps['faltando'] = gaps['faltando'].map(
            lambda dates: ', '.join(date.strftime('%Y-%m') for date in dates)
        )

        REPORT.line('Lacunas na sequência de períodos:')
        REPORT.table(gaps, index=False)

    # Nomes de arquivo que não seguem o formato exato esperado
    names = find_names_inconsistencies(inventory)

    if names.empty:

        REPORT.line('Nomes de arquivo fora do formato esperado: nenhum')

    else:

        REPORT.line(f'Nomes de arquivo fora do formato esperado: {len(names)}')
        REPORT.table(names, index=False)

        # Quantos desses nomes usam o símbolo de grau no lugar do ordinal
        degree_count = names['arquivo'].str.contains('°').sum()

        # Só mostra a contagem se o símbolo de grau realmente aparecer
        if degree_count > 0:
            REPORT.line(f'Usam o símbolo de grau (°) no lugar do ordinal (º): {degree_count}')

# endregion

# region Formato físico

def show_format(inventory: pd.DataFrame) -> None:
    """Imprime delimitadores e padrões de cabeçalho encontrados."""

    REPORT.title('FORMATO FÍSICO')

    # Delimitador de cada arquivo. None vira 'não detectado' para aparecer na tabela
    delimiters = inventory['caminho'].map(utils.find_delimiter).fillna('não detectado')

    # Contagem de arquivos por categoria e delimitador, com linha e coluna de total
    summary = pd.crosstab(
        inventory['categoria'],
        delimiters.rename('delimitador'),
        margins=True,
        margins_name='total'
    )

    REPORT.line('Delimitador detectado (número de arquivos):')
    REPORT.table(summary)

    # Se houver mais de um delimitador, lista os arquivos fora do predominante
    if delimiters.nunique() > 1:

        # Delimitador mais comum
        main_delim = delimiters.mode()[0]

        # Arquivos que usam outro delimitador
        exceptions = inventory.loc[delimiters != main_delim, ['categoria', 'arquivo']]

        REPORT.line(f'Arquivos fora do delimitador predominante ({main_delim}):')
        REPORT.table(exceptions, index=False)

    # Cabeçalho de cada arquivo, como tupla com o nome das colunas
    headers = inventory['caminho'].map(utils.read_header)

    # Agrupa os arquivos pelo cabeçalho. O cabeçalho vira o índice
    patterns = inventory.groupby(headers.rename('cabecalho')).agg(
        arquivos=('arquivo', 'count'),
        primeiro=('inicio', 'min'),
        ultimo=('inicio', 'max'),
    )

    # Um único cabeçalho: lista as colunas numeradas
    if len(patterns) == 1:

        # A tupla do único cabeçalho, que está no índice
        columns = patterns.index[0]

        REPORT.line(f'Cabeçalho: igual nos {len(inventory)} arquivos, com {len(columns)} colunas:')

        # Uma linha para cada coluna, numerada a partir de 1
        for number, name in enumerate(columns, start=1):

            REPORT.line(f'  {number:>2}. {name}')

        REPORT.line()

    # Mais de um cabeçalho: mostra cada padrão e o período em que aparece
    else:

        # Traz o cabeçalho do índice de volta para uma coluna
        table = patterns.reset_index()

        # Quantidade de colunas e datas formatadas
        table['colunas'] = table['cabecalho'].str.len()
        table['primeiro'] = table['primeiro'].dt.strftime('%Y-%m')
        table['ultimo'] = table['ultimo'].dt.strftime('%Y-%m')

        # Transforma a tupla de colunas em texto separado por vírgula
        table['cabecalho'] = table['cabecalho'].map(', '.join)

        REPORT.line(f'Cabeçalho: {len(patterns)} padrões diferentes:')
        REPORT.table(table[['arquivos', 'primeiro', 'ultimo', 'colunas', 'cabecalho']], index=False)

# endregion

# region Leitura de todos os arquivos

def profile_files(inventory: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lê cada arquivo uma vez e junta as medições de todos.

    Args:
        inventory: Inventário de arquivos

    Returns:
        Tupla com três DataFrames:

            reading: Medições da leitura. Colunas:
                'categoria': Nome da subpasta onde o arquivo está
                'arquivo': Nome do arquivo
                'tamanho': Tamanho do arquivo em disco, em MB
                'linhas': Quantidade de linhas, sem o cabeçalho
                'linhas_vazias': Quantidade de linhas com todos os campos ausentes
                'segundos': Tempo de leitura do arquivo
                'memoria_mb': Memória ocupada pelo DataFrame do arquivo, em MB
                'falhas_datas': Datas que não convertem com '%d/%m/%Y'
                'erro': Mensagem do erro, se a leitura falhou, ou None
                Uma linha por arquivo. As medições de um arquivo que falhou ficam vazias.

        nulls: Valores ausentes, uma linha por arquivo. Colunas:
            'categoria': Nome da subpasta onde o arquivo está
            Uma coluna para cada coluna do CSV, com a quantidade de valores ausentes.
            Arquivos que falharam ficam de fora.

        dates: Formatos da Data da Coleta, uma linha por arquivo e formato. Colunas:
            'categoria', 'arquivo', 'inicio': Identificação do arquivo
            'desenho': Formato da data, com cada dígito trocado por 9
            'linhas': Quantidade de linhas com esse formato
            Arquivos que falharam ficam de fora.
    """

    # Aviso de progresso: fica só no terminal, não vai para o relatório
    print()
    print('Lendo todos os arquivos inteiros...')

    # Medições de leitura e contagens de nulos, uma linha por arquivo
    reading_rows = []
    nulls_rows = []

    # Formatos de data, uma linha por arquivo e formato
    dates_rows = []

    # Total de arquivos, para mostrar o progresso
    total = len(inventory)

    # Quantidade de dígitos do total
    width = len(str(total))

    # enumerate numera as voltas do loop a partir de 1, para o print do progresso
    for number, row in enumerate(inventory.itertuples(), start=1):

        # Lê o arquivo e mede tudo de uma vez
        profile = utils.profile_file(row.caminho)

        # Mostra o progresso: tempo de leitura e memória do arquivo, ou ERRO se a leitura falhou
        result = ('ERRO' if profile['erro'] is not None else f'{profile["segundos"]:.2f} s, {utils.format_mb(profile["memoria_mb"])}')

        print(f'    [{number:>{width}}/{total}] {row.categoria} / {row.arquivo}: {result}')

        # Tira os nulos do dicionário, porque eles vão para outro DataFrame
        nulls = profile.pop('nulos')

        # Identifica de qual arquivo vieram as medições
        profile['categoria'] = row.categoria
        profile['arquivo'] = row.arquivo

        # Tamanho em disco, para comparar com a memória ocupada
        profile['tamanho'] = row.tamanho

        reading_rows.append(profile)

        # Arquivo que falhou não tem contagem de nulos
        if nulls is not None:

            # Identifica a categoria, usada para agrupar as porcentagens
            nulls['categoria'] = row.categoria

            nulls_rows.append(nulls)

        # Tira os formatos de data do dicionário, porque eles vão para outro DataFrame
        dates = profile.pop('datas')

        # Arquivo que falhou não tem formatos de data
        if dates is not None:

            # Cada formato do arquivo vira uma linha
            for shape, count in dates.items():

                dates_rows.append(
                    {
                        'categoria' : row.categoria,
                        'arquivo' : row.arquivo,
                        'inicio' : row.inicio,
                        'desenho' : shape,
                        'linhas' : count,
                    }
                )

    # Monta os DataFrames, com as colunas de identificação primeiro
    reading = pd.DataFrame(
        reading_rows,
        columns=[
            'categoria',
            'arquivo',
            'tamanho',
            'linhas',
            'linhas_vazias',
            'segundos',
            'memoria_mb',
            'falhas_datas',
            'erro'
            ]
        )
    nulls = pd.DataFrame(nulls_rows)
    dates = pd.DataFrame(dates_rows)

    return reading, nulls, dates

def show_reading(reading: pd.DataFrame) -> None:
    """Imprime arquivos que falharam, linhas, memória e tempo de leitura."""

    REPORT.title('LEITURA COMPLETA')

    # Arquivos em que a leitura falhou
    failures = reading[reading['erro'].notna()]

    REPORT.line(f'Arquivos lidos sem erro: {len(reading) - len(failures)} de {len(reading)}')
    REPORT.line()

    # Lista os arquivos que falharam, com a mensagem do erro
    if not failures.empty:

        # Tira a quebra de linha que o pandas coloca no fim da mensagem de erro
        failures = failures[['categoria', 'arquivo', 'erro']].copy()
        failures['erro'] = failures['erro'].str.strip()

        REPORT.line('Arquivos que falharam na leitura:')
        REPORT.table(failures, index=False)

    # Totais por categoria. O sum ignora os valores vazios dos arquivos que falharam
    summary = reading.groupby('categoria').agg(
        arquivos=('arquivo', 'count'),
        linhas=('linhas', 'sum'),
        linhas_vazias=('linhas_vazias', 'sum'),
        memoria=('memoria_mb', 'sum'),
        segundos=('segundos', 'sum'),
    )

    # Linha com o total geral, somando as categorias
    summary.loc['total'] = summary.sum()

    # Guarda os totais gerais antes de formatar a tabela
    total_lines = int(summary.loc['total', 'linhas'])
    total_memory = summary.loc['total', 'memoria']

    # Formata a tabela para exibição
    summary['arquivos'] = summary['arquivos'].astype(int)
    summary['linhas'] = summary['linhas'].astype(int)
    summary['linhas_vazias'] = summary['linhas_vazias'].astype(int)
    summary['memoria'] = summary['memoria'].map(utils.format_mb)

    REPORT.line('Totais por categoria (memoria = ocupada pelo pandas depois da leitura):')
    REPORT.table(summary)

    REPORT.line(f'Total de linhas: {total_lines:,}')

    # Arquivos com linhas em que todos os campos estão vazios
    with_empty_rows = reading.loc[reading['linhas_vazias'] > 0, ['categoria', 'arquivo', 'linhas_vazias']]

    # Volta a contagem para inteiro (ela vira decimal quando algum arquivo falhou e ficou None)
    with_empty_rows['linhas_vazias'] = with_empty_rows['linhas_vazias'].astype(int)

    if with_empty_rows.empty:

        REPORT.line('Linhas totalmente vazias: nenhuma')

    else:

        REPORT.line(f'Linhas totalmente vazias: {with_empty_rows["linhas_vazias"].sum():,} nos arquivos:')
        REPORT.table(with_empty_rows, index=False)

    # Quantas vezes o DataFrame é maior que o arquivo em disco
    ratio = reading['memoria_mb'] / reading['tamanho']

    REPORT.line(f'Memória / tamanho em disco: média de {ratio.mean():.1f}x (de {ratio.min():.1f}x a {ratio.max():.1f}x)')

    # Arquivo que ocupou mais memória
    largest = reading.loc[reading['memoria_mb'].idxmax()]

    REPORT.line(f'Maior arquivo em memória: {largest["categoria"]} / {largest["arquivo"]} ({utils.format_mb(largest["tamanho"])} em disco, {utils.format_mb(largest["memoria_mb"])} em memória)')

    REPORT.line(f'Histórico inteiro em memória: {utils.format_mb(total_memory)}')

def show_columns(nulls: pd.DataFrame, reading: pd.DataFrame) -> None:
    """Imprime a porcentagem de valores ausentes por coluna."""

    REPORT.title('PERFIL DAS COLUNAS')

    # Colunas do CSV: todas, menos a que identifica a categoria
    csv_columns = nulls.columns.drop('categoria')

    # Ausentes por categoria: uma linha por categoria, uma coluna por coluna do CSV
    nulls_by_category = nulls.groupby('categoria')[csv_columns].sum()

    # Total de linhas de cada categoria, medido na leitura
    rows_by_category = reading.groupby('categoria')['linhas'].sum()

    # Só as categorias que têm contagem de nulos (uma categoria em que todos os arquivos falharam fica de fora)
    rows_by_category = rows_by_category.loc[nulls_by_category.index]

    # Porcentagem de ausentes. axis=0 divide cada linha (categoria) pelo total de linhas dela
    percent = nulls_by_category.div(rows_by_category, axis=0) * 100

    # Inverte a tabela: as colunas do CSV viram as linhas e as categorias viram as colunas
    percent = percent.T
    percent.index.name = 'coluna'

    # Porcentagem no histórico inteiro, somando todas as categorias
    percent['total'] = nulls_by_category.sum() / rows_by_category.sum() * 100

    REPORT.line('Porcentagem de valores ausentes (campo vazio ou só com espaços), por categoria e no total:')
    REPORT.table(percent)

    # Colunas quase sempre preenchidas e colunas vazias em mais da metade das linhas
    almost_filled = percent.index[percent['total'] < 1]
    mostly_empty = percent.index[percent['total'] > 50]

    REPORT.line(f'Menos de 1% ausente: {", ".join(almost_filled) or "nenhuma"}')
    REPORT.line()
    REPORT.line(f'Mais de 50% ausente: {", ".join(mostly_empty) or "nenhuma"}')

def show_dates(dates: pd.DataFrame, reading: pd.DataFrame) -> None:
    """Imprime os formatos da Data da Coleta e quantas datas falham na conversão."""

    REPORT.title('DATA DA COLETA')

    # Agrupa as linhas de todos os arquivos pelo formato, como foi feito com os cabeçalhos
    patterns = dates.groupby('desenho').agg(
        linhas=('linhas', 'sum'),
        arquivos=('arquivo', 'nunique'),
        primeiro=('inicio', 'min'),
        ultimo=('inicio', 'max'),
    )

    # Formata as datas para exibição
    patterns['primeiro'] = patterns['primeiro'].dt.strftime('%Y-%m')
    patterns['ultimo'] = patterns['ultimo'].dt.strftime('%Y-%m')

    REPORT.line('Formatos encontrados (cada dígito trocado por 9):')
    REPORT.table(patterns)

    # Quantos formatos diferentes cada arquivo tem
    per_file = dates.groupby(['categoria', 'arquivo'])['desenho'].nunique()

    # Só os arquivos com mais de um formato
    mixed = per_file[per_file > 1]

    if mixed.empty:

        REPORT.line('Arquivos com mais de um formato: nenhum')
        REPORT.line()

    else:

        REPORT.line('Arquivos com mais de um formato:')
        REPORT.table(mixed.reset_index(name='formatos'), index=False)

    # Total de datas que não convertem com dia/mês/ano. O sum ignora os arquivos que falharam na leitura
    failures = int(reading['falhas_datas'].sum())

    REPORT.line(f"Datas que falham na conversão com '%d/%m/%Y': {failures:,}")

# endregion

# region Função principal

def main():

    # Lista os arquivos e o período que cada um cobre
    inventory = build_inventory(RAW_PATH)

    # Arquivos, períodos, lacunas e nomes
    show_inventory(inventory)

    # Delimitadores e cabeçalhos
    show_format(inventory)

    # Lê cada arquivo uma vez
    reading, nulls, dates = profile_files(inventory)

    # Linhas, memória, tempo e falhas de leitura
    show_reading(reading)

    # Valores ausentes por coluna
    show_columns(nulls, reading)

    # Formatos da Data da Coleta
    show_dates(dates, reading)

    # Salva o resultado da exploração em markdown
    REPORT.save(REPORT_PATH)

# endregion

if __name__ == '__main__':
    main()

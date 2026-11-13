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
        'com as datas reais de coleta fica para a etapa de anomalias. '
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
        f'Lacunas encontradas: {gaps_quantity}' if gaps_quantity > 0 else 'Nenhuma lacuna encontrada: todas as categorias têm a sequência completa entre o primeiro e o último período.',
        '',
        gaps.to_markdown(index=False),
    ]

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
        lines.append('')
        lines.append(
            'Na análise feita, o caso encontrado é o uso do símbolo de grau (°) no lugar '
            'do indicador ordinal (º). Os dois são visualmente iguais, mas são caracteres '
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
    inventory = build_inventory('raw')
    gaps = identify_gaps(inventory)
    name_inconsistencies = find_names_inconsistencies(inventory)
    delimiters = check_delimiter(inventory)

    sections = [
        header_section(),
        inventory_section(inventory),
        gaps_section(gaps),
        names_section(name_inconsistencies),
        delimiter_section(delimiters)
    ]

    write_report(sections, path=REPORT_PATH)

# endregion 

if __name__ == '__main__':
    main()
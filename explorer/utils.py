"""Funções auxiliares genéricas"""

# region Imports

# Biblioteca padrão
import csv
import time
from pathlib import Path

# Biblioteca de terceiros
import pandas as pd

# endregion

# region Impressão

class Report:
    """Prepara e grava o resultado da exploração"""

    def __init__(self):
        """Inicializador da classe."""

        # Linhas do relatório para salvar em markdown
        self.lines = []

    def line(self, text: str = '') -> None:
        """Mostra no terminal e guarda a linha"""

        # Mostra no terminal
        print(text)

        # Adiciona linha à lista
        self.lines.append(text)

    def title(self, text: str) -> None:
        """Mostra e guarda o título de uma etapa, centralizado numa linha de '='."""

        # Linha em branco para separar da etapa anterior
        self.line()

        # Texto centralizado numa linha de '='
        centered = f' {text} '.center(80, '=')

        # No terminal: só a linha de '='
        print(centered)

        # No arquivo: a mesma linha como título de markdown
        self.lines.append(f'## {centered}')

        # Linha em branco antes do conteúdo da etapa
        self.line()

    def table(self, df: pd.DataFrame, index: bool = True, floatfmt: str = '.1f') -> None:
        """Mostra no terminal e guarda um DataFrame como tabela markdown, seguida de uma linha em branco.

        O formato markdown deixa a tabela legível no terminal e no report.md.

        Args:
            df: Tabela a mostrar.
            index: Se o índice do DataFrame aparece como primeira coluna.
            floatfmt: Formato dos números decimais. Padrão: uma casa decimal.
        """

        # Converte para markdown, mostra e guarda
        self.line(df.to_markdown(index=index, floatfmt=floatfmt))

        # Linha em branco depois da tabela
        self.line()

    def save(self, path) -> None:
        """Salva o resultado da exploração em um markdown"""

        # Tira as linhas vazias: a separação entre os itens é feita no join abaixo
        lines = [line for line in self.lines if line]

        # Junta com uma linha em branco entre cada item, para o markdown não juntar linhas seguidas
        Path(path).write_text('\n\n'.join(lines) + '\n', encoding='utf-8')

# endregion

# region Formatação

def format_mb(value: float) -> str:
    """Formata um tamanho em MB como texto legível.

    Usa GB quando o valor passa de 1024 MB e MB caso contrário,
    sempre com duas casas decimais.

    Args:
        value: Tamanho em megabytes.

    Returns:
        Texto com o valor e a unidade.
    """

    return f"{value/1024:.2f} GB" if value > 1024 else f"{value:.2f} MB"

# endregion

# region Leitura dos arquivos

def find_delimiter(path, sample_size= 64 * 1024) -> str | None:
    """Encontra o delimitador de um arquivo

    Usa a classe Sniffer da biblioteca csv para procurar o delimitador,
    entre os delimitadores passados para o método sniff. Retorna None se o sniffer não encontrar.

    Args:
        path: Caminho para o arquivo.\n
        sample_size: Quantidade de caracteres lidos no início do arquivo. Opcional

    Returns:
        O delimitador em formato str ou None

    """

    # Abre o arquivo passado no path
    with open(path, encoding='utf-8', newline='') as f:

        # Lê amostra
        sample = f.read(sample_size)

    try:

        # Restringe a candidatos plausíveis
        return csv.Sniffer().sniff(sample, delimiters=';,|\t').delimiter

    # Se o sniffer não encontrar o delimitador
    except csv.Error:

        # Não conseguiu decidir
        return None

def read_header(path) -> tuple[str, ...]:
    """Lê a primeira linha do arquivo e devolve os nomes das colunas."""

    # Abre o arquivo no caminho recebido
    with open(path, encoding='utf-8', newline='') as f:

        # Como o único delimitador encontrado durante a exploração foi ';', ele foi escolhido como padrão
        reader = csv.reader(f, delimiter=';')

        # Retorna uma tupla contendo apenas a primeira linha. Cada item é o cabeçalho de uma coluna
        return tuple(next(reader))

def find_date_shapes(column:pd.Series) -> dict:
    """Conta os formatos de data de uma coluna, sem supor nenhum formato.

    Troca cada dígito por 9, então datas escritas do mesmo jeito ficam iguais.
    Campos vazios ficam de fora porque já foram contados como nulos.

    Args:
        column: Coluna de datas, como texto.

    Returns:
        Dict com os formatos encontrados e a quantidade de linhas.
    """

    # Troca cada dígito por 9, o que sobra é o desenho do formato
    shapes = column.str.replace(pat=r'\d', repl='9', regex=True)

    # Conta as linhas de cada desenho e transforma em dicionário
    return shapes.value_counts().to_dict()

def count_date_failures(column: pd.Series, date_format: str) -> int:
    """Conta as datas que não convertem com o formato informado.

    Falha é o campo preenchido que vira NaT na conversão. Campo vazio
    também vira NaT, mas não conta, porque já foi contado como nulo.

    Args:
        column: Coluna de datas, como texto.
        date_format: Formato usado na conversão, como '%d/%m/%Y'.

    Returns:
        Quantidade de linhas que falharam.
    """

    # Converte para data. O que não seguir o formato vira NaT
    dates = pd.to_datetime(column, format=date_format, errors='coerce')

    # Falha: o texto estava preenchido e mesmo assim virou NaT
    return int((column.notna() & dates.isna()).sum())

def profile_file(path) -> dict:
    """Lê um arquivo uma vez e devolve tudo o que a exploração mede nele.

    Na leitura foi padronizado o uso do separador ';' e o encoding UTF-8
    para todos os arquivos, decisão tomada a partir da etapa de formato físico.

    Conta como ausente o campo vazio e o campo que só tem espaços.
    O read_csv já transforma o campo vazio em nulo, mas mantém o campo
    só com espaços como texto, então ele é contado à parte.

    Args:
        path: Caminho para o arquivo

    Returns:
        Dict com as medições. Chaves:
            'segundos': Tempo de leitura, em segundos. \n
            'memoria_mb': Memória ocupada pelo DataFrame do arquivo, em MB. \n
            'linhas': Quantidade de linhas do arquivo, sem o cabeçalho. \n
            'linhas_vazias': Quantidade de linhas com todos os campos ausentes. \n
            'nulos': Dict com o nome de cada coluna e a quantidade de valores ausentes. \n
            'datas': Dict com cada formato da Data da Coleta e a quantidade de linhas. \n
            'falhas_datas': Quantidade de datas que não convertem com '%d/%m/%Y'. \n
            'erro': Mensagem do erro, se a leitura falhar, ou None. \n

        Se a leitura falhar (ParserError ou UnicodeDecodeError), todas as
        medições vêm como None e 'erro' traz a mensagem.
    """

    # Inicia o contador antes de ler o arquivo
    start = time.perf_counter()

    try:

        # Lê o arquivo inteiro, com todas as colunas como texto
        df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8')

    # Se o arquivo não puder ser lido, devolve só a mensagem do erro
    except (pd.errors.ParserError, UnicodeDecodeError) as e:

        return {'segundos': None, 'memoria_mb': None, 'linhas': None, 'linhas_vazias': None, 'nulos': None, 'datas' : None, 'falhas_datas' : None, 'erro': str(e)}

    # Diferença entre o contador do final da leitura e o contador do começo
    seconds = time.perf_counter() - start

    # Memória ocupada pelo DataFrame do arquivo. Em MB
    memory_mb = df.memory_usage(deep=True).sum() / 1024 ** 2

    # Quantidade de linhas do DataFrame
    rows = len(df)

    # True onde o campo veio vazio (o read_csv transformou em nulo)
    empty = df.isna()

    # True onde o campo só tem espaços. isspace() é False para texto vazio, mas esse caso já está coberto pelo isna()
    blank = df.apply(lambda column: column.str.isspace())

    # Ausente é o campo vazio OU só com espaços
    missing = empty | blank

    # Soma os True de cada coluna e transforma em dicionário: nome da coluna -> quantidade
    nulls = missing.sum().to_dict()

    # Linhas em que todos os campos estão ausentes. all(axis=1) olha a linha inteira
    empty_rows = int(missing.all(axis=1).sum())

    # Formatos de data encontrados no arquivo.
    date_shapes = find_date_shapes(df['Data da Coleta'])

    # Datas que não convertem com o formato dia/mês/ano, o único encontrado na exploração
    date_failures = count_date_failures(df['Data da Coleta'], '%d/%m/%Y')

    return {'segundos': seconds, 'memoria_mb': memory_mb, 'linhas': rows, 'linhas_vazias': empty_rows, 'nulos': nulls, 'datas' : date_shapes, 'falhas_datas' : date_failures, 'erro': None}

# endregion

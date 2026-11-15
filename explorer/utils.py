"""Funções auxiliares genéricas"""

# Biblioteca padrão
import csv
import time

# Biblioteca de terceiros
import pandas as pd

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

def find_delimiter(path, sample_size= 64 * 1024) -> str | None:
    """Encontra o delimitador de um arquivo
    
    Usa a classe Sniffer da biblioteca csv para procurar o delimitador, 
    entre os delimitadores passados para o método sniff. Retorna None se o sniffer não encontrar.
    
    Args:
        path: Caminho para o arquivo
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

def read_file_stats(path) -> dict:
    """Lê um arquivo e retorna as estatísticas.
    
    Na leitura foi padronizado o uso do separador ';' 
    e o enconding UTF-8 para todos os arquivos. Decisão tomada
    pelo resultado da exploração anterior.
    
    Args:
        path: Caminho para o arquivo
    
    Returns:
        Dict com os status. Chaves:
            'segundos': Tempo de leitura.
            'memoria_mb': Espaço ocupado pelo DataFrame do arquivo.
            'linhas': Quantidade de linhas do DataFrame do arquivo.
            'erro': Código de erro da leitura, caso nenhum então None.
    """

    # Inicia o contador antes de ler o arquivo
    start = time.perf_counter()

    try:
    
        df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8')
    
    except (pd.errors.ParserError, UnicodeDecodeError) as e:
    
        return {"segundos": None, "memoria_mb": None, "linhas": None, "erro": str(e)}

    # Diferença entre o contador do final da leitura e o contador do começo
    seconds = time.perf_counter() - start

    # Memória ocupada pelo DataFrame do arquivo. Em MB
    memory_mb = df.memory_usage(deep=True).sum() / 1024 ** 2

    # Quantidade de linhas do DataFrame
    rows = len(df)

    return {"segundos": seconds, "memoria_mb": memory_mb, "linhas": rows, "erro": None}
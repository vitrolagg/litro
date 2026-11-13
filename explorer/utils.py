"""Funções auxiliares genéricas"""

import csv

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
import requests
from bs4 import BeautifulSoup
import os
import time
import codecs
import shutil
import zipfile


# Diretório onde os arquivos serão salvos
dir_name = "raw"

ENCODINGS = ["utf-8-sig", "cp1252", "latin-1"]

def find_encoding(path: str) -> str:
    """Descobre em qual encoding o arquivo está"""

    for enc in ENCODINGS:

        # Decodificador incremental para este teste
        decoder = codecs.getincrementaldecoder(enc)()

        try:

            # Abre em modo binário
            with open(path, 'rb') as f:

                while True:

                    # Lê a cada 1 MB
                    chunk = f.read(1024 * 1024)

                    # Se o chunk vier vazio (final do arquivo)
                    if not chunk:

                        # Sai do loop
                        break

                    # Tenta decodificar o chunk. Lança UnicodeDecodeError se tiver byte inválido.
                    decoder.decode(chunk)

                # Fim do arquivo. Lança exceção se estiver esperando o resto de um caractere incompleto
                decoder.decode(b"", final=True)

            # Quando chega aqui, o arquivo é válido e a função retorna
            return enc

        # O encoding testado não serviu
        except UnicodeDecodeError:

            # Testa o próximo da lista
            continue

    # Latin-1 aceita qualquer coisa, então o código nunca deve chegar aqui
    return "latin-1"


def convert_to_utf8(origin: str, destination: str, encoding: str) -> None:
    """Lê o arquivo recebido no encoding informado e grava em UTF-8"""

    # Abre os arquivos de origem e de destino, nos modos de leitura e de escrita. A conversão do encoding acontece aqui. 
    with open(origin, 'r', encoding=encoding, newline="") as fin, open(destination, "w", encoding="utf-8", newline="") as fout: # Parâmetro newline desliga a tradução das quebras de linha

        # Copia 1 MB por vez, de um arquivo para o outro
        shutil.copyfileobj(fin, fout, 1024 * 1024)

def extract_csv_from_zip(path: str, destination: str) -> None:
    """Extrai o CSV de dentro do ZIP para o destino (sem converter)"""

    # Abre o ZIP recebido
    with zipfile.ZipFile(path) as z:

        # Lista todos os arquivos CSV dentro do zip
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]

        # Abre o csv de origem e o de destino. O de destino em escrita no modo binário
        with z.open(csvs[0]) as fin, open(destination, "wb") as fout:

            # Copia o conteúdo, 1 MB por vez
            shutil.copyfileobj(fin, fout, 1024 * 1024)

def do_request(name: str, cat: str, link: str) -> None:
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Cria os diretórios
    os.makedirs(dir_name, exist_ok=True)
    os.makedirs(f"{dir_name}/{cat}", exist_ok=True)
    
    # Caminho final exato para o arquivo
    dir_path = f"{dir_name}/{cat}/{name}.csv"

    # Arquivo temporário para os bytes crus
    temp_path = dir_path + ".part"

    print(f"Iniciando download do arquivo {name}")

    # Flag que indica se o download terminal
    success = False 

    # Devido a instabilidade da rede, foi escolhido um número máximo de tentativas maior. Para garantir que todos os arquivos serão extraídos em uma única execução.
    sleeping = 10
    for attempt in range(15):
        
        try:
            # stream=True baixa sem carregar tudo na memória RAM de uma vez
            response = requests.get(link, stream=True, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Salva os bytes crus no arquivo temporário
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)


            # Verifica se o arquivo salvo foi um ZIP
            if zipfile.is_zipfile(temp_path):
                print(f"Arquivo {name} veio compactado (ZIP), extraindo CSV")

                # Caminho do CSV extraído
                extracted_csv = temp_path + ".unzip"

                # Extrai o csv de dentro do ZIP
                extract_csv_from_zip(temp_path, extracted_csv)

                # Substitui o arquivo compactado pelo CSV
                os.replace(extracted_csv, temp_path)

            # Descobre o encoding do arquivo
            encoding = find_encoding(temp_path)

            # Converte para utf-8
            convert_to_utf8(temp_path, dir_path, encoding)

            # Apaga o arquivo temporário
            os.remove(temp_path)

            print(f"Arquivo {name} salvo com sucesso em: {dir_path}")
            
            # Set na flag de sucesso
            success = True

            # Sai do loop de tentativas
            break 
            
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            print(f"Tentativa {attempt + 1} falhou. Tentando de novo em {sleeping}s...")

            # Aguarda antes da próxima tentativa
            time.sleep(sleeping)
            
            # Incrementa 5 segundos na espera
            sleeping += 5

    # Se estourou a quantidade de tentativas e a flag continua False, avisa que falhou
    if not success:
        print(f"ERRO: Não foi possível baixar {name} após {attempt + 1} tentativas.")

# Url do site fonte de dados
url = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis"

print("Iniciando requisição na fonte de dados")

# Faz a requisição no site e extrai o html
response = requests.get(url)

print("Iniciando análise no html recebido")
# Analisa o documento HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Encontra a tag principal
elemento = soup.find(id="parent-fieldname-text")

if elemento:

    print("Tag principal encontrada")

    # 1. Encontra todos os <h3> dentro desse bloco
    tags_h3 = elemento.find_all('h3')
    
    # 2. Itera sobre cada <h3> encontrado
    for h3 in tags_h3:

        # Pega o texto do h3 (ex: "Combustíveis automotivos")
        nome_id = h3.get_text(strip=True)
        
        # Encontra o próximo elemento que seja um <ul> após o <h3>
        ul_seguinte = h3.find_next_sibling('ul')
        
        # Se a <ul> existir, adiciona o atributo 'id' a ela
        if ul_seguinte:
            ul_seguinte['id'] = nome_id

        # Separa a ul
        ul_combustiveis = soup.find(id=nome_id)

        # Se a tag existir
        if ul_combustiveis:
            
            # Encontra todas as tags <li> dentro da <ul>
            lista_de_lis = ul_combustiveis.find_all('li')
            
            # Itera sobre cada <li> encontrada
            for li in lista_de_lis:
            
                # Extrai o texto limpo do <li>
                legenda = li.get_text(strip=True).replace("\xa0", " ") # Faz o replace apra limpar o espaço não separável por um caractere de espaço comum
                
                # Se quiser extrair o link (href) que está dentro do <li>
                tag_a = li.find('a')
            
                if tag_a:
                    url = tag_a.get('href')

                    # Separador para organização visual dos logs
                    print("=" * 30)

                    # Chama a função de requisição dos links
                    do_request(name=legenda, cat=nome_id, link=url)

            print("Download dos arquivos concluído")
            
        else:
            print("A tag não foi encontrada.")


else:
    print("A tag não foi encontrada na página.")
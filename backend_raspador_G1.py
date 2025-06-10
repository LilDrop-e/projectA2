import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re
import json

def raspar_g1(paginas=3):
    """Raspagem detalhada do G1 com tratamento de erros robusto"""
    base_url = "https://g1.globo.com/ultimas-noticias/"
    noticias = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for pagina in range(1, paginas + 1):
        try:
            url = f"{base_url}index/feed/pagina-{pagina}.ghtml"
            resposta = requests.get(url, headers=headers, timeout=10)
            resposta.raise_for_status()
            
            sopa = BeautifulSoup(resposta.text, 'html.parser')
            links_noticias = sopa.find_all('a', class_='feed-post-link')

            for link in links_noticias[:15]:  # Limite por página para não sobrecarregar
                titulo = link.get_text(strip=True)
                url_noticia = link['href']
                
                # Verifica duplicatas
                if any(n['titulo'] == titulo for n in noticias):
                    continue
                
                # Processa detalhes da notícia
                data = extrair_data_noticia(url_noticia, headers)
                
                noticias.append({
                    'titulo': titulo,
                    'url': url_noticia,
                    'data': data,
                    'site': 'G1',
                    'secao': extrair_secao(url_noticia)
                })
                
                time.sleep(0.5)  # Delay entre requisições

            time.sleep(1)  # Delay entre páginas
            
        except Exception as e:
            print(f"Erro na página {pagina}: {str(e)}")
            continue
    
    return noticias

def extrair_data_noticia(url, headers):
    """Extrai data da página individual da notícia"""
    try:
        resposta = requests.get(url, headers=headers, timeout=5)
        if resposta.status_code == 200:
            sopa = BeautifulSoup(resposta.text, 'html.parser')
            
            # Tentativa 1: Meta tag
            meta_data = sopa.find('meta', property='article:published_time')
            if meta_data:
                return datetime.fromisoformat(meta_data['content'][:-1]).strftime('%Y-%m-%d')
            
            # Tentativa 2: Tag time
            time_tag = sopa.find('time')
            if time_tag and time_tag.has_attr('datetime'):
                return time_tag['datetime'].split('T')[0]
            
            # Tentativa 3: Texto da data
            data_texto = sopa.find('span', class_=re.compile('date|time', re.I))
            if data_texto:
                match = re.search(r'\d{2}/\d{2}/\d{4}', data_texto.get_text())
                if match:
                    return datetime.strptime(match.group(), '%d/%m/%Y').strftime('%Y-%m-%d')
    
    except Exception:
        pass
    
    return None

def extrair_secao(url):
    """Extrai seção da URL"""
    try:
        partes = url.split('/')
        if len(partes) > 3:
            return partes[3].replace('-', ' ').title()
    except Exception:
        pass
    return 'Geral'

def salvar_noticias(noticias, formato='json'):
    """Salva notícias em arquivo"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    nome_arquivo = f"noticias_g1_{timestamp}.{formato}"
    
    try:
        if formato == 'json':
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(noticias, f, ensure_ascii=False, indent=2)
        else:
            import csv
            with open(nome_arquivo, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=noticias[0].keys())
                writer.writeheader()
                writer.writerows(noticias)
                
        print(f"Notícias salvas em {nome_arquivo}")
        return nome_arquivo
    except Exception as e:
        print(f"Erro ao salvar arquivo: {str(e)}")
        return None

import requests
from bs4 import BeautifulSoup
import time
import datetime
import json
import re # Para correspondência de palavras inteiras (opcional, mas recomendado)

# --- Configurações Globais ---
BASE_URL_OLD_REDDIT = "https://old.reddit.com/r/brdev/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 MyBRDevScraper/0.1 (contato: seu_email@example.com)'
}

KEYWORDS_TECNOLOGIAS = [
    # Linguagens de Programação
    "Python", "JavaScript", "Java", "TypeScript", "C#", "Go", "Golang", "PHP", "Ruby", "Swift",
    "Kotlin", "Rust", "Elixir", "Dart", "Scala", "C++",
    # Frameworks e Bibliotecas (Frontend)
    "React", "React.js", "Angular", "Vue.js", "Next.js", "Svelte", "jQuery", "Flutter",
    "React Native",
    # Frameworks e Bibliotecas (Backend)
    "Node.js", "Express", "Express.js", "Spring", "Spring Boot", "Django", "Flask",
    "Ruby on Rails", "Rails", "Laravel", ".NET", "ASP.NET Core", "NestJS", "FastAPI",
    "Phoenix",
    # Bancos de Dados
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "SQLite", "Redis", "Microsoft SQL Server",
    "Oracle Database", "Cassandra", "Elasticsearch",
    # Cloud & DevOps
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud Platform",
    "Docker", "Kubernetes", "k8s", "Terraform", "Ansible", "Jenkins", "Git",
    "GitHub Actions", "GitLab CI",
    # Outras Ferramentas e Conceitos
    "GraphQL", "REST", "RESTful APIs", "Linux", "Apache Kafka", "Kafka", "RabbitMQ",
    "Nginx", "Apache", "WordPress", "WebAssembly", "Wasm"
]

# Normalizar keywords para lower case para facilitar a busca
KEYWORDS_TECNOLOGIAS_LOWER = [kw.lower() for kw in KEYWORDS_TECNOLOGIAS]
# Criar um mapeamento de keyword lower para original para guardar o nome correto
KEYWORDS_MAP = {kw.lower(): kw for kw in KEYWORDS_TECNOLOGIAS}


DATA_INICIO_FILTRO = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
# Data atual (simulada para o contexto do projeto)
DATA_ATUAL_PROJETO = datetime.datetime(2025, 5, 23, tzinfo=datetime.timezone.utc)

DADOS_COLETADOS = []
contador_instancias_globais = 0

# --- Funções Auxiliares ---

def fetch_page(url):
    """Busca o conteúdo de uma URL."""
    print(f"Buscando URL: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20) # Timeout aumentado
        response.raise_for_status()
        time.sleep(2.5) # Pausa um pouco maior
        return BeautifulSoup(response.content, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar {url}: {e}")
        return None

def parse_reddit_time(time_str):
    """Converte string de data do Reddit para objeto datetime."""
    if not time_str:
        return None
    try:
        # Formato comum em 'old.reddit.com' no atributo 'datetime' da tag <time>
        return datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except ValueError:
        print(f"Alerta: Não foi possível parsear a data no formato ISO: {time_str}. Tentar outros métodos se necessário.")
        # Aqui você poderia adicionar lógica para formatos como "X hours ago",
        # mas 'old.reddit' geralmente fornece o timestamp completo.
        return None

def buscar_tecnologias_no_texto(texto):
    """Busca keywords de tecnologias no texto fornecido."""
    if not texto:
        return []
    encontradas_originais = set()
    texto_lower = texto.lower()
    for kw_lower in KEYWORDS_TECNOLOGIAS_LOWER:
        # Usar regex com \b para encontrar palavras inteiras e evitar falsos positivos
        # Ex: evitar que "java" seja encontrado em "javascript" se "javascript" não for uma keyword por si só
        # ou que "go" seja encontrado em "gopher".
        padrao = r'\b' + re.escape(kw_lower) + r'\b'
        if re.search(padrao, texto_lower):
            encontradas_originais.add(KEYWORDS_MAP[kw_lower]) # Adiciona o nome original da tecnologia
    return list(encontradas_originais)

def adicionar_instancia_json(id_sufixo_item, url_reddit, data_ocorrencia, tipo_item, tecnologia, snippet, score_str):
    """Adiciona uma nova instância de menção à lista DADOS_COLETADOS."""
    global contador_instancias_globais
    contador_instancias_globais += 1

    # Processar score
    current_score = 0
    if score_str:
        match = re.search(r'(-?\d+)', score_str) # Procura por números, incluindo negativos
        if match:
            current_score = int(match.group(1))

    instancia = {
        "id_instancia": f"brdev_mention_{DATA_ATUAL_PROJETO.strftime('%Y%m%d')}_{id_sufixo_item.replace('-', '_')}_{contador_instancias_globais}",
        "url_reddit_fonte": url_reddit,
        "data_reddit_ocorrencia": data_ocorrencia.isoformat() if data_ocorrencia else None,
        "tipo_item_reddit": tipo_item,
        "tecnologia_mencionada": tecnologia,
        "snippet_contexto_reddit": snippet.strip()[:250], # Limita e remove espaços extras
        "score_item_reddit": current_score,
        "github_metrica_valor": None, # Placeholder - Será preenchido na Fase 4
        "github_metrica_descricao": "Número de repositórios com push desde 01/01/2025", # Exemplo
        "url_github_busca_metrica": None, # Placeholder
        "data_coleta_metrica_github": None, # Placeholder
        "data_processamento_instancia": DATA_ATUAL_PROJETO.now(datetime.timezone.utc).isoformat()
    }
    DADOS_COLETADOS.append(instancia)
    print(f"  Instância {contador_instancias_globais}: {tecnologia} ({tipo_item}) em {url_reddit}")

    if contador_instancias_globais % 20 == 0: # Salva a cada 20 instâncias
        salvar_dados_parciais(DADOS_COLETADOS, "reddit_data_parcial.json")

def salvar_dados_parciais(dados, nome_arquivo):
    """Salva os dados coletados em um arquivo JSON."""
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        print(f"Dados parciais ({len(dados)} instâncias) salvos em {nome_arquivo}")
    except IOError as e:
        print(f"Erro ao salvar dados parciais: {e}")

# --- Funções Principais de Scraping ---

def processar_comentarios_post(soup_post_pagina, url_post_original, data_limite_inferior):
    """Processa os comentários de uma página de post."""
    comment_area = soup_post_pagina.find('div', class_='commentarea') # !!! VERIFIQUE ESTE SELETOR !!!
    if not comment_area:
        return

    # !!! VERIFIQUE ESTE SELETOR PARA OS BLOCOS DE COMENTÁRIOS !!!
    # 'limit' é para não pegar comentários demais de um único post em testes iniciais
    comentarios_divs = comment_area.find_all('div', class_=re.compile(r'\bcomment\b'), recursive=False, limit=100)

    for i, comment_div in enumerate(comentarios_divs):
        # Pular se for o 'load more comments' ou se não for um comentário de fato
        if not comment_div.get('data-type') == 'comment' or 'deleted' in comment_div.get('class', []) or 'spam' in comment_div.get('class', []):
            continue

        # Permalink do comentário (!!! VERIFIQUE ESTE SELETOR !!!)
        permalink_tag = comment_div.find('a', class_='bylink') # Ou similar que contenha o link para o comentário
        comment_permalink_fragment = permalink_tag['href'] if permalink_tag and permalink_tag.has_attr('href') else f"#comment_manual_id_{i}"
        full_comment_url = url_post_original.split('?')[0].rstrip('/') + comment_permalink_fragment # Remove query params do post url

        # Texto do comentário (!!! VERIFIQUE ESTE SELETOR !!!)
        comment_text_tag = comment_div.find('div', class_='usertext-body')
        comment_text = comment_text_tag.get_text(separator=' ', strip=True) if comment_text_tag else ""

        # Data do comentário (!!! VERIFIQUE ESTE SELETOR !!!)
        time_tag = comment_div.find('time')
        comment_datetime_str = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
        comment_date_obj = parse_reddit_time(comment_datetime_str)

        # Score do comentário (!!! VERIFIQUE ESTE SELETOR !!!)
        score_tag = comment_div.find('span', class_='score')
        comment_score_str = score_tag.get_text(strip=True) if score_tag else "0 points"
        
        if not comment_date_obj or comment_date_obj < data_limite_inferior:
            # print(f"    Comentário antigo ou sem data: {comment_date_obj}")
            continue # Pula comentários antigos ou sem data válida

        tecnologias_no_comentario = buscar_tecnologias_no_texto(comment_text)
        for tech in tecnologias_no_comentario:
            adicionar_instancia_json(
                id_sufixo_item=comment_div.get('data-fullname', f"c_{i}"), # ID do comentário
                url_reddit=full_comment_url,
                data_ocorrencia=comment_date_obj,
                tipo_item="comentario",
                tecnologia=tech,
                snippet=comment_text,
                score_str=comment_score_str
            )

def processar_post_individual(post_url, post_title_listagem, post_date_obj_listagem, post_score_listagem_str):
    """Processa uma página de post individual e seus comentários."""
    print(f"  Processando Post: {post_url}")
    soup_post_pagina = fetch_page(post_url)
    if not soup_post_pagina:
        return

    # Corpo do Post (!!! VERIFIQUE ESTE SELETOR !!!)
    # O conteúdo do post original (selftext) pode estar em uma div com classes como 'expando' ou diretamente no 'entry'
    post_content_div = soup_post_pagina.find('div', class_='sitetable', id=re.compile(r'siteTable_t3_.*')) # Container do post
    post_body_text = ""
    if post_content_div:
        # !!! VERIFIQUE ESTE SELETOR PARA O CORPO DO POST !!!
        usertext_div = post_content_div.find('div', class_='usertext-body') # Dentro do 'entry'
        if usertext_div:
            post_body_text = usertext_div.get_text(separator=' ', strip=True)

    texto_completo_post = post_title_listagem + " " + post_body_text
    tecnologias_no_post = buscar_tecnologias_no_texto(texto_completo_post)

    for tech in tecnologias_no_post:
        adicionar_instancia_json(
            id_sufixo_item=post_url.split('/')[-3] if len(post_url.split('/')) > 3 else "post_unk", # ID do post
            url_reddit=post_url,
            data_ocorrencia=post_date_obj_listagem,
            tipo_item="post",
            tecnologia=tech,
            snippet=post_title_listagem + (" " + post_body_text[:100] + "..." if post_body_text else ""),
            score_str=post_score_listagem_str
        )
    
    # Processar comentários da página do post
    processar_comentarios_post(soup_post_pagina, post_url, DATA_INICIO_FILTRO)


def scraper_r_brdev(url_inicial, max_paginas_listagem=5):
    """Função principal para raspar o r/brdev."""
    url_atual_listagem = url_inicial
    paginas_listagem_processadas = 0
    parar_paginacao_listagem = False

    print(f"Iniciando scraper para r/brdev. Data Limite Inferior: {DATA_INICIO_FILTRO.date()}")

    while url_atual_listagem and paginas_listagem_processadas < max_paginas_listagem and not parar_paginacao_listagem:
        print(f"\nProcessando página de listagem: {url_atual_listagem} (Página {paginas_listagem_processadas + 1})")
        soup_pagina_listagem = fetch_page(url_atual_listagem)
        if not soup_pagina_listagem:
            break

        # Encontrar todos os contêineres de posts (!!! VERIFIQUE ESTE SELETOR !!!)
        posts_divs = soup_pagina_listagem.find_all('div', class_='thing', attrs={'data-domain': lambda x: x != 'i.redd.it'}) # Ignora posts de imagem direta

        if not posts_divs:
            print("Nenhum post encontrado na página de listagem. Verifique os seletores.")
            break

        for post_div in posts_divs:
            if 'promoted' in post_div.get('class', []): # Pular posts promovidos
                continue

            # Título e Link do Post (!!! VERIFIQUE ESTES SELETORES !!!)
            title_tag = post_div.find('a', class_='title')
            post_title = title_tag.get_text(strip=True) if title_tag else "N/A"
            post_url_relativo = title_tag['href'] if title_tag and title_tag.has_attr('href') else None

            if not post_url_relativo or not post_url_relativo.startswith('/r/brdev/comments/'): # Ignorar links externos na listagem
                continue
            post_url_completo = "https://old.reddit.com" + post_url_relativo

            # Data do Post (!!! VERIFIQUE ESTE SELETOR !!!)
            time_tag = post_div.find('time', class_='live-timestamp') # Ou apenas 'time'
            post_datetime_str = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
            post_date_obj = parse_reddit_time(post_datetime_str)

            # Score do Post (!!! VERIFIQUE ESTE SELETOR !!!)
            score_tag = post_div.find('div', class_=re.compile(r'\bscore\b')) # Ex: 'score unvoted', 'score likes', 'score dislikes'
            post_score_str = score_tag.get_text(strip=True) if score_tag else "0 points"
            
            if not post_date_obj:
                print(f"Post sem data válida: {post_title}. Pulando.")
                continue

            if post_date_obj >= DATA_INICIO_FILTRO:
                print(f"\nPost dentro do período: {post_title} ({post_date_obj.date()})")
                processar_post_individual(post_url_completo, post_title, post_date_obj, post_score_str)
            elif post_date_obj < DATA_INICIO_FILTRO:
                print(f"Post antigo encontrado na listagem ({post_title} - {post_date_obj.date()}). Parando paginação.")
                parar_paginacao_listagem = True
                break # Sai do loop de posts desta página
        
        if parar_paginacao_listagem:
            break # Sai do loop de páginas

        # Encontrar o link da próxima página de listagem (!!! VERIFIQUE ESTE SELETOR !!!)
        next_button_span = soup_pagina_listagem.find('span', class_='next-button')
        if next_button_span and next_button_span.find('a'):
            url_atual_listagem = next_button_span.find('a')['href']
        else:
            print("Fim da paginação da listagem ou não encontrou botão 'next'.")
            url_atual_listagem = None
        
        paginas_listagem_processadas += 1
        if paginas_listagem_processadas >= max_paginas_listagem:
            print(f"Limite máximo de {max_paginas_listagem} páginas de listagem atingido.")


# --- Execução Principal ---
if __name__ == "__main__":
    print("Iniciando scraper do Reddit para r/brdev...")
    try:
        scraper_r_brdev(BASE_URL_OLD_REDDIT, max_paginas_listagem=3) # Teste com 3 páginas de listagem
    except Exception as e:
        print(f"Ocorreu um erro geral no script: {e}")
    finally:
        salvar_dados_parciais(DADOS_COLETADOS, "reddit_data_FINAL.json")
        print(f"Scraping finalizado. Total de {len(DADOS_COLETADOS)} instâncias coletadas.")
        if not DADOS_COLETADOS:
            print("ALERTA: Nenhuma instância foi coletada. Verifique os seletores e a lógica do scraper.")
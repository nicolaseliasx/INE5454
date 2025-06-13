import requests
from bs4 import BeautifulSoup
import time
import datetime
import json
import re

# --- 1. Configurações Globais ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
KEYWORDS_TECNOLOGIAS = [
    "Python", "JavaScript", "Java", "TypeScript", "C#", "Go", "Golang", "PHP", "Ruby", "Swift", "Kotlin", "Rust", "Elixir", "Dart", "Scala", "C++",
    "React", "React.js", "Angular", "Vue.js", "Next.js", "Svelte", "jQuery", "Flutter", "React Native",
    "Node.js", "Express", "Express.js", "Spring", "Spring Boot", "Django", "Flask", "Ruby on Rails", "Rails", "Laravel", ".NET", "ASP.NET Core", "NestJS", "FastAPI", "Phoenix",
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "SQLite", "Redis", "Microsoft SQL Server", "Oracle Database", "Cassandra", "Elasticsearch",
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud Platform",
    "Docker", "Kubernetes", "k8s", "Terraform", "Ansible", "Jenkins", "Git", "GitHub Actions", "GitLab CI",
    "GraphQL", "REST", "RESTful APIs", "Linux", "Apache Kafka", "Kafka", "RabbitMQ", "Nginx", "Apache", "WordPress", "WebAssembly", "Wasm"
]
DATA_INICIO_FILTRO = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)

# --- 2. Scraper do Reddit ---
class RedditScraper:
    """
    Classe unificada e robusta para extrair dados do old.reddit.com,
    com lógica de retentativas e tratamento de bloqueios (429).
    """
    def __init__(self, headers):
        self.headers = headers
        self.base_url = "https://old.reddit.com"

    def _get_soup(self, url):
        max_tentativas = 5
        for tentativa in range(max_tentativas):
            try:
                print(f"    (Tentativa {tentativa + 1}/{max_tentativas}) Buscando: {url}")
                response = requests.get(url, headers=self.headers, timeout=30)

                if response.status_code == 429:
                    print(f"  -> AVISO: Bloqueado pelo Reddit (429). Esperando 10 minutos...")
                    time.sleep(600)
                    continue

                response.raise_for_status()
                time.sleep(4) 
                return BeautifulSoup(response.content, 'lxml')

            except requests.exceptions.RequestException as e:
                print(f"  -> ERRO ao buscar a página na tentativa {tentativa + 1}: {e}")
                if tentativa < max_tentativas - 1:
                    print("     ...esperando 30 segundos antes de tentar novamente.")
                    time.sleep(30)
                else:
                    print(f"     ...desistindo da URL {url} após {max_tentativas} tentativas.")
                    return None
        return None

    def get_posts_from_listing_page(self, listing_url):
        print(f"Buscando posts em: {listing_url}")
        soup = self._get_soup(listing_url)
        if not soup: return [], None
        
        posts_data, post_containers = [], soup.find_all('div', class_='thing')
        for post in post_containers:
            if 'stickied' in post.get('class', []) or 'promoted' in post.get('class', []): continue
            title_tag = post.select_one('p.title > a')
            if not title_tag: continue
            post_href = title_tag['href']
            post_url = post_href if post_href.startswith('http') else self.base_url + post_href
            score_tag, time_tag = post.select_one('div.score.unvoted'), post.find('time')
            posts_data.append({'title': title_tag.get_text(strip=True), 'url': post_url, 'score_str': score_tag.get_text(strip=True) if score_tag else '0', 'date_str': time_tag['datetime'] if time_tag else None})
        
        next_page_tag = soup.select_one('span.next-button a')
        return posts_data, next_page_tag['href'] if next_page_tag else None

    def get_post_and_comments_details(self, post_url):
        soup = self._get_soup(post_url)
        if not soup: return None, []
        
        post_body_tag = soup.select_one('div.expando .usertext-body')
        post_body = post_body_tag.get_text(separator=' ', strip=True) if post_body_tag else ""
        comments_data, comment_containers = [], soup.select('div.commentarea > .comment')
        for comment in comment_containers:
            if 'automoderator' in comment.select_one('a.author', '').get_text(strip=True).lower(): continue
            text_tag, time_tag, permalink_tag = comment.select_one('form .usertext-body'), comment.find('time'), comment.select_one('a.bylink')
            comments_data.append({'id_suffix': comment.get('data-fullname', ''), 'url': permalink_tag['href'] if permalink_tag else post_url, 'text': text_tag.get_text(separator=' ', strip=True) if text_tag else "", 'date_str': time_tag['datetime'] if time_tag else None, 'score_str': "0 points"})
        
        return post_body, comments_data


# --- 3. Scraper do GitHub ---
class GitHubScraper:
    """Classe focada em extrair métricas de repositórios do GitHub."""
    def __init__(self, headers):
        self.headers = headers

    def get_repo_count(self, tecnologia):
        ano_anterior = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        query = f'"{tecnologia}" pushed:>{ano_anterior}'
        url = f"https://github.com/search?q={requests.utils.quote(query)}&type=repositories"
        
        print(f"Buscando métrica para: {tecnologia}...")
        time.sleep(7)

        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            data_script = soup.find('script', attrs={'data-target': 'react-app.embeddedData'})
            if data_script:
                data = json.loads(data_script.text)
                count = data.get('payload', {}).get('result_count', 0)
                print(f"  -> SUCESSO: Encontrado {count} repositórios.")
                return {"valor": count, "url_busca": url, "data_coleta": datetime.datetime.now(datetime.timezone.utc).isoformat()}

        except requests.exceptions.RequestException as e:
            print(f"    -> ERRO: Falha na requisição para '{tecnologia}': {e}")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"    -> ERRO: Falha ao processar o JSON do GitHub para '{tecnologia}': {e}")
        
        print(f"  -> ALERTA: Não foi possível extrair a contagem para '{tecnologia}'. Retornando 0.")
        return {"valor": 0, "url_busca": url, "data_coleta": datetime.datetime.now(datetime.timezone.utc).isoformat()}

# --- 4. Funções Auxiliares ---
def parse_iso_date(date_str):
    if not date_str: return None
    try: return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError: return None

def find_technologies_in_text(text, keywords_map):
    if not text: return []
    encontradas_originais = set()
    texto_lower = text.lower()
    for kw_lower, kw_original in keywords_map.items():
        if re.search(r'\b' + re.escape(kw_lower) + r'\b', texto_lower, re.IGNORECASE):
            encontradas_originais.add(kw_original)
    return list(encontradas_originais)

# --- 5. Coletor e Montador de Dados ---
class DataCollector:
    """Classe responsável por montar e salvar o JSON final."""
    def __init__(self):
        self.collected_data, self.instance_counter = [], 0

    def add_mention(self, mention_data, github_data):
        self.instance_counter += 1
        match = re.search(r'(-?\d+)', mention_data.get('score_str', ''))
        current_score = int(match.group(1)) if match else 0
        instancia = {
            "id_instancia": f"brdev_mention_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}_{self.instance_counter}",
            "url_reddit_fonte": mention_data['url_reddit'],
            "data_reddit_ocorrencia": mention_data['data_ocorrencia'].isoformat(),
            "tipo_item_reddit": mention_data['tipo_item'],
            "tecnologia_mencionada": mention_data['tecnologia'],
            "snippet_contexto_reddit": mention_data['snippet'].strip()[:250],
            "score_item_reddit": current_score,
            "github_metrica_valor": github_data['valor'],
            "github_metrica_descricao": "Número de repositórios com push no último ano",
            "url_github_busca_metrica": github_data['url_busca'],
            "data_coleta_metrica_github": github_data['data_coleta'],
            "data_processamento_instancia": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.collected_data.append(instancia)

    def save_to_json(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f: json.dump(self.collected_data, f, ensure_ascii=False, indent=4)
            print(f"\nColetor: Dados ({len(self.collected_data)} instâncias) salvos em {filename}")
        except IOError as e: print(f"Coletor: Erro ao salvar dados: {e}")

# --- 6. Orquestração Principal ---
if __name__ == "__main__":
    print("Iniciando scraper integrado (Reddit + GitHub)...")
    reddit_scraper = RedditScraper(headers=HEADERS)
    github_scraper = GitHubScraper(headers=HEADERS)
    collector = DataCollector()
    keywords_map = {kw.lower(): kw for kw in KEYWORDS_TECNOLOGIAS}
    
    reddit_mentions = []
    
    try:
        # FASE 1: Coleta rápida de todas as menções do Reddit
        print("\n--- FASE 1: Coletando menções do Reddit ---")
        current_url, max_pages = "https://old.reddit.com/r/brdev/", 1
        for page_num in range(max_pages):
            if not current_url: break
            print(f"\n--- Processando Página do Reddit {page_num + 1} ---")
            posts, next_page_url = reddit_scraper.get_posts_from_listing_page(current_url)
            for post in posts:
                if "/r/brdev/comments/" not in post['url']: continue
                post_date = parse_iso_date(post['date_str'])
                if not post_date or post_date < DATA_INICIO_FILTRO: continue
                post_body, comments = reddit_scraper.get_post_and_comments_details(post['url'])
                if post_body is None: continue
                full_post_text = post['title'] + " " + post_body
                for tech in find_technologies_in_text(full_post_text, keywords_map):
                    reddit_mentions.append({'tecnologia': tech, 'url_reddit': post['url'], 'data_ocorrencia': post_date, 'tipo_item': "post", 'snippet': full_post_text, 'score_str': post['score_str']})
                for comment in comments:
                    comment_date = parse_iso_date(comment['date_str'])
                    if not comment_date or comment_date < DATA_INICIO_FILTRO: continue
                    for tech in find_technologies_in_text(comment['text'], keywords_map):
                        reddit_mentions.append({'tecnologia': tech, 'url_reddit': comment['url'], 'data_ocorrencia': comment_date, 'tipo_item': "comentario", 'snippet': comment['text'], 'score_str': comment['score_str']})
            current_url = next_page_url
        
        # FASE 2: Coleta lenta e controlada dos dados do GitHub
        print("\n--- FASE 2: Coletando métricas do GitHub em lote ---")
        unique_techs = sorted(list(set(mention['tecnologia'] for mention in reddit_mentions)))
        print(f"Encontradas {len(unique_techs)} tecnologias únicas para buscar no GitHub.")
        github_cache = {tech: github_scraper.get_repo_count(tech) for tech in unique_techs}
            
        # FASE 3: Montagem final do JSON
        print("\n--- FASE 3: Montando o dataset final ---")
        for mention in reddit_mentions:
            if github_data := github_cache.get(mention['tecnologia']):
                collector.add_mention(mention, github_data)
        print("\nProcesso de coleta finalizado com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.save_to_json("dataset_completo.json")
        if collector.instance_counter == 0:
            print("ALERTA: Nenhuma instância do Reddit foi coletada.")
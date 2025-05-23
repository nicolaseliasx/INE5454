import requests
from bs4 import BeautifulSoup
import time
import datetime
import json
import re

# --- Configurações (poderiam estar em um config.py) ---
BASE_URL_OLD_REDDIT = "https://old.reddit.com/r/brdev/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 MyBRDevScraper/0.1 (contato: seu_email@example.com)'
}
KEYWORDS_TECNOLOGIAS = [
    "Python", "JavaScript", "Java", "TypeScript", "C#", "Go", "Golang", "PHP", "Ruby", "Swift",
    "Kotlin", "Rust", "Elixir", "Dart", "Scala", "C++", "React", "React.js", "Angular", "Vue.js",
    "Next.js", "Svelte", "jQuery", "Flutter", "React Native", "Node.js", "Express", "Express.js",
    "Spring", "Spring Boot", "Django", "Flask", "Ruby on Rails", "Rails", "Laravel", ".NET",
    "ASP.NET Core", "NestJS", "FastAPI", "Phoenix", "PostgreSQL", "Postgres", "MySQL", "MongoDB",
    "SQLite", "Redis", "Microsoft SQL Server", "Oracle Database", "Cassandra", "Elasticsearch",
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "GCP", "Google Cloud Platform",
    "Docker", "Kubernetes", "k8s", "Terraform", "Ansible", "Jenkins", "Git", "GitHub Actions",
    "GitLab CI", "GraphQL", "REST", "RESTful APIs", "Linux", "Apache Kafka", "Kafka", "RabbitMQ",
    "Nginx", "Apache", "WordPress", "WebAssembly", "Wasm"
]
DATA_INICIO_FILTRO = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
DATA_ATUAL_PROJETO = datetime.datetime(2025, 5, 23, tzinfo=datetime.timezone.utc) # Simulação


class RedditCrawler:
    def __init__(self, headers):
        self.headers = headers

    def fetch_page_soup(self, url):
        print(f"Crawler: Buscando URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            time.sleep(2.5) # Pausa
            return BeautifulSoup(response.content, 'lxml')
        except requests.exceptions.RequestException as e:
            print(f"Crawler: Erro ao buscar {url}: {e}")
            return None

    def get_next_listing_page_url(self, soup_listing_page):
        if not soup_listing_page: return None
        # !!! VERIFIQUE ESTE SELETOR !!!
        next_button_span = soup_listing_page.find('span', class_='next-button')
        if next_button_span and next_button_span.find('a'):
            return next_button_span.find('a')['href']
        return None


class RedditScraperParser:
    def __init__(self, keywords_list):
        self.keywords_lower = [kw.lower() for kw in keywords_list]
        self.keywords_map = {kw.lower(): kw for kw in keywords_list}

    def _parse_reddit_time(self, time_str):
        if not time_str: return None
        try:
            return datetime.datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            return None # Lidar com outros formatos se necessário

    def find_technologies_in_text(self, text):
        if not text: return []
        encontradas_originais = set()
        texto_lower = text.lower()
        for kw_lower in self.keywords_lower:
            padrao = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(padrao, texto_lower):
                encontradas_originais.add(self.keywords_map[kw_lower])
        return list(encontradas_originais)

    def parse_post_items_from_listing(self, soup_listing_page):
        """Extrai infos básicas dos posts de uma página de listagem."""
        if not soup_listing_page: return []
        parsed_posts = []
        # !!! VERIFIQUE ESTE SELETOR PARA OS BLOCOS DE POSTS !!!
        posts_divs = soup_listing_page.find_all('div', class_='thing', attrs={'data-domain': lambda x: x != 'i.redd.it'})

        for post_div in posts_divs:
            if 'promoted' in post_div.get('class', []): continue

            # !!! VERIFIQUE ESTES SELETORES !!!
            title_tag = post_div.find('a', class_='title')
            post_title = title_tag.get_text(strip=True) if title_tag else "N/A"
            post_url_relativo = title_tag['href'] if title_tag and title_tag.has_attr('href') else None

            if not post_url_relativo or not post_url_relativo.startswith('/r/brdev/comments/'):
                continue
            post_url_completo = "https://old.reddit.com" + post_url_relativo

            time_tag = post_div.find('time') # Ou 'time', class_='live-timestamp'
            post_datetime_str = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
            post_date_obj = self._parse_reddit_time(post_datetime_str)

            score_tag = post_div.find('div', class_=re.compile(r'\bscore\b'))
            post_score_str = score_tag.get_text(strip=True) if score_tag else "0 points"

            if post_date_obj: # Apenas adiciona se tiver data válida
                parsed_posts.append({
                    "title": post_title,
                    "url": post_url_completo,
                    "date_obj": post_date_obj,
                    "score_str": post_score_str
                })
        return parsed_posts

    def parse_post_page_details(self, soup_post_page):
        """Extrai o corpo do texto de um post."""
        if not soup_post_page: return ""
        # !!! VERIFIQUE ESTE SELETOR !!! (Container do post)
        post_content_div = soup_post_page.find('div', class_='sitetable', id=re.compile(r'siteTable_t3_.*'))
        post_body_text = ""
        if post_content_div:
             # !!! VERIFIQUE ESTE SELETOR !!! (Corpo do post dentro do container)
            usertext_div = post_content_div.find('div', class_='usertext-body')
            if usertext_div:
                post_body_text = usertext_div.get_text(separator=' ', strip=True)
        return post_body_text

    def parse_comments_from_post_page(self, soup_post_page, post_url_original):
        """Extrai comentários de uma página de post."""
        if not soup_post_page: return []
        parsed_comments = []
        # !!! VERIFIQUE ESTE SELETOR !!!
        comment_area = soup_post_page.find('div', class_='commentarea')
        if not comment_area: return []

        # !!! VERIFIQUE ESTE SELETOR !!!
        comentarios_divs = comment_area.find_all('div', class_=re.compile(r'\bcomment\b'), recursive=False, limit=100)

        for i, comment_div in enumerate(comentarios_divs):
            if not comment_div.get('data-type') == 'comment' or \
               'deleted' in comment_div.get('class', []) or \
               'spam' in comment_div.get('class', []):
                continue

            # !!! VERIFIQUE ESTES SELETORES !!!
            permalink_tag = comment_div.find('a', class_='bylink')
            comment_permalink_fragment = permalink_tag['href'] if permalink_tag and permalink_tag.has_attr('href') else f"#comment_manual_id_{i}"
            full_comment_url = post_url_original.split('?')[0].rstrip('/') + comment_permalink_fragment

            comment_text_tag = comment_div.find('div', class_='usertext-body')
            comment_text = comment_text_tag.get_text(separator=' ', strip=True) if comment_text_tag else ""

            time_tag = comment_div.find('time')
            comment_datetime_str = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
            comment_date_obj = self._parse_reddit_time(comment_datetime_str)

            score_tag = comment_div.find('span', class_='score')
            comment_score_str = score_tag.get_text(strip=True) if score_tag else "0 points"
            
            # O ID do comentário para usar em id_sufixo_item
            comment_id_suffix = comment_div.get('data-fullname', f"c_{i}")


            if comment_date_obj:
                parsed_comments.append({
                    "id_suffix": comment_id_suffix,
                    "url": full_comment_url,
                    "text": comment_text,
                    "date_obj": comment_date_obj,
                    "score_str": comment_score_str
                })
        return parsed_comments


class DataCollector:
    def __init__(self, github_metric_desc="Número de repositórios com push desde 01/01/2025"):
        self.collected_data = []
        self.instance_counter = 0
        self.github_metric_description = github_metric_desc

    def add_mention(self, id_sufixo_item, url_reddit, data_ocorrencia, tipo_item, tecnologia, snippet, score_str):
        self.instance_counter += 1
        current_score = 0
        if score_str:
            match = re.search(r'(-?\d+)', score_str)
            if match:
                current_score = int(match.group(1))

        instancia = {
            "id_instancia": f"brdev_mention_{DATA_ATUAL_PROJETO.strftime('%Y%m%d')}_{id_sufixo_item.replace('-', '_')}_{self.instance_counter}",
            "url_reddit_fonte": url_reddit,
            "data_reddit_ocorrencia": data_ocorrencia.isoformat() if data_ocorrencia else None,
            "tipo_item_reddit": tipo_item,
            "tecnologia_mencionada": tecnologia,
            "snippet_contexto_reddit": snippet.strip()[:250],
            "score_item_reddit": current_score,
            "github_metrica_valor": None,
            "github_metrica_descricao": self.github_metric_description,
            "url_github_busca_metrica": None,
            "data_coleta_metrica_github": None,
            "data_processamento_instancia": DATA_ATUAL_PROJETO.now(datetime.timezone.utc).isoformat()
        }
        self.collected_data.append(instancia)
        print(f"  Collector: Instância {self.instance_counter} adicionada - {tecnologia} ({tipo_item})")

        if self.instance_counter % 20 == 0:
            self.save_to_json("reddit_data_parcial_OOP.json")

    def save_to_json(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=4)
            print(f"Collector: Dados ({len(self.collected_data)} instâncias) salvos em {filename}")
        except IOError as e:
            print(f"Collector: Erro ao salvar dados: {e}")

    def get_total_collected(self):
        return len(self.collected_data)

# --- Orquestração Principal ---
if __name__ == "__main__":
    print("Iniciando scraper do Reddit para r/brdev (Versão OOP)...")

    crawler = RedditCrawler(headers=HEADERS)
    parser = RedditScraperParser(keywords_list=KEYWORDS_TECNOLOGIAS)
    collector = DataCollector()

    current_listing_url = BASE_URL_OLD_REDDIT
    max_listing_pages = 3 # Limite para teste
    listing_pages_processed = 0
    stop_listing_pagination = False

    try:
        while current_listing_url and listing_pages_processed < max_listing_pages and not stop_listing_pagination:
            listing_pages_processed += 1
            print(f"\nOrquestrador: Processando página de listagem {listing_pages_processed}: {current_listing_url}")
            
            soup_listing = crawler.fetch_page_soup(current_listing_url)
            if not soup_listing:
                break

            post_items = parser.parse_post_items_from_listing(soup_listing)

            if not post_items:
                print("Orquestrador: Nenhum post encontrado na página de listagem. Verifique seletores do Parser.")
                break
            
            for post_data in post_items:
                if post_data["date_obj"] >= DATA_INICIO_FILTRO:
                    print(f"\nOrquestrador: Post dentro do período: {post_data['title']} ({post_data['date_obj'].date()})")
                    
                    soup_post_page = crawler.fetch_page_soup(post_data["url"])
                    if not soup_post_page:
                        continue

                    # Processar o próprio post (título + corpo)
                    post_body_text = parser.parse_post_page_details(soup_post_page)
                    full_post_text = post_data["title"] + " " + post_body_text
                    technologies_in_post = parser.find_technologies_in_text(full_post_text)
                    for tech in technologies_in_post:
                        collector.add_mention(
                            id_sufixo_item=post_data["url"].split('/')[-3] if len(post_data["url"].split('/')) > 3 else "post_unk",
                            url_reddit=post_data["url"],
                            data_ocorrencia=post_data["date_obj"],
                            tipo_item="post",
                            tecnologia=tech,
                            snippet=post_data["title"] + (" " + post_body_text[:100] + "..." if post_body_text else ""),
                            score_str=post_data["score_str"]
                        )

                    # Processar comentários do post
                    comments_data = parser.parse_comments_from_post_page(soup_post_page, post_data["url"])
                    for comment in comments_data:
                        if comment["date_obj"] >= DATA_INICIO_FILTRO:
                            technologies_in_comment = parser.find_technologies_in_text(comment["text"])
                            for tech in technologies_in_comment:
                                collector.add_mention(
                                    id_sufixo_item=comment["id_suffix"],
                                    url_reddit=comment["url"],
                                    data_ocorrencia=comment["date_obj"],
                                    tipo_item="comentario",
                                    tecnologia=tech,
                                    snippet=comment["text"],
                                    score_str=comment["score_str"]
                                )
                        elif comment["date_obj"] < DATA_INICIO_FILTRO:
                            # Comentários podem não estar em ordem cronológica estrita na página,
                            # então não paramos a análise de comentários de um post por causa de um antigo.
                            pass


                elif post_data["date_obj"] < DATA_INICIO_FILTRO:
                    print(f"Orquestrador: Post antigo encontrado na listagem ({post_data['title']} - {post_data['date_obj'].date()}). Parando paginação.")
                    stop_listing_pagination = True
                    break # Sai do loop de posts desta página de listagem
            
            if stop_listing_pagination:
                break # Sai do loop de páginas de listagem

            current_listing_url = crawler.get_next_listing_page_url(soup_listing)
            if not current_listing_url:
                print("Orquestrador: Fim da paginação da listagem.")

    except Exception as e:
        print(f"Orquestrador: Ocorreu um erro geral: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.save_to_json("reddit_data_FINAL_OOP.json")
        print(f"Scraping finalizado. Total de {collector.get_total_collected()} instâncias coletadas.")
        if collector.get_total_collected() == 0:
            print("ALERTA OOP: Nenhuma instância foi coletada. Verifique os seletores e a lógica.")
# Hype /brdev scrapper: Análise de Popularidade de Tecnologias

Este projeto realiza web scraping focado no subreddit `r/brdev` e na busca do GitHub para analisar a popularidade e a atividade de diversas tecnologias de programação. O objetivo é comparar o "hype" (menções na comunidade) com a "realidade" (número de projetos ativos), gerando insights para desenvolvedores.

Este trabalho foi desenvolvido para a disciplina INE5454 - Tópicos Avançados em Gerência de Dados.

## 🚀 Funcionalidades

- Scraping de posts e comentários do subreddit `r/brdev`.
- Coleta de métricas de repositórios do GitHub de forma otimizada para evitar bloqueios por taxa de uso.
- Geração de um dataset final em formato JSON com mais de 1000 instâncias.
- Análise dos dados e criação de gráficos para visualização dos resultados.

## 🛠️ Pré-requisitos

Antes de começar, garanta que você tem os seguintes softwares instalados:

- [Python](https://www.python.org/downloads/) (versão 3.10 ou superior)
- [Poetry](https://python-poetry.org/docs/#installation) (gerenciador de dependências)

## ⚙️ Instalação e Configuração

Siga os passos abaixo para configurar o ambiente do projeto:

1.  **Clone o repositório:**

    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Instale as dependências:**
    O Poetry irá ler o arquivo `pyproject.toml`, criar um ambiente virtual e instalar todas as bibliotecas necessárias (`requests`, `beautifulsoup4`, `pandas`, `matplotlib`, `seaborn`, etc.).
    ```bash
    poetry install
    ```

## ▶️ Como Executar

A execução é dividida em duas etapas principais, mas o scraper principal já está configurado para rodar tudo o que é preciso para a coleta.

### Passo 1: Coletar os Dados

Este comando executa o scraper principal. Ele primeiro varre o Reddit e depois o GitHub. **Este processo é longo e pode levar de 30 a 40 minutos**, dependendo da sua conexão.

```bash
poetry run python src/scraper.py
```

Ao final, ele criará o arquivo `dataset_completo.json` na raiz do projeto.

### Passo 2: Analisar os Dados e Gerar os Gráficos

Após a coleta, execute este script para ler o `dataset_completo.json`, analisar os dados e gerar os quatro gráficos de visualização.

```bash
poetry run python src/analise.py
```

## 📊 Arquivos Gerados

Após a execução dos scripts, os seguintes arquivos serão criados:

- `dataset_completo.json`: O dataset final com todas as menções coletadas e enriquecidas com os dados do GitHub.
- `grafico_1_hype_reddit.png`: Gráfico com o ranking de tecnologias por menções no `r/brdev`.
- `grafico_2_atividade_github.png`: Gráfico com o ranking de tecnologias por repositórios ativos no GitHub.
- `grafico_3_tendencia_temporal.png`: Gráfico de linhas mostrando a tendência de menções das Top 5 tecnologias.
- `grafico_4_ratio_hype.png`: Gráfico comparativo da proporção Hype vs. Atividade.

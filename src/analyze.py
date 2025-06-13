import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

def criar_graficos_analise(caminho_json: str):
    """
    Lê o dataset completo, analisa os dados e gera e salva os gráficos.
    """
    print("Iniciando análise do dataset...")

    # Carrega o dataset
    try:
        df = pd.read_json(caminho_json)
        # Converte a coluna de data para o formato datetime
        df['data_reddit_ocorrencia'] = pd.to_datetime(df['data_reddit_ocorrencia'])
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{caminho_json}' não encontrado. Execute o scraper primeiro.")
        return

    # --- Gráfico 1: Ranking de Hype (Menções no Reddit) ---
    plt.figure(figsize=(12, 8))
    top_15_hype = df['tecnologia_mencionada'].value_counts().nlargest(15)
    sns.barplot(x=top_15_hype.values, y=top_15_hype.index, palette='viridis')
    plt.title('Top 15 Tecnologias por Menções no r/brdev (Hype)', fontsize=16)
    plt.xlabel('Número de Menções', fontsize=12)
    plt.ylabel('Tecnologia', fontsize=12)
    plt.tight_layout()
    plt.savefig('grafico_1_hype_reddit.png')
    print("Gráfico 1 (Hype Reddit) salvo como 'grafico_1_hype_reddit.png'")

    # --- Gráfico 2: Ranking de Atividade (Repositórios no GitHub) ---
    df_github = df.drop_duplicates(subset=['tecnologia_mencionada']).set_index('tecnologia_mencionada')
    top_15_atividade = df_github['github_metrica_valor'].nlargest(15)
    plt.figure(figsize=(12, 8))
    sns.barplot(x=top_15_atividade.values, y=top_15_atividade.index, palette='plasma')
    plt.title('Top 15 Tecnologias por Repositórios Ativos no GitHub (Atividade)', fontsize=16)
    plt.xlabel('Número de Repositórios (com push no último ano)', fontsize=12)
    plt.ylabel('Tecnologia', fontsize=12)
    plt.tight_layout()
    plt.savefig('grafico_2_atividade_github.png')
    print("Gráfico 2 (Atividade GitHub) salvo como 'grafico_2_atividade_github.png'")

    # --- Gráfico 3: Análise de Tendência Temporal ---
    # Pegamos as 5 tecnologias mais mencionadas para a análise de tendência
    top_5_techs = top_15_hype.nlargest(5).index
    df_tendencia = df[df['tecnologia_mencionada'].isin(top_5_techs)]
    
    # Agrupamos por mês e tecnologia
    tendencia_mensal = df_tendencia.set_index('data_reddit_ocorrencia') \
        .groupby([pd.Grouper(freq='M'), 'tecnologia_mencionada']) \
        .size().unstack(fill_value=0)

    plt.figure(figsize=(14, 7))
    tendencia_mensal.plot(kind='line', marker='o', figsize=(14, 7))
    plt.title('Tendência de Menções das Top 5 Tecnologias ao Longo do Tempo', fontsize=16)
    plt.xlabel('Mês', fontsize=12)
    plt.ylabel('Número de Menções', fontsize=12)
    plt.legend(title='Tecnologia')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('grafico_3_tendencia_temporal.png')
    print("Gráfico 3 (Tendência Temporal) salvo como 'grafico_3_tendencia_temporal.png'")
    
    # --- Gráfico 4: Análise "Hype vs. Realidade" (Ratio) ---
    df_comparativo = pd.DataFrame({
        'Mencoes_Reddit': top_15_hype
    }).join(pd.DataFrame({
        'Repos_GitHub': top_15_atividade
    })).dropna() # Usamos apenas as techs que estão em ambos os Top 15

    # Calculamos o ratio, adicionando 1 para evitar divisão por zero
    df_comparativo['Ratio_Hype_vs_Atividade'] = df_comparativo['Mencoes_Reddit'] / (df_comparativo['Repos_GitHub'] + 1)
    df_comparativo = df_comparativo.sort_values(by='Ratio_Hype_vs_Atividade', ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=df_comparativo['Ratio_Hype_vs_Atividade'], y=df_comparativo.index, palette='coolwarm')
    plt.title('Análise "Hype vs. Realidade" (Proporção Menções / Repositórios)', fontsize=16)
    plt.xlabel('Ratio (Quanto maior, mais "hype")', fontsize=12)
    plt.ylabel('Tecnologia', fontsize=12)
    plt.tight_layout()
    plt.savefig('grafico_4_ratio_hype.png')
    print("Gráfico 4 (Ratio Hype) salvo como 'grafico_4_ratio_hype.png'")


if __name__ == "__main__":
    # Certifique-se de que o nome do arquivo corresponde ao que seu scraper gerou
    criar_graficos_analise("dataset_completo.json")
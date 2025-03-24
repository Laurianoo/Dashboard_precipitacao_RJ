import os
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

# Caminho dos dados
workspace = "dados"

# Carregando o arquivo de coordenadas das estações
estacoes_file = r"dados/estacoes_rj.csv"

# Listando os arquivos no diretório
files = [file for file in os.listdir(workspace) if file.endswith("_Chuvas.csv")]

# Dicionário para armazenar os DataFrames e acumulados
acumulados = {}

# Processando cada arquivo
for file in files:
    caminho_csv = os.path.join(workspace, file)

    try:
        # Lendo o arquivo ignorando as 14 primeiras linhas
        df = pd.read_csv(caminho_csv, encoding='iso-8859-1', sep=';', skiprows=14, on_bad_lines='skip')

        # Verifica se a coluna 'Data' existe
        if 'Data' not in df.columns:
            raise KeyError("Coluna 'Data' não encontrada no arquivo.")
        
        # Verifica se a coluna 'NivelConsistencia' existe
        if 'NivelConsistencia' not in df.columns:
            raise KeyError("Coluna 'NivelConsistencia' não encontrada no arquivo.")

        # Filtrando para manter apenas os dados com NivelConsistencia == 1
        df = df[df['NivelConsistencia'] == 1]

        # Tentando pegar os dias de chuva
        diaschuva = df['NumDiasDeChuva']
        diaschuva = diaschuva[:287]

        # Mantendo somente as colunas de interesse (sem status)
        precip_columns = [col for col in df.columns if col.startswith('Chuva') and not col.endswith('Status')]
        cols_to_keep = ['Data'] + precip_columns
        df = df[cols_to_keep]

        # Convertendo a coluna 'Data' para datetime
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')

        # Substituindo vírgulas por pontos e convertendo para numérico
        df[precip_columns] = df[precip_columns].replace(',', '.', regex=True).apply(pd.to_numeric, errors='coerce')

        rename_dict = {col: col.replace('Chuva', 'Dia') for col in precip_columns}
        df = df.rename(columns=rename_dict)
        precip_columns = [col for col in df.columns if col.startswith('Dia') and not col.endswith('Status')]
        
        # Filtrando o período de 2000 a 2023
        df = df[(df['Data'] >= '2000-01-01') & (df['Data'] <= '2023-12-31')]

        # Calculando o acumulado de precipitação por mês e ano
        df['MesAno'] = df['Data'].dt.to_period('M')
        df_acumulado = df.groupby('MesAno')[precip_columns].sum().reset_index()

        # Armazenando os acumulados no dicionário
        acumulados[file] = df_acumulado

    except KeyError as ke:
        print(f"Erro ao processar o arquivo {file}: {ke}")
    except Exception as e:
        print(f"Erro ao processar o arquivo {file}: {e}")

# Calculando os dias de chuva por mês e ano para toda a série de dados
dias_chuva_mensal = []
dias_chuva_anual = []

for file in files:
    df_acc = acumulados[file]

    # Convertendo o período MesAno para datetime
    df_acc['Data'] = df_acc['MesAno'].dt.to_timestamp()

    # Usando a coluna 'NumDiasDeChuva' diretamente (ajustando para o número correto de linhas se necessário)
    df_acc['DiasChuva'] = diaschuva  # Usando a coluna 'NumDiasDeChuva' que foi definida antes

    # Calculando os dias de chuva por mês
    dias_mensais = df_acc.groupby(df_acc['Data'].dt.to_period('M'))['DiasChuva'].sum().reset_index()
    dias_mensais['Estacao'] = file.replace("_Chuvas.csv", "")
    dias_chuva_mensal.append(dias_mensais)

    # Calculando os dias de chuva por ano
    dias_anuais = df_acc.groupby(df_acc['Data'].dt.year)['DiasChuva'].sum().reset_index()
    dias_anuais['Estacao'] = file.replace("_Chuvas.csv", "")
    dias_chuva_anual.append(dias_anuais)

# Concatenando dias de chuva mensais e anuais
df_dias_chuva_mensal = pd.concat(dias_chuva_mensal, ignore_index=True)
df_dias_chuva_anual = pd.concat(dias_chuva_anual, ignore_index=True)

# ------------------------------------------------------ STREAMLIT DASHBOARD ----------------------------------------------------

# Configurando a página
st.set_page_config(layout="wide")

# Título
st.write("""
         # Precipitação no estado do Rio de Janeiro
         Dados obtidos a partir de estações da ANA
         """)

# Lista de estações (extraindo do nome dos arquivos)
station_ids = [f.replace("_Chuvas.csv", "") for f in files]

# Seleção da estação
station_id = st.sidebar.selectbox("Selecione a Estação", station_ids)

# Lendo o DataFrame da estação selecionada
df_selecionado = acumulados[f"{station_id}_Chuvas.csv"]

# Adicionando a coluna 'Estacao' ao DataFrame
df_selecionado['Estacao'] = station_id

# Convertendo a coluna 'MesAno' para datetime e ordenando
df_selecionado['Data'] = df_selecionado['MesAno'].dt.to_timestamp()
df_selecionado = df_selecionado.sort_values('Data')

# Criando colunas de ano e mês
df_selecionado['Ano'] = df_selecionado['Data'].dt.year
df_selecionado['Mes'] = df_selecionado['Data'].dt.month

# Selecionando mês e ano no dashboard
selected_month = st.sidebar.selectbox("Selecione o Mês", df_selecionado['Mes'].unique())
selected_year = st.sidebar.selectbox("Selecione o Ano", df_selecionado['Ano'].unique())

# Filtrando os dados
df_filtrado = df_selecionado[(df_selecionado['Mes'] == selected_month) & (df_selecionado['Ano'] == selected_year)]

# Tratamentos para os mapas:
try:
    df_estacoes = pd.read_csv(estacoes_file, sep=';', decimal=',')

    # Substituindo vírgulas por pontos nas coordenadas
    df_estacoes['Latitude'] = df_estacoes['Latitude'].astype(str).str.replace(',', '.').astype(float)
    df_estacoes['Longitude'] = df_estacoes['Longitude'].astype(str).str.replace(',', '.').astype(float)

    # Convertendo a coluna 'Estacao' para string
    df_estacoes['Estacao'] = df_estacoes['Estacao'].astype(str)

    # Calculando o acumulado médio para cada estação
    acumulado_medio = {file.replace("_Chuvas.csv", ""): df_acc[precip_columns].sum().mean() for file, df_acc in acumulados.items()}

    # Criando DataFrame de acumulados médios
    df_acumulados = pd.DataFrame(list(acumulado_medio.items()), columns=['Estacao', 'AcumuladoMedio'])

    # Mesclando com o DataFrame de estações (conversão para str)
    df_estacoes['Estacao'] = df_estacoes['Estacao'].astype(str)
    df_acumulados['Estacao'] = df_acumulados['Estacao'].astype(str)

    df_mapa = pd.merge(df_estacoes, df_acumulados, on='Estacao')

    if df_mapa[['Latitude', 'Longitude']].isnull().any().any():
        st.warning("Coordenadas faltando para algumas estações.")

except FileNotFoundError:
    st.error(f"Arquivo {estacoes_file} não encontrado.")

# Calculando o acumulado médio para cada estação, considerando o mês escolhido
acumulado_medio_mensal = {}
for file, df_acc in acumulados.items():
    estacao = file.replace("_Chuvas.csv", "")
    df_acc_mes = df_acc[df_acc['MesAno'].dt.month == selected_month]
    acumulado_medio_mensal[estacao] = df_acc_mes[precip_columns].sum().mean()

# Criando DataFrame de acumulados médios mensais
df_acumulados_mensais = pd.DataFrame(list(acumulado_medio_mensal.items()), columns=['Estacao', 'AcumuladoMedioMensal'])

# Mesclando com o DataFrame de estações (conversão para str)
df_estacoes['Estacao'] = df_estacoes['Estacao'].astype(str)
df_acumulados_mensais['Estacao'] = df_acumulados_mensais['Estacao'].astype(str)

df_mapa_mensal = pd.merge(df_estacoes, df_acumulados_mensais, on='Estacao')

# Substituindo vírgulas por pontos nas coordenadas
df_mapa_mensal['Latitude'] = df_mapa_mensal['Latitude'].astype(str).str.replace(',', '.').astype(float)
df_mapa_mensal['Longitude'] = df_mapa_mensal['Longitude'].astype(str).str.replace(',', '.').astype(float)

# ========================================================================== MAPAS

st.markdown("## Mapas de Acumulados Médios de Chuva no RJ")
custom_colors = ['#F58518', '#19D3F3', '#1616A7', '#782AB6']
# ======================================== Mapa de Acumulados Médios de Chuva mensal no RJ

fig_mapa_mensal = px.scatter_mapbox(df_mapa_mensal, lat='Latitude', lon='Longitude', size='AcumuladoMedioMensal',
                                     hover_name='Estacao', color='AcumuladoMedioMensal',
                                     title=f"Mapa de Acumulados Médios de Chuva Mensal no RJ - Mês {selected_month}",
                                     color_continuous_scale=custom_colors, size_max=15, zoom=6)
fig_mapa_mensal.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_mapa_mensal, use_container_width=True)

# ======================================== Mapa de Acumulados Médios serie completa de Chuva no RJ

fig_mapa = px.scatter_mapbox(df_mapa, lat='Latitude', lon='Longitude', size='AcumuladoMedio',
                             hover_name='Estacao', color='AcumuladoMedio',
                             title="Mapa de Acumulados Médios de Chuva no RJ para a série de dados completa",
                             color_continuous_scale=custom_colors, size_max=15, zoom=6)
fig_mapa.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_mapa, use_container_width=True)

# ================================================================= Inicio dos Gráficos:

# Layout do Dashboard
col1, col2 = st.columns(2)

# Gráfico de acumulado de precipitação
fig_precip = px.bar(df_filtrado, x='Data', y=precip_columns,
                    title="Acumulado Mensal de Precipitação",
                    labels={precip_columns[0]: 'Precipitação (mm)', 'Data': 'Data'})
col1.plotly_chart(fig_precip, use_container_width=True)

# Gráfico de comparação de acumulado por ano (série histórica)
df_comparison = df_selecionado.groupby('Ano')[precip_columns].sum().reset_index()
fig_comparison = px.bar(df_comparison, x='Ano', y=precip_columns,
                        title="Acumulado de Precipitação Anual - Série Histórica",
                        labels={precip_columns[0]: 'Precipitação (mm)', 'Ano': 'Ano'})
col2.plotly_chart(fig_comparison, use_container_width=True)

# Gráfico de dias de chuva corrigido, com base no ano selecionado
if not df_dias_chuva_mensal.empty:
    # Filtrando os dados para a estação selecionada
    df_dias_chuva_filtrado = df_dias_chuva_mensal[df_dias_chuva_mensal['Estacao'] == station_id]

    # Convertendo a coluna 'Data' para datetime para plotagem
    df_dias_chuva_filtrado['MesAno'] = pd.to_datetime(df_dias_chuva_filtrado['Data'].astype(str) + '-01')

    # Filtrando pelo ano escolhido pelo usuário
    df_dias_chuva_filtrado = df_dias_chuva_filtrado[df_dias_chuva_filtrado['MesAno'].dt.year == selected_year]

    # Verificando se há dados disponíveis para o ano selecionado
    if not df_dias_chuva_filtrado.empty:
        # Plotando o gráfico de dias de chuva mensais com tamanho ajustado
        fig_dias_chuva = px.bar(df_dias_chuva_filtrado, x='MesAno', y='DiasChuva',
                                title=f"Dias de Chuva Mensais na Estação {station_id} - Ano {selected_year}",
                                labels={'DiasChuva': 'Dias de Chuva', 'MesAno': 'Mês/Ano'},
                                text_auto=True)

        col1.plotly_chart(fig_dias_chuva, use_container_width=True)
    else:
        st.warning(f"Nenhum dado disponível para o ano {selected_year}.")
else:
    st.warning("Nenhum dado disponível para dias de chuva mensais.")

# Plotar as médias dos acumulados mensais para todos os anos (de acordo com a estação selecionada)
# Agrupar os dados pelo mês e somar os acumulados de precipitação
df_acumed = df_selecionado.groupby('Mes')[precip_columns].sum().reset_index()

# Agora, calcular a média dos acumulados mensais dividindo pela quantidade de anos
df_acumed_avg = df_acumed.copy()
df_acumed_avg[precip_columns] = df_acumed[precip_columns] / df_selecionado['Ano'].nunique()  # Supondo que você tenha a coluna 'Ano'

# Gerar o gráfico com os acumulados médios mensais
fig_acumed = px.bar(df_acumed_avg, x='Mes', y=precip_columns,
                    title="Acumulado médio mensal de Precipitação - Série Histórica",
                    labels={precip_columns[0]: 'Precipitação (mm)', 'Mes': 'Mes'})

# Exibir o gráfico
col2.plotly_chart(fig_acumed, use_container_width=True)

# ======================================== Separação por estações do ano

# Definir as estações do ano
stations = {
    'Outono': [3, 4, 5],  # Março, Abril, Maio
    'Inverno': [6, 7, 8],  # Junho, Julho, Agosto
    'Primavera': [9, 10, 11],  # Setembro, Outubro, Novembro
    'Verão': [12, 1, 2],  # Dezembro, Janeiro, Fevereiro
}

# Selecionar a estação do ano escolhida pelo usuário
station_selected = st.selectbox('Selecione a estação do ano', list(stations.keys()))

# Filtrar os dados para a estação escolhida
df_station = df_selecionado[df_selecionado['Mes'].isin(stations[station_selected])]

# Calcular as médias de precipitação para a estação escolhida, agrupando por ano
df_station_avg = df_station.groupby('Ano')[precip_columns].mean().reset_index()

# Plotar o gráfico de médias de precipitação para a estação escolhida
fig_station_avg = px.bar(df_station_avg, x='Ano', y=precip_columns,
                          title=f"Médias de Precipitação na Estação {station_selected} (Agrupado por Ano)",
                          labels={precip_columns[0]: 'Precipitação (mm)', 'Ano': 'Ano'})

# Exibir o gráfico de médias
st.plotly_chart(fig_station_avg, use_container_width=True)

# Calcular os acumulados de precipitação para a estação escolhida, agrupando por ano
df_station_sum = df_station.groupby('Ano')[precip_columns].sum().reset_index()

# Plotar o gráfico de acumulados de precipitação para a estação escolhida
fig_station_sum = px.bar(df_station_sum, x='Ano', y=precip_columns,
                          title=f"Acumulados de Precipitação na Estação {station_selected} (Agrupado por Ano)",
                          labels={precip_columns[0]: 'Precipitação (mm)', 'Ano': 'Ano'})

# Exibir o gráfico de acumulados
st.plotly_chart(fig_station_sum, use_container_width=True)

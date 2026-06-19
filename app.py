import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuração da página e tema visual
st.set_page_config(
    page_title="HGJP - Dashboard de Atendimentos", 
    page_icon="🏥",
    layout="wide"
)

# --- INJEÇÃO DE IDENTIDADE VISUAL (CSS INSPIRADO NO HGJP) ---
st.markdown("""
    <style>
        /* Cor de fundo geral da aplicação */
        .stApp {
            background-color: #f8f9fa;
        }
        /* Estilização do título principal */
        .main-title {
            color: #0A2540; /* Azul Marinho Institucional */
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 700;
            border-left: 5px solid #194D33; /* Verde Oliva Militar */
            padding-left: 15px;
            margin-bottom: 5px;
        }
        /* Subtítulo */
        .sub-title {
            color: #6c757d;
            font-size: 14px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
        /* Customização dos Cards de Métricas */
        div[data-testid="stMetricValue"] {
            color: #0A2540 !important;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            color: #495057 !important;
            font-weight: 500 !important;
        }
        /* Divisores personalizados */
        .custom-hr {
            border: 0;
            height: 2px;
            background-image: linear-gradient(to right, #194D33, #0A2540, rgba(0,0,0,0));
            margin-top: 20px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_gradient=True, unsafe_allow_html=True)

# Título Customizado Estilo Portal Institucional
st.markdown('<h1 class="main-title">HOSPITAL GERAL DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diretoria de Saúde — Painel Analítico de Atendimentos Ambulatoriais</p>', unsafe_allow_html=True)

# Definição da Paleta de Cores para os Gráficos (Inspirada no Site)
PALETA_HGJP_AZUL = ['#0A2540', '#1C3D5A', '#2B547E', '#4682B4', '#87CEEB']
PALETA_HGJP_VERDE = ['#194D33', '#226343', '#2D8257', '#41A874', '#66BB8A']

# Carregar os dados
@st.cache_data
def load_data():
    df = pd.read_csv("dados.csv")
    df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
    
    # Criar coluna de Ano e Ano-Mês para agrupamentos posteriores
    df['Ano'] = df['Dia_Atendimento'].dt.year
    df['Ano_Mes'] = df['Dia_Atendimento'].dt.to_period('M').astype(str)
    
    # TRATAMENTO DE IDADE: Idades acima de 115 anos viram NaN (Inválidas/Não Informadas)
    df['Idade_Tratada'] = pd.to_numeric(df['Idade'], errors='coerce')
    df.loc[df['Idade_Tratada'] > 115, 'Idade_Tratada'] = np.nan
    
    # Criar faixas etárias de 10 em 10 anos (apenas para idades válidas)
    bins = list(range(0, 121, 10))
    labels = [f"{i}-{i+9}" for i in bins[:-1]]
    
    df['Faixa_Etaria'] = pd.cut(df['Idade_Tratada'], bins=bins, labels=labels, right=False)
    df['Faixa_Etaria'] = df['Faixa_Etaria'].astype(str).replace('nan', 'Não Informada')
    
    return df

try:
    df = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.markdown("<h3 style='color: #0A2540;'>Filtros de Pesquisa</h3>", unsafe_allow_html=True)
    
    # Filtro de Ano
    anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect(
        "Selecione o Ano:",
        options=anos_disponiveis,
        default=anos_disponiveis
    )
    
    # Filtro de Intervalo de Idade (0 a 115 anos)
    idade_min = 0
    idade_max = 115
    idade_selecionada = st.sidebar.slider(
        "Intervalo de Idade Válida:",
        min_value=idade_min,
        max_value=idade_max,
        value=(idade_min, idade_max)
    )
    
    # Filtro de Setor
    setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
    setores_selecionados = st.sidebar.multiselect(
        "Selecione o Setor:",
        options=setores_disponiveis,
        default=setores_disponiveis
    )
    
    # Filtro de Especialidade
    especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
    especialidades_selecionadas = st.sidebar.multiselect(
        "Selecione a Especialidade:",
        options=especialidades_disponiveis,
        default=especialidades_disponiveis
    )
    
    # Filtro de Sexo
    sexo_selecionado = st.sidebar.multiselect(
        "Selecione o Sexo:",
        options=df["Sexo"].unique(),
        default=df["Sexo"].unique()
    )

    # Aplicando os filtros globais
    df_filtrado = df[
        (df["Ano"].isin(anos_selecionados)) &
        (df["Setor_Atendimento"].isin(setores_selecionados)) &
        (df["Especialidade_Atendimento"].isin(especialidades_selecionadas)) &
        (df["Sexo"].isin(sexo_selecionado))
    ]
    
    # Aplicando o filtro específico do Slider de Idade
    df_filtrado = df_filtrado[
        (df_filtrado["Idade_Tratada"].between(idade_selecionada[0], idade_selecionada[1])) | 
        (df_filtrado["Idade_Tratada"].isna())
    ]

    # --- CARD INDICADORES MÉTRICOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total de Atendimentos", f"{len(df_filtrado)}")
    
    idades_validas = df_filtrado['Idade_Tratada'].dropna()
    col2.metric("🩺 Média de Idade (Válidas)", f"{idades_validas.mean():.1f} anos" if len(idades_validas) > 0 else "N/A")
    
    col3.metric("🔬 CIDs Únicos Identificados", f"{df_filtrado['Código_CID'].nunique()}")

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # --- GRÁFICOS INTERATIVOS ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("📈 Linha do Tempo de Atendimentos (Por Mês)")
        if len(df_filtrado) > 0:
            df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos')
            df_mes = df_mes.sort_values('Ano_Mes')
            
            fig_linha = px.bar(df_mes, x='Ano_Mes', y='Atendimentos',
                               labels={'Ano_Mes': 'Mês/Ano', 'Atendimentos': 'Atendimentos'},
                               color_discrete_sequence=['#0A2540']) # Azul Marinho Focado
            fig_linha.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

    with row1_col2:
        st.subheader("👥 Distribuição por Sexo Biológico")
        if len(df_filtrado) > 0:
            fig_pizza = px.pie(df_filtrado, names='Sexo', hole=0.4,
                               color_discrete_sequence=['#0A2540', '#194D33']) # Contraste Azul/Verde do Site
            fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("📊 Distribuição por Faixa Etária (Grupos de 10 Anos)")
        if len(df_filtrado) > 0:
            df_idade = df_filtrado.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
            df_idade['Faixa_Etaria'] = pd.Categorical(df_idade['Faixa_Etaria'], 
                                                        categories=[f"{i}-{i+9}" for i in range(0, 120, 10)] + ['Não Informada'], 
                                                        ordered=True)
            df_idade = df_idade.sort_values('Faixa_Etaria')
            
            fig_idade = px.bar(df_idade, x='Faixa_Etaria', y='Quantidade',
                               labels={'Faixa_Etaria': 'Grupo de Idade', 'Quantidade': 'Pacientes'},
                               color='Quantidade', color_continuous_scale='Greens') # Tons de verde militar
            fig_idade.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_idade, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    with row2_col2:
        st.subheader("📋 Top 10 Patologias Mais Frequentes (Código CID)")
        if len(df_filtrado) > 0:
            df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total')
            df_cid = df_cid.sort_values(by='Total', ascending=False).head(10)
            
            fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença',
                             labels={'Código_CID': 'Código CID', 'Total': 'Casos'},
                             color='Total', color_continuous_scale='Blues') # Gradiente azul
            fig_cid.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_cid, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    # --- TABELA DE DADOS ---
    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)
    st.subheader("🗃️ Registro de Dados Filtrados")
    
    df_exibicao = df_filtrado.copy()
    df_exibicao['Idade_Exibição'] = df_exibicao['Idade_Tratada'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "Inválida (>115)")
    
    st.dataframe(
        df_exibicao[['Idade_Exibição', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']], 
        use_container_width=True
    )

except Exception as e:
    st.error(f"Erro ao processar os dados. Detalhes: {e}")

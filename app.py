import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página e tema visual
st.set_page_config(
    page_title="HGJP - Dashboard de Atendimentos", 
    page_icon="🏥",
    layout="wide"
)

# --- INJEÇÃO DE IDENTIDADE VISUAL (CSS INSPIRADO NO HGJP) ---
st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        .main-title {
            color: #0A2540; 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 700;
            border-left: 5px solid #194D33; 
            padding-left: 15px;
            margin-bottom: 5px;
        }
        .sub-title {
            color: #6c757d;
            font-size: 14px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
        div[data-testid="stMetricValue"] {
            color: #0A2540 !important;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            color: #495057 !important;
            font-weight: 500 !important;
        }
        .custom-hr {
            border: 0;
            height: 2px;
            background-image: linear-gradient(to right, #194D33, #0A2540, rgba(0,0,0,0));
            margin-top: 20px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Título Customizado Estilo Portal Institucional
st.markdown('<h1 class="main-title">HOSPITAL GERAL DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diretoria de Saúde — Painel Analítico de Atendimentos Ambulatoriais</p>', unsafe_allow_html=True)

# Carregar os dados
@st.cache_data
def load_data():
    df = pd.read_csv("dados.csv")
    df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
    
    # Criar coluna de Ano e Ano-Mês para agrupamentos posteriores
    df['Ano'] = df['Dia_Atendimento'].dt.year
    df['Ano_Mes'] = df['Dia_Atendimento'].dt.to_period('M').astype(str)
    
    # TRATAMENTO DE IDADE: Converter para numérico e forçar valores acima de 115 a virarem nulos (None)
    df['Idade_Tratada'] = pd.to_numeric(df['Idade'], errors='coerce')
    df.loc[df['Idade_Tratada'] > 115, 'Idade_Tratada'] = None
    
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
    
    anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
    
    idade_min, idade_max = 0, 115
    idade_selecionada = st.sidebar.slider("Intervalo de Idade Válida:", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))
    
    setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
    setores_selecionados = st.sidebar.multiselect("Selecione o Setor:", options=setores_disponiveis, default=setores_disponiveis)
    
    especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
    especialidades_selecionadas = st.sidebar.multiselect("Selecione a Especialidade:", options=especialidades_disponiveis, default=especialidades_disponiveis)
    
    sexo_selecionado = st.sidebar.multiselect("Selecione o Sexo:", options=df["Sexo"].unique(), default=df["Sexo"].unique())

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
            df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos').sort_values('Ano_Mes')
            fig_linha = px.bar(df_mes, x='Ano_Mes', y='Atendimentos', labels={'Ano_Mes': 'Mês/Ano', 'Atendimentos': 'Atendimentos'}, color_discrete_sequence=['#0A2540'])
            fig_linha.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

    with row1_col2:
        st.subheader("👥 Distribuição por Sexo Biológico")
        if len(df_filtrado) > 0:
            fig_pizza = px.pie(df_filtrado, names='Sexo', hole=0.4, color_discrete_sequence=['#0A2540', '#194D33'])
            fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("📊 Distribuição por Faixa Etária (Grupos de 10 Anos)")
        if len(df_filtrado) > 0:
            df_idade = df_filtrado.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
            df_idade['Faixa_Etaria'] = pd.Categorical(df_idade['Faixa_Etaria'], categories=[f"{i}-{i+9}" for i in range(0, 120, 10)] + ['Não Informada'], ordered=True)
            df_idade = df_idade.sort_values('Faixa_Etaria')
            
            fig_idade = px.bar(df_idade, x='Faixa_Etaria', y='Quantidade', labels={'Faixa_Etaria': 'Grupo de Idade', 'Quantidade': 'Pacientes'}, color='Quantidade', color_continuous_scale='Greens')
            fig_idade.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_idade, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    with row2_col2:
        st.subheader("📋 Top 10 Patologias Mais Frequentes (Código CID)")
        if len(df_filtrado) > 0:
            df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total').sort_values(by='Total', ascending=False).head(10)
            fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença', labels={'Código_CID': 'Código CID', 'Total': 'Casos'}, color='Total', color_continuous_scale='Blues')
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

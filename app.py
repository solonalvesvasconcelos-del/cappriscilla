import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Atendimentos", layout="wide")

st.title("📊 Painel Analítico de Atendimentos Médicos")
st.markdown("Análise exploratória de perfis de pacientes, especialidades, setores e CIDs.")

# Carregar os dados
@st.cache_data
def load_data():
    df = pd.read_csv("dados.csv")
    df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
    
    # Filtro automático: Desconsiderar idades acima de 130 anos (limpeza de dados)
    df = df[df['Idade'] <= 130]
    
    # Criar coluna de Ano e Ano-Mês para agrupamentos posteriores
    df['Ano'] = df['Dia_Atendimento'].dt.year
    df['Ano_Mes'] = df['Dia_Atendimento'].dt.to_period('M').astype(str)
    
    # Criar faixas etárias de 10 em 10 anos
    bins = list(range(0, int(df['Idade'].max()) + 11, 10))
    labels = [f"{i}-{i+9}" for i in bins[:-1]]
    df['Faixa_Etaria'] = pd.cut(df['Idade'], bins=bins, labels=labels, right=False)
    
    return df

try:
    df = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Ano
    anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect(
        "Selecione o Ano:",
        options=anos_disponiveis,
        default=anos_disponiveis
    )
    
    # Filtro dinâmico de Idade (Forçado a iniciar em 0 e limitado ao máximo do banco até 130)
    idade_min = 0
    idade_max = int(df["Idade"].max())
    
    idade_selecionada = st.sidebar.slider(
        "Intervalo de Idade:",
        min_value=idade_min,
        max_value=idade_max,
        value=(idade_min, idade_max) # Inicializa o seletor selecionando de 0 até a idade máxima
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

    # Aplicando os filtros ao DataFrame
    df_filtrado = df[
        (df["Ano"].isin(anos_selecionados)) &
        (df["Idade"].between(idade_selecionada[0], idade_selecionada[1])) &
        (df["Setor_Atendimento"].isin(setores_selecionados)) &
        (df["Especialidade_Atendimento"].isin(especialidades_selecionadas)) &
        (df["Sexo"].isin(sexo_selecionado))
    ]

    # --- CARD INDICADORES MÉTRICOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
    col2.metric("Média de Idade", f"{df_filtrado['Idade'].mean():.1f} anos" if len(df_filtrado) > 0 else "0 anos")
    col3.metric("CIDs Únicos", f"{df_filtrado['Código_CID'].nunique()}")

    st.markdown("---")

    # --- GRÁFICOS INTERATIVOS ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Linha do Tempo de Atendimentos (Por Mês)")
        if len(df_filtrado) > 0:
            df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos')
            df_mes = df_mes.sort_values('Ano_Mes')
            
            fig_linha = px.bar(df_mes, x='Ano_Mes', y='Atendimentos',
                               labels={'Ano_Mes': 'Mês/Ano', 'Atendimentos': 'Qtd Atendimentos'},
                               color_discrete_sequence=['#4A90E2'])
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

    with row1_col2:
        st.subheader("Distribuição por Sexo")
        if len(df_filtrado) > 0:
            fig_pizza = px.pie(df_filtrado, names='Sexo', hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("Distribuição por Faixa Etária (10 em 10 anos)")
        if len(df_filtrado) > 0:
            df_idade = df_filtrado.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
            
            fig_idade = px.bar(df_idade, x='Faixa_Etaria', y='Quantidade',
                               labels={'Faixa_Etaria': 'Faixa Etária (Idade)', 'Quantidade': 'Total de Pacientes'},
                               color='Quantidade', color_continuous_scale='Blues')
            st.plotly_chart(fig_idade, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    with row2_col2:
        st.subheader("Top 10 Doenças Mais Frequentes (CID)")
        if len(df_filtrado) > 0:
            df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total')
            df_cid = df_cid.sort_values(by='Total', ascending=False).head(10)
            
            fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença',
                             labels={'Código_CID': 'Código CID', 'Total': 'Atendimentos'},
                             color='Total', color_continuous_scale='Purples')
            fig_cid.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cid, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("Visualização dos Dados Filtrados")
    st.dataframe(
        df_filtrado[['Idade', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']], 
        use_container_width=True
    )

except Exception as e:
    st.error(f"Erro ao processar os dados. Detalhes: {e}")

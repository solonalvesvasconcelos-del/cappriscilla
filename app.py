import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Atendimentos", layout="wide")

st.title("📊 Painel Analítico de Atendimentos Médicos")
st.markdown("Análise exploratória de perfis de pacientes, especialidades e CIDs.")

# Carregar os dados
@st.cache_data
def load_data():
    # Altere para o caminho correto se necessário
    df = pd.read_csv("dados.csv")
    df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
    return df

try:
    df = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Filtro de Especialidade
    especialidades = st.sidebar.multiselect(
        "Selecione a Especialidade:",
        options=df["Especialidade_Atendimento"].unique(),
        default=df["Especialidade_Atendimento"].unique()
    )
    
    # Filtro de Sexo
    sexo = st.sidebar.multiselect(
        "Selecione o Sexo:",
        options=df["Sexo"].unique(),
        default=df["Sexo"].unique()
    )
    
    # Filtro de Idade
    idade_min, idade_max = int(df["Idade"].min()), int(df["Idade"].max())
    idade_selecionada = st.sidebar.slider(
        "Intervalo de Idade:",
        min_value=idade_min,
        max_value=idade_max,
        value=(idade_min, idade_max)
    )

    # Aplicando os filtros ao DataFrame
    df_filtrado = df[
        (df["Especialidade_Atendimento"].isin(especialidades)) &
        (df["Sexo"].isin(sexo)) &
        (df["Idade"].between(idade_selecionada[0], idade_selecionada[1]))
    ]

    # --- CARD INDICADORES METRICOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
    col2.metric("Média de Idade", f"{df_filtrado['Idade'].mean():.1f} anos")
    col3.metric("CIDs Únicos", f"{df_filtrado['Código_CID'].nunique()}")

    st.markdown("---")

    # --- GRÁFICOS INTERATIVOS ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Linha do Tempo de Atendimentos")
        df_linha = df_filtrado.groupby('Dia_Atendimento').size().reset_index(name='Atendimentos')
        fig_linha = px.line(df_linha, x='Dia_Atendimento', y='Atendimentos', markers=True,
                            labels={'Dia_Atendimento': 'Data', 'Atendimentos': 'Qtd'})
        st.plotly_chart(fig_linha, use_container_width=True)

    with row1_col2:
        st.subheader("Distribuição por Sexo")
        fig_pizza = px.pie(df_filtrado, names='Sexo', hole=0.4,
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pizza, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("Top 10 Doenças Mais Frequentes (CID)")
        df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total')
        df_cid = df_cid.sort_values(by='Total', ascending=False).head(10)
        fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença',
                         labels={'Código_CID': 'Código CID', 'Total': 'Atendimentos'},
                         color='Total', color_continuous_scale='Blues')
        fig_cid.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_cid, use_container_width=True)

    with row2_col2:
        st.subheader("Distribuição por Faixa Etária")
        fig_hist = px.histogram(df_filtrado, x="Idade", nbins=20, 
                                labels={'Idade': 'Idade do Paciente', 'count': 'Frequência'},
                                color_discrete_sequence=['#4A90E2'])
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("Visualização dos Dados Filtrados")
    st.dataframe(df_filtrado[['Idade', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']], use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'dados.csv'. Certifique-se de que ele está na mesma pasta do script. Detalhes: {e}")
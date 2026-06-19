import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from streamlit_plotly_events import plotly_events

# Configuração da página
st.set_page_config(page_title="Dashboard de Atendimentos Interativo", layout="wide")

st.title("📊 Painel Analítico Interativo (Clique nos Gráficos para Filtrar)")
st.markdown("Experimente clicar nas fatias do gráfico de **Sexo** ou nas barras de **Faixa Etária** para filtrar todo o painel.")

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
    
    # Criar faixas etárias de 10 em 10 anos
    bins = list(range(0, 121, 10))
    labels = [f"{i}-{i+9}" for i in bins[:-1]]
    
    df['Faixa_Etaria'] = pd.cut(df['Idade_Tratada'], bins=bins, labels=labels, right=False)
    df['Faixa_Etaria'] = df['Faixa_Etaria'].astype(str).replace('nan', 'Não Informada')
    
    return df

try:
    df = load_data()

    # --- INICIALIZAÇÃO DOS ESTADOS DE CLIQUE ---
    if "clique_sexo" not in st.session_state:
        st.session_state.clique_sexo = None
    if "clique_faixa" not in st.session_state:
        st.session_state.clique_faixa = None

    # --- BARRA LATERAL (FILTROS MANUAIS) ---
    st.sidebar.header("Filtros Gerais")
    
    # Botão para limpar filtros de clique
    if st.session_state.clique_sexo or st.session_state.clique_faixa:
        if st.sidebar.button("🧹 Limpar Filtros de Clique"):
            st.session_state.clique_sexo = None
            st.session_state.clique_faixa = None
            st.rerun()

    # Exibe na barra lateral se houver filtros ativos por clique
    if st.session_state.clique_sexo:
        st.sidebar.info(f"Filtro ativo por clique: **Sexo = {st.session_state.clique_sexo}**")
    if st.session_state.clique_faixa:
        st.sidebar.info(f"Filtro ativo por clique: **Faixa Etária = {st.session_state.clique_faixa}**")

    # Filtros Tradicionais
    anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
    
    setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
    setores_selecionados = st.sidebar.multiselect("Selecione o Setor:", options=setores_disponiveis, default=setores_disponiveis)
    
    especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
    especialidades_selecionadas = st.sidebar.multiselect("Selecione a Especialidade:", options=especialidades_disponiveis, default=especialidades_disponiveis)

    # --- APLICANDO FILTROS MANUAIS + FILTROS DE CLIQUE ---
    df_filtrado = df[
        (df["Ano"].isin(anos_selecionados)) &
        (df["Setor_Atendimento"].isin(setores_selecionados)) &
        (df["Especialidade_Atendimento"].isin(especialidades_selecionadas))
    ]

    if st.session_state.clique_sexo:
        df_filtrado = df_filtrado[df_filtrado["Sexo"] == st.session_state.clique_sexo]
    
    if st.session_state.clique_faixa:
        df_filtrado = df_filtrado[df_filtrado["Faixa_Etaria"] == st.session_state.clique_faixa]

    # --- CARD INDICADORES MÉTRICOS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
    idades_validas = df_filtrado['Idade_Tratada'].dropna()
    col2.metric("Média de Idade (Válidas)", f"{idades_validas.mean():.1f} anos" if len(idades_validas) > 0 else "N/A")
    col3.metric("CIDs Únicos", f"{df_filtrado['Código_CID'].nunique()}")

    st.markdown("---")

    # --- ROW 1: GRÁFICOS INTERATIVOS DE SELEÇÃO POR CLIQUE ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Distribuição por Sexo (Clique para Filtrar)")
        if len(df_filtrado) > 0:
            # Para evitar recursão visual infinita, o gráfico de Sexo mostra os dados ignorando o próprio filtro de clique de sexo
            df_pizza_base = df[(df["Ano"].isin(anos_selecionados)) & (df["Setor_Atendimento"].isin(setores_selecionados)) & (df["Especialidade_Atendimento"].isin(especialidades_selecionadas))]
            if st.session_state.clique_faixa:
                df_pizza_base = df_pizza_base[df_pizza_base["Faixa_Etaria"] == st.session_state.clique_faixa]
            
            fig_pizza = px.pie(df_pizza_base, names='Sexo', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pizza.update_layout(clickmode='event+select')
            
            # Captura o clique na pizza
            selecao_pizza = plotly_events(fig_pizza, click_event=True, hover_event=False, override_height=350)
            
            if len(selecao_pizza) > 0:
                sexo_clicado = fig_pizza.data[0].labels[selecao_pizza[0]['pointNumber']]
                if st.session_state.clique_sexo != sexo_clicado:
                    st.session_state.clique_sexo = sexo_clicado
                    st.rerun()
        else:
            st.info("Sem dados.")

    with row1_col2:
        st.subheader("Distribuição por Faixa Etária (Clique para Filtrar)")
        if len(df_filtrado) > 0:
            df_idade_base = df[(df["Ano"].isin(anos_selecionados)) & (df["Setor_Atendimento"].isin(setores_selecionados)) & (df["Especialidade_Atendimento"].isin(especialidades_selecionadas))]
            if st.session_state.clique_sexo:
                df_idade_base = df_idade_base[df_idade_base["Sexo"] == st.session_state.clique_sexo]
                
            df_idade = df_idade_base.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
            df_idade['Faixa_Etaria'] = pd.Categorical(df_idade['Faixa_Etaria'], categories=[f"{i}-{i+9}" for i in range(0, 120, 10)] + ['Não Informada'], ordered=True)
            df_idade = df_idade.sort_values('Faixa_Etaria')
            
            fig_idade = px.bar(df_idade, x='Faixa_Etaria', y='Quantidade', labels={'Faixa_Etaria': 'Idade', 'Quantidade': 'Pacientes'}, color='Quantidade', color_continuous_scale='Blues')
            
            # Captura o clique na barra de faixas etárias
            selecao_barra = plotly_events(fig_idade, click_event=True, hover_event=False, override_height=350)
            
            if len(selecao_barra) > 0:
                faixa_clicada = df_idade.iloc[selecao_barra[0]['pointIndex']]['Faixa_Etaria']
                if st.session_state.clique_faixa != faixa_clicada:
                    st.session_state.clique_faixa = faixa_clicada
                    st.rerun()
        else:
            st.info("Sem dados.")

    # --- ROW 2: GRÁFICOS QUE REAGEM AOS CLIQUES ---
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("Linha do Tempo de Atendimentos (Por Mês)")
        if len(df_filtrado) > 0:
            df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos').sort_values('Ano_Mes')
            fig_linha = px.bar(df_mes, x='Ano_Mes', y='Atendimentos', labels={'Ano_Mes': 'Mês/Ano', 'Atendimentos': 'Qtd'}, color_discrete_sequence=['#4A90E2'])
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

    with row2_col2:
        st.subheader("Top 10 Doenças Mais Frequentes (CID)")
        if len(df_filtrado) > 0:
            df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total').sort_values(by='Total', ascending=False).head(10)
            fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença', labels={'Código_CID': 'CID', 'Total': 'Atendimentos'}, color='Total', color_continuous_scale='Purples')
            fig_cid.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cid, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

    # --- TABELA DE DADOS ---
    st.markdown("---")
    st.subheader("Visualização dos Dados Filtrados")
    df_exibicao = df_filtrado.copy()
    df_exibicao['Idade_Exibição'] = df_exibicao['Idade_Tratada'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "Inválida (>115)")
    st.dataframe(df_exibicao[['Idade_Exibição', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']], use_container_width=True)

except Exception as e:
    st.error(f"Erro ao processar os dados. Detalhes: {e}")

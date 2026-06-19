import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página e tema visual
st.set_page_config(
    page_title="HGuJP - Login Sistema", 
    page_icon="🏥",
    layout="wide"
)

# --- INJEÇÃO DE IDENTIDADE VISUAL (TEMA DARK HGuJP) ---
st.markdown("""
    <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .main-title {
            color: #FFFFFF; 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 700;
            border-left: 5px solid #4CAF50; 
            padding-left: 15px;
            margin-bottom: 5px;
        }
        .sub-title {
            color: #A0AAB2;
            font-size: 14px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
        div[data-testid="stMetricValue"] {
            color: #64B5F6 !important;
            font-weight: bold;
        }
        div[data-testid="stMetricLabel"] {
            color: #E0E0E0 !important;
            font-weight: 500 !important;
        }
        .custom-hr {
            border: 0;
            height: 2px;
            background-image: linear-gradient(to right, #4CAF50, #1E88E5, rgba(0,0,0,0));
            margin-top: 20px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONTROLO DE AUTENTICAÇÃO DIRETO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# SE NÃO ESTIVER AUTENTICADO, MOSTRA APENAS A TELA DE LOGIN
if not st.session_state.autenticado:
    st.markdown('<div style="text-align: center; margin-top: 40px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="display: inline-block; text-align: left;">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Diretoria de Saúde — Controlo de Acesso Restrito (HGuJP)</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.2, 1])
    
    with col_central:
        st.markdown("<h3 style='color: #64B5F6;'>Autenticação</h3>", unsafe_allow_html=True)
        usuario = st.text_input("Utilizador / Identidade Militar:", key="input_user")
        senha = st.text_input("Palavra-passe:", type="password", key="input_pass")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            if usuario == "admin" and senha == "hgujp2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Utilizador ou Palavra-passe incorretos.")
                
    st.stop() # FORÇA O STREAMLIT A PARAR AQUI E NÃO EXECUTAR MAIS NADA PARA BAIXO

# --- CASO ESTEJA AUTENTICADO, O DASHBOARD COMPLETO É EXECUTADO ---
if st.sidebar.button("🔒 Terminar Sessão (Logout)"):
    st.session_state.autenticado = False
    st.rerun()

st.sidebar.markdown("<h3 style='color: #64B5F6;'>Filtros de Pesquisa</h3>", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diretoria de Saúde — Painel Analítico de Atendimentos Ambulatoriais (HGuJP)</p>', unsafe_allow_html=True)

def aplicar_layout_dark(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#FAFAFA',
        title_font_color='#FAFAFA',
        legend_font_color='#FAFAFA'
    )
    fig.update_xaxes(gridcolor='#262730', zerolinecolor='#262730')
    fig.update_yaxes(gridcolor='#262730', zerolinecolor='#262730')
    return fig

@st.cache_data
def load_data():
    df = pd.read_csv("dados.csv")
    df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
    df['Ano'] = df['Dia_Atendimento'].dt.year
    df['Ano_Mes'] = df['Dia_Atendimento'].dt.to_period('M').astype(str)
    df['Idade_Tratada'] = pd.to_numeric(df['Idade'], errors='coerce')
    df.loc[df['Idade_Tratada'] > 115, 'Idade_Tratada'] = None
    
    bins = list(range(0, 121, 10))
    labels = [f"{i}-{i+9}" for i in bins[:-1]]
    df['Faixa_Etaria'] = pd.cut(df['Idade_Tratada'], bins=bins, labels=labels, right=False)
    df['Faixa_Etaria'] = df['Faixa_Etaria'].astype(str).replace('nan', 'Não Informada')
    return df

try:
    df = load_data()

    anos_disponiveis = sorted(df["Ano"].unique(), reverse=True)
    anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
    
    idade_min, idade_max = 0, 115
    idade_selecionada = st.sidebar.slider("Intervalo de Idade Válida:", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))
    
    setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
    setores_selecionados = st.sidebar.multiselect("Selecione o Setor:", options=setores_disponiveis, default=setores_disponiveis)
    
    especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
    especialidades_selecionadas = st.sidebar.multiselect("Selecione a Especialidade:", options=especialidades_disponiveis, default=especialidades_disponiveis)
    
    sexo_selecionado = st.sidebar.multiselect("Selecione o Sexo:", options=df["Sexo"].unique(), default=df["Sexo"].unique())

    df_filtrado = df[
        (df["Ano"].isin(anos

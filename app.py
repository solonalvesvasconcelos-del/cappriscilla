import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import hashlib
import secrets
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA INSTRUÇÃO)
st.set_page_config(
    page_title="HGuJP - Sistema de Gestão", 
    page_icon="🏥",
    layout="wide"
)

# --- CONFIGURAÇÃO DE FICHEIROS DE SISTEMA ---
DB_USERS = "usuarios_db.json"
LOG_FILE = "sistema_logs.csv"

# --- FUNÇÕES AVANÇADAS DE CRIPTOGRAFIA (SALT + PBKDF2) ---
def gerar_senha_segura(senha_pura):
    """Gera um Salt aleatório e aplica PBKDF2 com 100.000 iterações."""
    salt = secrets.token_bytes(16)
    senha_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        senha_pura.encode('utf-8'), 
        salt, 
        100000
    )
    return salt.hex() + ":" + senha_hash.hex()

def verificar_senha_segura(senha_pura, senha_armazenada):
    """Extrai o salt e valida se a senha digitada bate com o registro de forma segura."""
    try:
        salt_hex, hash_original_hex = senha_armazenada.split(":")
        salt = bytes.fromhex(salt_hex)
        novo_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            senha_pura.encode('utf-8'), 
            salt, 
            100000
        )
        return secrets.compare_digest(novo_hash.hex(), hash_original_hex)
    except Exception:
        return False

# --- INICIALIZAÇÃO DE BANCO DE DADOS E LOGS ---
if not os.path.exists(DB_USERS):
    admin_senha_cripto = gerar_senha_segura("hgujp2026")
    dados_iniciais = {"admin": {"senha": admin_senha_cripto, "criado_em": str(datetime.now())}}
    with open(DB_USERS, "w") as f:
        json.dump(dados_iniciais, f)

if not os.path.exists(LOG_FILE):
    df_logs_init = pd.DataFrame(columns=["Data_Hora", "Utilizador", "Evento", "Status"])
    df_logs_init.to_csv(LOG_FILE, index=False)

# --- FUNÇÕES DE AUDITORIA E USUÁRIOS ---
def registar_log(usuario, evento, status):
    """Regista um evento de auditoria no ficheiro CSV."""
    novo_log = {
        "Data_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Utilizador": usuario if usuario else "ANÓNIMO",
        "Evento": evento,
        "Status": status
    }
    df_novo = pd.DataFrame([novo_log])
    df_novo.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

def carregar_usuarios():
    with open(DB_USERS, "r") as f:
        return json.load(f)

def salvar_usuario(usuario, senha_pura):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    usuarios[usuario] = {
        "senha": gerar_senha_segura(senha_pura), 
        "criado_em": str(datetime.now())
    }
    with open(DB_USERS, "w") as f:
        json.dump(usuarios, f)
    return True

# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

# --- INJEÇÃO DE IDENTIDADE VISUAL (TEMA DARK HGuJP) ---
estilo_css = """
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .main-title {
        color: #FFFFFF; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700;
        border-left: 5px solid #4CAF50; padding-left: 15px; margin-bottom: 5px;
    }
    .sub-title { color: #A0AAB2; font-size: 14px; margin-top: -10px; margin-bottom: 25px; }
    div[data-testid="stMetricValue"] { color: #64B5F6 !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #E0E0E0 !important; font-weight: 500 !important; }
    .custom-hr {
        border: 0; height: 2px; background-image: linear-gradient(to right, #4CAF50, #1E88E5, rgba(0,0,0,0));
        margin-top: 20px; margin-bottom: 20px;
    }
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# --- TELA DE AUTENTICAÇÃO E CADASTRO ---
def tela_autenticacao():
    st.markdown('<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="display: inline-block; text-align: left;">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Diretoria de Saúde — Controlo de Atendimentos Ambulatoriais (HGuJP)</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    aba_login, aba_cadastro = st.tabs(["🔑 Aceder ao Sistema", "➕ Criar Utilizador Novo"])
    
    with aba_login:
        _, col_central, _ = st.columns([1, 1.5, 1])
        with col_central:
            with st.form(key="form_login"):
                st.markdown("<h3 style='color: #64B5F6; margin-top: 0;'>Identificação</h3>", unsafe_allow_html=True)
                usuario = st.text_input("Identidade Militar / Utilizador:", placeholder="Ex: sgt.solon")
                senha = st.text_input("Palavra-passe:", type="password", placeholder="******")
                botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
                
                if botao_login:
                    usuarios = carregar_usuarios()
                    if usuario in usuarios and verificar_senha_segura(senha, usuarios[usuario]["senha"]):
                        st.session_state.autenticado = True
                        st.session_state.usuario_atual = usuario
                        registar_log(usuario, "Login no Sistema", "Sucesso")
                        st.success("Autenticação efetuada com sucesso!")
                        st.rerun()
                    else:
                        registar_log(usuario, "Tentativa de Login", "Falha - Credenciais Incorretas")
                        st.error("Utilizador ou Palavra-passe incorretos. Acesso negado.")

    with aba_cadastro:
        _, col_central, _ = st.columns([1, 1.5, 1])
        with col_central:
            with st.form(key="form_cadastro"):
                st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>Registar Novo Operador</h3>", unsafe_allow_html=True)
                novo_usuario = st.text_input("Definir Nome de Utilizador:", placeholder="Ex: ten.silva")
                nova_senha = st.text_input("Definir Palavra-passe:", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_senha = st.text_input("Confirmar Palavra-passe:", type="password")
                botao_cadastrar = st.form_submit_button("Criar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if len(novo_usuario) < 3 or len(nova_senha) < 6:
                        st.error("O utilizador deve ter 3+ caracteres e a senha 6+ caracteres.")
                    elif nova_senha != confirmar_senha:
                        st.error("As palavras-passe não coincidem.")
                    else:
                        if salvar_usuario(novo_usuario, nova_senha):
                            operador = st.session_state.usuario_atual if st.session_state.usuario_atual else "Cadastro Inicial"
                            registar_log(operador, f"Criou utilizador: {novo_usuario}", "Sucesso")
                            st.success(f"Utilizador '{novo_usuario}' criado com sucesso! Use a aba ao lado para entrar.")
                        else:
                            st.error("Este nome de utilizador já se encontra registado no sistema.")

# --- CONTROLO DE FLUXO PRINCIPAL ---
if not st.session_state.autenticado:
    tela_autenticacao()
else:
    # --- BARRA LATERAL ADMINISTRATIVA ---
    if st.sidebar.button("🔒 Terminar Sessão (Logout)", use_container_width=True):
        registar_log(st.session_state.usuario_atual, "Logout do Sistema", "Sucesso")
        st.session_state.autenticado = False
        st.session_state.usuario_atual = None
        st.rerun()

    st.sidebar.markdown(f"👤 Operador: **{st.session_state.usuario_atual}**")
    st.sidebar.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
    
    modo_visao = st.sidebar.radio("Navegação do Sistema:", ["📊 Dashboard Ambulatorial", "📜 Logs de Auditoria"])

    # --- VISÃO 1: DASHBOARD DE SAÚDE ---
    if modo_visao == "📊 Dashboard Ambulatorial":
        st.markdown('<h1 class="main-title">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">Diretoria de Saúde — Painel Analítico de Atendimentos Ambulatoriais (HGuJP)</p>', unsafe_allow_html=True)

        def aplicar_layout_dark(fig):
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_color='#FAFAFA', title_font_color='#FAFAFA', legend_font_color='#FAFAFA'
            )
            fig.update_xaxes(gridcolor='#262730', zerolinecolor='#262730')
            fig.update_yaxes(gridcolor='#262730', zerolinecolor='#262730')
            return fig

        @st.cache_data
        def load_data():
            df = pd.read_csv("dados.csv")
            df['Dia_Atendimento'] = pd.to_datetime(df['Dia_Atendimento'])
            df['Ref_Ano'] = df['Dia_Atendimento'].dt.year
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

            st.sidebar.markdown("<h3 style='color: #64B5F6;'>Filtros de Pesquisa</h3>", unsafe_allow_html=True)
            anos_disponiveis = sorted(df["Ref_Ano"].unique(), reverse=True)
            anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
            
            idade_min, idade_max = 0, 115
            idade_selecionada = st.sidebar.slider("Intervalo de

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
    page_title="HGuJP - Dashboard de Atendimentos", 
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

# --- FUNÇÕES DE AUDITORIA ---
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

# --- INJEÇÃO DE IDENTIDADE VISUAL SEGURO (TEMA DARK HGuJP) ---
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

# --- CÓDIGO PRINCIPAL DO DASHBOARD ---
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
    df['Ano'] = df['Dia_Atendimento'].dt.year
    df['Ano_Mes'] = df['Dia_Atendimento'].dt.to_period('M').astype(str)
    df['Idade_Tratada'] = pd.to_numeric(df['Idade'], errors='coerce')
    df.loc[df['Idade_Tratada'] > 115, 'Idade_Tratada'] = None
    
    bins = list(range(0, 121, 10))
    labels =

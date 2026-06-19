import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import hashlib
import secrets
from datetime import datetime

# Configuração da página e tema visual
st.set_page_config(
    page_title="HGuJP - Gestão e Dashboard", 
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
    # Cria o admin mestre inicial usando a nova criptografia segura
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
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        .main-title {
            color: #FFFFFF; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700;
            border-left: 5px solid #4CAF50; padding-left: 15px; margin-bottom: 5px;
        }
        .sub-title { color: #A0AAB2;

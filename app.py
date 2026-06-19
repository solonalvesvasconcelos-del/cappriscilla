import streamlit as st

# Configuração da página de Login
st.set_page_config(
    page_title="HGuJP - Autenticação",
    page_icon="🏥",
    layout="centered"
)

# Inicializa a variável de controlo de acesso se ela não existir
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- CSS TEMA DARK + OCULTAR NAVEGAÇÃO NATIVA ---
st.markdown("""
    <style>
        /* Remove o menu lateral de páginas nativo do Streamlit */
        [data-testid="stSidebarNav"] {display: none !important;}
        
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        .main-title {
            color: #FFFFFF; font-family: sans-serif; font-weight: 700;
            border-left: 5px solid #4CAF50; padding-left: 15px;
        }
        .sub-title { color: #A0AAB2; font-size: 14px; }
        
        /* Ajuste para esconder a barra lateral inteira na tela de login se quiser */
        section[data-testid="stSidebar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diretoria de Saúde — Controlo de Acesso Restrito (HGuJP)</p>', unsafe_allow_html=True)

# Se já estiver autenticado, avisa e dá o botão de clique para o caminho correto
if st.session_state.autenticado:
    st.success("🔓 Você já se encontra autenticado no sistema.")
    st.info("Clique no botão abaixo para prosseguir para o painel de dados:")
    
    # Link direto para a página dentro da pasta /pages (repare no nome adaptado pelo Streamlit)
    st.markdown('<a href="/1_Dashboard" target="_self"><button style="width:100%; padding:10px; background-color:#1E88E5; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">Aceder ao Dashboard Ambulatorial</button></a>', unsafe_allow_html=True)

else:
    st.markdown("### Autenticação de Utilizador")
    usuario = st.text_input("Utilizador / Identidade Militar:", key="login_user")
    senha = st.text_input("Palavra-passe:", type="password", key="login_pass")

    if st.button("Entrar no Sistema", use_container_width=True):
        if usuario == "admin" and senha == "hgujp2026":
            st.session_state.autenticado = True
            st.success("Autenticação efetuada com sucesso!")
            st.rerun()
        else:
            st.error("Utilizador ou Palavra-passe incorretos.")

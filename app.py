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

# --- CSS TEMA DARK ---
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        .main-title {
            color: #FFFFFF; font-family: sans-serif; font-weight: 700;
            border-left: 5px solid #4CAF50; padding-left: 15px;
        }
        .sub-title { color: #A0AAB2; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Diretoria de Saúde — Controlo de Acesso Restrito (HGuJP)</p>', unsafe_allow_html=True)

st.markdown("### Autenticação de Utilizador")
usuario = st.text_input("Utilizador / Identidade Militar:", key="login_user")
senha = st.text_input("Palavra-passe:", type="password", key="login_pass")

if st.button("Entrar no Sistema", use_container_width=True):
    if usuario == "admin" and senha == "hgujp2026":
        st.session_state.autenticado = True
        st.success("Autenticação efetuada com sucesso! Utilize o menu lateral para aceder ao Dashboard.")
        st.rerun()
    else:
        st.error("Utilizador ou Palavra-passe incorretos.")

# Mensagem informativa de navegação se já estiver logado
if st.session_state.autenticado:
    st.info("🔓 Já se encontra autenticado. Clique em **Dashboard** no menu lateral esquerdo para visualizar os dados.")

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA (OBRIGATORIAMENTE A PRIMEIRA INSTRUÇÃO)
st.set_page_config(
    page_title="HGuJP - Sistema de Gestão", 
    page_icon="🏥",
    layout="wide"
)

# --- CONFIGURAÇÃO DE FICHEIROS DE SISTEMA ---
DB_USERS = "usuarios_db.json"
LOG_FILE = "sistema_logs.csv"
MAX_TENTATIVAS = 3 

# --- FUNÇÃO CENTRAL DE HORÁRIO LOCAL (BRASÍLIA UTC-3) ---
def obter_hora_brasilia():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(timezone.utc).astimezone(fuso_brasilia).replace(tzinfo=None)

# --- FUNÇÃO DE AUXÍLIO DE DESIGN GRÁFICO (TEMA PLOTLY DARK) ---
def aplicar_layout_dark(fig):
    """Aplica o tema escuro institucional nos gráficos do Plotly."""
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

# --- FUNÇÕES AVANÇADAS DE CRIPTOGRAFIA (SALT + PBKDF2) ---
def gerar_senha_segura(senha_pura):
    salt = secrets.token_bytes(16)
    senha_hash = hashlib.pbkdf2_hmac('sha256', senha_pura.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + senha_hash.hex()

def verificar_senha_segura(senha_pura, senha_armazenada):
    try:
        salt_hex, hash_original_hex = senha_armazenada.split(":")
        salt = bytes.fromhex(salt_hex)
        novo_hash = hashlib.pbkdf2_hmac('sha256', senha_pura.encode('utf-8'), salt, 100000)
        return secrets.compare_digest(novo_hash.hex(), hash_original_hex)
    except Exception:
        return False

# --- FUNÇÕES DE I/O OTIMIZADAS ---
def carregar_usuarios():
    with open(DB_USERS, "r") as f:
        return json.load(f)

def salvar_banco_usuarios(dados_usuarios):
    with open(DB_USERS, "w") as f:
        json.dump(dados_usuarios, f)

def registar_log(usuario, perfil, evento, status):
    novo_log = {
        "Data_Hora": obter_hora_brasilia().strftime("%Y-%m-%d %H:%M:%S"),
        "Utilizador": str(usuario) if usuario else "ANÓNIMO",
        "Perfil": str(perfil) if perfil else "N/A",
        "Evento": str(evento),
        "Status": str(status)
    }
    df_novo = pd.DataFrame([novo_log])
    df_novo.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

# --- INICIALIZAÇÃO CONTROLADA DE BASES ---
if not os.path.exists(DB_USERS):
    admin_senha_cripto = gerar_senha_segura("hgujp2026")
    agora = obter_hora_brasilia()
    dados_iniciais = {
        "admin": {
            "senha": admin_senha_cripto, "perfil": "admin", "ativo": True, "tentativas_falhas": 0,
            "criado_em": agora.strftime("%Y-%m-%d %H:%M:%S"), "validade_ate": (agora + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    salvar_banco_usuarios(dados_iniciais)

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["Data_Hora", "Utilizador", "Perfil", "Evento", "Status"]).to_csv(LOG_FILE, index=False)

def salvar_usuario(usuario, senha_pura, perfil_selecionado, ativo_selecionado):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    agora = obter_hora_brasilia()
    usuarios[usuario] = {
        "senha": gerar_senha_segura(senha_pura), "perfil": perfil_selecionado, "ativo": ativo_selecionado, "tentativas_falhas": 0,
        "criado_em": agora.strftime("%Y-%m-%d %H:%M:%S"), "validade_ate": (agora + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
    }
    salvar_banco_usuarios(usuarios)
    return True

def processar_exportacao_csv(dataframe_alvo):
    registar_log(st.session_state.get("usuario_atual", "admin"), st.session_state.get("perfil_atual", "admin"), "Exportou Dados Ambulatoriais (CSV)", "Sucesso")
    return dataframe_alvo.to_csv(index=False).encode('utf-8')

# --- ESTADOS DE SESSÃO ---
for chave, valor_padrao in [("autenticado", False), ("usuario_atual", None), ("perfil_atual", None), ("ultimo_filtro", {}), ("usuario_em_edicao", None)]:
    if chave not in st.session_state:
        st.session_state[chave] = valor_padrao

# --- INJEÇÃO DE IDENTIDADE VISUAL ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .main-title { color: #FFFFFF; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700; border-left: 5px solid #4CAF50; padding-left: 15px; margin-bottom: 5px; }
    .sub-title { color: #A0AAB2; font-size: 14px; margin-top: -10px; margin-bottom: 25px; }
    div[data-testid="stMetricValue"] { color: #64B5F6 !important; font-weight: bold; }
    .custom-hr { border: 0; height: 2px; background-image: linear-gradient(to right, #4CAF50, #1E88E5, rgba(0,0,0,0)); margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# --- PAINEL: GERENCIAR OPERADORES ---
def componente_gerenciar_operadores():
    st.markdown('<h1 class="main-title">GERENCIAMENTO DE OPERADORES</h1>', unsafe_allow_html=True)
    if st.session_state.perfil_atual != "admin":
        st.warning("⚠️ Permissão Negada.")
        return

    try:
        usuarios_cadastrados = carregar_usuarios()
        c_user, c_perf, c_status, c_criacao, c_validade, c_acao = st.columns([2, 1.5, 1, 2, 2, 1])
        c_user.markdown("**Usuário**")
        c_perf.markdown("**Perfil**")
        c_status.markdown("**Status**")
        c_criacao.markdown("**Criação**")
        c_validade.markdown("**Validade**")
        c_acao.markdown("**Ação**")
        st.markdown("<hr style='margin: 5px 0; border-color: #262730;'>", unsafe_allow_html=True)
        
        for nome_user, info in usuarios_cadastrados.items():
            c_user, c_perf, c_status, c_criacao, c_validade, c_acao = st.columns([2, 1.5, 1, 2, 2, 1])
            c_user.write(str(nome_user))
            c_perf.write(str(info.get("perfil", "viewer")).upper())
            c_status.write("🟢 Ativo" if info.get("ativo", True) and info.get("tentativas_falhas", 0) < MAX_TENTATIVAS else "🔒 Bloqueado/Inativo")
            c_criacao.write(str(info.get("criado_em", "N/A")))
            c_validade.write(str(info.get("validade_ate", "N/A")))
            if c_acao.button("📝 Editar", key=f"btn_edit_{nome_user}", use_container_width=True):
                st.session_state.usuario_em_edicao = nome_user
                st.rerun()
    except Exception as e:
        st.error(f"Erro: {e}")

    if st.session_state.usuario_em_edicao:
        u_edit = st.session_state.usuario_em_edicao
        info_u = usuarios_cadastrados[u_edit]
        with st.form(key="form_edicao_operador"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                perfil_edit = st.selectbox("Alterar Perfil:", ["admin", "viewer"], index=0 if info_u.get("perfil") == "admin" else 1)
                ativo_edit = st.checkbox("Conta Ativa", value=info_u.get("ativo", True))
                desbloquear = st.checkbox("Zerar tentativas incorretas (Desbloquear)", value=False)
            with col_e2:
                nova_senha_edit = st.text_input("Nova Palavra-passe:", type="password")
                validade_edit_dt = st.date_input("Nova Data de Validade:", value=datetime.strptime(info_u.get("validade_ate"), "%Y-%m-%d %H:%M:%S").date())
            
            if st.columns(2)[0].form_submit_button("Salvar Alterações", use_container_width=True):
                usuarios_atualizados = carregar_usuarios()
                usuarios_atualizados[u_edit].update({"perfil": perfil_edit, "ativo": ativo_edit, "validade_ate": f"{validade_edit_dt} 23:59:59"})
                if desbloquear:
                    usuarios_atualizados[u_edit]["tentativas_falhas"] = 0
                if len(nova_senha_edit.strip()) >= 6:
                    usuarios_atualizados[u_edit]["senha"] = gerar_senha_segura(nova_senha_edit)
                salvar_banco_usuarios(usuarios_atualizados)
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, f"Modificou operador {u_edit}", "Sucesso")
                st.session_state.usuario_em_edicao = None
                st.rerun()

    with st.expander("➕ Cadastrar Novo Operador"):
        cadastrar_usuario_acao = False
        with st.form(key="form_cadastro_operador", clear_on_submit=True):
            novo_usuario = st.text_input("Nome de Utilizador:")
            perfil_novo = st.selectbox("Perfil de Acesso:", ["admin", "viewer"])
            ativo_novo = st.checkbox("Ativar na criação", value=True)
            nova_senha = st.text_input("Definir Palavra-passe:", type="password")
            if st.form_submit_button("Confirmar e Salvar Conta", use_container_width=True) and len(novo_usuario) >= 3 and len(nova_senha) >= 6:
                cadastrar_usuario_acao = True
        if cadastrar_usuario_acao and salvar_usuario(novo_usuario, nova_senha, perfil_novo, ativo_novo):
            registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, f"Criou utilizador '{novo_usuario}'", "Sucesso")
            st.rerun()

# --- TELA DE AUTENTICAÇÃO ---
def tela_autenticacao():
    st.markdown('<div style="text-align: center; margin-top: 50px;"><h1 class="main-title" style="display: inline-block;">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1></div>', unsafe_allow_html=True)
    _, col_central, _ = st.columns([1, 1.3, 1])
    with col_central:
        with st.form(key="form_login_unico"):
            usuario = st.text_input("Utilizador:")
            senha = st.text_input("Palavra-passe:", type="password")
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                usuarios = carregar_usuarios()
                if usuario in usuarios and verificar_senha_segura(senha, usuarios[usuario]["senha"]):
                    info_user = usuarios[usuario]
                    if not info_user.get("ativo", True) or info_user.get("tentativas_falhas", 0) >= MAX_TENTATIVAS:
                        st.error("⚠️ Conta bloqueada ou inativa.")
                        st.stop()
                    if obter_hora_brasilia() > datetime.strptime(info_user["validade_ate"], "%Y-%m-%d %H:%M:%S"):
                        st.error("❌ Credencial expirada.")
                        st.stop()
                    st.session_state.update({"autenticado": True, "usuario_atual": usuario, "perfil_atual": info_user.get("perfil", "viewer")})
                    registar_log(usuario, info_user.get("perfil", "viewer"), "Login no Sistema", "Sucesso")
                    st.rerun()
                else:
                    st.error("Credenciais incorretas.")

# --- CONTROLADOR DE FLUXO ---
if not st.session_state.get("autenticado", False):
    tela_autenticacao()
else:
    if st.sidebar.button("🔒 Terminar Sessão (Logout)", use_container_width=True):
        registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Logout do Sistema", "Sucesso")
        st.session_state.update({"autenticado": False, "usuario_atual": None, "perfil_atual": None, "usuario_em_edicao": None})
        st.rerun()

    st.sidebar.markdown(f"👤 Operador: **{st.session_state.usuario_atual}** ({str(st.session_state.perfil_atual).upper()})")
    opcoes_navegacao = ["📊 Dashboard Ambulatorial"]
    if st.session_state.perfil_atual == "admin":
        opcoes_navegacao.extend(["📜 Logs de Auditoria", "➕ Gerenciar Operadores"])
    modo_visao = st.sidebar.radio("Navegação:", opcoes_navegacao)

    # --- PERFORMANCE CACHE ---
    @st.cache_data(ttl=3600)
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

    if modo_visao == "📊 Dashboard Ambulatorial":
        st.markdown('<h1 class="main-title">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
        try:
            df = load_data()
            st.sidebar.markdown("<h3 style='color: #64B5F6;'>Filtros</h3>", unsafe_allow_html=True)
            busca_cid_doenca = st.sidebar.text_input("🔍 Buscar Código CID ou Patologia:").strip()
            
            anos_selecionados = st.sidebar.multiselect("Ano:", options=sorted(df["Ref_Ano"].unique(), reverse=True))
            idade_selecionada = st.sidebar.slider("Idade:", 0, 115, (0, 115))
            setores_selecionados = st.sidebar.multiselect("Setor:", options=sorted(df["Setor_Atendimento"].dropna().unique()))
            especialidades_selecionadas = st.sidebar.multiselect("Especialidade:", options=sorted(df["Especialidade_Atendimento"].unique()))
            sexo_selecionado = st.sidebar.multiselect("Sexo:", options=df["Sexo"].unique(), default=df["Sexo"].unique())

            df_filtrado = df.copy()
            if busca_cid_doenca:
                df_filtrado = df_filtrado[df_filtrado["Código_CID"].str.contains(busca_cid_doenca, case=False, na=False) | df_filtrado["Nome_Doença"].str.contains(busca_cid_doenca, case=False, na=False)]
            if anos_selecionados:
                df_filtrado = df_filtrado[df_filtrado["Ref_Ano"].isin(anos_selecionados)]
            if setores_selecionados:
                df_filtrado = df_filtrado[df_filtrado["Setor_Atendimento"].isin(setores_selecionados)]
            if especialidades_selecionadas:
                df_filtrado = df_filtrado[df_filtrado["Especialidade_Atendimento"].isin(especialidades_selecionadas)]
            if sexo_selecionado:
                df_filtrado = df_filtrado[df_filtrado["Sexo"].isin(sexo_selecionado)]
            
            df_filtrado = df_filtrado[(df_filtrado["Idade_Tratada"].between(idade_selecionada[0], idade_selecionada[1])) | (df_filtrado["Idade_Tratada"].isna())]

            # --- RENDIMENTO VISUAL ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
            col2.metric("Média de Idade", f"{df_filtrado['Idade_Tratada'].dropna().mean():.1f} anos" if len(df_filtrado) > 0 else "N/A")
            col3.metric("CIDs Únicos", f"{df_filtrado['Código_CID'].nunique()}")

            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

            if len(df_filtrado) > 0:
                row1_col1, row1_col2 = st.columns(2)
                with row1_col1:
                    st.subheader("📈 Atendimentos por Mês")
                    df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos')
                    st.plotly_chart(aplicar_layout_dark(px.bar(df_mes, x='Ano_Mes', y='Atendimentos', color_discrete_sequence=['#1E88E5'])), use_container_width=True)
                with row1_col2:
                    st.subheader("👥 Distribuição por Sexo")
                    st.plotly_chart(aplicar_layout_dark(px.pie(df_filtrado, names='Sexo', hole=0.4, color_discrete_sequence=['#1E88E5', '#4CAF50'])), use_container_width=True)
                
                row2_col1, row2_col2 = st.columns(2)
                with row2_col1:
                    st.subheader("📊 Faixa Etária")
                    df_idade = df_filtrado.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
                    st.plotly_chart(aplicar_layout_dark(px.bar(df_idade, x='Faixa_Etaria', y='Quantidade', color_discrete_sequence=['#4CAF50'])), use_container_width=True)
                with row2_col2:
                    st.subheader("📋 Top 10 Patologias (CID)")
                    df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total').sort_values(by='Total', ascending=False).head(10)
                    st.plotly_chart(aplicar_layout_dark(px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença', color_discrete_sequence=['#64B5F6'])), use_container_width=True)
            else:
                st.info("Selecione filtros válidos.")

            # --- EXPORTAÇÃO ---
            df_exibicao = df_filtrado.copy()
            df_exibicao['Idade_Exibição'] = df_exibicao['Idade_Tratada'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "Inválida")
            df_para_download = df_exibicao[['Idade_Exibição', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']]
            
            st.download_button(label="📥 Exportar Planilha Filtrada para CSV", data=processar_exportacao_csv(df_para_download), file_name="HGuJP_atendimentos.csv", mime="text/csv", use_container_width=True)
            st.dataframe(df_para_download, use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}")

    elif modo_visao == "📜 Logs de Auditoria" and st.session_state.perfil_atual == "admin":
        st.markdown('<h1 class="main-title">LOGS DE AUDITORIA DO SISTEMA</h1>', unsafe_allow_html=True)
        try:
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            st.dataframe(df_logs.iloc[::-1], use_container_width=True)
            if st.button("🚨 Limpar Histórico de Logs", use_container_width=True):
                pd.DataFrame(columns=["Data_Hora", "Utilizador", "Perfil", "Evento", "Status"]).to_csv(LOG_FILE, index=False)
                st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    elif modo_visao == "➕ Gerenciar Operadores" and st.session_state.perfil_atual == "admin":
        componente_gerenciar_operadores()

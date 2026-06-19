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
MAX_TENTATIVAS = 3  # Limite para bloqueio de segurança

# --- FUNÇÃO CENTRAL DE HORÁRIO LOCAL (BRASÍLIA UTC-3) ---
def obter_hora_brasilia():
    """Retorna o datetime atual ajustado para o fuso horário de Brasília (UTC-3)."""
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(timezone.utc).astimezone(fuso_brasilia).replace(tzinfo=None)

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
    """Extrai o salt e valida se a senha digitada bate com o registro."""
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

# --- FUNÇÕES DE CARREGAMENTO E SALVAMENTO ---
def carregar_usuarios():
    with open(DB_USERS, "r") as f:
        return json.load(f)

def salvar_banco_usuarios(dados_usuarios):
    with open(DB_USERS, "w") as f:
        json.dump(dados_usuarios, f)

# --- INICIALIZAÇÃO DO BANCO DE DADOS E ESTRUTURAS ---
if not os.path.exists(DB_USERS):
    admin_senha_cripto = gerar_senha_segura("hgujp2026")
    agora = obter_hora_brasilia()
    validade = agora + timedelta(days=365)
    dados_iniciais = {
        "admin": {
            "senha": admin_senha_cripto, 
            "perfil": "admin",
            "ativo": True,
            "tentativas_falhas": 0,
            "criado_em": agora.strftime("%Y-%m-%d %H:%M:%S"),
            "validade_ate": validade.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    salvar_banco_usuarios(dados_iniciais)
else:
    try:
        usuarios_atuais = carregar_usuarios()
        alteracao_detectada = False
        agora = obter_hora_brasilia()
        
        for usuario, info in usuarios_atuais.items():
            if "tentativas_falhas" not in info:
                usuarios_atuais[usuario]["tentativas_falhas"] = 0
                alteracao_detectada = True
            if "ativo" not in info:
                usuarios_atuais[usuario]["ativo"] = True
                alteracao_detectada = True
            if "validade_ate" not in info:
                try:
                    criado_em = datetime.strptime(info.get("criado_em", agora.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                except:
                    criado_em = agora
                usuarios_atuais[usuario]["validade_ate"] = (criado_em + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
                alteracao_detectada = True
        
        if alteracao_detectada:
            salvar_banco_usuarios(usuarios_atuais)
    except Exception:
        pass

if not os.path.exists(LOG_FILE):
    df_logs_init = pd.DataFrame(columns=["Data_Hora", "Utilizador", "Perfil", "Evento", "Status"])
    df_logs_init.to_csv(LOG_FILE, index=False)

# --- FUNÇÕES DE AUDITORIA ---
def registar_log(usuario, perfil, evento, status):
    """Regista um evento de auditoria detalhado no ficheiro CSV."""
    novo_log = {
        "Data_Hora": obter_hora_brasilia().strftime("%Y-%m-%d %H:%M:%S"),
        "Utilizador": str(usuario) if usuario else "ANÓNIMO",
        "Perfil": str(perfil) if perfil else "N/A",
        "Evento": str(evento),
        "Status": str(status)
    }
    df_novo = pd.DataFrame([novo_log])
    df_novo.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

def salvar_usuario(usuario, senha_pura, perfil_selecionado, ativo_selecionado):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    agora = obter_hora_brasilia()
    validade = agora + timedelta(days=365)
    usuarios[usuario] = {
        "senha": gerar_senha_segura(senha_pura), 
        "perfil": perfil_selecionado,
        "ativo": ativo_selecionado,
        "tentativas_falhas": 0,
        "criado_em": agora.strftime("%Y-%m-%d %H:%M:%S"),
        "validade_ate": validade.strftime("%Y-%m-%d %H:%M:%S")
    }
    salvar_banco_usuarios(usuarios)
    return True

def processar_exportacao_csv(dataframe_alvo):
    """Gera a string CSV dos dados filtrados e armazena a ação no arquivo de auditoria."""
    registar_log(
        st.session_state.get("usuario_atual", "admin"), 
        st.session_state.get("perfil_atual", "admin"), 
        "Exportou Dados Ambulatoriais (CSV)", 
        "Sucesso"
    )
    return dataframe_alvo.to_csv(index=False).encode('utf-8')

# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "perfil_atual" not in st.session_state:
    st.session_state.perfil_atual = None
if "ultimo_filtro" not in st.session_state:
    st.session_state.ultimo_filtro = {}
if "usuario_em_edicao" not in st.session_state:
    st.session_state.usuario_em_edicao = None

# --- INJEÇÃO DE IDENTIDADE VISUAL COM REMOÇÃO DE MENUS NATIVOS ---
estilo_css = """
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
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


# --- PAINEL: GERENCIAR OPERADORES (RESTRITO AO PERFIL ADMIN) ---
def componente_gerenciar_operadores():
    st.markdown('<h1 class="main-title">GERENCIAMENTO DE OPERADORES</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">HGuJP — Controle de Credenciais, Níveis de Acesso e Perfis</p>', unsafe_allow_html=True)
    
    if st.session_state.perfil_atual != "admin":
        st.warning("⚠️ Permissão Negada. Painel restrito ao perfil Administrador.")
        return

    st.subheader("👥 Operadores Cadastrados no Sistema")
    try:
        usuarios_cadastrados = carregar_usuarios()
        
        c_user, c_perf, c_status, c_criacao, c_validade, c_acao = st.columns([2, 1.5, 1, 2, 2, 1])
        c_user.markdown("**Usuário**")
        c_perf.markdown("**Perfil**")
        c_status.markdown("**Status**")
        c_criacao.markdown("**Criação**")
        c_validade.markdown("**Validade (1 Ano)**")
        c_acao.markdown("**Ação**")
        st.markdown("<hr style='margin: 5px 0; border-color: #262730;'>", unsafe_allow_html=True)
        
        for nome_user, info in usuarios_cadastrados.items():
            c_user, c_perf, c_status, c_criacao, c_validade, c_acao = st.columns([2, 1.5, 1, 2, 2, 1])
            c_user.write(str(nome_user))
            c_perf.write(str(info.get("perfil", "viewer")).upper())
            
            is_ativo = info.get("ativo", True)
            falhas = info.get("tentativas_falhas", 0)
            status_txt = "🟢 Ativo" if is_ativo else "🔴 Inativo"
            if falhas >= MAX_TENTATIVAS:
                status_txt = "🔒 Bloqueado (Força Bruta)"
            c_status.write(status_txt)
            
            c_criacao.write(str(info.get("criado_em", "N/A")))
            c_validade.write(str(info.get("validade_ate", "N/A")))
            
            if c_acao.button("📝 Editar", key=f"btn_edit_{nome_user}", use_container_width=True):
                st.session_state.usuario_em_edicao = nome_user
                st.rerun()
                
    except Exception as e:
        st.error(f"Erro ao carregar lista de utilizadores: {e}")

    if st.session_state.usuario_em_edicao:
        st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)
        u_edit = st.session_state.usuario_em_edicao
        info_u = usuarios_cadastrados[u_edit]
        
        st.subheader(f"⚙️ Editando Operador: {u_edit}")
        with st.form(key="form_edicao_operador"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                perfil_edit = st.selectbox("Alterar Perfil:", ["admin", "viewer"], index=0 if info_u.get("perfil") == "admin" else 1)
                ativo_edit = st.checkbox("Conta Ativa", value=info_u.get("ativo", True))
                desbloquear = st.checkbox("Zerar tentativas de login incorretas (Desbloquear)", value=False)
            with col_e2:
                nova_senha_edit = st.text_input("Nova Palavra-passe (Em branco mantém atual):", type="password")
                data_val_atual = datetime.strptime(info_u.get("validade_ate"), "%Y-%m-%d %H:%M:%S")
                validade_edit_dt = st.date_input("Nova Data de Validade:", value=data_val_atual.date())
            
            c_b1, c_b2 = st.columns(2)
            submit_edicao = c_b1.form_submit_button("Salvar Alterações", use_container_width=True)
            cancel_edicao = c_b2.form_submit_button("Cancelar Edição", use_container_width=True)
            
            if submit_edicao:
                usuarios_atualizados = carregar_usuarios()
                usuarios_atualizados[u_edit]["perfil"] = perfil_edit
                usuarios_atualizados[u_edit]["ativo"] = ativo_edit
                usuarios_atualizados[u_edit]["validade_ate"] = f"{validade_edit_dt} 23:59:59"
                
                if desbloquear:
                    usuarios_atualizados[u_edit]["tentativas_falhas"] = 0
                
                if len(nova_senha_edit.strip()) >= 6:
                    usuarios_atualizados[u_edit]["senha"] = gerar_senha_segura(nova_senha_edit)
                    log_msg = f"Modificou dados e senha do usuário '{u_edit}'"
                elif len(nova_senha_edit.strip()) > 0:
                    st.error("A nova senha precisa ter no mínimo 6 caracteres!")
                    st.stop()
                else:
                    log_msg = f"Modificou dados estruturais do usuário '{u_edit}'"
                
                salvar_banco_usuarios(usuarios_atualizados)
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, log_msg, "Sucesso")
                st.success(f"Dados do operador '{u_edit}' atualizados!")
                st.session_state.usuario_em_edicao = None
                st.rerun()
                
            if cancel_edicao:
                st.session_state.usuario_em_edicao = None
                st.rerun()

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # --- CORREÇÃO DO LOG DE CADASTRO ---
    with st.expander("➕ Cadastrar Novo Operador / Utilizador"):
        _, col_central, _ = st.columns([1, 1.5, 1])
        with col_central:
            # Variáveis para capturar o resultado fora do formulário
            cadastrar_usuario_acao = False
            
            with st.form(key="form_cadastro_operador", clear_on_submit=True):
                st.markdown("<h4 style='color: #4CAF50; margin-top: 0;'>Dados do Novo Operador</h4>", unsafe_allow_html=True)
                novo_usuario = st.text_input("Nome de Utilizador:", placeholder="Ex: ten.silva")
                perfil_novo = st.selectbox("Perfil de Acesso:", ["admin", "viewer"])
                ativo_novo = st.checkbox("Ativar na criação", value=True)
                nova_senha = st.text_input("Definir Palavra-passe:", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_senha = st.text_input("Confirmar Palavra-passe:", type="password")
                botao_cadastrar = st.form_submit_button("Confirmar e Salvar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if len(novo_usuario) < 3 or len(nova_senha) < 6:
                        st.error("O utilizador deve ter pelo menos 3 caracteres e a senha 6+ caracteres.")
                    elif nova_senha != confirmar_senha:
                        st.error("As passwords não coincidem.")
                    else:
                        cadastrar_usuario_acao = True

            # Processamento seguro executado fora do escopo do st.form
            if cadastrar_usuario_acao:
                if salvar_usuario(novo_usuario, nova_senha, perfil_novo, ativo_novo):
                    registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, f"Criou utilizador '{novo_usuario}'", "Sucesso")
                    st.success(f"Utilizador '{novo_usuario}' registrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Este utilizador já existe no sistema.")


# --- TELA DE AUTENTICAÇÃO INICIAL ---
def tela_autenticacao():
    st.markdown('<div style="text-align: center; margin-top: 50px;">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title" style="display: inline-block; text-align: left;">HOSPITAL DE GUARNIÇÃO DE JOÃO PESSOA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Diretoria de Saúde — Controlo de Atendimentos Ambulatoriais (HGuJP)</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.3, 1])
    with col_central:
        with st.form(key="form_login_unico"):
            st.markdown("<h3 style='color: #64B5F6; margin-top: 0; text-align: center;'>🔑 Acesso ao Sistema</h3>", unsafe_allow_html=True)
            usuario = st.text_input("Identidade Militar / Utilizador:", placeholder="Ex: admin")
            senha = st.text_input("Palavra-passe:", type="password", placeholder="******")
            botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_login:
                usuarios = carregar_usuarios()
                if usuario in usuarios:
                    info_user = usuarios[usuario]
                    
                    if not info_user.get("ativo", True) or info_user.get("tentativas_falhas", 0) >= MAX_TENTATIVAS:
                        registar_log(usuario, info_user.get("perfil", "N/A"), "Tentativa de Login", "Bloqueado - Conta Inativa ou Bloqueada")
                        st.error("⚠️ Esta conta está inativa ou bloqueada por tentativas excessivas de login. Contate o Administrador.")
                        st.stop()
                        
                    if verificar_senha_segura(senha, info_user["senha"]):
                        info_user["tentativas_falhas"] = 0
                        usuarios[usuario] = info_user
                        salvar_banco_usuarios(usuarios)
                        
                        data_validade_str = info_user.get("validade_ate")
                        if data_validade_str:
                            data_validade = datetime.strptime(data_validade_str, "%Y-%m-%d %H:%M:%S")
                            if obter_hora_brasilia() > data_validade:
                                registar_log(usuario, info_user.get("perfil", "N/A"), "Tentativa de Login", "Bloqueado - Validade Expirada")
                                st.error("❌ A validade desta credencial expirou.")
                                st.stop()
                        
                        perfil_detectado = info_user.get("perfil", "viewer")
                        st.session_state.autenticado = True
                        st.session_state.usuario_atual = usuario
                        st.session_state.perfil_atual = perfil_detectado
                        
                        registar_log(usuario, perfil_detectado, "Login no Sistema", "Sucesso")
                        st.success("Autenticação efetuada!")
                        st.rerun()
                    else:
                        info_user["tentativas_falhas"] = info_user.get("tentativas_falhas", 0) + 1
                        avisos_restantes = MAX_TENTATIVAS - info_user["tentativas_falhas"]
                        
                        if info_user["tentativas_falhas"] >= MAX_TENTATIVAS:
                            info_user["ativo"] = False
                            registar_log(usuario, info_user.get("perfil", "N/A"), "Bloqueio de Segurança", f"Bloqueado após {MAX_TENTATIVAS} falhas")
                            st.error(f"❌ Conta bloqueada automaticamente devido a {MAX_TENTATIVAS} tentativas malsucedidas.")
                        else:
                            registar_log(usuario, "N/A", "Tentativa de Login", f"Falha - Restam {avisos_restantes} tentativas")
                            st.error(f"Utilizador ou Palavra-passe incorretos. Restam {avisos_restantes} tentativas.")
                            
                        usuarios[usuario] = info_user
                        salvar_banco_usuarios(usuarios)
                else:
                    registar_log(usuario, "N/A", "Tentativa de Login", "Falha - Usuário Inexistente")
                    st.error("Utilizador ou Palavra-passe incorretos.")


# --- CONTROLO DE FLUXO PRINCIPAL ---
if not st.session_state.get("autenticado", False):
    tela_autenticacao()
else:
    if st.sidebar.button("🔒 Terminar Sessão (Logout)", use_container_width=True):
        registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Logout (Logof) do Sistema", "Sucesso")
        st.session_state.autenticado = False
        st.session_state.usuario_atual = None
        st.session_state.perfil_atual = None
        st.session_state.usuario_em_edicao = None
        st.rerun()

    u_display = str(st.session_state.get("usuario_atual", "admin"))
    p_display = str(st.session_state.get("perfil_atual", "ADMIN")).upper()

    st.sidebar.markdown(f"👤 Operador: **{u_display}** ({p_display})")
    st.sidebar.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
    
    opcoes_navegacao = ["📊 Dashboard Ambulatorial"]
    if st.session_state.perfil_atual == "admin":
        opcoes_navegacao.append("📜 Logs de Auditoria")
        opcoes_navegacao.append("➕ Gerenciar Operadores")
        
    modo_visao = st.sidebar.radio("Navegação do Sistema:", opcoes_navegacao)

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
            
            busca_cid_doenca = st.sidebar.text_input("🔍 Buscar Código CID ou Patologia:", placeholder="Ex: Dengue, I10...").strip()

            anos_disponiveis = sorted(df["Ref_Ano"].unique(), reverse=True)
            anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
            
            idade_min, idade_max = 0, 115
            idade_selecionada = st.sidebar.slider("Intervalo de Idade Válida:", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))
            
            setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
            setores_selecionados = st.sidebar.multiselect("Selecione o Setor:", options=setores_disponiveis, default=setores_disponiveis)
            
            especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
            especialidades_selecionadas = st.sidebar.multiselect("Selecione a Especialidade:", options=especialidades_disponiveis, default=especialidades_disponiveis)
            
            sexo_selecionado = st.sidebar.multiselect("Selecione o Sexo:", options=df["Sexo"].unique(), default=df["Sexo"].unique())

            estado_filtros_atual = {
                "busca": busca_cid_doenca, "anos": anos_selecionados, "idade": idade_selecionada, 
                "setores": setores_selecionados, "especialidades": especialidades_selecionadas, "sexo": sexo_selecionado
            }
            if st.session_state.ultimo_filtro and st.session_state.ultimo_filtro != estado_filtros_atual:
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Alterou Filtros do Dashboard", "Sucesso")
            st.session_state.ultimo_filtro = estado_filtros_atual

            df_filtrado = df.copy()
            
            if busca_cid_doenca:
                cond_cid = df_filtrado["Código_CID"].str.contains(busca_cid_doenca, case=False, na=False)
                cond_nome = df_filtrado["Nome_Doença"].str.contains(busca_cid_doenca, case=False, na=False)
                df_filtrado = df_filtrado[cond_cid | cond_nome]

            if anos_selecionados:
                df_filtrado = df_filtrado[df_filtrado["Ref_Ano"].isin(anos_selecionados)]
            if setores_selecionados:
                df_filtrado = df_filtrado[df_filtrado["Setor_Atendimento"].isin(setores_selecionados)]
            if especialidades_selecionadas:
                df_filtrado = df_filtrado[df_filtrado["Especialidade_Atendimento"].isin(especialidades_selecionadas)]
            if sexo_selecionado:
                df_filtrado = df_filtrado[df_filtrado["Sexo"].isin(sexo_selecionado)]
                
            cond_valida = df_filtrado["Idade_Tratada"].between(idade_selecionada[0], idade_selecionada[1])
            cond_nula = df_filtrado["Idade_Tratada"].isna()
            df_filtrado = df_filtrado[cond_valida | cond_nula]

            # --- CARDS DE MÉTRICAS ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
            idades_validas = df_filtrado['Idade_Tratada'].dropna()
            col2.metric("Média de Idade (Válidas)", f"{idades_validas.mean():.1f} anos" if len(idades_validas) > 0 else "N/A")
            col3.metric("CIDs Únicos Identificados", f"{df_filtrado['Código_CID'].nunique()}")

            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

            # --- GRÁFICOS ---
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                st.subheader("📈 Linha do Tempo de Atendimentos (Por Mês)")
                if len(df_filtrado) > 0:
                    df_mes = df_filtrado.groupby('Ano_Mes').size().reset_index(name='Atendimentos').sort_values('Ano_Mes')
                    fig_linha = px.bar(df_mes, x='Ano_Mes', y='Atendimentos', labels={'Ano_Mes': 'Mês/Ano', 'Atendimentos': 'Atendimentos'}, color_discrete_sequence=['#1E88E5'])
                    fig_linha = aplicar_layout_dark(fig_linha)
                    st.plotly_chart(fig_linha, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado.")

            with row1_col2:
                st.subheader("👥 Distribuição por Sexo Biológico")
                if len(df_filtrado) > 0:
                    fig_pizza = px.pie(df_filtrado, names='Sexo', hole=0.4, color_discrete_sequence=['#1E88E5', '#4CAF50'])
                    fig_pizza = aplicar_layout_dark(fig_pizza)
                    st.plotly_chart(fig_pizza, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado.")

            row2_col1, row2_col2 = st.columns(2)

            with row2_col1:
                st.subheader("📊 Distribuição por Faixa Etária (Grupos de 10 Anos)")
                if len(df_filtrado) > 0:
                    df_idade = df_filtrado.groupby('Faixa_Etaria', observed=False).size().reset_index(name='Quantidade')
                    df_idade['Faixa_Etaria'] = pd.Categorical(df_idade['Faixa_Etaria'], categories=[f"{i}-{i+9}" for i in range(0, 120, 10)] + ['Não Informada'], ordered=True)
                    df_idade = df_idade.sort_values('Faixa_Etaria')
                    fig_idade = px.bar(df_idade, x='Faixa_Etaria', y='Quantidade', labels={'Faixa_Etaria': 'Grupo de Idade', 'Quantidade': 'Pacientes'}, color='Quantidade', color_continuous_scale='YlGnBu')
                    fig_idade = aplicar_layout_dark(fig_idade)
                    st.plotly_chart(fig_idade, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado.")

            with row2_col2:
                st.subheader("📋 Top 10 Patologias Mais Frequentes (Código CID)")
                if len(df_filtrado) > 0:
                    df_cid = df_filtrado.groupby(['Código_CID', 'Nome_Doença']).size().reset_index(name='Total').sort_values(by='Total', ascending=False).head(10)
                    fig_cid = px.bar(df_cid, x='Total', y='Código_CID', orientation='h', text='Nome_Doença', labels={'Código_CID': 'Código CID', 'Total': 'Casos'}, color='Total', color_continuous_scale='Blues')
                    fig_cid.update_layout(yaxis={'categoryorder':'total ascending'})
                    fig_cid = aplicar_layout_dark(fig_cid)
                    st.plotly_chart(fig_cid, use_container_width=True)
                else:
                    st.info("Nenhum dado encontrado.")

            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)
            st.subheader("🗃️ Registro de Dados Filtrados")
            
            df_exibicao = df_filtrado.copy()
            df_exibicao['Idade_Exibição'] = df_exibicao['Idade_Tratada'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "Inválida (>115)")
            
            df_para_download = df_exibicao[['Idade_Exibição', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']]
            
            st.download_button(
                label="📥 Exportar Planilha Filtrada para CSV",
                data=processar_exportacao_csv(df_para_download),
                file_name=f"HGuJP_atendimentos_{obter_hora_brasilia().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.dataframe(df_para_download, use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao processar os dados. Detalhes: {e}")

    # --- VISÃO 2: LOGS DE AUDITORIA (RESTRITO AO ADMIN) ---
    elif modo_visao == "📜 Logs de Auditoria" and st.session_state.perfil_atual == "admin":
        st.markdown('<h1 class="main-title">LOGS DE AUDITORIA DO SISTEMA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">HGuJP — Histórico de Acessos, Filtros e Ações de Utilizadores</p>', unsafe_allow_html=True)
        
        try:
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            df_logs = df_logs.iloc[::-1]
            
            c1, c2 = st.columns(2)
            c1.metric("Total de Eventos Gravados", len(df_logs))
            c2.metric("Falhas/Bloqueios Detetados", len(df_logs[df_logs["Status"].str.contains("Falha|Bloqueado", na=False)]))
            
            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)
            st.dataframe(df_logs, use_container_width=True)
            
            if st.button("🚨 Limpar Histórico de Logs", use_container_width=True):
                df_vazio = pd.DataFrame(columns=["Data_Hora", "Utilizador", "Perfil", "Evento", "Status"])
                df_vazio.to_csv(LOG_FILE, index=False)
                registar_log("admin", "admin", "Limpeza de Logs de Auditoria", "Sucesso")
                st.success("Histórico limpo!")
                st.rerun()
                    
        except Exception as e:
            st.error(f"Erro ao ler o ficheiro de auditoria: {e}")

    # --- VISÃO 3: GERENCIAR OPERADORES (RESTRITO AO ADMIN) ---
    elif modo_visao == "➕ Gerenciar Operadores" and st.session_state.perfil_atual == "admin":
        componente_gerenciar_operadores()

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

# --- FUNÇÕES DE CARREGAMENTO E SALVAMENTO ---
def carregar_usuarios():
    with open(DB_USERS, "r") as f:
        return json.load(f)

def salvar_banco_usuarios(dados_usuarios):
    with open(DB_USERS, "w") as f:
        json.dump(dados_usuarios, f)

# --- INICIALIZAÇÃO DE BANCO DE DADOS, LOGS E CONVERSÃO EM LOTE ---
if not os.path.exists(DB_USERS):
    admin_senha_cripto = gerar_senha_segura("hgujp2026")
    dados_iniciais = {
        "admin": {
            "senha": admin_senha_cripto, 
            "perfil": "admin",
            "criado_em": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        }
    }
    salvar_banco_usuarios(dados_iniciais)
else:
    # --- ASSEGURA QUE TODOS OS USUÁRIOS EXISTENTES SEJAM ADMIN ---
    try:
        usuarios_atuais = carregar_usuarios()
        alteracao_detectada = False
        
        for usuario, info in usuarios_atuais.items():
            if info.get("perfil") != "admin":
                usuarios_atuais[usuario]["perfil"] = "admin"
                alteracao_detectada = True
        
        if alteracao_detectada:
            salvar_banco_usuarios(usuarios_atuais)
    except Exception:
        pass

# Inicializa o arquivo de logs limpo com o cabeçalho correto de 5 colunas
if not os.path.exists(LOG_FILE):
    df_logs_init = pd.DataFrame(columns=["Data_Hora", "Utilizador", "Perfil", "Evento", "Status"])
    df_logs_init.to_csv(LOG_FILE, index=False)

# --- FUNÇÕES DE AUDITORIA ---
def registar_log(usuario, perfil, evento, status):
    """Regista um evento de auditoria detalhado no ficheiro CSV."""
    novo_log = {
        "Data_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Utilizador": usuario if usuario else "ANÓNIMO",
        "Perfil": perfil if perfil else "N/A",
        "Evento": evento,
        "Status": status
    }
    df_novo = pd.DataFrame([novo_log])
    df_novo.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

def salvar_usuario(usuario, senha_pura, perfil_selecionado):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    usuarios[usuario] = {
        "senha": gerar_senha_segura(senha_pura), 
        "perfil": perfil_selecionado,
        "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    salvar_banco_usuarios(usuarios)
    return True

# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "perfil_atual" not in st.session_state:
    st.session_state.perfil_atual = None
if "ultimo_filtro" not in st.session_state:
    st.session_state.ultimo_filtro = {}

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


# --- PAINEL: GERENCIAR OPERADORES (RESTRITO AO PERFIL ADMIN) ---
def componente_gerenciar_operadores():
    st.markdown('<h1 class="main-title">GERENCIAMENTO DE OPERADORES</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">HGuJP — Controle de Credenciais, Níveis de Acesso e Perfis</p>', unsafe_allow_html=True)
    
    if st.session_state.perfil_atual != "admin":
        st.warning("⚠️ Permissão Negada. Painel restrito ao perfil Administrador.")
        return

    # 1. LISTA DE OPERADORES EXISTENTES
    st.subheader("👥 Operadores Cadastrados no Sistema")
    try:
        usuarios_cadastrados = carregar_usuarios()
        lista_dados = []
        for nome_user, info in usuarios_cadastrados.items():
            lista_dados.append({
                "Nome de Utilizador": nome_user,
                "Perfil de Acesso": info.get("perfil", "viewer").upper(),
                "Data de Criação": info.get("criado_em", "N/A")
            })
        
        df_usuarios = pd.DataFrame(lista_dados)
        st.dataframe(df_usuarios, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar lista de utilizadores: {e}")

    st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

    # 2. EXPANDER PARA ADICIONAR OPERADOR COM PERFIL
    with st.expander("➕ Cadastrar Novo Operador / Utilizador"):
        _, col_central, _ = st.columns([1, 1.5, 1])
        with col_central:
            with st.form(key="form_cadastro_operador", clear_on_submit=True):
                st.markdown("<h4 style='color: #4CAF50; margin-top: 0;'>Dados do Novo Operador</h4>", unsafe_allow_html=True)
                novo_usuario = st.text_input("Nome de Utilizador:", placeholder="Ex: ten.silva")
                perfil_novo = st.selectbox("Perfil de Acesso:", ["admin", "viewer"], help="Admin: Acesso total | Viewer: Apenas relatórios")
                nova_senha = st.text_input("Definir Palavra-passe:", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_senha = st.text_input("Confirmar Palavra-passe:", type="password")
                botao_cadastrar = st.form_submit_button("Confirmar e Salvar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if len(novo_usuario) < 3 or len(nova_senha) < 6:
                        st.error("O utilizador deve ter pelo menos 3 caracteres e a senha 6+ caracteres.")
                    elif nova_senha != confirmar_senha:
                        st.error("As palavras-passe inseridas não coincidem.")
                    else:
                        if salvar_usuario(novo_usuario, nova_senha, perfil_novo):
                            registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, f"Criou utilizador '{novo_usuario}' com perfil '{perfil_novo}'", "Sucesso")
                            st.success(f"Utilizador '{novo_usuario}' registrado como {perfil_novo.upper()} com sucesso!")
                            st.rerun()
                        else:
                            st.error("Este nome de utilizador já se encontra registado no sistema.")


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
                if usuario in usuarios and verificar_senha_segura(senha, usuarios[usuario]["senha"]):
                    perfil_detectado = usuarios[usuario].get("perfil", "viewer")
                    st.session_state.autenticado = True
                    st.session_state.usuario_atual = usuario
                    st.session_state.perfil_atual = perfil_detectado
                    
                    registar_log(usuario, perfil_detectado, "Login no Sistema", "Sucesso")
                    st.success("Autenticação efetuada!")
                    st.rerun()
                else:
                    registar_log(usuario, "N/A", "Tentativa de Login", "Falha - Credenciais Incorretas")
                    st.error("Utilizador ou Palavra-passe incorretos. Acesso negado.")


# --- CONTROLO DE FLUXO PRINCIPAL ---
if not st.session_state.autenticado:
    tela_autenticacao()
else:
    # --- BARRA LATERAL ADMINISTRATIVA ---
    if st.sidebar.button("🔒 Terminar Sessão (Logout)", use_container_width=True):
        registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Logout (Logof) do Sistema", "Sucesso")
        st.session_state.autenticado = False
        st.session_state.usuario_atual = None
        st.session_state.perfil_atual = None
        st.rerun()

    st.sidebar.markdown(f"👤 Operador: **{st.session_state.usuario_atual}** ({st.session_state.perfil_atual.upper()})")
    st.sidebar.markdown("<div class='custom-hr'></div>", unsafe_allow_html=True)
    
    # CONSTRUÇÃO DINÂMICA DO MENU BASEADO NO PERFIL DE ACESSO
    opcoes_navegacao = ["📊 Dashboard Ambulatorial"]
    if st.session_state.perfil_atual == "admin":
        opcoes_navegacao.append("📜 Logs de Auditoria")
        opcoes_navegacao.append("➕ Gerenciar Operadores")
        
    modo_visao = st.sidebar.radio("Navegação do Sistema:", opcoes_navegacao)

    # --- VISÃO 1: DASHBOARD DE SAÚDE (ACESSO GERAL) ---
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
            
            # --- MONITORIZAÇÃO ATIVA DE FILTROS ---
            anos_disponiveis = sorted(df["Ref_Ano"].unique(), reverse=True)
            anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
            
            idade_min, idade_max = 0, 115
            idade_selecionada = st.sidebar.slider("Intervalo de Idade Válida:", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))
            
            setores_disponiveis = sorted(df["Setor_Atendimento"].dropna().unique())
            setores_selecionados = st.sidebar.multiselect("Selecione o Setor:", options=setores_disponiveis, default=setores_disponiveis)
            
            especialidades_disponiveis = sorted(df["Especialidade_Atendimento"].unique())
            especialidades_selecionadas = st.sidebar.multiselect("Selecione a Especialidade:", options=especialidades_disponiveis, default=especialidades_disponiveis)
            
            sexo_selecionado = st.sidebar.multiselect("Selecione o Sexo:", options=df["Sexo"].unique(), default=df["Sexo"].unique())

            # Lógica de comparação para detectar modificações em filtros
            estado_filtros_atual = {
                "anos": anos_selecionados, "idade": idade_selecionada, 
                "setores": setores_selecionados, "especialidades": especialidades_selecionadas, "sexo": sexo_selecionado
            }
            if st.session_state.ultimo_filtro and st.session_state.ultimo_filtro != estado_filtros_atual:
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Alterou Filtros do Dashboard", "Sucesso")
            st.session_state.ultimo_filtro = estado_filtros_atual

            # Filtros Sequenciais
            df_filtrado = df.copy()
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

            # --- MONITORIZAÇÃO DE CLIQUES EM ELEMENTOS ESPECÍFICOS ---
            col1, col2, col3 = st.columns(3)
            
            if col1.button("📊 Ver Detalhes: Total de Atendimentos", use_container_width=True):
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Clicou: Detalhes Total Atendimentos", "Sucesso")
            col1.metric("Total de Atendimentos", f"{len(df_filtrado)}")
            
            if col2.button("🩺 Ver Detalhes: Média de Idades", use_container_width=True):
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Clicou: Detalhes Média Idades", "Sucesso")
            idades_validas = df_filtrado['Idade_Tratada'].dropna()
            col2.metric("Média de Idade (Válidas)", f"{idades_validas.mean():.1f} anos" if len(idades_validas) > 0 else "N/A")
            
            if col3.button("🔬 Ver Detalhes: CIDs Únicos", use_container_width=True):
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Clicou: Detalhes CIDs Identificados", "Sucesso")
            col3.metric("CIDs Únicos Identificados", f"{df_filtrado['Código_CID'].nunique()}")

            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)

            # --- GRÁFICOS INTERATIVOS ---
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

            # --- TABELA E EXPORTAÇÃO SEGURO ---
            st.markdown('<div class="custom-hr"></div>', unsafe_allow_html=True)
            st.subheader("🗃️ Registro de Dados Filtrados")
            
            if st.button("📥 Exportar Planilha Filtrada para CSV", use_container_width=True):
                registar_log(st.session_state.usuario_atual, st.session_state.perfil_atual, "Exportou Dados Ambulatoriais (CSV)", "Sucesso")
                
            df_exibicao = df_filtrado.copy()
            df_exibicao['Idade_Exibição'] = df_exibicao['Idade_Tratada'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "Inválida (>115)")
            st.dataframe(df_exibicao[['Idade_Exibição', 'Faixa_Etaria', 'Sexo', 'Dia_Atendimento', 'Código_CID', 'Nome_Doença', 'Especialidade_Atendimento', 'Setor_Atendimento']], use_container_width=True)

        except Exception as e:
            st.error(f"Erro ao processar os dados. Detalhes: {e}")

    # --- VISÃO 2: LOGS DE AUDITORIA (RESTRITO AO ADMIN) ---
    elif modo_visao == "📜 Logs de Auditoria" and st.session_state.perfil_atual == "admin":
        st.markdown('<h1 class="main-title">LOGS DE AUDITORIA DO SISTEMA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">HGuJP — Histórico de Acessos, Cliques, Filtros e Ações de Utilizadores</p>', unsafe_allow_html=True)
        
        try:
            # Tratamento adaptivo: ignora linhas corrompidas antigas de 4 colunas se houverem
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            df_logs = df_logs.iloc[::-1]
            
            c1, c2 = st.columns(2)
            c1.metric("Total de Eventos Gravados", len(df_logs))
            c2.metric("Falhas de Login Detetadas", len(df_logs[df_logs["Status"].str.contains("Falha", na=False)]))
            
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

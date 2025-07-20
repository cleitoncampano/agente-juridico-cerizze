import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt
import json
import os
from datetime import datetime, timedelta

# === CONFIG DE AUTENTICAÇÃO ===
def carregar_config_auth():
    """Carrega configuração de autenticação do arquivo YAML"""
    if not os.path.exists('config/auth.yaml'):
        criar_config_inicial()
    
    with open('config/auth.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def criar_config_inicial():
    """Cria configuração inicial de usuários"""
    os.makedirs('config', exist_ok=True)
    
    # Hash das senhas
    senhas_hash = stauth.Hasher(['admin123', 'cerizze2024']).generate()
    
    config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'admin@cerizze.com',
                    'name': 'Administrador Cerizze',
                    'password': senhas_hash[0],
                    'role': 'admin',
                    'areas_permitidas': ['Todas']
                },
                'advogado1': {
                    'email': 'advogado@cerizze.com',
                    'name': 'Advogado Cerizze',
                    'password': senhas_hash[1],
                    'role': 'lawyer',
                    'areas_permitidas': ['Societário', 'Tributário', 'Empresarial']
                }
            }
        },
        'cookie': {
            'expiry_days': 7,
            'key': 'cerizze_auth_key_2024',
            'name': 'cerizze_auth_cookie'
        },
        'preauthorized': {
            'emails': ['admin@cerizze.com']
        }
    }
    
    with open('config/auth.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def inicializar_autenticacao():
    """Inicializa sistema de autenticação"""
    config = carregar_config_auth()
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    
    return authenticator, config

def exibir_login():
    """Exibe interface de login"""
    authenticator, config = inicializar_autenticacao()
    
    # Login widget
    name, authentication_status, username = authenticator.login()
    
    if authentication_status == False:
        st.error('❌ Usuário/senha incorretos')
        return None, None, None
    elif authentication_status == None:
        st.warning('👤 Por favor, insira suas credenciais')
        return None, None, None
    elif authentication_status:
        # Login bem-sucedido
        user_info = config['credentials']['usernames'][username]
        
        # Salva informações na sessão
        st.session_state.usuario_logado = user_info['email']
        st.session_state.nome_usuario = user_info['name']
        st.session_state.role_usuario = user_info['role']
        st.session_state.areas_permitidas = user_info['areas_permitidas']
        
        # Registra login
        registrar_atividade('login', username, user_info['email'])
        
        return authenticator, username, user_info
    
    return None, None, None

def registrar_atividade(acao: str, username: str, email: str):
    """Registra atividades dos usuários"""
    log_atividade = {
        'timestamp': datetime.now().isoformat(),
        'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'acao': acao,
        'username': username,
        'email': email,
        'ip': st.session_state.get('client_ip', 'unknown')
    }
    
    os.makedirs('data/logs', exist_ok=True)
    arquivo_atividade = f"data/logs/atividades_{datetime.now().strftime('%Y%m')}.jsonl"
    
    with open(arquivo_atividade, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_atividade, ensure_ascii=False) + '\n')

def verificar_permissao_area(area_solicitada: str) -> bool:
    """Verifica se usuário tem permissão para área específica"""
    if not st.session_state.get('areas_permitidas'):
        return False
    
    areas_permitidas = st.session_state.areas_permitidas
    
    # Admin tem acesso a tudo
    if 'Todas' in areas_permitidas:
        return True
    
    return area_solicitada in areas_permitidas

def exibir_info_usuario():
    """Exibe informações do usuário logado na sidebar"""
    if st.session_state.get('usuario_logado'):
        st.sidebar.markdown("### 👤 Usuário Logado")
        st.sidebar.write(f"**Nome:** {st.session_state.nome_usuario}")
        st.sidebar.write(f"**Email:** {st.session_state.usuario_logado}")
        st.sidebar.write(f"**Perfil:** {st.session_state.role_usuario}")
        
        # Áreas permitidas
        if st.session_state.areas_permitidas:
            st.sidebar.write("**Áreas permitidas:**")
            for area in st.session_state.areas_permitidas:
                st.sidebar.write(f"• {area}")

def filtrar_areas_por_usuario():
    """Retorna lista de áreas que o usuário pode acessar"""
    if not st.session_state.get('areas_permitidas'):
        return ["Societário"]  # Default
    
    areas_permitidas = st.session_state.areas_permitidas
    
    if 'Todas' in areas_permitidas:
        return ["Societário", "Tributário", "Trabalhista", "Cível", 
                "Empresarial", "Licitações", "Regulatório", "Ambiental"]
    
    return areas_permitidas

def obter_limite_consultas() -> int:
    """Retorna limite de consultas por usuário"""
    role = st.session_state.get('role_usuario', 'lawyer')
    
    limites = {
        'admin': 1000,  # Sem limite prático
        'lawyer': 50,   # 50 consultas por dia
        'intern': 10    # 10 consultas por dia
    }
    
    return limites.get(role, 10)

def verificar_limite_consultas() -> bool:
    """Verifica se usuário atingiu limite de consultas diário"""
    if not st.session_state.get('usuario_logado'):
        return False
    
    limite = obter_limite_consultas()
    if limite >= 1000:  # Admin
        return True
    
    # Conta consultas do dia atual
    hoje = datetime.now().strftime('%Y-%m-%d')
    arquivo_log = f"data/logs/interacoes_{datetime.now().strftime('%Y%m')}.jsonl"
    
    if not os.path.exists(arquivo_log):
        return True
    
    consultas_hoje = 0
    email_usuario = st.session_state.usuario_logado
    
    try:
        with open(arquivo_log, 'r', encoding='utf-8') as f:
            for linha in f:
                log = json.loads(linha)
                if (log.get('user') == email_usuario and 
                    log.get('data', '').startswith(hoje) and
                    log.get('status') == 'sucesso'):
                    consultas_hoje += 1
    except:
        pass
    
    return consultas_hoje < limite

# === INTEGRAÇÃO PRINCIPAL ===
def app_com_auth():
    """Função principal da aplicação com autenticação"""
    # Verifica se usuário está logado
    if not st.session_state.get('usuario_logado'):
        st.title("🏛️ Sistema Jurídico Cerizze")
        st.markdown("### Acesso Restrito")
        
        authenticator, username, user_info = exibir_login()
        
        if not authenticator:
            st.stop()
    
    # Usuário logado - continua com aplicação
    authenticator, config = inicializar_autenticacao()
    
    # Botão de logout na sidebar
    st.sidebar.title("⚙️ IA Cerizze")
    exibir_info_usuario()
    
    if st.sidebar.button("🚪 Logout"):
        registrar_atividade('logout', 
                          st.session_state.get('username', 'unknown'),
                          st.session_state.usuario_logado)
        
        # Limpa sessão
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Verificar limite de consultas
    if not verificar_limite_consultas():
        st.error("❌ Limite de consultas diário atingido!")
        st.info(f"Limite: {obter_limite_consultas()} consultas por dia")
        st.stop()
    
    return True
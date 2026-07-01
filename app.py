import streamlit as st
import sqlite3
import pandas as pd
import os
import re
from datetime import date 
import shutil
from datetime import datetime, timedelta
def formatar_tabela(df):
    # Aplica formatação: cores alternadas, realce no cabeçalho e alinhamento
    return df.style.set_properties(**{
        'text-align': 'left',
        'border-color': '#d1d1d1',
        'padding': '10px'
    }).set_table_styles([{
        'selector': 'th',
        'props': [('background-color', '#2c3e50'), ('color', 'white'), ('font-weight', 'bold')]
    }, {
        'selector': 'tr:nth-of-type(even)',
        'props': [('background-color', '#f2f2f2')]
    }])
# Configuração da página
st.set_page_config(page_title="Sistema Escolar Pro", layout="wide", page_icon="🎓")

# --- CSS PARA ESTILO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2c3e50; color: white; }
    .titulo-principal { font-size: 2.5em; color: #2c3e50; font-weight: bold; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSE DO SISTEMA ---
class SistemaEscolar:
    def __init__(self, db_name="escola.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, data_nascimento TEXT, turma TEXT, classe TEXT, comprovativo TEXT)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_curso TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS matriculas (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, curso_id INTEGER, status TEXT, valor REAL, data_reg TEXT,
                          FOREIGN KEY(aluno_id) REFERENCES alunos(id), FOREIGN KEY(curso_id) REFERENCES cursos(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, usuario TEXT, acao TEXT)''')
        self.conn.commit()

    def matricular(self, usuario, nome, data_nasc, turma, classe, nome_curso, valor, comprovativo):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO alunos (nome, data_nascimento, turma, classe, comprovativo) VALUES (?, ?, ?, ?, ?)", (nome, str(data_nasc), turma, classe, comprovativo))
        aluno_id = cursor.lastrowid
        cursor.execute("INSERT OR IGNORE INTO cursos (nome_curso) VALUES (?)", (nome_curso,))
        cursor.execute("SELECT id FROM cursos WHERE nome_curso = ?", (nome_curso,))
        curso_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id, status, valor, data_reg) VALUES (?, ?, ?, ?, ?)", (aluno_id, curso_id, "Ativo", valor, datetime.now().strftime("%Y-%m-%d")))
        self.conn.commit()
        cursor.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Matriculou: {nome} | Comp: {comprovativo}"))
        self.conn.commit()

    def listar_tudo(self):
        query = 'SELECT m.id AS Matrícula, a.nome AS Aluno, a.classe AS Classe, a.turma AS Turma, c.nome_curso AS Curso, m.valor AS Valor, m.data_reg AS Data, a.comprovativo AS Comprovativo FROM matriculas m JOIN alunos a ON m.aluno_id = a.id JOIN cursos c ON m.curso_id = c.id'
        try: return pd.read_sql_query(query, self.conn)
        except: return pd.DataFrame()

    def editar_matricula(self, usuario, mat_id, nome, turma, classe, valor):
        cursor = self.conn.cursor()
        cursor.execute("SELECT aluno_id FROM matriculas WHERE id = ?", (mat_id,))
        aluno_id = cursor.fetchone()[0]
        cursor.execute("UPDATE alunos SET nome = ?, turma = ?, classe = ? WHERE id = ?", (nome, turma, classe, aluno_id))
        cursor.execute("UPDATE matriculas SET valor = ? WHERE id = ?", (valor, mat_id))
        self.conn.commit()
        self.conn.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Editou ID: {mat_id}"))
        self.conn.commit()

    def deletar_matricula(self, usuario, mat_id):
        self.conn.execute("DELETE FROM matriculas WHERE id = ?", (mat_id,))
        self.conn.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Deletou ID: {mat_id}"))
        self.conn.commit()

def realizar_backup():
    if not os.path.exists("backups"): os.makedirs("backups")
    shutil.copy("escola.db", f"backups/escola_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

# --- INTERFACE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'sistema' not in st.session_state: st.session_state.sistema = SistemaEscolar()

if not st.session_state.logged_in:
    st.markdown('<h1 class="titulo-principal" style="margin-bottom: 50px;">Sistema de Gestão de Matrícula - Complexo Escolar DF</h1>', unsafe_allow_html=True)
    
    # Criamos 3 colunas: [Espaço, Login, Imagem, Espaço] para centralizar tudo
    # Isso evita que o conteúdo fique colado nas bordas da tela
    _, col_login, col_img, _ = st.columns([0.5, 2, 2, 0.5])
    
    with col_login:
        st.markdown("<br>", unsafe_allow_html=True) # Espaçamento superior
        st.subheader("🔐 Acesso Restrito")
        perfil = st.radio("Selecione o seu perfil:", ["Secretaria", "Dr.", "Aluno"])
        
        if perfil != "Aluno":
            pwd = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                if (perfil == "Secretaria" and pwd == "secretaria123") or (perfil == "Dr." and pwd == "doutor123"):
                    st.session_state.logged_in = True
                    st.session_state.user_role = perfil
                    st.rerun()
                else: 
                    st.error("Senha incorreta!")
        else:
            if st.button("Acessar Matrícula", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.user_role = "Aluno"
                st.rerun()
                
    with col_img:
        # Definimos uma largura fixa proporcional para a imagem não ficar gigante
        try:
            st.image("foto_escola.jpg", use_container_width=True)
        except:
            st.warning("Imagem não encontrada.")

else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    menu = st.sidebar.radio("Navegação", ["Início", "Dashboard", "Matricular", "Consultar", "Gerenciar", "Relatórios"] if st.session_state.user_role != "Aluno" else ["Matricular"])
    
    if menu == "Início":
        st.markdown('<h1 class="titulo-principal">Complexo Escolar Privado DF</h1>', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align: center; color: #2c3e50;">Excelência, Inovação e Compromisso com o Saber</h2>', unsafe_allow_html=True)
        
        st.write("---")
        
        # Tentativa de carregar a imagem local
        if os.path.exists("escola_principal.jpg"):
            st.image("escola_principal.jpg", use_container_width=True)
        else:
            # Caso a imagem não exista, uma alternativa profissional via link direto
            st.image("https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=1600", 
                     caption="Infraestrutura de classe mundial",
                     use_container_width=True)
        
        st.write("---")
        
        # Colunas para organizar links rápidos
        col1, col2, col3 = st.columns(3)
        with col1: st.success("🎓 Matrículas Abertas")
        with col2: st.info("📅 Calendário Escolar")
        with col3: st.warning("📞 Suporte Administrativo")
    elif menu == "Dashboard":
        st.subheader("📊 Painel Executivo")
        df = st.session_state.sistema.listar_tudo()
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(df['Classe'].value_counts())
                st.metric("Receita Total", f"Kz {df['Valor'].sum():,.2f}")
            with col2:
                # Imagem de volta no Dashboard
                st.image("https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800", use_container_width=True)
        else:
            st.info("Nenhum dado disponível para o painel.")

    elif menu == "Matricular":
        st.markdown('<h1 class="titulo-principal">🎓 Matrícula de Aluno - Complexo Escolar DF</h1>', unsafe_allow_html=True)
        st.write("---")
        
        # Usamos st.form para agrupar e limpar campos automaticamente após o clique
        with st.form("form_matricula", clear_on_submit=True):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                nome = st.text_input("👤 Nome Completo", placeholder="Ex: João da Silva")
                data = st.date_input("📅 Data de Nascimento", max_value=date.today())
                
                col_a, col_b = st.columns(2)
                with col_a:
                    classe = st.selectbox("📚 Classe", [f"{i}ª Classe" for i in range(1, 13)])
                with col_b:
                    turma = st.text_input("🏫 Turma", placeholder="Ex: A")
                
                curso = st.text_input("🎓 Curso", placeholder="Ex: Ciências Físicas e Biológicas")
                valor = st.number_input("💰 Valor da Matrícula (Kz)", min_value=0.0, format="%.2f")
                comp = st.text_input("🧾 Código do Comprovativo", placeholder="Ex: REF123456789")
                
                # O botão deve ser um form_submit_button para limpar o formulário
                btn_confirmar = st.form_submit_button("✅ Confirmar Matrícula", use_container_width=True)
            
            with col2:
                st.markdown(
                    """
                    <div style="width: 100%; min-height: 400px; background-color: #f0f2f6; border-radius: 10px; overflow: hidden;">
                        <img src="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800" 
                             style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                st.info("ℹ️ **Nota:** O sistema valida automaticamente o formato dos dados.")

            # Lógica de validação pós-clique
            if btn_confirmar:
                if len(nome.split()) < 2:
                    st.error("Erro: Insira o nome completo.")
                elif not re.match(r"^[0-9]{0,2}[A-Za-z]$", turma.strip()):
                    st.error("Erro: Turma inválida (Ex: A ou 10A).")
                elif not re.match(r"^[A-Za-z\s]+$", curso.strip()):
                    st.error("Erro: O curso deve conter apenas letras.")
                elif valor < 1000:
                    st.error("Erro: Valor da matrícula insuficiente.")
                else:
                    # Chame a sua função original
                    st.session_state.sistema.matricular(st.session_state.user_role, nome, data, turma, classe, curso, valor, comp)
                    st.success("Matrícula processada com sucesso! Campos limpos.")
                    st.balloons()
    elif menu == "Consultar":
        st.subheader("🔍 Consultar")
        
        # 1. Inicializa o estado de busca se não existir
        if 'pesquisa_ativa' not in st.session_state:
            st.session_state.pesquisa_ativa = False
            st.session_state.termo_atual = ""
            
        # 2. Entrada de dados
        termo = st.text_input("Busca rápida (Nome, Classe ou Curso)", value=st.session_state.termo_atual)
        
        col_b1, col_b2 = st.columns([1, 4])
        btn_buscar = col_b1.button("Buscar")
        btn_limpar = col_b2.button("Limpar Consulta")
        
        if btn_limpar:
            st.session_state.pesquisa_ativa = False
            st.session_state.termo_atual = ""
            st.rerun()
        
        # 3. Se o botão for clicado, ativa a busca e guarda o termo
        if btn_buscar:
            st.session_state.pesquisa_ativa = True
            st.session_state.termo_atual = termo
            
        # 4. Exibição Condicional
        if st.session_state.pesquisa_ativa:
            df = st.session_state.sistema.listar_tudo()
            termo_uso = st.session_state.termo_atual
            
            # Filtragem
            df_filtrado = df.query("Aluno.str.contains(@termo_uso, case=False) or Classe == @termo_uso or Curso.str.contains(@termo_uso, case=False)")
            
            if not df_filtrado.empty:
                st.write(formatar_tabela(df_filtrado).to_html(), unsafe_allow_html=True)
            else:
                st.warning(f"Nenhum resultado encontrado para: {termo_uso}")
        else:
            st.info("Por favor, insira um termo e clique em 'Buscar' para visualizar os dados.")
        
        # 5. Imagem fixa
        st.write("---")
        st.image("https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=1600", use_container_width=True)
    elif menu == "Gerenciar":
        if st.session_state.user_role == "Dr.":
            st.subheader("✏️ Gerenciar Matrículas")
            
            # 1. Carregar dados
            df = st.session_state.sistema.listar_tudo()
            
            if not df.empty:
                # 2. Seleção e Edição
                id_sel = st.selectbox("Selecione o ID da Matrícula para Editar:", df['Matrícula'].tolist())
                aluno_dados = df[df['Matrícula'] == id_sel].iloc[0]
                
                st.write("---")
                st.write(f"Editando registro: **{aluno_dados['Aluno']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome do Aluno", value=aluno_dados['Aluno'])
                    nova_turma = st.text_input("Turma", value=aluno_dados['Turma'])
                with col2:
                    nova_classe = st.selectbox("Classe", [f"{i}ª Classe" for i in range(1, 13)], index=int(aluno_dados['Classe'].split('ª')[0])-1)
                    novo_valor = st.number_input("Valor da Matrícula", value=float(aluno_dados['Valor']))
                
                # 3. Ações
                col_a, col_b = st.columns(2)
                if col_a.button("💾 Salvar Alterações"):
                    st.session_state.sistema.editar_matricula(st.session_state.user_role, id_sel, novo_nome, nova_turma, nova_classe, novo_valor)
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()
                
                if col_b.button("🗑️ Excluir Registro"):
                    st.session_state.sistema.deletar_matricula(st.session_state.user_role, id_sel)
                    st.warning("Registro excluído!")
                    st.rerun()
            else:
                st.info("Nenhum registro encontrado para gerenciar.")

            # 4. Rodapé Visual (Imagem de Gerenciamento)
            st.write("<br>", unsafe_allow_html=True)
            st.image(
                "https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=1600", 
                use_container_width=True,
                caption="Gerenciamento de Matrículas - Sistema Escolar"
            )
        else:
            st.warning("Acesso restrito apenas ao perfil Dr.")
    elif menu == "Relatórios":
        from io import BytesIO
        st.subheader("📊 Relatórios")
        
        # 1. Inicializa o estado
        if 'relatorio_ativo' not in st.session_state:
            st.session_state.relatorio_ativo = False
            
        # 2. Botões de Ação
        col_btn1, col_btn2 = st.columns([1, 4])
        if col_btn1.button("Gerar Relatório"):
            st.session_state.relatorio_ativo = True
        if col_btn2.button("Limpar Relatório"):
            st.session_state.relatorio_ativo = False
            st.rerun()

        # 3. Lógica de exibição condicional (apenas a tabela e métricas aqui)
        if st.session_state.relatorio_ativo:
            df_original = st.session_state.sistema.listar_tudo()
            
            if not df_original.empty:
                df_original['Data'] = pd.to_datetime(df_original['Data'])
                filtro = st.selectbox("Período", ["Geral", "Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual"])
                
                # Filtragem
                hoje = datetime.now()
                df = df_original.copy()
                if filtro == "Diário": df = df[df['Data'].dt.date == hoje.date()]
                elif filtro == "Semanal": df = df[df['Data'] >= (hoje - timedelta(days=7))]
                elif filtro == "Mensal": df = df[df['Data'].dt.month == hoje.month]
                elif filtro == "Trimestral": df = df[df['Data'] >= (hoje - timedelta(days=90))]
                elif filtro == "Semestral": df = df[df['Data'] >= (hoje - timedelta(days=180))]
                elif filtro == "Anual": df = df[df['Data'].dt.year == hoje.year]
                
                # Exibição
                st.write(formatar_tabela(df).to_html(), unsafe_allow_html=True)
                st.metric(f"Total {filtro}", f"Kz {df['Valor'].sum():,.2f}")
                
                # Download
                st.write("### 📥 Opções de Download")
                col_d1, col_d2 = st.columns(2)
                csv = df.to_csv(index=False).encode('utf-8')
                col_d1.download_button("📥 Baixar CSV", csv, f'relatorio_{filtro}.csv', 'text/csv')
                
                try:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Relatorio')
                    col_d2.download_button("📊 Baixar Excel", output.getvalue(), f'relatorio_{filtro}.xlsx', 
                                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                except Exception:
                    col_d2.error("Erro: Instale o 'xlsxwriter'.")
            else:
                st.warning("Nenhum dado disponível para gerar relatórios.")
        else:
            st.info("Clique em 'Gerar Relatório' para visualizar os dados financeiros.")
        
        # 4. A IMAGEM FICA AQUI FORA (sempre visível no rodapé)
        st.write("---")
        st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1600", use_container_width=True)
    if st.sidebar.button("Sair"):
        realizar_backup()
        st.session_state.logged_in = False
        st.rerun()
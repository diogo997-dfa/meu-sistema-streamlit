import streamlit as st
import sqlite3
import pandas as pd
import os
import shutil
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema Escolar Pro", layout="wide", page_icon="🎓")

# --- CSS PARA ESTILO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2c3e50; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASSE DO SISTEMA ---
class SistemaEscolar:
    def __init__(self, db_name="escola.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, data_nascimento TEXT, turma TEXT, classe TEXT)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_curso TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS matriculas (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, curso_id INTEGER, status TEXT, valor REAL, data_reg TEXT,
                          FOREIGN KEY(aluno_id) REFERENCES alunos(id), FOREIGN KEY(curso_id) REFERENCES cursos(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, usuario TEXT, acao TEXT)''')
        self.conn.commit()

    def listar_tudo(self):
        query = 'SELECT m.id AS Matrícula, a.nome AS Aluno, a.classe AS Classe, a.turma AS Turma, c.nome_curso AS Curso, m.valor AS Valor, m.data_reg AS Data FROM matriculas m JOIN alunos a ON m.aluno_id = a.id JOIN cursos c ON m.curso_id = c.id'
        try: return pd.read_sql_query(query, self.conn)
        except: return pd.DataFrame()

    def buscar_avancada(self, termo):
        query = 'SELECT m.id AS Matrícula, a.nome AS Aluno, a.classe AS Classe, a.turma AS Turma, c.nome_curso AS Curso, m.valor AS Valor, m.data_reg AS Data FROM matriculas m JOIN alunos a ON m.aluno_id = a.id JOIN cursos c ON m.curso_id = c.id WHERE a.nome LIKE ? OR a.classe = ? OR c.nome_curso LIKE ?'
        return pd.read_sql_query(query, self.conn, params=(f'%{termo}%', termo, f'%{termo}%'))

    def matricular(self, usuario, nome, data_nasc, turma, classe, nome_curso, valor):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO alunos (nome, data_nascimento, turma, classe) VALUES (?, ?, ?, ?)", (nome, str(data_nasc), turma, classe))
        aluno_id = cursor.lastrowid
        cursor.execute("INSERT OR IGNORE INTO cursos (nome_curso) VALUES (?)", (nome_curso,))
        cursor.execute("SELECT id FROM cursos WHERE nome_curso = ?", (nome_curso,))
        curso_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id, status, valor, data_reg) VALUES (?, ?, ?, ?, ?)", (aluno_id, curso_id, "Ativo", valor, datetime.now().strftime("%Y-%m-%d")))
        self.conn.commit()
        cursor.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Matriculou: {nome}"))
        self.conn.commit()

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
    st.title("🔐 Login de Acesso")
    user = st.selectbox("Usuário", ["Secretaria", "Dr."])
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if pwd in ["secretaria123", "doutor123"]:
            st.session_state.logged_in = True
            st.session_state.user_role = user
            st.rerun()
        else: st.error("Senha incorreta!")
else:
    st.sidebar.title(f"👤 {st.session_state.user_role}")
    menu = st.sidebar.radio("Navegação", ["Início", "Dashboard", "Matricular", "Consultar", "Gerenciar", "Relatórios"])
    
    if menu == "Início": st.title("🏠 Bem-vindo ao Sistema Escolar")

    elif menu == "Dashboard":
        st.subheader("📊 Painel Executivo")
        df = st.session_state.sistema.listar_tudo()
        if not df.empty:
            c1, c2 = st.columns(2)
            c1.bar_chart(df['Classe'].value_counts())
            c2.metric("Receita Total", f"Kz {df['Valor'].sum():,.2f}")

    elif menu == "Matricular":
        st.subheader("📝 Nova Matrícula")
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome Completo")
            data = st.date_input("Nascimento")
            classe = st.selectbox("Classe", [f"{i}ª Classe" for i in range(1, 13)])
        with c2:
            turma = st.text_input("Turma")
            curso = st.text_input("Curso")
            valor = st.number_input("Valor (Kz)", min_value=0.0)
        if st.button("Confirmar Matrícula"):
            st.session_state.sistema.matricular(st.session_state.user_role, nome, data, turma, classe, curso, valor)
            st.success("Matrícula efetuada!")

    elif menu == "Consultar":
        termo = st.text_input("Busca rápida")
        if termo: st.dataframe(st.session_state.sistema.buscar_avancada(termo), use_container_width=True)
        else: st.dataframe(st.session_state.sistema.listar_tudo(), use_container_width=True)

    elif menu == "Gerenciar":
        if st.session_state.user_role == "Dr.":
            st.dataframe(st.session_state.sistema.listar_tudo(), use_container_width=True)
            with st.expander("✏️ Editar/🗑️ Excluir"):
                id_sel = st.number_input("ID do Registro", step=1)
                n, t, c, v = st.text_input("Novo Nome"), st.text_input("Nova Turma"), st.selectbox("Classe", [f"{i}ª Classe" for i in range(1, 13)]), st.number_input("Novo Valor")
                if st.button("Atualizar"): st.session_state.sistema.editar_matricula(st.session_state.user_role, id_sel, n, t, c, v); st.rerun()
                if st.button("Excluir"): st.session_state.sistema.deletar_matricula(st.session_state.user_role, id_sel); st.rerun()
        else: st.warning("Acesso restrito.")

    elif menu == "Relatórios":
        st.subheader("📊 Relatórios")
        df = st.session_state.sistema.listar_tudo()
        if not df.empty:
            df['Data_Temp'] = pd.to_datetime(df['Data'], errors='coerce')
            tipo = st.radio("Escolha o filtro:", ["Geral", "Por Curso", "Mensal", "Semanal"], horizontal=True)
            
            df_final = df
            if tipo == "Por Curso":
                curso = st.selectbox("Selecione o Curso", df['Curso'].unique())
                df_final = df[df['Curso'] == curso]
            elif tipo == "Mensal":
                mes = st.selectbox("Selecione o Mês", range(1, 13))
                df_final = df[df['Data_Temp'].dt.month == mes]
            elif tipo == "Semanal":
                sem = st.number_input("Semana (1-52)", 1, 52)
                df_final = df[df['Data_Temp'].dt.isocalendar().week == sem]
            
            st.dataframe(df_final.drop(columns=['Data_Temp']), use_container_width=True)
            st.download_button("📥 Baixar CSV", df_final.to_csv(index=False).encode('utf-8'), "relatorio.csv")

    if st.sidebar.button("Sair"):
        realizar_backup()
        st.session_state.logged_in = False
        st.rerun()
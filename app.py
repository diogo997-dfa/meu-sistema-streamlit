import streamlit as st
import sqlite3
import pandas as pd
import os
import re
from datetime import date, datetime, timedelta
import shutil

# 1. DEFINIÇÃO DA CLASSE (Única e completa)
class SistemaEscolar:
    def __init__(self, db_name="escola.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, data_nascimento TEXT, bi TEXT, turma TEXT, classe TEXT, comprovativo TEXT)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_curso TEXT)')
        # Adicionado DEFAULT 'Pendente' no status
        cursor.execute('''CREATE TABLE IF NOT EXISTS matriculas (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, curso_id INTEGER, status TEXT DEFAULT 'Pendente', valor REAL, data_reg TEXT,
                          FOREIGN KEY(aluno_id) REFERENCES alunos(id), FOREIGN KEY(curso_id) REFERENCES cursos(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, usuario TEXT, acao TEXT)''')
        self.conn.commit()

    def aprovar_matricula(self, usuario, mat_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE matriculas SET status = 'Aprovado' WHERE id = ?", (mat_id,))
        cursor.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", 
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Aprovou matrícula ID: {mat_id}"))
        self.conn.commit()

    def matricular(self, usuario, nome, data_nasc, bi, turma, classe, nome_curso, valor, comprovativo):
        cursor = self.conn.cursor()
        
        # 1. Inserir aluno
        cursor.execute("INSERT INTO alunos (nome, data_nascimento, bi, turma, classe, comprovativo) VALUES (?, ?, ?, ?, ?, ?)", 
                       (nome, str(data_nasc), bi, turma, classe, comprovativo))
        aluno_id = cursor.lastrowid
        
        # 2. Inserir curso (se não existir) e buscar o ID
        cursor.execute("INSERT OR IGNORE INTO cursos (nome_curso) VALUES (?)", (nome_curso,))
        cursor.execute("SELECT id FROM cursos WHERE nome_curso = ?", (nome_curso,))
        resultado = cursor.fetchone()
        curso_id = resultado[0] if resultado else 1 
        
        # 3. Inserir matrícula (Apenas uma vez!)
        # O status será automaticamente 'Pendente' pelo DEFAULT na criação da tabela
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id, valor, data_reg) VALUES (?, ?, ?, ?)", 
                       (aluno_id, curso_id, valor, datetime.now().strftime("%Y-%m-%d")))
        
        # 4. Log (Apenas uma vez!)
        cursor.execute("INSERT INTO logs (data, usuario, acao) VALUES (?, ?, ?)", 
                       (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, f"Matriculou: {nome} (Status: Pendente)"))
        st.session_state.ultima_matricula = {
            'Aluno': nome,
            'Classe': classe,
            'Curso': nome_curso,
            'Data': str(data_nasc),
            'Valor': valor
        }
        # Commita tudo de uma vez no final para garantir integridade
        self.conn.commit()

    def listar_tudo(self):
        # Usamos o 'AS' para que as colunas tenham os nomes exatos que o seu código original espera
        # Adicionei 'a.comprovativo AS Comprovativo' para permitir o download dos ficheiros
        query = '''
            SELECT a.nome AS Aluno, 
                   a.classe AS Classe, 
                   c.nome_curso AS Curso,
                   a.data_nascimento AS Data,
                   m.valor AS Valor,
                   a.comprovativo AS Comprovativo
            FROM alunos a
            JOIN matriculas m ON a.id = m.aluno_id
            JOIN cursos c ON m.curso_id = c.id
        '''
        return pd.read_sql_query(query, self.conn)

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema Escolar Pro", layout="wide", page_icon="🎓")

# 3. INICIALIZAÇÃO SEGURA
if "sistema" in st.session_state:
    del st.session_state.sistema

if "sistema" not in st.session_state:
    st.session_state.sistema = SistemaEscolar()

# 4. FUNÇÕES AUXILIARES
def formatar_tabela(df):
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

# Estas funções devem estar fora de formatar_tabela e fazem parte da classe SistemaEscolar
# (Certifique-se de que estão dentro da classe no seu código original)

def realizar_backup():
    if not os.path.exists("backups"): os.makedirs("backups")
    shutil.copy("escola.db", f"backups/escola_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

from fpdf import FPDF

def gerar_ficha_matricula(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Cabeçalho
    pdf.cell(200, 10, txt="Complexo Escolar Privado DF", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt="Ficha de Comprovativo de Matrícula", ln=True, align='C')
    pdf.ln(10)
    
    # Dados do Aluno
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Aluno: {dados['Aluno']}", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Classe: {dados['Classe']}", ln=True)
    pdf.cell(200, 10, txt=f"Curso: {dados['Curso']}", ln=True)
    pdf.cell(200, 10, txt=f"Data de Nascimento: {dados['Data']}", ln=True)
    pdf.cell(200, 10, txt=f"Valor Pago: Kz {float(dados['Valor']):,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Data da Matrícula: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    
    pdf.ln(20)
    pdf.cell(200, 10, txt="__________________________", ln=True, align='C')
    pdf.cell(200, 10, txt="Assinatura da Secretaria", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')
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
        perfil = st.radio("Selecione o seu perfil:", ["Secretaria", "Dr.", "Público"])
        
        if perfil != "Público":
            pwd = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                if (perfil == "Secretaria" and pwd == "secretaria123") or (perfil == "Dr." and pwd == "doutor123"):
                    st.session_state.logged_in = True
                    st.session_state.user_role = perfil
                    st.rerun()
                else: 
                    st.error("Senha incorreta!")
                    
        else:
            # Opção para o Aluno (Público)
            st.info("Insira o seu BI para consultar o estado da matrícula.")
            bi_consulta = st.text_input("Nº do BI:")
            
            if st.button("Acessar Matrícula", use_container_width=True):
                if bi_consulta:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "Aluno"
                    st.session_state.bi_aluno = bi_consulta # Armazena o BI para futuras consultas
                    st.rerun()
                else:
                    st.warning("Por favor, insira o seu BI.")
                
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

        # Define o papel do usuário
        role = st.session_state.get("user_role")
        exibir_formulario_matricula = True  # Por padrão, assume que deve exibir

        # Lógica apenas se for Aluno
        if role == "Aluno":
            bi = st.session_state.get('bi_aluno')
            cursor = st.session_state.sistema.conn.cursor()
            query_status = """
                SELECT m.status 
                FROM matriculas m 
                JOIN alunos a ON m.aluno_id = a.id 
                WHERE a.bi = ? 
                ORDER BY m.id DESC LIMIT 1
            """
            cursor.execute(query_status, (bi,))
            resultado = cursor.fetchone()
            
            if resultado:
                status = resultado[0]
                if status == "Pendente":
                    st.warning("⚠️ **Status da sua Matrícula:** Pendente. Aguarde a validação da secretaria.")
                    exibir_formulario_matricula = False
                else:
                    st.success("✅ **Status da sua Matrícula:** Aprovado! Seja bem-vindo(a).")
                    exibir_formulario_matricula = False
            else:
                st.info("Preencha o formulário abaixo para iniciar sua matrícula:")
                exibir_formulario_matricula = True

        # Exibe o formulário se a lógica acima permitir
        if exibir_formulario_matricula:
            with st.form("form_matricula", clear_on_submit=True):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    nome = st.text_input("👤 Nome Completo", placeholder="Ex: João da Silva")
                    col_d, col_bi = st.columns(2)
                    with col_d:
                        data = st.date_input("📅 Data de Nascimento", max_value=date.today())
                    with col_bi:
                        bi = st.text_input("🆔 Nº do BI", value=st.session_state.get('bi_aluno', ''), placeholder="Ex: 000000000LA000")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        classe = st.selectbox("📚 Classe", [f"{i}ª Classe" for i in range(1, 13)])
                    with col_b:
                        turma = st.text_input("🏫 Turma", placeholder="Ex: A")
                    
                    curso = st.text_input("🎓 Curso", placeholder="Ex: Ciências Físicas e Biológicas")
                    valor = st.number_input("💰 Valor da Matrícula (Kz)", min_value=0.0, format="%.2f")
                    comp_file = st.file_uploader("🧾 Carregar Comprovativo", type=['png', 'jpg', 'jpeg', 'pdf'])
                    
                    btn_confirmar = st.form_submit_button("✅ Confirmar Matrícula", use_container_width=True)
                
                with col2:
                    st.markdown("""<div style="width: 100%; min-height: 400px; background-color: #f0f2f6; border-radius: 10px; overflow: hidden;">
                                    <img src="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800" style="width: 100%; height: 100%; object-fit: cover;">
                                </div>""", unsafe_allow_html=True)
                    st.info("ℹ️ **Nota:** O sistema valida automaticamente o formato dos dados.")

            # --- A LÓGICA DE VALIDAÇÃO ESTÁ AQUI (FORA DO WITH ST.FORM) ---
            if btn_confirmar:
                if len(nome.split()) < 2:
                    st.error("Erro: Insira o nome completo.")
                elif not bi:
                    st.error("Erro: O número do BI é obrigatório.")
                elif not re.match(r"^[0-9]{0,2}[A-Za-z]$", turma.strip()):
                    st.error("Erro: Turma inválida (Ex: A ou 10A).")
                elif not re.match(r"^[A-Za-z\s]+$", curso.strip()):
                    st.error("Erro: O curso deve conter apenas letras.")
                elif valor < 1000:
                    st.error("Erro: Valor da matrícula insuficiente.")
                elif comp_file is None:
                    st.error("Erro: Por favor, carregue o comprovativo.")
                else:
                    if not os.path.exists("uploads"):
                        os.makedirs("uploads")
                    
                    caminho_ficheiro = f"uploads/{datetime.now().strftime('%Y%m%d%H%M%S')}_{comp_file.name}"
                    with open(caminho_ficheiro, "wb") as f:
                        f.write(comp_file.getbuffer())
                    
                    # Usa 'role' definido no início. Se for público, passamos "Visitante"
                    user_type = role if role else "Visitante"
                    st.session_state.sistema.matricular(user_type, nome, data, bi, turma, classe, curso, valor, caminho_ficheiro)
                    
                    st.success("Matrícula processada com sucesso!")
                    st.balloons()
                    st.rerun()

            # AQUI ESTÁ A CORREÇÃO PARA O BOTÃO APARECER ---
        if "ultima_matricula" in st.session_state:
            dados = st.session_state.ultima_matricula
            st.write("---")
            st.info("Matrícula realizada! Você já pode baixar seu comprovativo abaixo.")
            
            pdf_bytes = gerar_ficha_matricula(dados)
            st.download_button(
                label="📥 Baixar Ficha de Matrícula",
                data=pdf_bytes,
                file_name=f"ficha_{dados['Aluno'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            
            # Opcional: botão para limpar e permitir nova matrícula
            if st.button("Nova Matrícula"):
                del st.session_state.ultima_matricula
                st.rerun()
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
                
                # --- ATUALIZAÇÃO: Download do Comprovativo na Consulta ---
                st.write("---")
                st.write("### 📂 Baixar Comprovativo dos Resultados")
                # Permite escolher apenas entre os alunos filtrados
                aluno_escolhido = st.selectbox("Selecione um aluno da lista para baixar o comprovativo:", df_filtrado['Aluno'].unique())
                
                if aluno_escolhido:
                    caminho = df_filtrado.loc[df_filtrado['Aluno'] == aluno_escolhido, 'Comprovativo'].values[0]
                    if caminho and os.path.exists(caminho):
                        with open(caminho, "rb") as file:
                            st.download_button(
                                label=f"📥 Baixar comprovativo: {aluno_escolhido}",
                                data=file,
                                file_name=os.path.basename(caminho),
                                mime="application/octet-stream"
                            )
                    else:
                        st.warning("Comprovativo não encontrado.")
            else:
                st.warning(f"Nenhum resultado encontrado para: {termo_uso}")
        else:
            st.info("Por favor, insira um termo e clique em 'Buscar' para visualizar os dados.")
        
        # 5. Imagem fixa
        st.write("---")
        st.image("https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=1600", use_container_width=True)
    elif menu == "Gerenciar":
        st.subheader("📋 Gestão de Matrículas Pendentes")
        
        # 1. Área de Aprovação (Disponível para ambos: Dr. e Secretaria)
        if st.session_state.get("user_role") in ["Dr.", "Secretaria"]:
            pendentes = pd.read_sql("SELECT * FROM matriculas WHERE status = 'Pendente'", st.session_state.sistema.conn)
            
            if not pendentes.empty:
                for index, row in pendentes.iterrows():
                    st.write(f"---")
                    st.write(f"**ID:** {row['id']} | **Aluno ID:** {row['aluno_id']} | **Valor:** {row['valor']} Kz")
                    if st.button(f"✅ Ativar Matrícula {row['id']}", key=f"btn_{row['id']}"):
                        st.session_state.sistema.aprovar_matricula(st.session_state.user_role, row['id'])
                        st.success(f"Matrícula {row['id']} ativada!")
                        st.rerun()
            else:
                st.info("Não existem matrículas pendentes de momento.")
        
        st.write("---")

        # 2. Área de Edição e Exclusão (Restrita apenas ao Dr.)
        if st.session_state.user_role == "Dr.":
            st.subheader("✏️ Gerenciar Matrículas (Edição/Exclusão)")
            
            # Carregar dados
            df = st.session_state.sistema.listar_tudo()
            
            if not df.empty:
                # Seleção
                id_sel = st.selectbox("Selecione o ID da Matrícula para Editar:", df['Matrícula'].tolist())
                aluno_dados = df[df['Matrícula'] == id_sel].iloc[0]
                
                st.write(f"Editando registro: **{aluno_dados['Aluno']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome do Aluno", value=aluno_dados['Aluno'])
                    novo_bi = st.text_input("Nº do BI", value=aluno_dados.get('BI', ''))
                    nova_data = st.date_input("Data de Nascimento", value=pd.to_datetime(aluno_dados.get('Data', '1990-01-01')))
                
                with col2:
                    col_sub1, col_sub2 = st.columns(2)
                    with col_sub1:
                        nova_classe = st.selectbox("Classe", [f"{i}ª Classe" for i in range(1, 13)], index=int(aluno_dados['Classe'].split('ª')[0])-1)
                    with col_sub2:
                        nova_turma = st.text_input("Turma", value=aluno_dados['Turma'])
                    
                    novo_curso = st.text_input("Curso", value=aluno_dados.get('Curso', ''))
                    novo_valor = st.number_input("Valor da Matrícula", value=float(aluno_dados['Valor']))
                
                # Ações
                col_a, col_b = st.columns(2)
                if col_a.button("💾 Salvar Alterações"):
                    st.session_state.sistema.editar_matricula(st.session_state.user_role, id_sel, novo_nome, nova_turma, nova_classe, novo_valor, novo_bi, novo_curso, str(nova_data))
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()
                
                if col_b.button("🗑️ Excluir Registro"):
                    st.session_state.sistema.deletar_matricula(st.session_state.user_role, id_sel)
                    st.warning("Registro excluído!")
                    st.rerun()
            else:
                st.info("Nenhum registro encontrado para gerenciar.")

            # Rodapé Visual
            st.write("<br>", unsafe_allow_html=True)
            st.image(
                "https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=1600", 
                use_container_width=True,
                caption="Gerenciamento de Matrículas - Sistema Escolar"
            )
        else:
            st.info("Apenas o Dr. tem acesso às funções de Edição e Exclusão.")
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

        # 3. Lógica de exibição condicional
        if st.session_state.relatorio_ativo:
            df_original = st.session_state.sistema.listar_tudo()
            
            if not df_original.empty:
                # Conversão segura de datas
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
                
                # Exibição da tabela
                st.write(formatar_tabela(df).to_html(), unsafe_allow_html=True)
                st.metric(f"Total {filtro}", f"Kz {df['Valor'].sum():,.2f}")
                
                # --- NOVA ATUALIZAÇÃO: Visualizar Comprovativo ---
                st.write("---")
                st.write("### 📂 Visualizar Comprovativos")
                nome_selecionado = st.selectbox("Selecione o aluno para baixar o comprovativo:", df['Aluno'].unique())
                
                if nome_selecionado:
                    caminho = df.loc[df['Aluno'] == nome_selecionado, 'Comprovativo'].values[0]
                    if caminho and os.path.exists(caminho):
                        with open(caminho, "rb") as file:
                            st.download_button(
                                label=f"📥 Baixar comprovativo de {nome_selecionado}",
                                data=file,
                                file_name=os.path.basename(caminho),
                                mime="application/octet-stream"
                            )
                    else:
                        st.warning("Comprovativo não encontrado.")
                
                # Download de Relatórios
                st.write("---")
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
        
        # 4. A IMAGEM
        st.write("---")
        st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1600", use_container_width=True)
    if st.sidebar.button("Sair"):
        realizar_backup()
        st.session_state.logged_in = False
        st.rerun()
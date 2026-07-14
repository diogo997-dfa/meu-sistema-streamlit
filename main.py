import streamlit as st  # Importa a biblioteca Streamlit para construir a interface web do software.
import sqlite3  # Importa o módulo SQLite3 para gerir o banco de dados local.
import pandas as pd  # Importa o Pandas para ler dados do SQL e exibi-los em tabelas organizadas.

# Define o título da aba do navegador e centraliza o layout visual do aplicativo.
st.set_page_config(page_title="Quiz Educativo Pro", layout="centered")
def inicializar_bd():  # Declara a função que cria a estrutura inicial do banco de dados.
    conn = sqlite3.connect('escola.db')  # Abre a conexão com o ficheiro de banco de dados chamado 'escola.db'.
    cursor = conn.cursor()  # Cria um objeto cursor para poder executar comandos SQL no banco.
    
    # Executa o comando SQL para criar a tabela de utilizadores (caso ela ainda não exista).
    cursor.execute('CREATE TABLE IF NOT EXISTS utilizadores (id INTEGER PRIMARY KEY, user TEXT, pass TEXT)')
    
    # Executa o comando SQL para criar a tabela de resultados para armazenar o progresso dos alunos.
    cursor.execute('CREATE TABLE IF NOT EXISTS resultados (id INTEGER PRIMARY KEY, user TEXT, pontuacao INTEGER)')
    
    conn.commit()  # Grava e consolida todas as alterações feitas no banco de dados.
    conn.close()  # Fecha a conexão com o banco de dados para libertar memória do sistema.

inicializar_bd()  # Chama a função de inicialização imediatamente ao iniciar o script.

def mostrar_progresso():  # Declara a função para exibir os resultados na tela de forma rápida.
    st.subheader("📊 Relatório de Desempenho")  # Adiciona um subtítulo visual na interface.
    conn = sqlite3.connect('escola.db')  # Conecta ao arquivo de banco de dados.
    data = pd.read_sql_query("SELECT * FROM resultados", conn)  # Faz uma consulta SQL e converte os dados diretamente num DataFrame Pandas.
    st.table(data)  # Desenha uma tabela estática na tela com os dados obtidos.
    conn.close()  # Fecha a conexão com o banco de dados.
# Declara a lista global que guarda o banco de questões estruturado do Quiz.
questoes = [
    {"pergunta": "O que é o Hardware?", "opcoes": ["A parte física", "Programas", "Dados", "Redes"], "correta": "A parte física", "img": "https://picsum.photos/id/1/400/300"},
    {"pergunta": "Qual destes é um Software?", "opcoes": ["Monitor", "Teclado", "Windows", "Rato"], "correta": "Windows", "img": "https://picsum.photos/id/2/400/300"},
    {"pergunta": "O que é a CPU?", "opcoes": ["Memória", "Processador", "Disco", "Fonte"], "correta": "Processador", "img": "https://picsum.photos/id/3/400/300"}, 
    {"pergunta": "O que faz a memória RAM?", "opcoes": ["Armazena ficheiros", "Armazena temporariamente", "Conecta rede", "Calcula vídeo"], "correta": "Armazena temporariamente", "img": "https://picsum.photos/id/4/400/300"}, 
    {"pergunta": "Qual o periférico de entrada?", "opcoes": ["Monitor", "Impressora", "Teclado", "Colunas"], "correta": "Teclado", "img": "https://picsum.photos/id/5/400/300"},
    {"pergunta": "O que é um Sistema Operativo?", "opcoes": ["Um Software", "Um Hardware", "Um periférico", "Um cabo"], "correta": "Um Software", "img": "https://picsum.photos/id/6/400/300"},
    {"pergunta": "O que significa 'Input'?", "opcoes": ["Saída", "Entrada", "Processamento", "Armazenamento"], "correta": "Entrada", "img": "https://picsum.photos/id/7/400/300"},
    {"pergunta": "O que faz um Disco Rígido?", "opcoes": ["Processa dados", "Armazena permanentemente", "Exibe imagem", "Som"], "correta": "Armazena permanentemente", "img": "https://picsum.photos/id/8/400/300"},
    {"pergunta": "O que é Wi-Fi?", "opcoes": ["Cabo", "Rede sem fios", "Processador", "Software"], "correta": "Rede sem fios", "img": "https://picsum.photos/id/9/400/300"},
    {"pergunta": "Qual componente exibe a imagem?", "opcoes": ["Fonte", "Monitor", "Teclado", "Motherboard"], "correta": "Monitor", "img": "https://picsum.photos/id/10/400/300"}
]
if 'pagina' not in st.session_state: st.session_state.pagina = 'bem-vindo'  # Define a página inicial como 'bem-vindo'.
if 'idx' not in st.session_state: st.session_state.idx = 0  # Inicializa o índice da pergunta atual na posição 0.
if 'score' not in st.session_state: st.session_state.score = 0  # Inicializa a pontuação do aluno a zeros.
if 'feedback' not in st.session_state: st.session_state.feedback = None  # Define o estado inicial do feedback da resposta como vazio.
if 'usuario_atual' not in st.session_state: st.session_state.usuario_atual = None  # Armazena o nome do aluno atualmente logado.
if 'admin_logado' not in st.session_state: st.session_state.admin_logado = False  # Controla se o professor já passou pela autenticação.
if st.session_state.pagina == 'bem-vindo':  # Verifica se a página ativa na sessão é a de boas-vindas.
    st.title("🌟 Bem-vindo ao Portal do Saber!")  # Exibe o título principal estilizado no topo da página.
    st.image("https://images.unsplash.com/photo-1523240795612-9a054b0db644?q=80&w=800")  # Renderiza uma imagem ilustrativa da internet.
    
    if st.button("👉 Clique aqui para fazer o Login (Aluno)"):  # Cria um botão de ação para o perfil do estudante.
        st.session_state.pagina = 'login'  # Modifica o estado para direcionar o utilizador para o ecrã de login do aluno.
        st.rerun()  # Reinicia a execução do script para atualizar os elementos visuais no ecrã de imediato.
        
    if st.sidebar.button("⚙️ Painel do Professor"):  # Insere um botão de acesso administrativo na barra lateral da interface.
        st.session_state.pagina = 'admin'  # Redireciona o fluxo da sessão para a página administrativa do docente.
        st.rerun()  # Recarrega a aplicação instantaneamente para aplicar a mudança de ecrã.
elif st.session_state.pagina == 'admin':  # Entra nesta ramificação caso a página ativa seja a área do professor.
    st.title("👨‍🏫 Painel de Administração")  # Define o título principal do painel do professor.
    
    if not st.session_state.admin_logado:  # Verifica se o administrador ainda não validou o seu acesso.
        senha_admin = st.text_input("Código de Acesso Admin", type="password")  # Cria um campo de texto protegido para inserção da senha.
        if senha_admin == "admin123":  # Avalia se o texto digitado corresponde à chave mestra programada.
            st.session_state.admin_logado = True  # Valida o estado de login do administrador na sessão corrente.
            st.rerun()  # Atualiza o ecrã imediatamente para liberar as funcionalidades restritas.
        elif senha_admin != "":  # Se algo incorreto foi digitado no campo:
            st.warning("Senha incorreta.")  # Mostra uma tarja amarela de aviso informando o erro de digitação.
    
    else:  # Caso o professor já se encontre autenticado no sistema:
        col_conteudo, col_imagem = st.columns([1, 1])  # Divide o espaço útil da janela web em duas colunas de tamanhos iguais.
            
        with col_conteudo:  # Inicia a manipulação de blocos visuais na coluna da esquerda.
            tab1, tab2 = st.tabs(["📊 Relatório", "⚙️ Gestão"])  # Cria duas abas navegáveis para organizar o fluxo de trabalho.
            
            with tab1:  # Foco na primeira aba: visualização de notas.
                st.subheader("Relatório de Progresso")  # Subtítulo da secção de dados.
                conn = sqlite3.connect('escola.db')  # Abre conexão de leitura com o banco de dados.
                try:  # Inicia um bloco de tratamento de exceções preventivo.
                    df = pd.read_sql_query("SELECT * FROM resultados", conn)  # Extrai todo o histórico contido na tabela resultados.
                    if not df.empty:  # Caso a tabela possua pelo menos uma linha de dados gravada:
                        if st.button("🔄 Atualizar"): st.rerun()  # Botão manual para recarregar o banco de dados.
                        st.table(df)  # Imprime o DataFrame na tela no formato de listagem académica.
                    else:
                        st.info("Sem resultados.")  # Alerta o docente caso nenhum aluno tenha finalizado o teste ainda.
                except:
                    st.warning("Tabela não encontrada.")  # Disparado se houver problemas estruturais no banco de dados.
                conn.close()  # Garante o fechamento da conexão de dados ao fim do processo.
                
            with tab2:  # Foco na segunda aba: cadastro de turmas/alunos.
                st.subheader("Adicionar Aluno")  # Subtítulo indicador da ação.
                with st.form("form_novo_aluno"):  # Isola os campos dentro de um formulário seguro do Streamlit.
                    novo_user = st.text_input("Nome")  # Campo para digitar o nome de login do novo estudante.
                    nova_pw = st.text_input("Palavra-passe", type="password")  # Campo para registrar a senha de acesso do aluno.
                    if st.form_submit_button("Adicionar"):  # Cria o botão de submissão do formulário.
                        if novo_user and nova_pw:  # Valida se os dois campos foram devidamente preenchidos.
                            conn = sqlite3.connect('escola.db')  # Conecta ao arquivo físico do banco.
                            cursor = conn.cursor()  # Instancia o executor de instruções.
                            # Insere com segurança as variáveis de texto sanitizadas na tabela utilizadores.
                            cursor.execute("INSERT INTO utilizadores (user, pass) VALUES (?, ?)", (novo_user, nova_pw))
                            conn.commit()  # Salva o novo registro de aluno no banco de dados.
                            conn.close()  # Fecha o canal com o banco.
                            st.success("Adicionado!")  # Emite feedback visual verde de sucesso.
                        else:
                            st.error("Preencha tudo.")  # Exibe erro caso algum dos campos tenha ficado vazio.
        
        with col_imagem:  # Passa a estruturar os elementos da coluna do lado direito.
            st.markdown("""
                <div style="text-align: center; padding-top: 50px;">
                    <h1 style="font-size: 150px;">👨‍🏫</h1>
                    <h3 style="color: #4A90E2;">Painel de Controlo Pedagógico</h3>
                </div>
            """, unsafe_allow_html=True)  # Renderiza um bloco HTML customizado para exibição de um ícone minimalista fixo.
            
            if st.button("🚪 Sair do Painel"):  # Cria um botão para o encerramento da sessão administrativa.
                st.session_state.admin_logado = False  # Altera a flag de validação para falso.
                st.rerun()  # Recarrega a aplicação, bloqueando o painel novamente.

    st.divider()  # Traça uma linha horizontal de separação visual no ecrã.
    if st.button("⬅️ Voltar ao Início"):  # Cria um botão de retorno global.
        st.session_state.pagina = 'bem-vindo'  # Restaura a rota para a tela inicial.
        st.rerun()  # Força a atualização imediata dos ecrãs.
elif st.session_state.pagina == 'quiz':  # Entra nesta ramificação quando o aluno inicia o questionário.
    q = questoes[st.session_state.idx]  # Captura o dicionário da pergunta atual com base no índice da sessão.
    st.subheader(f"Questão {st.session_state.idx + 1} de 10")  # Mostra o indicador de progresso textual dinâmico.
    st.image(q["img"])  # Carrega a imagem configurada para a pergunta em execução.
    
    escolha = st.radio(q["pergunta"], q["opcoes"], key="radio_quiz")  # Cria os botões de escolha única com o enunciado da questão.
    
    if st.button("Submeter Resposta"):  # Botão que desencadeia a verificação lógica da resposta.
        if escolha == q["correta"]:  # Avalia se a string selecionada bate perfeitamente com o campo 'correta'.
            # Salva na sessão um feedback de sucesso e armazena a mensagem correspondente.
            st.session_state.feedback = ("success", f"Correto! A resposta '{escolha}' está certa.")
            st.session_state.score += 1  # Incrementa em 1 ponto o marcador de acertos do estudante.
            st.session_state.efeito = "baloes"  # Define que o efeito visual comemorativo será de balões subindo.
        else:  # Caso a string selecionada seja diferente da resposta correta:
            # Configura na sessão um feedback de erro contendo a resposta certa correta do banco.
            st.session_state.feedback = ("error", f"Ops! A correta era: {q['correta']}.")
            st.session_state.efeito = "neve"  # Define que o efeito visual de erro será simulação de neve caindo.
        st.rerun()  # Atualiza o ecrã instantaneamente para processar e exibir os efeitos.

    if st.session_state.feedback:  # Se existir um feedback ativo guardado na memória da sessão:
        tipo, msg = st.session_state.feedback  # Desempacota a tupla contendo o tipo (success/error) e a mensagem de texto.
        if tipo == "success":  # Se for um feedback positivo:
            st.success(msg)  # Renderiza a mensagem dentro de uma caixa verde na tela.
            if st.session_state.efeito == "baloes": st.balloons()  # Dispara a animação nativa de balões flutuantes na tela.
        else:  # Se for um feedback negativo:
            st.error(msg)  # Desenha a mensagem explicativa dentro de uma caixa vermelha de erro.
            if st.session_state.efeito == "neve": st.snow()  # Aciona a animação gráfica de flocos de neve caindo.
        
        st.session_state.efeito = None  # Limpa o registo do efeito para impedir que a animação rode repetidamente em loops.
        
        if st.button("➡️ Avançar"):  # Exibe o botão para avançar para o próximo estágio ou pergunta.
            st.session_state.feedback = None  # Limpa o feedback atual para a nova questão começar zerada.
            if st.session_state.idx + 1 < len(questoes):  # Verifica se ainda existem perguntas pendentes na lista.
                st.session_state.idx += 1  # Avança o contador de índice em uma unidade.
            else:  # Se o aluno respondeu à última pergunta:
                st.session_state.pagina = 'resultado-final'  # Redireciona o estado da sessão para o ecrã de encerramento.
            st.rerun()  # Recarrega a tela para apresentar o novo estado configurado.

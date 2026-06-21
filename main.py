import sqlite3 # Importa a biblioteca para trabalhar com bancos de dados SQLite

class SistemaEscolar:
    # Método construtor: roda automaticamente ao criar o objeto 'sistema'
    def __init__(self, db_name="escola.db"):
        self.conn = sqlite3.connect(db_name) # Conecta ao arquivo do banco (ou cria se não existir)
        self.criar_tabelas() # Chama a função que garante que as tabelas existam

    # Método para criar a estrutura das tabelas no banco de dados
    def criar_tabelas(self):
        cursor = self.conn.cursor() # Cursor é o "ponteiro" que executa comandos SQL
        
        # Tabela de alunos com campos extras de turma e data de nascimento
        cursor.execute('''CREATE TABLE IF NOT EXISTS alunos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            nome TEXT, 
                            data_nascimento TEXT, 
                            turma TEXT)''')
        
        # Tabela de cursos (apenas nome e ID)
        cursor.execute('CREATE TABLE IF NOT EXISTS cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_curso TEXT)')
        
        # Tabela de matrículas: conecta Aluno e Curso (Relacionamento) e guarda o valor pago
        cursor.execute('''CREATE TABLE IF NOT EXISTS matriculas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            aluno_id INTEGER, 
                            curso_id INTEGER, 
                            status TEXT, 
                            valor REAL,
                            FOREIGN KEY(aluno_id) REFERENCES alunos(id), 
                            FOREIGN KEY(curso_id) REFERENCES cursos(id))''')
        self.conn.commit() # Salva (confirma) todas as alterações no banco

    # Método para buscar um curso ou criá-lo automaticamente se não existir
    def obter_ou_criar_curso(self, nome_curso):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM cursos WHERE nome_curso = ?", (nome_curso,))
        resultado = cursor.fetchone() # Pega a primeira linha encontrada
        if resultado:
            return resultado[0] # Retorna o ID se o curso já existir
        else:
            # Insere novo curso se não existir e retorna o ID criado
            cursor.execute("INSERT INTO cursos (nome_curso) VALUES (?)", (nome_curso,))
            self.conn.commit()
            return cursor.lastrowid # Retorna o ID gerado automaticamente para esse novo registro

    # Método para cadastrar aluno e matrícula em uma única operação
    def matricular_rapido(self, nome, data_nasc, turma, nome_curso):
        cursor = self.conn.cursor()
        # Adiciona um novo aluno sempre, permitindo nomes iguais no sistema
        cursor.execute("INSERT INTO alunos (nome, data_nascimento, turma) VALUES (?, ?, ?)", (nome, data_nasc, turma))
        aluno_id = cursor.lastrowid # Pega o ID desse novo aluno cadastrado
        
        # Chama a função acima para garantir que temos um curso válido (e seu ID)
        curso_id = self.obter_ou_criar_curso(nome_curso)
        
        valor_matricula = 1500.00 # Valor fixo definido para qualquer matrícula
        
        # Insere a ligação entre o aluno, o curso e os dados financeiros
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id, status, valor) VALUES (?, ?, ?, ?)",
                       (aluno_id, curso_id, "Pendente", valor_matricula))
        self.conn.commit()

    # Método de busca que une as três tabelas para mostrar o perfil completo do aluno
    def buscar_matricula_inteligente(self, termo):
        cursor = self.conn.cursor()
        # Query SQL com JOINs para pegar o nome do aluno e do curso a partir dos IDs
        query = '''SELECT m.id, a.nome, a.data_nascimento, a.turma, c.nome_curso, m.valor 
                   FROM matriculas m
                   JOIN alunos a ON m.aluno_id = a.id
                   JOIN cursos c ON m.curso_id = c.id
                   WHERE a.id = ? OR a.nome LIKE ?''' # Busca por ID exato ou parte do nome
        cursor.execute(query, (termo, f'%{termo}%')) # O % permite busca parcial (ex: "dio" encontra "diogo")
        return cursor.fetchall() # Retorna todas as linhas encontradas

# Bloco principal: executa o menu interativo
if __name__ == "__main__":
    sistema = SistemaEscolar() # Inicia o sistema
    
    while True: # Loop infinito para manter o menu aparecendo
        print("\n--- MATRÍCULA ÁGIL ---")
        print("1. Matricular Aluno")
        print("2. Listar/Buscar")
        print("3. Sair")
        
        escolha = input("Escolha: ")
        
        if escolha == "1": # Cadastro
            nome = input("Nome do aluno: ")
            data = input("Data de nascimento (DD/MM/AAAA): ")
            turma = input("Turma: ")
            curso = input("Curso: ")
            sistema.matricular_rapido(nome, data, turma, curso)
            print("Matrícula realizada com sucesso!")
            
        elif escolha == "2": # Busca
            termo = input("Digite nome ou ID: ")
            resultados = sistema.buscar_matricula_inteligente(termo)
            for r in resultados: # Exibe os resultados um por um
                print(f"-> {r[1]} (Nasc: {r[2]}, Turma: {r[3]}) | Curso: {r[4]} | Valor: {r[5]} Kz")
                
        elif escolha == "3": # Encerra o programa
            break
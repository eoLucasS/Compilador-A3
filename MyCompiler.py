import sys
from MyLexer import *
from MyParser import *
from MyEmitter import *
from tkinter import *
from tkinter import messagebox
import tkinter.scrolledtext as tkst

# Função que é acionada quando o botão 'Compilar' é clicado
def compile_Click():
    # Obtém o texto de entrada do widget ScrolledText 'codeInput'
    input_text = codeInput.get("1.0", 'end')

    # Limpa os widgets 'st' e 'cCode'
    st.delete("1.0", "end")
    cCode.delete("1.0", "end")

    # Inicializa as instâncias do analisador léxico, emissor e analisador
    lexer = Lexer(input_text)
    emitter = Emitter("out.c")
    parser = Parser(lexer, emitter)

    # Realiza a análise sintática e léxica do código de entrada
    parser.parse()

    # Insere informações sobre variáveis e etiquetas no widget 'st'
    st.insert(INSERT, "Tabela de Símbolos:\n\n-> Variáveis:\n")
    if len(parser.symbols) > 1:
        st.insert(END, parser.symbols)
    else:
        st.insert(END, "Nenhuma variável declarada!\n")
    if len(parser.labelsDeclared) > 1:
        st.insert(END, "\n-> Etiquetas:\n")
        st.insert(END, parser.labelsDeclared)
    else:
        st.insert(END, "\n-> Etiquetas:\nNenhuma etiqueta declarada!\n")

    # Insere o cabeçalho e o código compilado no widget 'cCode'
    cCode.insert(INSERT, emitter.header)
    cCode.insert(END, emitter.code)

    # Escreve o código compilado em um arquivo
    emitter.writeFile()

    # Exibe uma caixa de diálogo indicando que a compilação foi bem-sucedida
    messagebox.showinfo("Sucesso", "Compilação bem-sucedida!")

# Configuração da interface gráfica usando Tkinter
root = Tk()
root.geometry('1300x600')
root.configure(background='#F0F8FF')
root.title('Compilador de BASIC para C - Lucas, Nycolas, Breno e Gustavo')

# Rótulo para o campo de entrada de código fonte
Label(root, text='Código Fonte em BASIC', bg='#F0F8FF', font=('Arial', 14, 'bold')).place(x=30, y=25)

# Widget ScrolledText para a entrada de código
codeInput = tkst.ScrolledText(root, width=40, height=20, bd=5, relief='sunken')
codeInput.pack()
codeInput.place(x=30, y=50)

# Rótulo para a tabela de símbolos
Label(root, text='Tabela de Símbolos', bg='#F0F8FF', font=('Arial', 14, 'bold')).place(x=450, y=25)

# Widget ScrolledText para exibir a tabela de símbolos
st = tkst.ScrolledText(root, width=40, height=20, bd=5, relief='sunken')
st.pack()
st.place(x=450, y=50)

# Rótulo para o código compilado em C
Label(root, text='Código Compilado em C', bg='#F0F8FF', font=('Arial', 14, 'bold')).place(x=870, y=25)

# Widget ScrolledText para exibir o código compilado em C
cCode = tkst.ScrolledText(root, width=40, height=20, bd=5, relief='sunken')
cCode.pack()
cCode.place(x=870, y=50)

# Botão para acionar a função de compilação
Button(root, text='Compilar', bg='#ADD8E6', font=('Arial', 14, 'bold'), command=lambda: compile_Click()).place(x=550, y=500)

# Rótulo para os créditos dos desenvolvedores
Label(root, text='Desenvolvido por: Lucas Lopes, Nycolas Garcia, Breno Melo e Gustavo Henrique', bg='#F0F8FF', font=('Arial', 12, 'italic', 'bold'), fg='#808080').place(x=30, y=570)

# Inicia o loop principal da interface gráfica
root.mainloop()
import enum
# Importa o módulo de enumeração.

from tkinter import *
# Importa todas as classes, funções e variáveis do módulo tkinter.

from tkinter import messagebox
# Importa a função messagebox do módulo tkinter.

root = Tk()
root.withdraw()
# Cria uma instância de Tkinter e a retira da exibição.

# O objeto Lexer acompanha a posição atual no código-fonte e produz cada token.

class Lexer:
    def __init__(self, input):
        # Código-fonte a ser analisado como uma string. Anexa uma nova linha para simplificar a análise/análise sintática do último token/declaração.
        self.source = input + '\n'
        self.curChar = ''   # Caractere atual na string.
        self.curPos = -1    # Posição atual na string.
        self.nextChar()

    # Processa o próximo caractere.
    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'  # EOF
        else:
            self.curChar = self.source[self.curPos]

    # Retorna o caractere seguinte.
    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'
        return self.source[self.curPos+1]

    # Se um token inválido for encontrado, exibe a mensagem de erro.
    def abort(self, message):
        messagebox.showerror("Error", message)
        root.mainloop()

    # Retorna o próximo token.
    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        # Verifica o primeiro caractere deste token para ver se podemos decidir o que é.
        # Se for um operador de vários caracteres (por exemplo, !=), número, identificador ou palavra-chave, processaremos o restante.
        if self.curChar == '+':
            token = Token(self.curChar, TokenType.PLUS)
        elif self.curChar == '-':
            token = Token(self.curChar, TokenType.MINUS)
        elif self.curChar == '*':
            token = Token(self.curChar, TokenType.ASTERISK)
        elif self.curChar == '/':
            token = Token(self.curChar, TokenType.SLASH)
        elif self.curChar == '=':
            # Verifica se este token é = ou ==
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.EQEQ)
            else:
                token = Token(self.curChar, TokenType.EQ)
        elif self.curChar == '>':
            # Verifica se este token é > ou >=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ)
            else:
                token = Token(self.curChar, TokenType.GT)
        elif self.curChar == '<':
            # Verifica se este token é < ou <=
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.LTEQ)
            else:
                token = Token(self.curChar, TokenType.LT)
        elif self.curChar == '!':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.NOTEQ)
            else:
                self.abort("Esperado !=, obtido !" + self.peek())

        elif self.curChar == '\"':
            # Obtém caracteres entre aspas.
            self.nextChar()
            startPos = self.curPos

            while self.curChar != '\"':
                # Não permite caracteres especiais na string. Sem caracteres de escape, novas linhas, tabs ou %.
                # Será usado o printf do C nesta string.
                if self.curChar == '\r' or self.curChar == '\n' or self.curChar == '\t' or self.curChar == '\\' or self.curChar == '%':
                    self.abort("Caractere ilegal na string.")
                self.nextChar()

            tokText = self.source[startPos: self.curPos]  # Obtém a substring.
            token = Token(tokText, TokenType.STRING)

        elif self.curChar.isdigit():
            # O caractere inicial é um dígito, então deve ser um número.
            # Obtém todos os dígitos consecutivos e o decimal, se houver.
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.':  # Decimal!
                self.nextChar()

                # Deve ter pelo menos um dígito após o ponto decimal.
                if not self.peek().isdigit():
                    # Erro!
                    self.abort("Caractere ilegal no número.")
                while self.peek().isdigit():
                    self.nextChar()

            # Obtém a substring.
            tokText = self.source[startPos: self.curPos + 1]
            token = Token(tokText, TokenType.NUMBER)
        elif self.curChar.isalpha():
            # O caractere inicial é uma letra, então deve ser um identificador ou uma palavra-chave.
            # Obtém todos os caracteres alfanuméricos consecutivos.
            startPos = self.curPos
            while self.peek().isalnum():
                self.nextChar()

            # Verifica se o token está na lista de palavras-chave.
            # Obtém a substring.
            tokText = self.source[startPos: self.curPos + 1]
            keyword = Token.checkIfKeyword(tokText)
            if keyword == None:  # Identificador
                token = Token(tokText, TokenType.IDENT)
            else:   # Palavra-chave
                token = Token(tokText, keyword)
        elif self.curChar == '\n':
            # Nova linha.
            token = Token('\n', TokenType.NEWLINE)
        elif self.curChar == '\0':
            # EOF.
            token = Token('', TokenType.EOF)
        else:
            # Token desconhecido!
            self.abort("Token desconhecido: " + self.curChar)

        self.nextChar()
        return token

    # Ignora os espaços em branco, exceto as novas linhas, que serão usadas para indicar o fim de uma declaração.
    def skipWhitespace(self):
        while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
            self.nextChar()

    def skipComment(self):
        if self.curChar == '#':
            while self.curChar != '\n':
                self.nextChar()

# Token contém o texto original e o tipo de token.
class Token:
    def __init__(self, tokenText, tokenKind):
        # Texto real do token. Usado para identificadores, strings e números.
        self.text = tokenText
        # O TokenType ao qual este token é classificado.
        self.kind = tokenKind

    @staticmethod
    def checkIfKeyword(tokenText):
        for kind in TokenType:
            # Depende de todos os valores de enumeração de palavra-chave sendo 1XX.
            if kind.name == tokenText and kind.value >= 100 and kind.value < 200:
                return kind
        return None

# TokenType é a enumeração para todos os tipos de tokens.
class TokenType(enum.Enum):
    EOF = -1
    NEWLINE = 0
    NUMBER = 1
    IDENT = 2
    STRING = 3
    # Palavras-chave.
    LABEL = 101
    GOTO = 102
    PRINT = 103
    INPUT = 104
    LET = 105
    IF = 106
    THEN = 107
    ENDIF = 108
    WHILE = 109
    REPEAT = 110
    ENDWHILE = 111
    # Operadores.
    EQ = 201
    PLUS = 202
    MINUS = 203
    ASTERISK = 204
    SLASH = 205
    EQEQ = 206
    NOTEQ = 207
    LT = 208
    LTEQ = 209
    GT = 210
    GTEQ = 211






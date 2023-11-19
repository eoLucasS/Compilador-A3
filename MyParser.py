from MyLexer import *
from tkinter import *
from tkinter import messagebox

root = Tk()
root.withdraw()


# O objeto Parser mantém o controle do token atual, verifica se o código corresponde à gramática e emite o código conforme necessário.
class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set()  # Todas as variáveis que declaramos até agora.
        self.labelsDeclared = set()  # Mantém o controle de todos os rótulos declarados.
        # Todos os rótulos "goto", para sabermos se eles existem ou não.
        self.labelsGotoed = set()

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()  # Chame isso duas vezes para inicializar o token atual e o próximo.

    # Retorna verdadeiro se o token atual corresponder.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Retorna verdadeiro se o próximo token corresponder.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Tenta corresponder ao token atual. Se não, gera um erro. Avança o token atual.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Esperava " + kind.name +
                       ", obteve " + self.curToken.kind.name)
        self.nextToken()

    # Avança para o próximo token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # Não precisa se preocupar em passar o EOF, o lexer lida com isso.

    # Retorna verdadeiro se o token atual for um operador de comparação.
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

    def abort(self, message):
        messagebox.showerror("Erro", message)
        root.mainloop()

    # Regras de produção.

    # parse ::= {instrução}

    def parse(self):
        self.emitter.headerLine("#include <stdio.h>")
        self.emitter.headerLine("void main(void){")

        # Como algumas novas linhas são necessárias em nossa gramática, é necessário pular o excesso.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Analisa todas as instruções no programa.
        while not self.checkToken(TokenType.EOF):

            self.statement()

        # Finaliza as coisas.
        self.emitter.emitLine("return;")
        self.emitter.emitLine("}")

        # Verifica se cada rótulo referenciado em um GOTO está declarado.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Tentando ir para um rótulo não declarado: " + label)

    # Uma das seguintes instruções...

    def statement(self):
        # Verifica o primeiro token para ver que tipo de instrução é esta.

        # "PRINT" (expressão | string)
        if self.checkToken(TokenType.PRINT):
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                # String simples, então imprime.
                self.emitter.emitLine(
                    "printf(\"" + self.curToken.text + "\\n\");")
                self.nextToken()

            else:
                # Espera uma expressão e imprime o resultado.
                self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                self.emitter.emitLine("));")

        # "IF" comparação "THEN" bloco "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if(")
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine("){")

            # Zero ou mais instruções no corpo.
            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        # "WHILE" comparação "REPEAT" bloco "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()
            self.emitter.emitLine("){")

            # Zero ou mais instruções no corpo do loop.
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.emitter.emitLine("}")

        # "LABEL" identificador
        elif self.checkToken(TokenType.LABEL):
            self.nextToken()

            # Verifica se este rótulo ainda não existe.
            if self.curToken.text in self.labelsDeclared:
                self.abort("Rótulo já existe: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.emitter.emitLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)

        # "GOTO" identificador
        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.emitter.emitLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)

        # "LET" identificador = expressão
        elif self.checkToken(TokenType.LET):
            self.nextToken()

            # Verifica se o identificador existe na tabela de símbolos. Se não, declare.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            self.emitter.emit(self.curToken.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()
            self.emitter.emitLine(";")

        # "INPUT" identificador
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            # Se a variável ainda não existe, declare-a.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.emitter.headerLine("float " + self.curToken.text + ";")

            # Emite scanf, mas também valida a entrada. Se for inválida, define a variável como 0 e limpa a entrada.
            self.emitter.emitLine(
                "if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
            self.emitter.emitLine(self.curToken.text + " = 0;")
            self.emitter.emit("scanf(\"%")
            self.emitter.emitLine("*s\");")
            self.emitter.emitLine("}")
            self.match(TokenType.IDENT)

        # Esta não é uma instrução válida. Erro!
        else:
            self.abort("Instrução inválida em " + self.curToken.text +
                       " (" + self.curToken.kind.name + ")")

        # Nova linha.
        self.nl()

    # comparação ::= expressão (("==" | "!=" | ">" | ">=" | "<" | "<=") expressão)+

    def comparison(self):
        self.expression()
        # Deve haver pelo menos um operador de comparação e outra expressão.
        if self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()
        # Pode ter 0 ou mais operadores de comparação e expressões.
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    # expressão ::= termo {( "-" | "+" ) termo}

    def expression(self):
        self.term()
        # Pode ter 0 ou mais +/- e expressões.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.term()

    # termo ::= unário {( "/" | "*" ) unário}

    def term(self):
        self.unary()
        # Pode ter 0 ou mais *// e expressões.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.unary()

    # unário ::= ["+" | "-"] primário

    def unary(self):
        # + / - unários opcionais
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        self.primary()

    # primário ::= número | identificador

    def primary(self):
        if self.checkToken(TokenType.NUMBER):
            self.emitter.emit(self.curToken.text)
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Garante que a variável já exista.
            if self.curToken.text not in self.symbols:
                self.abort(
                    "Referência à variável antes da atribuição: " + self.curToken.text)

            self.emitter.emit(self.curToken.text)
            self.nextToken()
        else:
            # Erro!
            self.abort("Token inesperado em " + self.curToken.text)

    # nl ::= '\n'+
    def nl(self):
        # Exige pelo menos uma nova linha.
        self.match(TokenType.NEWLINE)
        # Mas também permitimos novas linhas extras, é claro.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

            

            
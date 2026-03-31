import enum


class CompilerError(Exception):
    """Base exception for compiler errors with line/position tracking."""
    pass


class LexerError(CompilerError):
    pass


class Lexer:
    def __init__(self, source):
        self.source = source + '\n'
        self.curChar = ''
        self.curPos = -1
        self.line = 1
        self.col = 0
        self.nextChar()

    def nextChar(self):
        self.curPos += 1
        if self.curPos >= len(self.source):
            self.curChar = '\0'
        else:
            self.curChar = self.source[self.curPos]
            if self.curChar == '\n':
                self.line += 1
                self.col = 0
            else:
                self.col += 1

    def peek(self):
        if self.curPos + 1 >= len(self.source):
            return '\0'
        return self.source[self.curPos + 1]

    def abort(self, message):
        raise LexerError(f"Line {self.line}, col {self.col}: {message}")

    def skipWhitespace(self):
        while self.curChar in (' ', '\t', '\r'):
            self.nextChar()

    def skipComment(self):
        if self.curChar == '#':
            while self.curChar != '\n':
                self.nextChar()

    def getToken(self):
        self.skipWhitespace()
        self.skipComment()
        token = None

        if self.curChar == '+':
            token = Token(self.curChar, TokenType.PLUS)
        elif self.curChar == '-':
            token = Token(self.curChar, TokenType.MINUS)
        elif self.curChar == '*':
            token = Token(self.curChar, TokenType.ASTERISK)
        elif self.curChar == '/':
            token = Token(self.curChar, TokenType.SLASH)

        elif self.curChar == '=':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.EQEQ)
            else:
                token = Token(self.curChar, TokenType.EQ)

        elif self.curChar == '>':
            if self.peek() == '=':
                lastChar = self.curChar
                self.nextChar()
                token = Token(lastChar + self.curChar, TokenType.GTEQ)
            else:
                token = Token(self.curChar, TokenType.GT)

        elif self.curChar == '<':
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
                self.abort(f"Expected '!=', got '!{self.peek()}'")

        elif self.curChar == '"':
            self.nextChar()
            startPos = self.curPos
            while self.curChar != '"':
                if self.curChar in ('\r', '\n', '\t', '\\', '%'):
                    self.abort("Illegal character in string literal")
                if self.curChar == '\0':
                    self.abort("Unterminated string literal")
                self.nextChar()
            tokText = self.source[startPos:self.curPos]
            token = Token(tokText, TokenType.STRING)

        elif self.curChar.isdigit():
            startPos = self.curPos
            while self.peek().isdigit():
                self.nextChar()
            if self.peek() == '.':
                self.nextChar()
                if not self.peek().isdigit():
                    self.abort("Invalid decimal number — expected digit after '.'")
                while self.peek().isdigit():
                    self.nextChar()
            tokText = self.source[startPos:self.curPos + 1]
            token = Token(tokText, TokenType.NUMBER)

        elif self.curChar.isalpha():
            startPos = self.curPos
            while self.peek().isalnum() or self.peek() == '_':
                self.nextChar()
            tokText = self.source[startPos:self.curPos + 1]
            keyword = Token.checkIfKeyword(tokText)
            if keyword is None:
                token = Token(tokText, TokenType.IDENT)
            else:
                token = Token(tokText, keyword)

        elif self.curChar == '\n':
            token = Token('\n', TokenType.NEWLINE)

        elif self.curChar == '\0':
            token = Token('', TokenType.EOF)

        else:
            self.abort(f"Unknown token: '{self.curChar}'")

        self.nextChar()
        return token


class Token:
    def __init__(self, text, kind):
        self.text = text
        self.kind = kind

    @staticmethod
    def checkIfKeyword(text):
        for kind in TokenType:
            if kind.name == text and 100 <= kind.value < 200:
                return kind
        return None


class TokenType(enum.Enum):
    EOF = -1
    NEWLINE = 0
    NUMBER = 1
    IDENT = 2
    STRING = 3
    # Keywords (100-199)
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
    # Operators (200+)
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

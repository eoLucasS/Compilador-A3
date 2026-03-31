class Emitter:
    def __init__(self, fullPath):
        self.fullPath = fullPath
        self.header = ""
        self.code = ""

    def emit(self, code):
        self.code += code

    def emitLine(self, code):
        self.code += code + '\n'

    def headerLine(self, code):
        self.header += code + '\n'

    def getOutput(self):
        return self.header + self.code

    def writeFile(self):
        with open(self.fullPath, 'w') as f:
            f.write(self.getOutput())

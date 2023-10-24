from status import Status


class Fetch:
    def __init__(self, instrMem, decode):
        self.instrMem = instrMem
        self.addr = 0
        self.decode = decode
        self.currentVectorLength = 64
        self.__status = Status.FREE

    def run(self):

        # instr = self.instrMem.Read(self.addr)  # Reading the instruction
        if len(self.instrMem) == self.addr or self.__status == Status.COMPLETED:
            self.__status = Status.COMPLETED
            return Status.SUCCESS, None

        instr = self.instrMem[self.addr]

        if instr.split()[0] == 'MTCL':
            if self.decode.isClear():
                self.currentVectorLength = int(instr.split()[-1])
                self.addr = self.addr + 1
                return Status.SUCCESS, instr
            else:
                return Status.SUCCESS, None
        else:
            self.addr = self.addr + 1
            return Status.SUCCESS, instr


    def getCurrentVectorLength(self):
        return self.currentVectorLength

    def getStatus(self):
        return self.__status
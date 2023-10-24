from decode import Decode
from status import Status


class DataEngine:

    def __init__(self, bankBusyTime, numberOfBanks, loadStorePipeline):
        self.bankBusyTime = bankBusyTime
        self.numberOfBanks = numberOfBanks
        self.loadStorePipeline = loadStorePipeline
        self.bankBusyBoard = [0] * numberOfBanks
        self.addresses = []
        self.__status = Status.FREE
        self.pipeline = [None] * self.loadStorePipeline
        self.element = None
        self.freeBusyBoard = None
        self.instr = None
        pass

    def run(self, dataInstr):
        for i in range(self.numberOfBanks):
            self.bankBusyBoard[i] = max(0, self.bankBusyBoard[i] - 1)

        if dataInstr is not None and self.__status == Status.FREE:
            self.instr = dataInstr
            self.__status = Status.BUSY
            self.addresses = dataInstr.get(Decode.INSTR_ADDRESS)

        if self.__status == Status.BUSY and len(self.addresses) > 0:
            address = self.pipeline[-1]
            if address is not None:
                bankNo = address % self.numberOfBanks
                if self.bankBusyBoard[bankNo] == 0:
                    self.bankBusyBoard[bankNo] = self.bankBusyTime
                    self.pipeline.pop()
                    self.pipeline.insert(0, self.addresses.pop())
            else:
                self.pipeline.pop()
                self.pipeline.insert(0, self.addresses.pop())

        # print(self.addresses)
        if len(self.addresses) == 0 and self.areBanksFree():
            self.freeBusyBoard(self.instr)
            self.__status = Status.FREE

    def getStatus(self):
        return self.__status

    def setFreeBusyBoard(self, freeBusyBoard):
        self.freeBusyBoard = freeBusyBoard

    def areBanksFree(self):
        for element in self.bankBusyBoard:
            if element != 0:
                return False
        return True

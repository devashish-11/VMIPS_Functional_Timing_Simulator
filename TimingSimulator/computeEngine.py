from decode import Decode
from status import Status


class ComputeEngine:
    addPipelineInstr = ['ADDVV', 'SUBVV', 'ADDVS', 'SUBVS', 'SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV',
                        'SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLEVS']
    mulPipelineInstr = ['MULVV', 'MULVS']
    divPipelineInstr = ['DIVVV', 'DIVVS']

    def __init__(self, addPipelineDepth, mulPipelineDepth, divPipelineDepth, numberOfLanes):
        self.addPipelineDepth = addPipelineDepth
        self.mulPipelineDepth = mulPipelineDepth
        self.divPipelineDepth = divPipelineDepth
        self.numberOfLanes = numberOfLanes
        self.currentAddInstr = None
        self.currentDivInstr = None
        self.currentMulInstr = None
        self.__addPipelineStatus = Status.FREE
        self.__mulPipelineStatus = Status.FREE
        self.__divPipelineStatus = Status.FREE
        self.addCycle = 0
        self.mulCycle = 0
        self.divCycle = 0
        self.freeBusyBoard = None

    def run(self, computeInstr, currentVectorLength):
        self.addCycle = max(0, self.addCycle - 1)
        self.mulCycle = max(0, self.mulCycle - 1)
        self.divCycle = max(0, self.divCycle - 1)

        if computeInstr is not None:
            if computeInstr.get(Decode.INSTR_NAME) in ComputeEngine.addPipelineInstr and self.__addPipelineStatus == Status.FREE:
                self.__addPipelineStatus = Status.BUSY
                self.currentAddInstr = computeInstr
                self.addCycle = self.addPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1


            elif computeInstr.get(Decode.INSTR_NAME) in ComputeEngine.mulPipelineInstr and self.__mulPipelineStatus == Status.FREE:
                self.__mulPipelineStatus = Status.BUSY
                self.currentMulInstr = computeInstr
                self.mulCycle = self.mulPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1
            else:
                self.__divPipelineStatus = Status.BUSY
                self.currentDivInstr = computeInstr
                self.divCycle = self.divPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1

        if self.addCycle == 0 and self.__addPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentAddInstr)
            self.__addPipelineStatus = Status.FREE
        if self.mulCycle == 0 and self.__mulPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentMulInstr)
            self.__mulPipelineStatus = Status.FREE
        if self.divCycle == 0 and self.__divPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentDivInstr)
            self.__divPipelineStatus = Status.FREE

    def getPipelineStatus(self):
        return self.__addPipelineStatus, self.__mulPipelineStatus, self.__divPipelineStatus

    def getAddPipelineStatus(self):
        return self.__addPipelineStatus

    def getMulPipelineStatus(self):
        return self.__mulPipelineStatus

    def getDivPipelineStatus(self):
        return self.__divPipelineStatus

    def setFreeBusyBoard(self, freeBusyBoard):
        self.freeBusyBoard = freeBusyBoard

    def isDone(self):
        return self.__divPipelineStatus == Status.FREE and self.__mulPipelineStatus == Status.FREE and self.__addPipelineStatus == Status.FREE

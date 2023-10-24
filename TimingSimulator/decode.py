import computeEngine
from status import Status


class Decode:
    INSTR_EMPTY = 0
    INSTR_COMPUTE = 1
    INSTR_DATA = 2
    INSTR_SCALAR = 3
    INSTR_TYPE = "Type"
    INSTR_SDEST = "SDest"
    INSTR_VDEST = "VDest"
    INSTR_VSRC = "VSrc"
    INSTR_SSRC = "SSrc"
    INSTR_NAME = "Name"
    INSTR_ADDRESS = "Address"
    INSTR_ARGS = "Args"

    INS = dict.fromkeys(['LS', 'SS', 'ADD', 'SUB', 'SRA', 'SRL', 'SLL', 'AND', 'OR',
                         'XOR', 'BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE', 'MFCL', 'MTCL', 'CVM', 'POP', 'HALT'],
                        INSTR_SCALAR)
    INS.update(dict.fromkeys(['LV', 'SV', 'LVWS', 'SVWS', 'LVI', 'SVI'], INSTR_DATA))
    INS.update(dict.fromkeys(['ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV',
                              'ADDVS', 'SUBVS', 'MULVS', 'DIVVS', 'SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLVES'],
                             INSTR_COMPUTE))

    def __init__(self, computeQueueDepth, dataQueueDepth, vectorRegisterLength, scalarRegisterLength, computeEngine,
                 dataEngine):
        self.computeQueueDepth = computeQueueDepth
        self.dataQueueDepth = dataQueueDepth
        self.computeEngine = computeEngine
        self.dataEngine = dataEngine
        self.computeQueue = []
        self.dataQueue = []
        self.scalarQueue = []
        self.args = 0
        self.__computeStatus = Status.FREE
        self.__dataStatus = Status.FREE
        self.instr = None
        self.vectorBusyBoard = [0] * vectorRegisterLength
        self.scalarBusyBoard = [0] * scalarRegisterLength
        self.priorityQueue = []

    def run(self, instr):

        # region Popping out of the queue
        if self.shouldPopCompute():
            computeInstr = self.computeQueue.pop(0) if len(self.computeQueue) > 0 else None
            self.__computeStatus = Status.FREE
        else:
            computeInstr = None

        if self.shouldPopData():
            dataInstr = self.dataQueue.pop(0) if len(self.dataQueue) > 0 else None
            self.__dataStatus = Status.FREE
        else:
            dataInstr = None

        scalarInstr = self.scalarQueue.pop(0) if len(self.scalarQueue) > 0 else None
        self.freeBusyBoard(scalarInstr)
        # endregion

        # Adding to Queue
        if instr is not None:
            self.args = instr.split()
            self.instr = {Decode.INSTR_TYPE: self.INS.get(self.args[0], None),
                          Decode.INSTR_NAME: self.args[0],
                          Decode.INSTR_ARGS: instr.split()}
            self.priorityQueue.append(self.instr)
            if self.instr.get(Decode.INSTR_TYPE) is None:
                return Status.FAILED, None, None, None
        toggle = False
        for index, instr in enumerate(self.priorityQueue):
            self.instr = instr
            self.args = instr.get(Decode.INSTR_ARGS)
            self.parseInstruction()
            # Compute part
            if self.__computeStatus == Status.FREE and instr.get(Decode.INSTR_TYPE) == Decode.INSTR_COMPUTE:
                if self.checkBusyBoard():
                    self.updateBusyBoard()
                    self.computeQueue.append(self.instr)
                    toggle = True
                    if len(self.computeQueue) == self.computeQueueDepth:
                        self.__computeStatus = Status.BUSY
                    else:
                        self.__computeStatus = Status.FREE

            # Data Part
            elif self.__dataStatus == Status.FREE and instr.get(Decode.INSTR_TYPE) == Decode.INSTR_DATA:
                if self.checkBusyBoard():
                    self.updateBusyBoard()
                    self.dataQueue.append(self.instr)
                    toggle = True
                    if len(self.dataQueue) == self.dataQueueDepth:
                        self.__dataStatus = Status.BUSY
                    else:
                        self.__dataStatus = Status.FREE

            # Scalar Part
            elif instr.get(Decode.INSTR_TYPE) == Decode.INSTR_SCALAR and self.checkBusyBoard():
                self.updateBusyBoard()
                toggle = True
                self.scalarQueue.append(self.instr)

            if toggle:
                self.priorityQueue.pop(index)
                break

        return Status.SUCCESS, computeInstr, dataInstr, scalarInstr

    def getComputeStatus(self):
        return self.__computeStatus

    def getDataStatus(self):
        return self.__dataStatus

    def isClear(self):
        # a = self.shouldPopCompute() and len(self.computeQueue) == 1
        # b = self.shouldPopData() and len(self.dataQueue) == 1
        c = len(self.computeQueue) == 0
        d = len(self.dataQueue) == 0
        e = self.dataEngine.getStatus() == Status.FREE
        f = self.computeEngine.isDone()
        if c and d and e and f:
            return True
        else:
            return False

    def shouldPopCompute(self):
        return len(self.computeQueue) > 0 and ((self.computeQueue[0].get(
            Decode.INSTR_NAME) in computeEngine.ComputeEngine.addPipelineInstr and self.computeEngine.getAddPipelineStatus() == Status.FREE)
                                               or (self.computeQueue[0].get(
                    Decode.INSTR_NAME) in computeEngine.ComputeEngine.mulPipelineInstr and self.computeEngine.getMulPipelineStatus() == Status.FREE)
                                               or (self.computeQueue[0].get(
                    Decode.INSTR_NAME) in computeEngine.ComputeEngine.divPipelineInstr and self.computeEngine.getDivPipelineStatus() == Status.FREE))

    def shouldPopData(self):
        return self.dataEngine.getStatus() == Status.FREE

    def freeBusyBoard(self, instr):
        if instr is not None:
            sdest = instr.get(Decode.INSTR_SDEST)
            if sdest is not None:
                self.scalarBusyBoard[sdest] = 0

            vdest = instr.get(Decode.INSTR_VDEST)
            if vdest is not None:
                self.vectorBusyBoard[vdest] = 0

    def parseInstruction(self):
        name = self.instr[Decode.INSTR_NAME]
        type = self.instr[Decode.INSTR_TYPE]

        if type == Decode.INSTR_COMPUTE:
            if name in ['ADDVV', 'SUBVV', 'MULVV', 'DIVVV']:
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_VSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]
            elif name in ['ADDVS', 'SUBVS', 'MULVS', 'DIVVS']:
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_VSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[3][2:])]
            elif name in ['SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV']:
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name in ['SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLVES']:
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
        elif type == Decode.INSTR_SCALAR:
            if name == 'SS':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name == 'LS':
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA']:
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]
            elif name in ['BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE']:
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name in ['MFCL', 'POP']:
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
            elif name == 'MTCL':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:])]
        else:
            self.instr[Decode.INSTR_ADDRESS] = [int(num) for num in self.args[-1].strip('()').split(',')]
            if name == 'LV':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name == 'LVI':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_VSRC] = [int(self.args[3][2:])]
            elif name == 'LVWS':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[3][2:])]
            elif name == 'SV':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name == 'SVI':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:]), int(self.args[3][2:])]
            elif name == 'SVWS':
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]

    def checkBusyBoard(self):
        ssrc = self.instr.get(Decode.INSTR_SSRC)
        if ssrc is not None:
            for i in ssrc:
                if self.scalarBusyBoard[i]:
                    return False

        vsrc = self.instr.get(Decode.INSTR_VSRC)
        if vsrc is not None:
            for i in vsrc:
                if self.vectorBusyBoard[i]:
                    return False

        sdest = self.instr.get(Decode.INSTR_SDEST)
        if sdest is not None:
            if self.scalarBusyBoard[sdest]:
                return False

        vdest = self.instr.get(Decode.INSTR_VDEST)
        if vdest is not None:
            if self.vectorBusyBoard[vdest]:
                return False

        return True

    def updateBusyBoard(self):
        sdest = self.instr.get(Decode.INSTR_SDEST)
        if sdest is not None:
            self.scalarBusyBoard[sdest] = 1

        vdest = self.instr.get(Decode.INSTR_VDEST)
        if vdest is not None:
            self.vectorBusyBoard[vdest] = 1

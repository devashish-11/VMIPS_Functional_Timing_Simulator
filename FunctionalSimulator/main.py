import os
import argparse
import instructions as ins


# Written by Aswin Raj K (ar7997) and Devashish (dg4015)
# Functional Simulator main file

class IMEM(object):
    def __init__(self, iodir, name="Code.asm"):
        self.size = pow(2, 16)  # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, name))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [instruction.split('#')[0].strip() for instruction in insf.readlines() if
                                     not (instruction.startswith('#') or instruction.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)

    def Read(self, idx):  # Use this to read from IMEM.
        if idx < self.size:
            return self.instructions[idx]  # Returing the instruction
        else:
            print("IMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)
            return None  # If out of bounds return None


class DMEM(object):
    # Word addressible - each address contains 32 bits.
    def __init__(self, name, iodir, addressLen):
        self.name = name
        self.size = pow(2, addressLen)
        self.min_value = -pow(2, 31)
        self.max_value = pow(2, 31) - 1
        self.ipfilepath = os.path.abspath(os.path.join(iodir, name + ".txt"))
        self.opfilepath = os.path.abspath(os.path.join(iodir, name + "OP.txt"))
        self.data = []

        try:
            with open(self.ipfilepath, 'r') as ipf:
                self.data = [int(line.strip()) for line in ipf.readlines()]
            print(self.name, "- Data loaded from file:", self.ipfilepath)
            self.data.extend([0x0 for _ in range(self.size - len(self.data))])  # Initialize the remaining as zeroes
        except:
            print(self.name, "- ERROR: Couldn't open input file in path:", self.ipfilepath)

    def Read(self, idx):  # Use this to read from DMEM.
        if idx < self.size:
            return self.data[idx]  # Returning the value at index idx
        else:
            print("Error : Memory Out of bounds exception")
            return None  # If out of bounds return None

    def Write(self, idx, val):  # Use this to write into DMEM.
        if idx < self.size:
            self.data[idx] = val  # Writing the val at index idx
        else:
            print("Error : Memory Out of bounds exception")
            return None  # If out of bounds return None

    def dump(self):
        try:
            with open(self.opfilepath, 'w') as opf:
                lines = [str(data) + '\n' for data in self.data]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", self.opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", self.opfilepath)


class RegisterFile(object):
    def __init__(self, name, count, length=1, size=32):
        self.name = name
        self.reg_count = count
        self.vec_length = length  # Number of 32 bit words in a register.
        self.reg_bits = size
        self.min_value = -pow(2, self.reg_bits - 1)
        self.max_value = pow(2, self.reg_bits - 1) - 1
        self.registers = [[0x0 for _ in range(self.vec_length)] for r in
                          range(self.reg_count)]  # list of lists of integers

    def Read(self, idx=0):
        if idx < self.reg_count:
            val = self.registers[idx]
            if len(val) != 1:  # For vector registers and VMR
                return self.registers[idx]
            else:  # For scalar register and VLR
                return self.registers[idx][0]
        else:
            print("Error : Memory Out of bounds exception")
            return None  # If out of bounds return None

    def Write(self, idx, val):
        if idx < self.reg_count:
            if type(val) == int:  # For scalar register and VLR
                self.registers[idx] = [val]
            else:  # For vector registers and VMR
                self.registers[idx] = val
        else:
            print("Error : Memory Out of bounds exception")
            return None  # If out of bounds return None

    def dump(self, iodir):
        opfilepath = os.path.abspath(os.path.join(iodir, self.name + ".txt"))
        try:
            with open(opfilepath, 'w') as opf:
                row_format = "{:<13}" * self.vec_length
                lines = [row_format.format(*[str(i) for i in range(self.vec_length)]) + "\n",
                         '-' * (self.vec_length * 13) + "\n"]
                lines += [row_format.format(*[str(val) for val in data]) + "\n" for data in self.registers]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", opfilepath)


class Core:
    # Status variables
    SUCCESS = 1  # For successful core execution
    FAILED = 0  # For failed core execution
    INFINITE = -1  # When core leads to infinite loop
    # Added two handlers pre-execution handler which will be invoked before executing an instruction,
    # and post-execution handler which will be invoked after instruction execution, only if they are specified. This
    # is used for the verification of instruction set.
    HANDLER_FAILED = -2  # When post or pre execution handler fails

    # Register File Names
    VRF = "VRF"
    SRF = "SRF"
    VMR = "VMR"
    VLR = "VLR"

    def __init__(self, instrMem, scalarDataMem, vectorDataMem):
        self.IMEM = instrMem
        self.SDMEM = scalarDataMem
        self.VDMEM = vectorDataMem
        self.RFs = {Core.SRF: RegisterFile(Core.SRF, 8),  # Scalar Register
                    Core.VRF: RegisterFile(Core.VRF, 8, 64),  # Vector Register
                    Core.VMR: RegisterFile(Core.VMR, 1, 64, 1),  # Vector mask register
                    Core.VLR: RegisterFile(Core.VLR, 1, 1)}  # Vector length register
        self.PC = 0  # Program counter
        self.MVL = 64  # Maximum vector length
        self.getRegisterFile(Core.VLR).Write(0, self.MVL)  # initializing the VLR to MVL
        self.getRegisterFile(Core.VMR).Write(0, [1] * 64)  # changing mask register to all ones
        self.ins = ins.Instructions(self)  # Instruction list
        self.resolvedData = []
        # Declaring execution handlers
        self.preInstructionExecutionHandler = None
        self.postInstructionExecutionHandler = None
        print("==================================")
        print("Core Initialized")

    # Function to get the register files
    def getRegisterFile(self, type):
        return self.RFs.get(type, 0)

    # Function to set the handlers, each of the these handlers should be in the following format
    # preInstructionExecutionHandler(instr, current_PC)
    # postInstructionExecutionHandler(instr, current_PC, result)
    # instr : instruction executed or going to be executed (in the case of preInstructionHandler)
    # current_PC : the current Program counter value
    # result : The result after instruction execution
    # returnValue : True, if handler is successful. False, if handler fails
    def setHandlers(self, preExecutionHandler, postExecutionHandler=None):
        self.preInstructionExecutionHandler = preExecutionHandler
        self.postInstructionExecutionHandler = postExecutionHandler

    def run(self):
        print("Functional Simulation started")
        while True:
            current_PC = self.PC  # creating a copy of the program counter value
            try:
                instr = self.IMEM.Read(self.PC)  # Reading the instruction
                # Calling the preInstructionExecutionHandler if specified
                if self.preInstructionExecutionHandler is not None:
                    if not self.preInstructionExecutionHandler(instr,
                                                               current_PC):  # If handler fails end the simulation
                        # and return HANDLER_FAILED as result
                        print("Functional Simulation Failed")
                        print("==================================")
                        return Core.HANDLER_FAILED

                result, resolvedData = self.ins.execute(instr)

                if result in [ins.Instructions.SUCCESS, ins.Instructions.SUCCESS_TERMINATION]:
                    self.resolvedData.append(resolvedData)
                    # Execute postInstructionExecutionHanlder if specified and the result of execution of instruction is successful
                    if self.postInstructionExecutionHandler is not None:
                        if not self.postInstructionExecutionHandler(instr, current_PC,
                                                                    result):  # If handler fails end the simulation and return HANDLER_FAILED as result
                            print("Functional Simulation Failed")
                            print("==================================")
                            return Core.HANDLER_FAILED

            except IndexError:  # All instructions executed
                print("Error - Instruction out of bounds; check if failed to add HALT at the end of Code.asm")
                print("Functional Simulation Failed")
                print("==================================")
                return Core.FAILED

            if result == self.ins.FAILED:  # Execution failed
                print("Functional Simulation Failed")
                print("==================================")
                return Core.FAILED
            elif result == self.ins.SUCCESS_TERMINATION:  # Called HALT
                print("Functional Simulation Completed Successfully")
                print("==================================")
                return Core.SUCCESS  # Execution successful
            elif current_PC == self.PC:
                print("Functional Simulation Lead to Infinite Loop")
                print("==================================")
                return Core.INFINITE  # Going for infinite loop

    def dumpRegs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

    def dumpResolvedData(self, iodir, name="resolvedData"):
        path = os.path.abspath(os.path.join(iodir, name + ".txt"))
        try:
            with open(path, 'w') as opf:
                lines = [str(data) + '\n' for data in self.resolvedData]
                opf.writelines(lines)
            print(name, "- Dumped resolved data into output file in path:", path)
        except:
            print(name, "- ERROR: Couldn't open output file in path:", path)


if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="", type=str,
                        help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)
    # Parse IMEM
    imem = IMEM(iodir)
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 25)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem)
    result = vcore.run()
    if result == Core.FAILED:  # If the core failed to run exit from the program
        exit()

    # Dumping final register values
    vcore.dumpRegs(iodir)
    vcore.dumpResolvedData(iodir)
    sdmem.dump()
    vdmem.dump()


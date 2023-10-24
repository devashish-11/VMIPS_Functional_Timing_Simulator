# Written by Aswin Raj K (ar7997) and Devashish (dg4015)

# This class contains the methods for all the instructions and its associated functions. It will check syntax error
# and register number out of bounds exception before executing each instructions (try making some syntax errors in the
# Code.asm to see the functionality). Each of the instruction methods will return if the execution was successful or
# not, they also update the program counter

import main as vs


class Instructions:
    # Return values for instruction methods
    SUCCESS = 1  # Indicates successful instruction execution
    FAILED = 0  # Indicates failed instruction execution
    SUCCESS_TERMINATION = -1  # Indicates successful termination of the instruction eg : HALT

    # Assembly Syntax format
    SR = "SR"  # For scalar register
    VR = "VR"  # For vector register
    IMM = "IMM"

    def __init__(self, core):
        self.core = core
        # Map to all the instruction functions
        self.INS = {
            "ADDVV": self.ADDVV,
            "SUBVV": self.SUBVV,
            "MULVV": self.MULVV,
            "DIVVV": self.DIVVV,
            "SEQVV": self.SEQVV,
            "SNEVV": self.SNEVV,
            "SGTVV": self.SGTVV,
            "SLTVV": self.SLTVV,
            "SGEVV": self.SGEVV,
            "SLEVV": self.SLEVV,
            "ADDVS": self.ADDVS,
            "SUBVS": self.SUBVS,
            "MULVS": self.MULVS,
            "DIVVS": self.DIVVS,
            "SEQVS": self.SEQVS,
            "SNEVS": self.SNEVS,
            "SGTVS": self.SGTVS,
            "SLTVS": self.SLTVS,
            "SGEVS": self.SGEVS,
            "SLEVS": self.SLEVS,
            "POP": self.POP,
            "MTCL": self.MTCL,
            "MFCL": self.MFCL,
            "LV": self.LV,
            "SV": self.SV,
            "LS": self.LS,
            "SS": self.SS,
            "LVWS": self.LVWS,
            "SVWS": self.SVWS,
            "LVI": self.LVI,
            "SVI": self.SVI,
            "ADD": self.ADD,
            "SUB": self.SUB,
            "SRA": self.SRA,
            "SRL": self.SRL,
            "SLL": self.SLL,
            "AND": self.AND,
            "OR": self.OR,
            "XOR": self.XOR,
            "BEQ": self.BEQ,
            "BNE": self.BNE,
            "BGT": self.BGT,
            "BLT": self.BLT,
            "BGE": self.BGE,
            "BLE": self.BLE,
            "CVM": self.CVM,
            "HALT": self.HALT
        }
        self.args = []

    # Function to execute an instructon
    # instr : instruction to be executed
    # ReturnValue : Instructions.SUCCESS, Instructions.FAILED, Instructions.SUCCESS_TERMINATION
    def execute(self, instr):
        self.args = instr.split()
        val = self.INS.get(self.args[0], self.Default)()
        return val

    # Function to check for syntax or register out of bounds exception in the assembly
    # expectedParamType : expected params for the instruction
    # eg : for instrution LV VR1 SR2 SR0 , expectedParamType = [Instructions.VR, Instructions.SR, Instructions.SR]
    def checkParams(self, expectedParamType=None):
        if expectedParamType is None:
            expectedParamType = []
        expectedParamCount = len(expectedParamType)
        if (len(self.args) - 1) == expectedParamCount:  # Checking if parameter count is as required
            i = 1
            for type in expectedParamType:
                if type == Instructions.VR or type == Instructions.SR:
                    if self.args[i][0:2] != type:
                        print("Error : Parameter mismatch for instruction", self.args[0], ", instruction number:",
                              self.core.PC + 1)
                        print("Expected ", type, " Given ", self.args[i][0:2])
                        return Instructions.FAILED
                    elif not self.args[i][2:].isdigit():  # To check if VR and SR is followed by a positive digit
                        print("Error :  Unidentified register number for instruction", self.args[0],
                              ", instruction number:",
                              self.core.PC + 1)
                        return Instructions.FAILED
                    elif int(self.args[i][2:]) >= self.core.getRegisterFile(
                            vs.Core.VRF if type == Instructions.VR else vs.Core.SRF).reg_count:  # To check if register numbers are within range in out case 0-7
                        print("Error : Register address out of bounds exception for instruction", self.args[0],
                              ", instruction number:",
                              self.core.PC + 1)
                        return Instructions.FAILED
                elif type == Instructions.IMM:  # Check if IMM is a digit
                    if not (self.args[i].isdigit() or (self.args[i][0] == '-' and self.args[i][1:].isdigit())):
                        print("Error : Parameter mismatch for instruction", self.args[0], ", instruction number:",
                              self.core.PC + 1)
                        print("Expected", type, " Given", self.args[i])
                        return Instructions.FAILED
                i += 1
            return Instructions.SUCCESS
        else:  # If the parameters provided for each instruction is less or more
            print("Parameter mismatch for instruction ", self.args[0], ", instruction number: ", self.core.PC + 1)
            print("Expected params", expectedParamCount, ", given", (len(self.args) - 1))
            return Instructions.FAILED

    # region Miscellaneous
    # Function to consider VMR, write only if VMR[i] == 1
    def maskWrite(self, index, value, vector_length=-1):
        value_current = self.core.getRegisterFile(vs.Core.VRF).Read(index)
        mask_val = self.core.getRegisterFile(vs.Core.VMR).Read()
        if vector_length == -1:
            vector_length = self.core.getRegisterFile(vs.Core.VLR).Read()
        for i in range(vector_length):
            if mask_val[i]:
                value_current[i] = value[i]

        return value_current

    def arithmeticRightShift(self, n, shift):
        # Performing right arithmetic shift
        if n < 0:
            # Filling the vacant position at the leftmost end with a copy of the sign bit.
            n = (n >> 1) & ~(1 << 31)
            for i in range(shift - 1):
                # Performs an additional b-1 shifts to the right while setting the leftmost bit to 1 with the mask
                n = (n >> 1) | (1 << 31)
        else:
            n = n >> shift
        return n

    def logicalLeftShift(self, n, shift):
        # Performs arithmetic shift and then applies the bitwise AND operation with the 0xffffffff mask to ensure
        # that the result is a 32-bit unsigned integer.
        return (n << shift) & 0xffffffff

    def logicalRightShift(self, n, shift):
        # Convert n to an unsigned integer by masking with 0xffffffff
        n_unsigned = n & 0xffffffff

        # Perform the logical right shift on the unsigned integer
        result_unsigned = n_unsigned >> shift

        # Convert the unsigned result back to a signed integer
        # if the original integer was negative
        if n < 0:
            # Check if the leftmost bit is set in the result
            if result_unsigned & 0x80000000:
                # If it is, set the other leftmost bits to 1
                result_signed = -((~result_unsigned + 1) & 0xffffffff)
            else:
                result_signed = result_unsigned
        else:
            result_signed = result_unsigned

        return result_signed

    # endregion

    ###############CODE FOR EXECUTING EACH INSTRUTION#####################
    ##Self explainable

    # region Vector-Vector Operations
    def ADDVV(self):
        result = self.checkParams([Instructions.VR] * 3)
        if result == Instructions.FAILED:  # If there is any error in syntax
            return Instructions.FAILED
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        if vx_value is None or vy_value is None:  # To check if address is out of bounds
            return Instructions.FAILED

        vz_value_final = [vx_value[i] + vy_value[i] for i in range(0, vl_val)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final, vl_val))
        self.core.PC += 1  # Updating the program counter

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # Further instructions almost follow the same procedure which is easily understandable

    def SUBVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vz_value_final = [vx_value[i] - vy_value[i] for i in range(0, vl_val)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final, vl_val))
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def MULVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vz_value_final = [vx_value[i] * vy_value[i] for i in range(0, vl_val)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final, vl_val))
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # Check for division by zero error
    def DIVVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        try:
            vz_value_final = [vx_value[i] / vy_value[i] for i in range(0, vl)]
        except ZeroDivisionError:
            print("Error - Division by zero")
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final))
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Vector-Vector Mask Operations
    def SEQVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] == vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SNEVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] != vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SGTVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] > vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SLTVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] < vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SGEVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] >= vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SLEVV(self):
        result = self.checkParams([Instructions.VR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if vx_value is None or vy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] <= vy_value[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Vector-Scalar Operations
    def ADDVS(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        vz_value_final = [vx_value[i] + sy_value for i in range(0, vl)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SUBVS(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        vz_value_final = [vx_value[i] - sy_value for i in range(0, vl)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def MULVS(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        vz_value_final = [vx_value[i] * sy_value for i in range(0, vl)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def DIVVS(self):
        result = self.checkParams([Instructions.VR, Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        try:
            vz_value_final = [vx_value[i] / sy_value for i in range(0, vl)]
        except ZeroDivisionError:
            print("Error - Division by zero")
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.VRF).Write(vz, self.maskWrite(vz, vz_value_final))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Vector-Scalar Mask Operations
    def SEQVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] == sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SNEVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] != sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SGTVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] > sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SLTVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] < sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SGEVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] >= sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SLEVS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl = self.core.getRegisterFile(vs.Core.VLR).Read()
        masked_reg = [int(vx_value[i] <= sy_value) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.getRegisterFile(vs.Core.VMR).Write(0, masked_reg)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Mask Operations

    def POP(self):
        result = self.checkParams([Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sy = (self.args[0], int(self.args[1][2:]))
        masked_reg = self.core.getRegisterFile(vs.Core.VMR).Read(0)
        sy_value = 0
        for i in masked_reg:
            sy_value += i
        self.core.getRegisterFile(vs.Core.SRF).Write(sy, sy_value)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def CVM(self):
        result = self.checkParams()
        if result == Instructions.FAILED:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.VMR).Write(0, [1] * 64)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Vector Length Register Operations
    def MTCL(self):
        result = self.checkParams([Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sy = (self.args[0], int(self.args[1][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if sy_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.VLR).Write(0, sy_value)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        resolvedData += str(sy_value)
        return Instructions.SUCCESS, resolvedData.strip()

    def MFCL(self):
        result = self.checkParams([Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sy = (self.args[0], int(self.args[1][2:]))
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        self.core.getRegisterFile(vs.Core.SRF).Write(sy, vl_val)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Load Store Operations

    def LV(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        if sy_value is None:
            return Instructions.FAILED
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        vx_value_final = [self.core.VDMEM.Read(sy_value + i) for i in range(vl_val)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vx, self.maskWrite(vx, vx_value_final, vl_val))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in range(vl_val):
            resolvedData += str(sy_value + i) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    def SV(self):
        result = self.checkParams([Instructions.VR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        vx_value = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        if vx_value is None or sy_value is None:
            return Instructions.FAILED
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        mask_val = self.core.getRegisterFile(vs.Core.VMR).Read()
        for i in range(sy_value, sy_value + vl_val):
            if mask_val[i - sy_value]:
                self.core.VDMEM.Write(i, vx_value[i - sy_value])
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in range(vl_val):
            resolvedData += str(sy_value + i) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    def LS(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.SDMEM.Read(sy_value + imm)

        if sy_value is None or sx_value is None:
            return Instructions.FAILED

        self.core.getRegisterFile(vs.Core.SRF).Write(sx, sx_value)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SS(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sx_value is None:
            return Instructions.FAILED

        self.core.SDMEM.Write(sy + imm, sx_value)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def LVWS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy, sx = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        vx_value_final = [self.core.VDMEM.Read(sy_value + i * sx_value) for i in range(vl_val)]
        self.core.getRegisterFile(vs.Core.VRF).Write(vx, self.maskWrite(vx, vx_value_final, vl_val))
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in range(vl_val):
            resolvedData += str(sy_value + i * sx_value) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    def SVWS(self):
        result = self.checkParams([Instructions.VR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy, sx = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        vx_val = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        mask_val = self.core.getRegisterFile(vs.Core.VMR).Read()
        for i in range(vl_val):
            if mask_val[i]:
                self.core.VDMEM.Write(sy_value + i * sx_value, vx_val[i])
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in range(vl_val):
            resolvedData += str(sy_value + i * sx_value) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    def LVI(self):
        result = self.checkParams([Instructions.VR, Instructions.SR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if sy_value is None or vy_value is None:
            return Instructions.FAILED
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        vx_value_final = [self.core.VDMEM.Read(sy_value + i) for i in vy_value[0:vl_val]]
        self.core.VDMEM.Write(vx, self.maskWrite(vx, vx_value_final, vl_val))
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in vy_value[0:vl_val]:
            resolvedData += str(sy_value + i) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    def SVI(self):
        result = self.checkParams([Instructions.VR, Instructions.SR, Instructions.VR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, vx, sy, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        vy_value = self.core.getRegisterFile(vs.Core.VRF).Read(vy)
        if sy_value is None or vy_value is None:
            return Instructions.FAILED
        vx_val = self.core.getRegisterFile(vs.Core.VRF).Read(vx)
        vl_val = self.core.getRegisterFile(vs.Core.VLR).Read()
        mask_val = self.core.getRegisterFile(vs.Core.VMR).Read()
        for i in range(vl_val):
            if mask_val[i]:
                self.core.VDMEM.Write(sy_value + vy_value[i], vx_val[i])
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "
        resolvedData += "("

        for i in vy_value[0:vl_val]:
            resolvedData += str(sy_value + i) + ","

        resolvedData = resolvedData[:-1] + ")"

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Scalar-Scalar Operations
    def ADD(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, sx_value + sy_value)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SUB(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, sx_value - sy_value)
        self.core.PC += 1

        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SRA(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, self.arithmeticRightShift(sx_value, sy_value))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SRL(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, self.logicalRightShift(sx_value, sy_value))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def SLL(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, self.logicalLeftShift(sx_value, sy_value))
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def AND(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, sx_value & sy_value)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def OR(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, sx_value | sy_value)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def XOR(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.SR])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        self.core.getRegisterFile(vs.Core.SRF).Write(sz, sx_value ^ sy_value)
        self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Branch Operations
    def BEQ(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value == sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def BNE(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value != sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def BGT(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value < sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def BLT(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value > sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def BGE(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value <= sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    def BLE(self):
        result = self.checkParams([Instructions.SR, Instructions.SR, Instructions.IMM])
        if result == Instructions.FAILED:
            return Instructions.FAILED
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vs.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vs.Core.SRF).Read(sx)
        if sy_value is None or sx_value is None:
            return Instructions.FAILED
        if sy_value >= sx_value:
            self.core.PC += imm
        else:
            self.core.PC += 1
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS, resolvedData.strip()

    # endregion

    # region Termination operations
    def HALT(self):
        self.checkParams()
        resolvedData = ""
        for i in self.args:
            resolvedData += i + " "

        return Instructions.SUCCESS_TERMINATION, resolvedData.strip()

    # endregion

    # region Default
    # Is executed if no instruction is found
    def Default(self):
        print("Error : Instruction", self.args[0], "Not Found!", ", instruction number:",
              self.core.PC + 1)
        return Instructions.FAILED
    # endregion

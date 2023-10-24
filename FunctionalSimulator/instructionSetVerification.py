import os
import argparse

import ar7997_dg4015_funcsimulator as vp
from instructions import Instructions


# Written by Aswin Raj K (ar7997) and Devashish (dg4015)
# Class for verifying the working of all the instructions
class InstructionSetVerification:
    VERIFICATION_SUCCESS = 1  # If verification is successful
    VERIFICATION_FAILED = 0  # If verifications fails

    def __init__(self, iodir):
        self.iodir = iodir
        self.args = None
        self.prevVectorRegisterValue = []  # For storing vector register values before an instruction is executed
        self.prevMaskRegisterValues = []  # For storing vector mask register values before an instruction is executed
        self.current_PC = -1
        self.executionResult = None  # For storing the result of current instruction execution
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
        }  # Map to all the instruction verification methods

    def init(self):
        if not self.isCodeAvailable():  # Check if Code.asm is available
            return InstructionSetVerification.VERIFICATION_FAILED
        # Parse SMEM
        self.sdmem = vp.DMEM("SDMEM", self.iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
        # Parse VMEM
        self.vdmem = vp.DMEM("VDMEM", self.iodir, 17)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.
        # Parse IMEM
        self.imem = vp.IMEM(self.iodir)
        # Create Vector Core
        self.core = vp.Core(self.imem, self.sdmem, self.vdmem)
        # Setting handlers
        # self.__preExecutionHandler will be executed before an instruction execution so we can store the values in registers before its execution.
        # self.__postExecutionHandler will be executed after an instruciton execution so we can verify the result.
        self.core.setHandlers(self.__preExecutionHandler, self.__postExecutionHandler)

    # Function to start the verification
    def verify(self):
        result = self.core.run()  # Running the simulator
        if result == vp.Core.FAILED:
            print("Core failed due to errors in .asm file - Verification unsuccessful")
            return InstructionSetVerification.VERIFICATION_FAILED
        elif result == vp.Core.INFINITE:
            print("Assembly led to infinite loop - Verification unsuccessful")
            return InstructionSetVerification.VERIFICATION_FAILED
        elif result == vp.Core.HANDLER_FAILED:
            print("Instruction executed incorrectly - Verification unsuccessful")
            return InstructionSetVerification.VERIFICATION_FAILED

        print("All instructions verified - Verification Successful")
        return InstructionSetVerification.VERIFICATION_SUCCESS

    # region Handler
    # This is function is called before an instruction is executed
    def __preExecutionHandler(self, instr, PC):
        self.args = instr.split()
        # Creating a copy of register values for verifying later
        self.prevVectorRegisterValue = []
        self.current_PC = PC
        self.prevMaskRegisterValues = self.core.getRegisterFile(vp.Core.VMR).Read()

        if len(self.args) > 1 and self.args[1][:2] == Instructions.VR:
            self.prevVectorRegisterValue = self.core.getRegisterFile(vp.Core.VRF).Read(int(self.args[1][2:]))
        return True

    # This is function is called after an instruction is executed
    def __postExecutionHandler(self, instr, PC, result):
        self.executionResult = result
        status = self.INS.get(self.args[0],
                              self.Default())()  # Calling the verification function for each of the instruction
        if status == InstructionSetVerification.VERIFICATION_FAILED:  # If verfication fails return False
            print("Verification failed for instruction", self.args[0])
            return False

        return True

    # endregion

    # region Miscellaneous
    def isCodeAvailable(self):
        codeFilePath = os.path.join(self.iodir, "Code.asm")
        return os.path.isfile(codeFilePath)

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

    # ##################Contains function for the verification of each instruction####################
    # Code is self explanatory Each of these function will return, InstructionSetVerification.VERIFICATION_SUCCESS if the
    # instruction is verified and return InstructionSetVerification.VERIFICATION_FAILED if the instruction fails
    # verification

    # region Vector-Vector Operations
    def ADDVV(self):
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vp.Core.VLR).Read()
        vmr_val = self.core.getRegisterFile(vp.Core.VMR).Read()
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        vz_prev_value = self.prevVectorRegisterValue

        # Verifying till current VL
        for i in range(vl_val):
            sum = vx_value[i] + vy_value[i]
            if sum != vz_value[i] and vmr_val[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            if not vmr_val[i] and vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        # Verifying if the values after current VL remains unchanged
        for i in range(vl_val + 1, self.core.MVL):
            if vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SUBVV(self):
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vp.Core.VLR).Read()
        vmr_val = self.core.getRegisterFile(vp.Core.VMR).Read()
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        vz_prev_value = self.prevVectorRegisterValue
        for i in range(vl_val):
            sub = vx_value[i] - vy_value[i]
            if sub != vz_value[i] and vmr_val[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            if not vmr_val[i] and vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl_val + 1, self.core.MVL):
            if vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def MULVV(self):
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vp.Core.VLR).Read()
        vmr_val = self.core.getRegisterFile(vp.Core.VMR).Read()
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        vz_prev_value = self.prevVectorRegisterValue
        for i in range(vl_val):
            mul = vx_value[i] * vy_value[i]
            if mul != vz_value[i] and vmr_val[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            if not vmr_val[i] and vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl_val + 1, self.core.MVL):
            if vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # Check for division by zero error
    def DIVVV(self):
        ins, vz, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl_val = self.core.getRegisterFile(vp.Core.VLR).Read()
        vmr_val = self.core.getRegisterFile(vp.Core.VMR).Read()
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        vz_prev_value = self.prevVectorRegisterValue
        for i in range(vl_val):
            div = vx_value[i] / vy_value[i]
            if div != vz_value[i] and vmr_val[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            if not vmr_val[i] and vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl_val + 1, self.core.MVL):
            if vz_value != vz_prev_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Vector-Vector Mask Operations
    def SEQVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if vx_value[i] == vy_value[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SNEVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] != vy_value[i]) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SGTVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] > vy_value[i]) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SLTVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] < vy_value[i]) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SGEVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] >= vy_value[i]) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SLEVV(self):
        ins, vx, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] <= vy_value[i]) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Vector-Scalar Operations
    def ADDVS(self):
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        prev_vz_value = self.prevVectorRegisterValue
        vmr_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        for i in range(vl):
            sum = vx_value[i] + sy_value
            if sum != vz_value[i] and vmr_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not vmr_value[i] and prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SUBVS(self):
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        prev_vz_value = self.prevVectorRegisterValue
        vmr_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        for i in range(vl):
            sum = vx_value[i] - sy_value
            if sum != vz_value[i] and vmr_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not vmr_value[i] and prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def MULVS(self):
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        prev_vz_value = self.prevVectorRegisterValue
        vmr_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        for i in range(vl):
            mul = vx_value[i] * sy_value
            if mul != vz_value[i] and vmr_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not vmr_value[i] and prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def DIVVS(self):
        ins, vz, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vz_value = self.core.getRegisterFile(vp.Core.VRF).Read(vz)
        prev_vz_value = self.prevVectorRegisterValue
        vmr_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        for i in range(vl):
            div = vx_value[i] / sy_value
            if div != vz_value[i] and vmr_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not vmr_value[i] and prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if prev_vz_value[i] != vz_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Vector-Scalar Mask Operations
    def SEQVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] == sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SNEVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] != sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SGTVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] > sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SLTVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] < sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SGEVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] >= sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SLEVS(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        masked_reg_value = self.core.getRegisterFile(vp.Core.VMR).Read()
        for i in range(vl):
            if (vx_value[i] <= sy_value) != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if self.prevMaskRegisterValues[i] != masked_reg_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Mask Operations

    def POP(self):
        ins, sy = (self.args[0], int(self.args[1][2:]))
        mask_reg = self.core.getRegisterFile(vp.Core.VMR).Read(0)
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)

        count = 0
        for i in mask_reg:
            count += i
        if sy_value != count:
            return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def CVM(self):
        mask_reg = self.core.getRegisterFile(vp.Core.VMR).Read()
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        for i in range(vl):
            if mask_reg[i] != 1:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Vector Length Register Operations
    def MTCL(self):
        ins, sy = (self.args[0], int(self.args[1][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        if vl != sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def MFCL(self):
        return self.MTCL()

    # endregion

    # region Load Store Operations

    def LV(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vmem_data = self.core.VDMEM.data[sy_value:sy_value + vl]
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        for i in range(vl):
            if vx_value[i] != vmem_data[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not mask_value[i] and vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SV(self):
        ins, vx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vmem_data = self.core.VDMEM.data[sy_value:sy_value + vl]
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        for i in range(vl):
            if vx_value[i] != vmem_data[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def LS(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sx_value != self.core.SDMEM.Read(sy_value + imm):
            return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SS(self):
        return self.LS()

    def LVWS(self):
        ins, vx, sy, sx = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        vx_value_final = [self.core.VDMEM.Read(sy_value + i * sx_value) for i in range(vl)]

        for i in range(vl):
            if vx_value[i] != vx_value_final[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not mask_value[i] and vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SVWS(self):
        ins, vx, sy, sx = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        vx_value_final = [self.core.VDMEM.Read(sy_value + i * sx_value) for i in range(vl)]

        for i in range(vl):
            if vx_value[i] != vx_value_final[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def LVI(self):
        ins, vx, sy, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value_final = [self.core.VDMEM.Read(sy_value + i) for i in vy_value[0:vl]]
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        for i in range(vl):
            if vx_value_final[i] != vx_value[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED
            elif not mask_value[i] and vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        for i in range(vl + 1, self.core.MVL):
            if vx_value[i] != self.prevVectorRegisterValue[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SVI(self):
        ins, vx, sy, vy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        vy_value = self.core.getRegisterFile(vp.Core.VRF).Read(vy)
        vx_value = self.core.getRegisterFile(vp.Core.VRF).Read(vx)
        vl = self.core.getRegisterFile(vp.Core.VLR).Read()
        vx_value_final = [self.core.VDMEM.Read(sy_value + i) for i in vy_value[0:vl]]
        mask_value = self.core.getRegisterFile(vp.Core.VMR).Read()

        for i in range(vl):
            if vx_value_final[i] != vx_value[i] and mask_value[i]:
                return InstructionSetVerification.VERIFICATION_FAILED

        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Scalar-Scalar Operations
    def ADD(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != sx_value + sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SUB(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != sx_value - sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SRA(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != self.arithmeticRightShift(sx_value, sy_value):
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SRL(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != self.logicalRightShift(sx_value, sy_value):
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def SLL(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != self.logicalLeftShift(sx_value, sy_value):
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def AND(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != sx_value & sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def OR(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != sx_value | sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def XOR(self):
        ins, sz, sx, sy = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3][2:]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        sz_value = self.core.getRegisterFile(vp.Core.SRF).Read(sz)
        if sz_value != sx_value ^ sy_value:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Branch Operations
    def BEQ(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sy_value == sx_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def BNE(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sy_value != sx_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def BGT(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sx_value > sy_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def BLT(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sx_value < sy_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def BGE(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sx_value >= sy_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    def BLE(self):
        ins, sx, sy, imm = (self.args[0], int(self.args[1][2:]), int(self.args[2][2:]), int(self.args[3]))
        sy_value = self.core.getRegisterFile(vp.Core.SRF).Read(sy)
        sx_value = self.core.getRegisterFile(vp.Core.SRF).Read(sx)
        if sx_value <= sy_value:
            if self.core.PC != self.current_PC + imm:
                return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    # region Termination operations
    def HALT(self):
        if self.executionResult != Instructions.SUCCESS_TERMINATION:
            return InstructionSetVerification.VERIFICATION_FAILED
        return InstructionSetVerification.VERIFICATION_SUCCESS

    # endregion

    def Default(self):
        return InstructionSetVerification.VERIFICATION_SUCCESS


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="IO_Instruction_Set_Verification", type=str,
                        help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()
    return os.path.abspath(args.iodir)


if __name__ == "__main__":
    iodir = parseArguments()
    verifier = InstructionSetVerification(iodir)
    if verifier.init() == InstructionSetVerification.VERIFICATION_FAILED:
        print("Error - Code.asm not found in the directory", iodir)
        exit()
    verifier.verify()

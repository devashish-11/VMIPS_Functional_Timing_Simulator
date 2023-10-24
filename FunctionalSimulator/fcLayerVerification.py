import random
import math
import argparse
import main as vp
import os


# Written by Aswin Raj K (ar7997) and Devashish (dg4015)
# This file verifies the working of the simulator


# Function to run the simulator
def runSimulator(iodir):
    # Parse IMEM
    imem = vp.IMEM(iodir)
    # Parse SMEM
    sdmem = vp.DMEM("SDMEM", iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = vp.DMEM("VDMEM", iodir, 18)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.

    # Create Vector Core
    vcore = vp.Core(imem, sdmem, vdmem)
    result = vcore.run()
    if result == vp.Core.FAILED:  # If core fails
        return vp.Core.FAILED

    # Dumping the final values
    vcore.dumpRegs(iodir)
    sdmem.dump()
    vdmem.dump()
    vcore.dumpResolvedData(iodir)
    return vcore


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="IO_FC_Layer_Verification", type=str,
                        help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()
    return os.path.abspath(args.iodir)


# Function to check if the iodir has Code.asm defined
def isCodeAvailable(iodir):
    codeFilePath = os.path.join(iodir, "Code.asm")
    return os.path.isfile(codeFilePath)


# Initializing VDMEM
# rand = 1, VDMEM is initialized with random values between 0 and 999
def initializeVDMEM(iodir):
    vdmem = [random.randint(0, 1000) for i in range(256)]
    vdmem.extend([random.randint(0, 1000) for i in range(256 * 256)])

    # Initializing the VDMEM.txt
    ipfilepath = os.path.abspath(os.path.join(iodir, "VDMEM.txt"))
    try:
        with open(ipfilepath, 'w') as file:
            for item in vdmem:
                file.write("%d\n" % item)
    except:
        print("VDMEM", "- ERROR: Couldn't open input file in path:", ipfilepath)
    return vdmem


# Function to find the dot pdt
def findDotPdt(vector, matrix):
    pdt = []

    for i in range(256):
        sum = 0
        for j in range(256):
            sum += vector[j] * matrix[i * 256 + j]
        pdt.append(sum)

    return pdt


if __name__ == "__main__":
    iodir = parseArguments()
    if not isCodeAvailable(iodir):  # Checking if Code.asm is present in iodir
        print("Error : Code.asm not found in path", iodir)
        exit()

    vdmem = initializeVDMEM(iodir)
    sum = findDotPdt(vdmem[0:256], vdmem[256:])  # Finding dot pdt for comparison

    print("=========RUNNING SIMULATOR========")
    result = runSimulator(iodir)  # Running simulator
    if result == vp.Core.FAILED:
        exit()

    result = []
    # Verifying the output
    with open(iodir + '\VDMEMOP.txt', 'r') as file:
        lines = file.readlines()
        for i in range(256):
            line = lines[65792+i]
            result.append(int(line.strip()))
    print("==================================")

    print("==============RESULT==============")
    for i in range(256):
        if sum[i] != result[i]:  # If dot pdt is same, verification is successfull
            print("Dot pdt failed!")
            print("==================================")
            exit()
    print("Dot pdt is verified and is equal to", result)
    print("==================================")

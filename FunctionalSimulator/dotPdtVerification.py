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
    vdmem = vp.DMEM("VDMEM", iodir, 17)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.

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
    parser.add_argument('--iodir', default="IO_Dot_Product_Verification", type=str,
                        help='Path to the folder containing the input files - instructions and data.')
    parser.add_argument('--vectorlength', default=450, type=int,
                        help='Vector length for dot pdt can be 1 to max(int)')
    parser.add_argument('--dotpdtaddr', default=2048, type=int,
                        help='Dot pdt address in the VDMEM')
    parser.add_argument('--random', default=0, type=int,
                        help='Whether to initialize VDMEM with random values')
    args = parser.parse_args()
    return (os.path.abspath(args.iodir), args.vectorlength, args.dotpdtaddr, args.random)


# Function to check if the iodir has Code.asm defined
def isCodeAvailable(iodir):
    codeFilePath = os.path.join(iodir, "Code.asm")
    return os.path.isfile(codeFilePath)


# Initializing VDMEM
# rand = 1, VDMEM is initialized with random values between 0 and 999
def initializeVDMEM(iodir, vector_len, rand=False):
    if rand:
        vdmem = [random.randint(0, 1000) for i in range(vector_len * 2)]
    else:
        vdmem = [i for i in range(vector_len)]
        vdmem.extend([i for i in range(vector_len)])

    # Initializing the VDMEM.txt
    ipfilepath = os.path.abspath(os.path.join(iodir, "VDMEM.txt"))
    try:
        with open(ipfilepath, 'w') as file:
            for item in vdmem:
                file.write("%d\n" % item)
    except:
        print("VDMEM", "- ERROR: Couldn't open input file in path:", ipfilepath)
    return vdmem


# Function to initializes the SDMEM values for a given vector_len The values of sdmem is as follows :
# [1, starting VLR value, Ceil(vector_len/(starting VLR value)), vector_len % (starting VLR value), starting address of
# vector 1 in VDMEM, starting address of vector 2 in VDMEM, address in VDMEM where the dot pdt need to be stored]
# In this case starting address of vector 2 is same as vector length and starting address of vector 1 is 0
def initializeSDMEM(iodir, vector_len):
    # Calculating starting value of VLR
    # eg: if vector_len >= 64 VLR = 64, if 32 <= vector_len < 64 VLG = 32 and so on..
    starting_vlr = 64
    while vector_len / starting_vlr < 1:
        starting_vlr = int(starting_vlr / 2)
    # Initializing the SDMEM.txt
    sdmem = [1, starting_vlr, math.ceil(vector_len / starting_vlr), vector_len % starting_vlr, 0, vector_len,
             dot_pdt_addr]

    ipfilepath = os.path.abspath(os.path.join(iodir, "SDMEM.txt"))
    try:
        with open(ipfilepath, 'w') as file:
            for item in sdmem:
                file.write("%d\n" % item)
    except:
        print("SDMEM", "- ERROR: Couldn't open input file in path:", ipfilepath)
    return sdmem


# Function to find the dot pdt
def findDotPdt(vector_len):
    sum = 0
    for i in range(vector_len):
        sum += vdmem[i] * vdmem[i + vector_len]
    return sum


if __name__ == "__main__":

    # Added three argument which are, iodir : input output directory vectorlength (optional, default = 450): vector
    # length for the dot pdt can be from 1 to max(int) dotpdtaddr (optional, default = 2048): address for the result
    # in the VDMEM random (optional, default = 0) : 1 => Initialize VDMEM with random values, 0 => Initialize VDMEM
    # as given in the problem statement To run this use the following commmand : python3 dotPdtVerification.py
    # --iodir IO_Dot_Product_Verification --vectorlength 450  --dotpdtaddr 2048 --random 0
    # uses IO_Dot_Product_Verification as the input-output directory, vector length used is 450, result will be stored at
    # address 2048 and uses vectors given in the problem statement
    iodir, vector_len, dot_pdt_addr, rand = parseArguments()
    if not isCodeAvailable(iodir):  # Checking if Code.asm is present in iodir
        print("Error : Code.asm not found in path", iodir)
        exit()

    vdmem = initializeVDMEM(iodir, vector_len, rand)
    sum = findDotPdt(vector_len)  # Finding dot pdt for comparison
    sdmem = initializeSDMEM(iodir, vector_len)

    print("=========RUNNING SIMULATOR========")
    result = runSimulator(iodir)  # Running simulator
    if result == vp.Core.FAILED:
        exit()

    # Verifying the output
    with open(iodir + '\VDMEMOP.txt', 'r') as file:
        line = file.readlines()[dot_pdt_addr]
        result = int(line.strip())
    print("==================================")

    print("==============RESULT==============")
    if sum == result:  # If dot pdt is same, verification is successfull
        print("Dot pdt is verified and is equal to", result)
    else:
        print("Dot pdt failed!")
    print("==================================")

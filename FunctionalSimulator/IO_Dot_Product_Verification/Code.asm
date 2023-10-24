# This is the assembly code for finding the dot pdt of two vectors using the functional simulator.
# The length of the vector can be of any value from 1 to max(int), with some initial values specified in SDMEM.txt
# SDMEM.txt should have these values in order, [1, starting VLR value, Ceil(vector_len/(starting VLR value)), vector_len % (starting VLR value), starting address of
# vector 1 in VDMEM, starting address of vector 2 in VDMEM, address in VDMEM where the dot pdt need to be stored]
# uses two loops one to multiply and add, and the other one to sum up the elements in a vector register

CVM # Making all bits in the mask as 1
# Loading the initial values
LS SR1 SR0 0 #Loading 1
LS SR2 SR0 1 #Loading maximum vector allowed in the architecture
LS SR3 SR0 2 #Loading int(length of the vector to perform dot pdt) / 2 + 1
LS SR4 SR0 3 #Loading length of the vector to perform dot pdt % maximum vector allowed in the architecture
LS SR5 SR0 4 #Loading the start address of vector 1
LS SR6 SR0 5 #Loading the start address of vector 2
LS SR7 SR0 6 #Loading the address to store the dot pdt

MTCL SR2 # Changing the length of the VLR to maximum vector allowed in the architecture

#Loading vector 1 and vector 2 into the vector registers
LV VR1 SR5
LV VR2 SR6

MULVV VR3 VR1 VR2 # Performing multiplication
ADDVV VR4 VR3 VR4# Performing addition
ADD SR5 SR5 SR2 # Incrementing the start address of vector 1
ADD SR6 SR6 SR2 # Incrementing the start address of vector 2
SUB SR3 SR3 SR1
BEQ SR4 SR0 3 # Checking if (length of the vector to perform dot pdt % maximum vector allowed in the architecture)
BNE SR3 SR1 2 # Checking for the last part of the vector set
MTCL SR4 #Changing value in VLR  to
#(length of the vector to perform dot pdt) % (maximum vector allowed in the architecture)

BNE SR3 SR0 -10 # Checking if the all the sets are multiplied and added

MTCL SR2 # Changing the VLR to maximum vector allowed in the architecture

# Code for performing the summation of each elements in the vector
SV VR4 SR7 # Loading the final vector in VR4 back to memory at address to store the dot pdt
BNE SR2 SR1 2 # Checking if vector length is one, then the dot pdt is finished
HALT
SRA SR2 SR2 SR1 # Dividing the current vector length by 2
MTCL SR2 # Changing the VLR to value in SR2
LV VR1 SR7 # Loading the first half of the vector back from the memory to the vector register
ADD SR5 SR7 SR2 # Calculating the address for the second half the vector
LV VR2 SR5 # Loading the second half
ADDVV VR4 VR1 VR2 # Adding both half's
SV VR4 SR7 # Storing back the sum
BNE SR2 SR1 -7 # Checking if the value in VLR is 1

HALT
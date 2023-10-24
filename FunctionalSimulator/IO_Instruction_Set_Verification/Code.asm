#This file contains all the instructions
#Add all the instructions in this file to check its working
CVM
LS SR1 SR0 0 #loads the first element from sdmem
LS SR2 SR0 1 #loads the second element from sdmem
LS SR4 SR0 3
LS SR5 SR0 4
LV VR1 SR1 #loads the sr1'th element from vdmem
LVWS VR2 SR1 SR2 #loads the sr1'th element with stride sr2
SVWS VR2 SR1 SR2
LVI VR3 SR1 VR1  #loads the sr1'th element with corresponding offset vr1
ADD SR3 SR1 SR2
ADDVV VR4 VR1 VR2
SS SR3 SR0 2
SV VR4 SR1
SVI VR4 SR5 VR1

#Checking Arithmetic instructions
CVM
LS SR1 SR0 0 #loads the first element from sdmem
LS SR2 SR0 1 #loads the second element from sdmem
LV VR1 SR1 #loads the sr1'th element from vdmem
LV VR2 SR2
ADDVV VR3 VR1 VR2
ADDVS VR4 VR1 SR2
SUBVV VR5 VR1 VR2
SUBVS VR6 VR1 SR2
MULVV VR4 VR3 VR2
MULVS VR5 VR3 SR2
DIVVV VR5 VR3 VR2
DIVVS VR6 VR4 SR2

#Scalar operations
AND SR3 SR1 SR2
OR SR3 SR1 SR2
XOR SR3 SR1 SR2
ADD SR3 SR1 SR2
SUB SR3 SR1 SR2
SLL SR3 SR1 SR2
SRL SR3 SR1 SR2
SRA SR3 SR1 SR2

#VLR Operations
MTCL SR2
MFCL SR3

#VMR Operations
SEQVV VR1 VR2
SNEVV VR1 VR2
SGTVV VR1 VR2
SLTVV VR1 VR2
SGEVV VR1 VR2
SLEVV VR1 VR2
SEQVS VR1 SR1
SNEVS VR1 SR1
SGTVS VR1 SR1
SLTVS VR1 SR1
SGEVS VR1 SR1
SLEVS VR1 SR1
POP SR1
HALT
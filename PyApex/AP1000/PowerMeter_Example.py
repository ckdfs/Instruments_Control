# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 11:47:18 2021

Calibration du polarimètre en utilisant un polarimètre AP1000

@author: Administrator
"""

import time
# import os
# import datetime
# import threading
# import numpy as np
# import matplotlib.pyplot as plt



import PyApex
import PyApex.AP1000 as AP1000

# ----------------------------------------------------------------------------
#       Be sure your polarimeter software is opening
# ----------------------------------------------------------------------------
Connection_procedure = True

# ----------------------------------------------------------------------------
#                      Opens Polarimeter connection
# ----------------------------------------------------------------------------

AP1000 = AP1000("192.168.1.110")
ID = AP1000.GetID() 
print(ID)    
#Find how many slot in the AP1000
numslot = ID[25]

for i in range(int(numslot)):
    slotID = AP1000.SlotID(i)
    print(slotID)
    res = slotID.find("3314-B")
    if (res !=-1):
        slotNum = i
        print(slotNum)
         
PowerMeter = AP1000.PowerMeterB(slotNum)
print("Connexion PowerMeter AP1000 done") 

aaa      
#%%%#
#===========================================================================
#                       PowerMeter function
# =============================================================================
#Get Unit
unit = PowerMeter.GetUnit()
print(unit)
#Set Unit
PowerMeter.SetUnit("mW")# "dBm"
#Get Wavelength of the channel ChNumber of the PWM equipment 
# channel number by default = 1 (2 channels : 1 or 2)
wlch1 = PowerMeter.GetWavelength(1)
print(wlch1)
wlch2 = PowerMeter.GetWavelength(2)
print(wlch2)
powch1 = PowerMeter.GetPower(1)
print(powch1)
powch2 = PowerMeter.GetPower(2)
print(powch2)

#Set WL [980,1310,1480,1550,1610]
PowerMeter.SetWavelength(1550.0,1)
PowerMeter.SetWavelength(1550.0,2)
   


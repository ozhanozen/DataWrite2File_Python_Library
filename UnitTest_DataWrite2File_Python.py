import numpy as np
import time
import DataWrite2File_Python



myFile = DataWrite2File_Python.DataWrite2File_Python(1000, "UnitTest", "Ozhan", 3, ("Time","xPos","yPos") )
#myFile.Set_Period(0.25)
myFile.Set_Debug(True)
#myFile.Set_Append(False)
#myFile.Set_TimeCheck(True)
#myFile.Set_SafeSave(True)
#myFile.Set_Header_On(True)
myFile.Set_Folder("./TestFolder/")

time0 = time.time()
timeNow = time.time() - time0

myFile.Start_Writing()
while (timeNow < 4):
    myFile.RECENT_VALUES[0] = timeNow
    myFile.RECENT_VALUES[1] = 20 * np.sin(2 * np.pi * 0.2 * timeNow)
    myFile.RECENT_VALUES[2] = 30 * np.sin(2 * np.pi * 0.2 * timeNow)
    timeNow = time.time() - time0
    time.sleep(0.000005)
myFile.Close_W2File()



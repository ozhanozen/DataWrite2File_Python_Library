import numpy as np
import time
import DataWrite2File_Python


myFile = DataWrite2File_Python.DataWrite2File_Python(100, "UnitTest", "Ozhan", 30, ("Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos","Time","xPos","yPos") )
myFile.Set_Period(2)
myFile.Set_Debug(True)
myFile.Set_SafeSave(False)
myFile.Set_Header_On(False)
myFile.Set_Folder("./TestFolder/")

time0 = time.time()
timeNow = time.time() - time0

myFile.Start_Writing()
while (timeNow < 4):
    timeNow = time.time() - time0
    print(timeNow)
    for i in range(0,10):
        myFile.RECENT_VALUES[0+i*3] = timeNow
        myFile.RECENT_VALUES[1+i*3] = 20 * np.sin(2 * np.pi * 0.2 * timeNow)
        myFile.RECENT_VALUES[2+i*3] = 30 * np.sin(2 * np.pi * 0.2 * timeNow)
    time.sleep(0.000005)
myFile.Close_W2File()



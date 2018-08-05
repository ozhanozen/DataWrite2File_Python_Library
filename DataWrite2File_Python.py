# Data Logger for Python written by Ozhan Ozen. Last update was done 19.07.2018.
import threading
import numpy as np
import time
import datetime
import os

# Class to be called from the code. Create two additional threads: responsible for buffers of the same size. While
# one buffer is recording data, the other one write its data to a file. When it stops recording data (when it is fully),
# it releases the other one (which already finished writing) so that it can start recording data immediately, and starts
# writing its full buffer to a file. This python class is not hard real time since you cannot set priorities in python and
# it runs slow as hell. So if you do not want to miss any data from a source, use another logger in the source system as well.
#
# OOOOOOOOOOOOOOOOOOOO
#
# The inputs are the size for the buffers (min 50), the file name, author name, # of variables and the vector tuple
# which contains the names of the variables. Once you initialize (and change the settings if necessary), you should call
# Start_Writing function to start writing. When you are done, use Close W2File. IF YOU FIRST VARIABLE IS NOT YOU TIME,
# DISABLE THE TimeCheck PROPERTY.
#
# OOOOOOOOOOOOOOOOOOOO
#
# By default, the header is on, time-checker is on, safe_save is off, debug is off, period is 1ms and append mode is off.
# You can change these value if you desire using public functions (but do it before Start_Writing).


class DataWrite2File_Python:
    def __init__(self, BufferSize, FileName, AuthorName, nVar, VarNames):

        # Sets buffer size.
        if BufferSize < 50:
            print("Buffer size cannot be smaller than 50, therefore is set to 50")
            self.__BUFFER_SIZE = 50
        else:
            self.__BUFFER_SIZE = BufferSize
        # Name, # of variables, default mode.
        self.__FILE_NAME = FileName + datetime.datetime.now().strftime("_%d%m%y_%H%M.csv")
        self.__FOLDER_PATH = "./DataLogger/"
        self.__FILE_PATH = ""
        self.__nVAR = nVar
        self.__MODE = "w+"
        # Vectors for recent values and buffers.
        self.RECENT_VALUES = np.ndarray(shape=(nVar,1), dtype=float)
        self.__BUFFER_1 = np.ndarray(shape=(nVar,self.__BUFFER_SIZE), dtype=float)
        self.__BUFFER_2 = np.ndarray(shape=(nVar,self.__BUFFER_SIZE), dtype=float)
        # Buffer pointer.
        self.__BUFFER_COUNTER = 0
        # Close Flag.
        self.__WRITING_FLAG = True
        # Default period.
        self.__PERIOD = 1 / 1000
        # This is for making data writing having lower priority. You should not make 1000 lower.
        self.__WRITE_RELAXER = 1000
        # Names
        self.__VAR_NAMES = VarNames
        self.__AUTHOR_NAME = AuthorName
        # Some default settings.
        self.__TIME_CHECK = True
        self.__HEADER_ON = True
        self.__SAFE_SAVE = False
        self.__DEBUG = False
        # Mutex for buffer threads.
        self.__LOCK = threading.Lock()
        self.__LOCK.acquire()

        # Run the "run" code
        self.run()

    def run(self):
        # Open the threads.
        self.__W2F_OBJECT_1 = threading.Thread(target=self.__Write_1)
        self.__W2F_OBJECT_2 = threading.Thread(target=self.__Write_2)



    # Private functions.

    # Thread 1
    def __Write_1(self):
        RECORDING = False
        while self.__WRITING_FLAG:
            RECORDING = True
            TIME_START = time.time()

            # The value before pointer, for comparision to check if the data is changed or not.
            if (self.__BUFFER_COUNTER == 0):
                index = self.__BUFFER_SIZE - 1
            else:
                index = self.__BUFFER_COUNTER - 1

            # If the data is changed (or you set this feature off)
            if ( not(self.RECENT_VALUES[0] == self.__BUFFER_1[0,index]) or self.__TIME_CHECK == False ):

                # Update buffer
                for i in range(0, self.__nVAR):
                    self.__BUFFER_1[i, self.__BUFFER_COUNTER] = self.RECENT_VALUES[i]
                self.__BUFFER_COUNTER = self.__BUFFER_COUNTER + 1

                # If buffer is full, release the other thread first, then start writing, then lock yourself.
                if (self.__BUFFER_COUNTER >= self.__BUFFER_SIZE):
                    self.__BUFFER_COUNTER = 0
                    RECORDING = False
                    self.__LOCK.release()
                    self.__WriteLine(1, self.__BUFFER_SIZE)
                    self.__LOCK.acquire()

            # If you finished before (since you did not update?) then wait for a while, dont overload processor.
            TIME_END = time.time()
            if ((TIME_END - TIME_START) < self.__PERIOD):
                time.sleep(self.__PERIOD - (TIME_END - TIME_START))
            else:
                if ( (self.__DEBUG == True and not (self.__BUFFER_COUNTER == 0) ) and (self.__WRITING_FLAG) ):
                    print("Writing period is violated.")
        # Write also the not-full buffer when you are done.
        if ( not(self.__BUFFER_COUNTER ==0) and (RECORDING==True) ):
            self.__WriteLine(1, self.__BUFFER_COUNTER)
        if (self.__DEBUG == True):
            print("The W2File thread 1 was closed.")

    # Thread 2. Almost the same, so no comments again.
    def __Write_2(self):
        # Start locked. The other thread starts first.
        self.__LOCK.acquire()
        RECORDING = False
        while self.__WRITING_FLAG:
            RECORDING = True
            TIME_START = time.time()

            if (self.__BUFFER_COUNTER == 0):
                index = self.__BUFFER_SIZE - 1
            else:
                index = self.__BUFFER_COUNTER - 1

            if (not (self.RECENT_VALUES[0] == self.__BUFFER_2[0, index]) or self.__TIME_CHECK == False):

                for i in range(0, self.__nVAR):
                    self.__BUFFER_2[i, self.__BUFFER_COUNTER] = self.RECENT_VALUES[i]
                self.__BUFFER_COUNTER = self.__BUFFER_COUNTER + 1

                if (self.__BUFFER_COUNTER >= self.__BUFFER_SIZE):
                    self.__BUFFER_COUNTER = 0
                    RECORDING = False
                    self.__LOCK.release()
                    self.__WriteLine(2, self.__BUFFER_SIZE)
                    self.__LOCK.acquire()

            TIME_END = time.time()
            if ((TIME_END - TIME_START) < self.__PERIOD):
                time.sleep(self.__PERIOD - (TIME_END - TIME_START))
            else:
                if ( (self.__DEBUG == True and not (self.__BUFFER_COUNTER == 0)) and (self.__WRITING_FLAG) ):
                    print("Writing period is violated.")
        if ( not(self.__BUFFER_COUNTER ==0) and (RECORDING==True) ):
            self.__WriteLine(2, self.__BUFFER_COUNTER)
        if (self.__DEBUG == True):
            print("The W2File thread 2 was closed.")

    # Writes the header in the beginning if the setting is on.
    def __Write_Header(self,):
        if (self.__HEADER_ON == True):
            self.__FILE_OBJECT.write("Experimental data file created by " + self.__AUTHOR_NAME + " at "+ datetime.datetime.now().strftime("%H:%M") + " on "+ datetime.datetime.now().strftime("%d.%m.%Y.") + "\n \n" )

    # Writes variable names.
    def __WriteNames(self,):
        for i in range(0, self.__nVAR):
            if (i < self.__nVAR - 1):
                self.__FILE_OBJECT.write(self.__VAR_NAMES[i] + " , ")
            else:
                self.__FILE_OBJECT.write(self.__VAR_NAMES[i] + "\n")

    # Function that writes the variables in rows.
    def __WriteLine(self, Thread_Number, WriteSize):
        # If SafeSafe is on, you open and close the function before/after writing.
        if (self.__SAFE_SAVE == True):
            self.__FILE_OBJECT = open(self.__FILE_PATH, "a+")

        if (Thread_Number == 1):
            for i in range(0, WriteSize):
                for k in range(0, self.__nVAR):
                    if (k < self.__nVAR - 1):
                        self.__FILE_OBJECT.write(str(self.__BUFFER_1[k, i]) + " , ")
                    else:
                        self.__FILE_OBJECT.write(str(self.__BUFFER_1[k, i]) + "\n")
                    time.sleep(self.__PERIOD / self.__BUFFER_SIZE / self.__WRITE_RELAXER)
        elif(Thread_Number == 2):
            for i in range(0, WriteSize):
                for k in range(0, self.__nVAR):
                    if (k < self.__nVAR - 1):
                        self.__FILE_OBJECT.write(str(self.__BUFFER_2[k, i]) + " , ")
                    else:
                        self.__FILE_OBJECT.write(str(self.__BUFFER_2[k, i]) + "\n")
                    time.sleep(self.__PERIOD / self.__BUFFER_SIZE / self.__WRITE_RELAXER)
        else:
            print("Error in Thread_Number")
        # If SafeSafe is on, you open and close the function before/after writing.
        if (self.__SAFE_SAVE == True):
            self.__FILE_OBJECT.close()



    # Public functions.

    # Sets the setting which allows you to continue a file (same name) or overwrite the file.
    def Set_Append(self, True_False):
        if (True_False == True):
            self.__MODE = "a+"
        elif (True_False == False):
            self.__MODE = "w+"
        else:
            print("Wrong boolean input for Set_Append")

    # Sets the period. Cannot be lower than 0.25. No guarantee though.
    def Set_Period(self, Period):
        if Period < 0.25:
            print("Period size cannot be smaller than 0.25 ms, therefore is set to 0.25 ms")
            self.__PERIOD = 0.25 / 1000
        else:
            self.__PERIOD = Period / 1000

    # Do you wanna see period violations? Turn this on.
    def Set_Debug(self, Debug):
        if (Debug == True):
            self.__DEBUG = True
        elif (Debug == False):
            self.__DEBUG = False
        else:
            print("Wrong boolean input for Set_Debug")

    # Open/Close the file each time data is written.
    def Set_SafeSave(self, True_False):
        if (True_False == True):
            self.__SAFE_SAVE = True
        elif (True_False == False):
            self.__SAFE_SAVE = False
        else:
            print("Wrong boolean input for Set_SafeSave")

    # If you first variable is time, this is useful. If not, disable this feature.
    def Set_TimeCheck(self, True_False):
        if (True_False == True):
            self.__TIME_CHECK = True
        elif (True_False == False):
            self.__TIME_CHECK = False
        else:
            print("Wrong boolean input for Set_TimeCheck")

    # Disable if you dont want header.
    def Set_Header_On(self, True_False):
        if (True_False == True):
            self.__HEADER_ON = True
        elif (True_False == False):
            self.__HEADER_ON = False
        else:
            print("Wrong boolean input for Set_Header_On")

    # Sets custom folder to put the data.
    def Set_Folder(self, Path):
        if (Path.endswith('/')):
            self.__FOLDER_PATH = Path
        else:
            self.__FOLDER_PATH = Path + "/"

    # Close the file when you are done.
    def Close_W2File(self):
        self.__WRITING_FLAG = False
        self.__LOCK.release()
        self.__W2F_OBJECT_1.join()
        self.__W2F_OBJECT_2.join()
        if (self.__SAFE_SAVE == False):
            self.__FILE_OBJECT.close()

    # Start writing the file.
    def Start_Writing(self,):
        self.__FILE_PATH = self.__FOLDER_PATH + self.__FILE_NAME
        if not os.path.exists(self.__FOLDER_PATH):
            os.makedirs(self.__FOLDER_PATH)
        self.__FILE_OBJECT = open(self.__FILE_PATH, self.__MODE)
        self.__Write_Header()
        self.__WriteNames()
        self.__W2F_OBJECT_1.start()
        self.__W2F_OBJECT_2.start()
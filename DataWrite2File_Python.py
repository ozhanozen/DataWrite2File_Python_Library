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
        self.RECENT_VALUES = np.zeros(shape=(nVar,1), dtype=float)
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
        self.__RECORD_LOCK = threading.Lock()
        self.__WRITE_LOCK = threading.Lock()

        # Run the "run" code
        self.run()

    def run(self):
        # Open the threads.
        self.__W2F_OBJECT_1 = threading.Thread(target=self.__LOGGER_LOOP,args = (1,))
        self.__W2F_OBJECT_2 = threading.Thread(target=self.__LOGGER_LOOP,args = (2,))



    # Private functions.

    # Main function for the threads
    def __LOGGER_LOOP(self, threadN):

        BUFFER = np.ndarray(shape=(self.__nVAR,self.__BUFFER_SIZE), dtype=float)

        # Main loop
        while self.__WRITING_FLAG:

            LAST_RECORDED_BUFFER_INDEX = self.__RECORD(BUFFER,threadN)
            self.__WRITE(BUFFER,LAST_RECORDED_BUFFER_INDEX,threadN) # Write up to LAST_RECORDED_BUFFER_INDEX

        if (self.__DEBUG == True):
            print("The thread "+ str(threadN) + " is closed.", flush=True)

    # Data recording to buffer
    def __RECORD(self, BUFFER, threadN):

        # Acquire the lock, wait here if lock is already acquired.
        self.__RECORD_LOCK.acquire()

        LAST_RECORDED_BUFFER_INDEX = self.__RecordLoop(threadN, BUFFER)

        # Release the lock when done
        if self.__RECORD_LOCK.locked():
            self.__RECORD_LOCK.release()

        return LAST_RECORDED_BUFFER_INDEX

    # Writing buffer to CSV
    def __WRITE(self, BUFFER, LAST_RECORDED_BUFFER_INDEX, threadN):

        if LAST_RECORDED_BUFFER_INDEX > -1: # If data recording is performed for at least one step
            
            # Acquire the lock, wait here if lock is already acquired.
            self.__WRITE_LOCK.acquire()

            self.__WriteLoop(threadN, LAST_RECORDED_BUFFER_INDEX + 1, BUFFER) # No need to interrupt the loop, so it is inside the function

            # Release the lock when done
            if self.__WRITE_LOCK.locked():
                self.__WRITE_LOCK.release()

    # Function that loops over the buffer for recording
    def __RecordLoop(self, threadN, BUFFER):

        self.__BUFFER_COUNTER = 0
        LAST_RECORDED_BUFFER_INDEX = -1

        # Record to buffer until the class is closed or buffer is full
        while self.__WRITING_FLAG: 

            TIME_START = time.time()
            pIndex = self.__returnPindex() # Index before the BUFFER_COUNTER (circular)

            # If the data is changed (or you set this feature off)
            if ( not(self.RECENT_VALUES[0] == BUFFER[0,pIndex]) or self.__TIME_CHECK == False ):
                self.__updateBuffer(BUFFER)
                LAST_RECORDED_BUFFER_INDEX = self.__BUFFER_COUNTER - 1

            # Exit if buffer is full
            if (self.__BUFFER_COUNTER >= self.__BUFFER_SIZE):
                break
            
            # Wait for the loop to finish
            self.__wait4periodEnd(threadN,TIME_START)

        return LAST_RECORDED_BUFFER_INDEX

    # The value before pointer, for comparision to check if the data is changed or not.
    def __returnPindex(self):
        
        if (self.__BUFFER_COUNTER == 0):
            pIndex = self.__BUFFER_SIZE - 1
        else:
            pIndex = self.__BUFFER_COUNTER - 1

        return pIndex

    # Recording: Updating the buffer
    def __updateBuffer(self,BUFFER):

        for i in range(0, self.__nVAR):
            BUFFER[i, self.__BUFFER_COUNTER] = self.RECENT_VALUES[i]

        self.__BUFFER_COUNTER = self.__BUFFER_COUNTER + 1

    # If you finished before (since you did not update?) then wait for a while, dont overload processor.
    def __wait4periodEnd(self,threadN,TIME_START):

        TIME_END = time.time()

        if ((TIME_END - TIME_START) < self.__PERIOD):
            time.sleep(self.__PERIOD - (TIME_END - TIME_START))
        else:
            if ( (self.__DEBUG == True and not (self.__BUFFER_COUNTER == 0) ) and (self.__WRITING_FLAG) ):
                print("Writing period is violated (thread "+str(threadN)+"): " + str((TIME_END - TIME_START)) + "s", flush=True)

    # Function that writes the variables to a csv file in rows.
    def __WriteLoop(self, threadN, WriteSize, BUFFER):

        # If SafeSafe is on, you open and close the function before/after writing.
        if (self.__SAFE_SAVE == True):
            self.__FILE_OBJECT = open(self.__FILE_PATH, "a+")

        for i in range(0, WriteSize):
            for k in range(0, self.__nVAR):
                if (k < self.__nVAR - 1):
                    self.__FILE_OBJECT.write(str(BUFFER[k, i]) + " , ")
                else:
                    if (self.__DEBUG == True):
                        self.__FILE_OBJECT.write(str(BUFFER[k, i]) + " , " + str(threadN)+ " , "+ str(self.__WRITING_FLAG) + " , " + str(i) + " \n")
                    else:
                        self.__FILE_OBJECT.write(str(BUFFER[k, i]) + " \n")
                time.sleep(self.__PERIOD / self.__BUFFER_SIZE / self.__WRITE_RELAXER)
       
        # If SafeSafe is on, you open and close the function before/after writing.
        if (self.__SAFE_SAVE == True and self.__WRITING_FLAG == True):
            self.__FILE_OBJECT.close()

    # Writes the header in the beginning if the setting is on.
    def __Write_Header(self,):

        if (self.__HEADER_ON == True):
            self.__FILE_OBJECT.write("Data file created by " + self.__AUTHOR_NAME + " at "+ datetime.datetime.now().strftime("%H:%M") + " on "+ datetime.datetime.now().strftime("%d.%m.%Y.") + "\n \n" )

    # Writes variable names.
    def __WriteNames(self,):

        for i in range(0, self.__nVAR):
            if (i < self.__nVAR - 1):
                self.__FILE_OBJECT.write(self.__VAR_NAMES[i] + " , ")
            else:
                if (self.__DEBUG == True):
                    self.__FILE_OBJECT.write(self.__VAR_NAMES[i] + " , ThreadN , WritingFlag , BufferIndex\n")
                else:
                    self.__FILE_OBJECT.write(self.__VAR_NAMES[i] + "\n")

    

    # Public functions.

    # Sets the setting which allows you to continue a file (same name) or overwrite the file.
    def Set_Append(self, True_False):

        if (True_False == True):
            self.__MODE = "a+"
        elif (True_False == False):
            self.__MODE = "w+"
        else:
            print("Wrong boolean input for Set_Append")

    # Sets the period in ms. Cannot be lower than 0.25 ms. No guarantee though.
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

        print("Closing the logger.", flush=True)
        self.__WRITING_FLAG = False
        self.__W2F_OBJECT_1.join()
        self.__W2F_OBJECT_2.join()
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
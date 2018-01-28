#!/usr/bin/env python3

# Dependancies include: matplotlib, pyserial, pynmea2

import matplotlib
matplotlib.use('TkAgg')

import pylab, csv, serial, time, threading, pynmea2, os, math
import serial.tools.list_ports
#import matplotlib.animation as animation       # Not used yet, but soon.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

#from pylab import *
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfile, askdirectory
from datetime import datetime, date

Cone_File    = ""                       # Default cone file, for testing
Output_File  = ""
Record_Lap   = False
Lap_Names    = []                       # Create lap names list
counter      = 0                        # Important for Serial, dunno why
Stop_GPS     = True
Directory    = os.getcwd()              # Gets current directory for default dir name
GPS_Time_Ref = 0                        # Sets GPS reference time for TPS logging
Ard_Loc      = ""
GPS_Loc      = "" 

fig_size     = [.1,.1]                  # Graph Drawing Stuff
TheGraphFigure = Figure(figsize=fig_size, dpi=100, linewidth=0 )
TheGraphFigure.set_facecolor('#6a6e09')
plot = TheGraphFigure.add_axes([0,0,1,1])   # Makes graph match frame size



class Application(Frame):           # Main window Tkinter setup
    def __init__(self, master=None):
        global  GPS_Display_Lon, GPS_Display_Lat, GPS_Display_Speed, GPS_Display_Speed_Raw, GPS_Display_Status, Arduino_Status
        global TPS_Live, GPS_Label_Speedo
        Frame.__init__(self, master)
        self.grid()
        self.master.title("Cory's Gps Logger")

        style = ttk.Style()         # We like TTK because themes make it look better-er
        #print(style.theme_names())
        if sys.platform.startswith('win'): 
            style.theme_use('vista')# If we're on Sindows, Vista looks way better.
            File_Slashes = "\\"
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            style.theme_use('clam') # Vista doesn't work on Linux, so use clam
            File_Slashes = "/"
        elif sys.platform.startswith('darwin'):
            style.theme_use('clam') 

        style.configure('startg.TButton', background='green'  )     # Start Green 
        style.configure('starty.TButton', background='orange' )     # Start Yellow
        style.configure('startr.TButton', background='red'    )     # Start Red

                                    #Configure rows/columns recursively
        for x in range(0,24):
            self.master.rowconfigure(x, weight=1)

        for y in range(0,2):
            self.master.columnconfigure(y, weight=0)

        for y in range(3,6):
            self.master.columnconfigure(y, weight=2)

        nb = ttk.Notebook(master)   # Define nb as notebook doober
        nb.grid(row = 0, column = 3, rowspan = 24, columnspan = 3, sticky = W+E+N+S)        
        
        self.NBook1 = ttk.Frame(nb) # Define some tabs
        self.NBook1b = ttk.Frame(self.NBook1) # Create frame inside tab for graph clearing
        self.NBook3 = ttk.Frame(nb)
        self.NBook4 = ttk.Frame(nb)
        self.NBook5 = ttk.Frame(nb)
        
        nb.add(self.NBook1, text = " Map "          )
        nb.add(self.NBook3, text = " Raw Data ",     state = "disabled")
        nb.add(self.NBook4, text = " Setup ",        state = "disabled")
        nb.add(self.NBook5, text = " GPS Speedo "   )
        
        
                                    # Create some frames, give them labels
        self.Frame1 = ttk.LabelFrame(master, text=" Live Info ", )
        self.Frame2 = ttk.LabelFrame(master, text=" Laps ", )
                                    # Define some Frames
        self.Frame1.grid(row = 0, column = 0, rowspan = 2,  columnspan = 3, sticky = W+E+N+S)
        self.Frame2.grid(row = 2, column = 0, rowspan = 21, columnspan = 3, sticky = W+E+N+S)
        self.Frame3 = Canvas()      # for menu buttons
        self.Frame3.grid(row = 24, column = 2, rowspan = 1, columnspan = 5, sticky = E+N+S)
        self.Frame4 = Canvas()      # for start button
        self.Frame4.grid(row = 23, column = 0, rowspan = 2, columnspan = 2, sticky = W+E+N+S)
                                    # Create some buttons, define what they do
        self.b1 = ttk.Button(self.Frame4,  text="NO GPS",   command=Btn_Start , style='startr.TButton')
        self.b4 = ttk.Button(self.Frame3,  text="Load Course", command=btnLoadCourse)
        self.b5 = ttk.Button(self.Frame3,  text="Load Run Folder",   command=btnLoadRuns)
        self.b6 = ttk.Button(self.Frame3,  text="Exit",        command=btnExit)
        
        self.b1.grid(ipadx=30, ipady=20)    # Makes start button bigger than the rest
        self.b6.pack(side=RIGHT,  expand=TRUE, fill=BOTH)
        self.b5.pack(side=RIGHT,  expand=TRUE, fill=X)
        self.b4.pack(side=RIGHT,  expand=TRUE, fill=X)
                                    # GPS display in upper left, and creates global vars for threads
        GPS_Display_Lat         = StringVar()
        GPS_Display_Lon         = StringVar()
        GPS_Display_Speed       = StringVar()
        GPS_Display_Speed_Raw   = StringVar()
        GPS_Display_Status      = StringVar()
        Arduino_Status          = StringVar()
        TPS_Live                = DoubleVar()

        GPS_Label_Lat           = Label(self.Frame1, textvariable=GPS_Display_Lon,    state=ACTIVE, justify=LEFT, anchor=W)
        GPS_Label_Lon           = Label(self.Frame1, textvariable=GPS_Display_Lat,    state=ACTIVE, justify=LEFT, anchor=W)
        GPS_Label_Speed         = Label(self.Frame1, textvariable=GPS_Display_Speed,  state=ACTIVE, justify=LEFT, anchor=W)
        GPS_Label_Status        = Label(self.Frame1, textvariable=GPS_Display_Status, state=ACTIVE, justify=LEFT, anchor=W)
        Ard_Label_Status        = Label(self.Frame1, textvariable=Arduino_Status,     state=ACTIVE, justify=LEFT, anchor=W)

        
        tps_pb = ttk.Progressbar(master, orient=HORIZONTAL, mode='determinate', variable=TPS_Live)

        GPS_Label_Status.pack( in_=self.Frame1, expand=TRUE, fill=X )
        GPS_Label_Lat.pack(    in_=self.Frame1, expand=TRUE, fill=X )
        GPS_Label_Lon.pack(    in_=self.Frame1, expand=TRUE, fill=X )
        GPS_Label_Speed.pack(  in_=self.Frame1, expand=TRUE, fill=X )
        Ard_Label_Status.pack( in_=self.Frame1, expand=TRUE, fill=X )
        tps_pb.pack(           in_=self.Frame1, expand=TRUE, fill=X ) 

                                    # Listbox for Lap Times
        self.listbox = Listbox(self.Frame2, selectmode=MULTIPLE)
        self.listbox.pack(expand=TRUE, fill=BOTH)

                                    # Default labels for GPS_Label
        GPS_Display_Status.set('Status: No Connection')
        GPS_Display_Lat.set('Lat: ' )                             
        GPS_Display_Lon.set('Long: ' )
        GPS_Display_Speed.set('Spd: ')
        Arduino_Status.set('Arduino:  No Arduino')
        TPS_Live.set(1)
        
        
                                    # Default label for tab: GPS SPEEDO
        GPS_Display_Speed_Raw.set('No Connection')
        GPS_Label_Speedo = Label(self.NBook5, textvariable=GPS_Display_Speed_Raw, state=ACTIVE, justify=CENTER )
        GPS_Label_Speedo.configure(font=('Arial', 30, 'bold'), fg="blue", bg="red")
        GPS_Label_Speedo.pack(in_ =self.NBook5, expand=TRUE, fill=BOTH, )
        self.NBook5.update()

#### End of INIT ####





#### Start of Buttons ####
        
def Btn_Start():
    global Record_Lap, Record_Thread, GPS_Found, Lap_Names, Output_File, TPS_Log_File
    
    if sys.platform.startswith('win'): 
        File_Slashes = "\\"
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        File_Slashes = "/"
        
    if GPS_Found == True:
        Filename = Check_File_Path("RunLog", ".csv", 1)   # Check the file path, returns next avail filename
        tpslog = Check_File_Path("TPSLog", ".csv", 1)
        Lap_Names.append(Filename)                      # Adds the files to the Lap_Names list
        #print("Laps this session: " + str(Lap_Names))
        Output_File = open(os.fsdecode(Directory) + File_Slashes + Filename, 'w')               # Opens the file for writing
        TPS_Log_File = open(os.fsdecode(Directory) + File_Slashes + tpslog, 'w')
        Record_Lap = True                               # When Record_Lap goes true, the gps daemon starts recording
    else:
        top = Toplevel()                                # Creates popup
        top.title("Not Recording")
        top.attributes('-topmost', 1)                   # Make sure it's on top
        top.grab_set()                                  # Force focus, must close to return to program
        msg = Message(top, text="Not currently recording a lap\n\n GPS Data error", padx=20, pady=20, width=200 )
        msg.pack()
        button = ttk.Button(top, text = "\nDismiss\n", command = top.destroy, style='startr.TButton')
        button.pack(expand=TRUE, fill=BOTH)
        

def Btn_Stop():
    global Record_Lap, Record_Thread, Lap_Names, Output_File, TPS_Log_File

    Record_Lap = False                                                          # Stop Recording
    Output_File.flush()
    Output_File.close()                                                         # Close output file
    TPS_Log_File.flush()
    TPS_Log_File.close()
    app.listbox.delete(0,END)                                                   # Empties the listbox
    app.listbox.insert(1, *Lap_Names)                                           # Fills the updated listbox
    app.listbox.bind('<<ListboxSelect>>', onselect)                             # Enables clicking the listbox
    app.b1.configure(text="   START    ", style='startg.TButton', command=Btn_Start)    # Put the start button back to normal
    

def btnLoadCourse(*ReDraw):
    global Cone_File
    if bool(ReDraw) == True:            # if the course is already loaded, we're loading a run instead
        Graph_It(Cone_File, 1)          #   or we're loading multple runs because user selected more than one
        return                          #   Mostly this avoids askopenfilename() because we write runs on top of the *old* Cone_File graph
    plot.clear()
    Cone_File = askopenfilename()       # Opens the "Open File" dialog, puts result into Cone_File
    Graph_It(Cone_File, 1)
    

def btnLoadRuns():
    global Directory, Cone_File
    
    runfolder = askdirectory()          # ask the user which directory
    Directory = os.fsencode(runfolder)  # encode it with whatever the os uses
    for file in os.listdir(Directory):  # for each file:
        Filename = os.fsdecode(file)    # decode the system path addres
        if Filename.endswith(".csv"):   # If it's a CSV 
            Lap_Names.append(Filename)  # add it to the Lap_Names list
    app.listbox.insert(1, *Lap_Names)   # Fills the updated listbox
    app.listbox.bind('<<ListboxSelect>>', onselect) # Bind the list, so that when you click it, it launches onselect()
    

def btnExit():
    global Record_Lap, Stop_GPS, Record_Thread, GPS_Thread, Arduino_Thread
    
    Stop_GPS = False                    # stop the GPS parsing
    Record_Lap = False                  # if we're recording a lap, stop that too
        
    try:                                # See if GPS_Thread exists
        GPS_Thread
    except NameError:                   # If it doesn't exist, exit program
        #print("No GPS Thread")
        root.destroy()
        raise SystemExit
    
    if GPS_Thread.isAlive():            # If it does exist, join the thread to update the stopping vars
        #print("Stopping GPS Thread")
        GPS_Thread.join(.1)             # 5 seconds for port scanner to finish it's cycle, so thread can be emo and kill itself

    if Arduino_Thread.isAlive():
        #print("Stopping Arduino Thread")
        Arduino_Thread.join(.1)
        
    root.destroy()                      # And then kill it all
    time.sleep(5.5)                       
    raise SystemExit

def onselect(event):                    # This is for clicking the listbox, and selecting certain runs
    global Directory, prevIndexCnt, Cone_File    # Holds the directory of the run folder

    w = event.widget
    
    try:                                # Defines prevIndexCnt for first run
        prevIndexCnt
    except NameError:
        prevIndexCnt = 0
        
    indexCnt = len(w.curselection())    # How many items are currently selected?
    if indexCnt < prevIndexCnt:         # If we used to have more items, clear the old graph
        plot.clear()
        #plot2.clear()
        if Cone_File != "NONE":          
            Graph_It(Cone_File, 1)
            
        prevInexCnt = indexCnt
        
    else:
        prevIndexCnt = len(w.curselection()) # Store number of items for the next time around


    for lsNum in w.curselection()[0:]:  # Iterates through multiple selections in list
        index = int(lsNum)              # Gets the list Number of what was clicked
        value = (w.get(index)).encode('utf-8')  # Gets the label (text) from the list number
        btnLoadCourse(True)             # Re-draw cone course, it's True that we're re-drawing it

        # print(str(lsNum))
        
        try:
            Directory = Directory.encode('utf-8')
        except AttributeError:
            pass

        value = os.path.join(Directory, value)  # Make sure the full filepath is present
        if Cone_File == "NONE":         # If we don't select a Cone_File, map it anyway, use points for extents
            Cone_File = value
            Graph_It(value, 1)
            
        else:
            Graph_It(value)             # Draw run file
            
#### End of Buttons!!!! ####

        


#### Meat 'n Taters ####
        
def Graph_It(Cone_File, *Set_Extents):
    global Ext_High_Lat, Ext_Low_Lat, Ext_High_Lon, Ext_Low_Lon, Lat_Lon_Ratio, Times
    global SF_Cone_Y, SF_Cone_X
    
    if Cone_File == "NONE":                      # If we haven't selected a Cone_File
        return                                  # then don't graph anything!
    if Cone_File == "":                          # If user hits cancel, don't do anything
        return
    
    file = open(Cone_File)
    CSV_Data = csv.reader(file, quoting=csv.QUOTE_NONE)
    file.seek(0)
    
    Lat_C_List = []
    Lon_C_List = []
    C_List_Y = []
    C_List_X = []
    SF_Cone_Lat = []
    SF_Cone_Lon = []
    Times = []
    StartStopCount = 0
    Row_Str = ""
    
    try:                                        # Defines lists for first run, because we dont want to over-write them later
        SF_Cone_Y
    except NameError:
        SF_Cone_Y = []
        SF_Cone_X = []

    for row in CSV_Data:                         # Build lists of latitude/Longitude
        if not ''.join(row).strip():            # If we get to an empty line, don't error out
            break
        
        if row[0] == 'StopStart':               # Start/Stop cone row
            Row_Str = pynmea2.RMC('GP', 'RMC', (row[2:13]))             # Converts row list to sentance
            Cone_GPS_Sent = pynmea2.parse(str(Row_Str), check=False)    # Uses Pynmea2 to parse GPRMC sentance
            StartStopCount = StartStopCount + 1                         # Counts how many start/stop cones we have (should only be 4)
            SF_Cone_Lat.append(-360*(90-Cone_GPS_Sent.latitude)/180)  
            Lat_C_List.append(-360*(90-Cone_GPS_Sent.latitude)/180)     # For graph scaling
            SF_Cone_Lon.append(480*(180+Cone_GPS_Sent.longitude)/360)
            Lon_C_List.append(480*(180+Cone_GPS_Sent.longitude)/360)
            
        else:                                   # Actual GPS Coords run or cone row
            Row_Str = pynmea2.RMC('GP', 'RMC', (row[1:12]))             # Converts row list to sentance
            Cone_GPS_Sent = pynmea2.parse(str(Row_Str), check=False)    # Uses Pynmea2 to parse GPRMC sentance
            
        latC = Cone_GPS_Sent.latitude           # Loads latitude csv vals into variable
        lonC = Cone_GPS_Sent.longitude          # Loads longitude csv vals into variable
        laty = -(360*(90-latC)/180)             # Does math to make them look right
        lonx = 480*(180+lonC)/360
        Lat_C_List.append(laty)                 # Loads computed value into list
        Lon_C_List.append(lonx)
        
        Times.append(Cone_GPS_Sent.timestamp)   # Loads times into list for timing later


    # We need the extents for future graphing, but don't want to reset them if it's not a Cone_File
    if bool(Set_Extents) == True:
        Ext_High_Lat  = max(Lat_C_List)
        Ext_Low_Lat = min(Lat_C_List)
        Ext_High_Lon  = max(Lon_C_List)
        Ext_Low_Lon = min(Lon_C_List)
                                    # We need the ratio between corrected lat and corrected long for graphing to look right
        try:
            Lat_Lon_Ratio = (Ext_High_Lat-Ext_Low_Lat)/(Ext_High_Lon-Ext_Low_Lon)
        except Exception as ex:
            print(ex)
            Lat_Lon_Ratio = 1

        plot.axis('image')                      #Sets the scaling
        plot.set_xlim(-3, 103/Lat_Lon_Ratio)    #Sets plot scale limits
        plot.set_ylim(-3, 103)
        plot.axis('off')

        app.NBook1b.destroy()                   # Clears the graph
        app.NBook1b = Frame(app.NBook1)         # Then re-draws it
        canvas = FigureCanvasTkAgg(TheGraphFigure, app.master)
        canvas.get_tk_widget().pack( in_=app.NBook1b, expand=TRUE, fill=BOTH)
        app.NBook1b.pack(in_ = app.NBook1, expand=TRUE, fill=BOTH)
        
        
    i=int(0)
    imax = len(Lat_C_List)
    
    while i < imax:                             #Converts lat/lon to percent 0-100 for reasons
        C_List_Y.append(Value_Map(Lat_C_List[i], Ext_Low_Lat, Ext_High_Lat, 0, 100))
        C_List_X.append(Value_Map(Lon_C_List[i], Ext_Low_Lon, Ext_High_Lon, 0, 100/Lat_Lon_Ratio))
        if i < StartStopCount:
            SF_Cone_Y.append(Value_Map(SF_Cone_Lat[i], Ext_Low_Lat, Ext_High_Lat, 0, 100))
            SF_Cone_X.append(Value_Map(SF_Cone_Lon[i], Ext_Low_Lon, Ext_High_Lon, 0, 100/Lat_Lon_Ratio))
        i = i+1

    if bool(Set_Extents) == True:    
        plot.scatter(C_List_X, C_List_Y, c='orange', marker='^', s=2)       #Plot the orange cones!
        
    else:
        plot.plot(C_List_X, C_List_Y, c='red', linestyle='-', linewidth=1)  # Plot the run line!
        Timing(SF_Cone_Y, SF_Cone_X, C_List_X, C_List_Y, Times) #After drawing, pass the runfile on to timing, with start/stop locations     

    if StartStopCount > 0:
        plot.scatter(SF_Cone_X, SF_Cone_Y, c='red', marker='^', s=10)                       # Plot start/stop cones
        plot.plot(SF_Cone_X[0:2], SF_Cone_Y[0:2], color='k', linestyle='-', linewidth=1)    # Start line
        plot.plot(SF_Cone_X[2:4], SF_Cone_Y[2:4], color='k', linestyle='-', linewidth=1)    # Stop line


def Timing(SF_Y, SF_X, Run_X, Run_Y, Times):        # This handles doing the timing, decinding which points are at st/fin, etc.
    Start_Dist = []
    Finish_Dist = []
    Start_Chopped_Run = []
    Finish_Chopped_Run = []

    if SF_Y == [] or SF_X == []:                    # If we don't have a cone file with start/fin, then don't do timing
        return

    # First we cut down the list of possible points to only the ones near the cones...
    # Think of drawing 2 circles the radius of the start line around the start cones, we only want points from in those circles.
    
    Start_Line_Distance = math.hypot(SF_X[1] - SF_X[0], SF_Y[1] - SF_Y[0])        # Distance of start line, used for excluing points too far away
    Finish_Line_Distance = math.hypot(SF_X[3] - SF_X[2], SF_Y[3] - SF_Y[2])        # Distance of finish line, used for excluing points too far away

    for i in range(len(Run_Y)):
        Start_Line_DistancePt = math.hypot(Run_X[i] - SF_X[0], Run_Y[i] - SF_Y[0])    # Distance of point from the Start cones
        Start_Line_DistancePt2 = math.hypot(Run_X[i] - SF_X[1], Run_Y[i] - SF_Y[1])   # Distance from the other cone
        if Start_Line_DistancePt > Start_Line_Distance and Start_Line_DistancePt2 > Start_Line_Distance:    # If the cone is further from a cone than the other start cone, pass on it
            continue
        else:
            Start_Chopped_Run.append([Run_X[i], Run_Y[i], Times[i]])       # Add cones to list of near cones
    
    for i in range(len(Run_Y)):
        Finish_Line_DistancePt = math.hypot(Run_X[i]-SF_X[2], Run_Y[i] - SF_Y[2])  # Distance of point from one of the Finish cones
        Finish_Line_DistancePt2 = math.hypot(Run_X[i]-SF_X[3], Run_Y[i] - SF_Y[3]) # Distance from the other cone
        if Finish_Line_DistancePt > Finish_Line_Distance and Finish_Line_DistancePt2 > Finish_Line_Distance:    # If the cone is further from the cone than the other start cone, pass on it
            continue
        else:
            Finish_Chopped_Run.append([Run_X[i], Run_Y[i], Times[i]])         # Add cones to list of near cones

    # Now we do math on the shortened list to figure out which points are closest to the cones    

    sDen = math.sqrt((SF_Y[1]-SF_Y[0])**2 + (SF_X[1]-SF_X[0])**2)       #Start Denominator
    fDen = math.sqrt((SF_Y[3]-SF_Y[2])**2 + (SF_X[3]-SF_X[2])**2)       #Finish Denominator

    for i in range(len(Start_Chopped_Run)):                              # Iterate over choprun list of lists, and find the distances to the start or finish line
        #print("Str: " + str(Start_Chopped_Run[i]))
        sNum  = abs(((SF_Y[1]-SF_Y[0])*Start_Chopped_Run[i][0]) - ((SF_X[1]-SF_X[0])*Start_Chopped_Run[i][1]) + (SF_X[1]*SF_Y[0]) - (SF_Y[1]*SF_X[0]))
        Start_Dist.append(sNum/sDen)

    for i in range(len(Finish_Chopped_Run)):
        #print("Fin: " + str(Finish_Chopped_Run[i]))
        fNum = abs(((SF_Y[3]-SF_Y[2])*Finish_Chopped_Run[i][0]) - ((SF_X[3]-SF_X[2])*Finish_Chopped_Run[i][1]) + (SF_X[3]*SF_Y[2]) - (SF_Y[3]*SF_X[2]))
        Finish_Dist.append(fNum/fDen)

    Start_Index  = Start_Dist.index(min(Start_Dist))                                 # Find the numbers associated with the indexes
    Start_Index2 = Start_Dist.index(min2(Start_Dist))                                # sorted by the minimum distance from the id'd cone
    Finish_Index  = Finish_Dist.index(min(Finish_Dist))
    Finish_Index2 = Finish_Dist.index(min2(Finish_Dist))

    plot.scatter(Start_Chopped_Run[Start_Index][0], Start_Chopped_Run[Start_Index][1], c='black', marker='.', s=100)
    plot.scatter(Start_Chopped_Run[Start_Index2][0], Start_Chopped_Run[Start_Index2][1], c='black', marker='.', s=100)
    
    plot.scatter(Finish_Chopped_Run[Finish_Index][0], Finish_Chopped_Run[Finish_Index][1], c='yellow', marker='.', s=100)
    plot.scatter(Finish_Chopped_Run[Finish_Index2][0], Finish_Chopped_Run[Finish_Index2][1], c='yellow', marker='.', s=100)

    #print("The time of Start is: " + str(Start_Chopped_Run[Start_Index][2]))
    #print("The time of Finish is: " + str(Finish_Chopped_Run[Finish_Index2][2]))
    
    time1 = datetime.combine(date.today(), Start_Chopped_Run[Start_Index][2])
    time2 = datetime.combine(date.today(), Finish_Chopped_Run[Finish_Index2][2])
    time3 = time2 - time1
    #print("Run Length: " + str(time3))

    
#### End of Meat 'n Taters ####



##### Threads! #####


def GPSHandler_Thread():
    global Stop_GPS, GPS_Output_Speed_Raw, GPS_Display_Lon, GPS_Display_Lat
    global Lap_Names, GPS_Display_Speed, GPS_Display_Speed_Raw, GPS_Display_Status, GPS_Found, Record_Lap, Output_File
    global GPS_Time
    
    line = []                                                   # Create new list
    # maybe move this to original declare vars for cleanliness
    
    while Stop_GPS == True:                                      # Need nested while-not loops because of GPS disconnect/reconnect reasons
        try:                                                    # Try to connect to the serial port
            Found_Port = Scan_Ports()                           # but we've gotta find a port outputing NMEA first
            Found_Port = str(Found_Port).split(" ")
            ser = serial.Serial( port=Found_Port[0], baudrate = 115200, timeout=.2 )
            print("Trying to connect on: " + str(Found_Port[0]))
            
            while Stop_GPS:  # If the thread was searching for connection, or had connection, need to be able to stop either with True
                if ser.isOpen() == False:                       # Verify serial port is still open in case of unplugging/interruption
                    time.sleep(5)                               # if it's not, wait a little bit for user to fix it
                    try:                                        
                        ser.open()                              # then re-try opening it    
                        ser.flush()                             # when you re-open, it'll need a flush
                        app.b1.configure(text="   START    ", style='startg.TButton', command=Btn_Start) # Set button to green
                    except Exception as ex:                     
                        Found_Port = Scan_Ports()               # ser.open isnt' configured? Better run a portscan
                        Found_Port = str(Found_Port).split(" ")
                        ser = serial.Serial( port=Found_Port[0], baudrate = 115200, timeout=.2 )
                        pass
                    
                else:                                           # We finally have a good connection!
                    for c in ser.read():
                        line.append(chr(c))                                 # Adds character to sentance
                        GPS_Line = "".join(str(v) for v in line)            # Converts to ascii string
                        
                        if (len(GPS_Line) > 100) or (GPS_Line[0] != "$"):   # If it gets too long, flush it, she's trash
                            GPS_Line = []
                            line = []
                            continue
                        
                            
                        if chr(c) == '\n' and GPS_Line[0] == '$' and GPS_Line[5] == 'C':    # Find the $GPRMC NMEA data
                            try:
                                GPS_Parsed = pynmea2.parse(GPS_Line)                        # Use pynmea2 to parse it into use-able stuff
                                GPS_Output_Lat = 'Lat:    ' + str('{:.6f}'.format(round(GPS_Parsed.latitude, 6)))
                                GPS_Output_Lon = 'Lon: ' + str('{:.6f}'.format(round(GPS_Parsed.longitude, 6)))         # Full name for decimal
                                GPS_Output_Speed_Raw = str('{:.1f}'.format(round(int(GPS_Parsed.spd_over_grnd)*1.151))) # speed for big screen, kts->mph
                                GPS_Output_Speed = 'Speed: ' + GPS_Output_Speed_Raw + " MPH"                            # For labels
                                GPS_Time = GPS_Parsed.timestamp

                                if str(GPS_Parsed.status) == "V":
                                    status = "No Fix"
                                    app.b1.configure(text="  No Lock   ", style='starty.TButton', command="")
                                    
                                else:
                                    status = "Fix"
                                    GPS_Found = True                                        # Let's Start/stop record know that GPS is working
                                    if Record_Lap == False:
                                        app.b1.configure(text="   START    ", style='startg.TButton', command=Btn_Start)
                                GPS_Output_Status = 'Status: ' + status

                                
                                if Record_Lap == True:                                      # Write it if we're writing
                                    try:
                                        app.b1.configure(text="   STOP     ", style='startr.TButton', command=Btn_Stop) # Set button to say stop
                                        Output_File.write(str(GPS_Line))
                                        #print(str(GPS_Line))
                                        line = []
                                        
                                    except Exception as ex:
                                        print(ex)
                                        
                                line = []                                                   # Clear the line
                            except Exception as ex:                                         # If we have a problem, print it
                                print(ex)
                                
                            GPS_Label_Speedo.configure(font=('Arial', 100, 'bold'), fg="blue", bg="red") # Changes the text/font size since we've got a reading
                            GPS_Display_Lat.set(GPS_Output_Lat)                             # Update the label text
                            GPS_Display_Lon.set(GPS_Output_Lon)
                            GPS_Display_Speed.set(GPS_Output_Speed)
                            GPS_Display_Speed_Raw.set(GPS_Output_Speed_Raw)
                            GPS_Display_Status.set(GPS_Output_Status)
                            continue
                        
                        elif chr(c) == '\n' and GPS_Line[0] == '$' and GPS_Line[3] == "G":  # Find the $GPGGA data
                            #print("GGA line: " + GPS_Line)                                  # Future? do we need altitude? 
                            line = []
                            ser.flush()
                        else:
                            if chr(c) == '\n':                          # It's not GPGGA or GPRMC, so we don't want it
                                #print("False news line: " + str(line))
                                line = []                               # If it wasn't a GPS line, it was garbage anyway
                                ser.flush()
                            continue
                        
        except Exception as ex:
            print(ex)
            try:
                ser.close()
            except:
                pass
            GPS_Display_Status.set("No GPS Found                 ")
            GPS_Found = False
            app.b1.configure(text="NO GPS CONN ", style='starty.TButton', command="")      # Sets the button color when no GPS is found
            
            pass
            time.sleep(.5)                  # Prevents program hang by waiting 2 seconds before checking again
    try:
        ser.close()                         # Close the serial port for housekeeping
    except Exception:
        pass


def Arduino_TPS():                                          # Checks for arduino, updates TPS_Live var if it's got a TPS sentance
    global Stop_GPS, Arduino_Status, Ard_Loc, TPS_Live, GPS_Loc
    line = []
    while Stop_GPS == True:
        try:
            ports = (serial.tools.list_ports.comports())    # Returns list of ports
            if len(ports) == 0:                             # List is empty? Wait a while
                print("No ports found. ardtps\n")
                ports = ""
                try:                                        # Must try because if we're sleeping the thread can't close right
                    Arduino_Status.set('Ard Status: No Ports.')    
                    time.sleep(1)
                    Arduino_Status.set('Ard Status: No Ports..')
                    time.sleep(1)
                    Arduino_Status.set('Ard Status: No Ports...')
                    time.sleep(1)
                    Arduino_Status.set('Ard Status: No Ports....')
                    time.sleep(1)
                    continue
                except:
                    continue
    
            else:
                for p in ports:
                    try:
                        print("Description: " + str(p.description))
                        
                        if str(p.device) == GPS_Loc:                         # If it's an arduino port, skip it
                            print("Already GPS port" + str(p))
                            time.sleep(1)                       
                            continue
                        
                        elif "CH340" or "CH341" in p.description: 
                            time.sleep(.1)
                            Arduino_Status.set('Ard Status: Connecting')
                            Ard_Loc = p.device                      # Lists the device name COM5, etc.
                            print("Arduino found on: " + str(Ard_Loc))
                            ardSer = serial.Serial(port=str(Ard_Loc), baudrate=9600, timeout=3)
                            p = ""                                  # Clear the Port 
                            ardSer.flush()                          # Flush the buffer
                            while ardSer.isOpen() == True and Stop_GPS == True:     # This is the main TPS recording loop
                                line = ardSer.readline()        
                                Arduino_Status.set("TPS: ")
                                TPS_Str = str(line.decode().strip('\r\n'))
                                try:
                                    TPS_Var = "".join(filter(lambda x: x.isdigit(), TPS_Str))   # Removes formatting
                                    TPS_Live.set(TPS_Var)           # Sets progress bar
                                    TPS_Log(TPS_Var)                # Logs TPS value to TPS log
                                    continue
                                except Exception as e:
                                    print(e)
                                    break
                                
                            else:
                                """For UAC in windows, com port access needs admin privlidges"""
                                #import ctypes, sys
                                #ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
                                print("Port not open")
                                continue
                                                
                        else:
                            #print("No Arduino found on: " + str(p))
                            p = ""
                            try:                                    # Must try because if we're sleeping the thread can't close right
                                Arduino_Status.set('Ard Status: .')    
                                time.sleep(1)
                                Arduino_Status.set('Ard Status: ..')
                                time.sleep(1)
                                Arduino_Status.set('Ard Status: ...')
                                time.sleep(1)
                                Arduino_Status.set('Ard Status: ....')
                                time.sleep(1)
                                continue
                            except Exception as e:
                                pass
                    except Exception as e:
                        pass        
        except Exception as ex:
            pass

#### End of Threads ####



#### Little tools ####

def TPS_Log(TPS_Val):                                   # TPS Value Logger
    global GPS_Time, Record_Lap, TPS_Log_File, GPS_Time_Ref
    
    if Record_Lap == True:                              # If we're supposed to be recording
        if len(TPS_Val) > 0:                            # And if TPS is non-zero
            #print("TPS VAL INPUT: " + str(TPS_Val))
            try:
                if str(GPS_Time) == str(GPS_Time_Ref):  # If GPS hasn't updated, then we log all the data we received in-between GPS updates
                    TPS_Val += ',\n'
                    TPS_Log_File.write(TPS_Val)
                    
                else:                                   # If the GPS time has updated, we log the GPS time so we can reference the position/speed later
                    GPS_Time_Ref = GPS_Time             # Keep track of the old GPS time for comparing
                    #GPS_Time = str('{:.1}'.format(GPS_Time))
                    TPS_Val += "," + str(GPS_Time) + '\n'   # Format the record line with newline and CSV
                    TPS_Log_File.write(TPS_Val)         # Wtite it
                    
            except Exception as e:
                print("Error: " + str(e))


def Scan_Ports():                               # GPS port scan
    global Ard_Loc, GPS_Loc
    while Stop_GPS == True:
        ports = (serial.tools.list_ports.comports())    # Shows current system serial ports
        #print("Found ports: " + str(ports))
        if len(ports) == 0:                     # If system has no ports, wait for ports
            print("No ports found. Scan_Ports")
            try:                                    # Must try because if we're sleeping the thread can't close right
                GPS_Display_Status.set("GPS Status: .")    
                time.sleep(1)
                GPS_Display_Status.set("GPS Status: ..")
                time.sleep(1)
                GPS_Display_Status.set("GPS Status: ...")
                time.sleep(1)
                GPS_Display_Status.set("GPS Status: ....")
                time.sleep(1)
            except:
                pass
            continue
        
        else:                                   # try to parse, pynmea errors out if it's not a nmea sentance
            for port in ports:
                try:
                    if str(port.device) == Ard_Loc:                         # If it's an arduino port, skip it
                        print("Already arduino port" + str(port))
                        #port = ""
                    
                        continue
                    else:
                        with serial.Serial(port[0], 115200, timeout=1) as ser:
                            print("Trying port: " + str(port))
                            try:
                                line = []
                                line = ser.readline()
                                #line = str(line.decode('ascii').strip('\r\n'))
                                print("Line is: " + str(line.decode('UTF-8').strip('\r\n')))
                                #pynmea2.parse(line, error='replace')
                                pynmea2.parse(line.decode('ascii', errors='replace'))
                                GPS_Loc = port.device
                                return port
                            except Exception as e:
                                print('Error: ' + str(e))
                                continue
                            #print('Found data on: ' + str(port))
                            

                except Exception as e:          # We got an error from pynmea, so it's not a GPS signal
                    print("Out of loop Error: " + str(e))
                    #print('No GPS found on: ' + str(port))
                    try:                        # Try because ser might not exist yet
                        if ser.isOpen():        # Double check that we've closed the port
                            ser.Close()
                    except:
                        pass
                    pass                        
        try:                                    # Must try because if we're sleeping the thread can't close right
            GPS_Display_Status.set("GPS Status: .")    
            time.sleep(1)
            GPS_Display_Status.set("GPS Status: ..")
            time.sleep(1)
            GPS_Display_Status.set("GPS Status: ...")
            time.sleep(1)
            GPS_Display_Status.set("GPS Status: ....")
            time.sleep(1)
        except:
            pass

        
def min2(Number_List):                   # Used to find second smallest number in a list, for start/finish line timing
    low1, low2 = float('inf'), float('inf')
    for x in Number_List:
        if x <= low1:
            low1, low2 = x, low1
        elif x < low2:
            low2 = x
    return low2     

def Check_File_Path(Name, ext, count):          # recursively checks filenames for first free filename
    global Directory

    if sys.platform.startswith('win'): 
        File_Slashes = "\\"
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        File_Slashes = "/"
        
    print(os.fsdecode(Directory) + File_Slashes + Name + str(count) + ext)
    if os.path.exists(os.fsdecode(Directory) + File_Slashes + Name + str(count) + ext):
        
        return Check_File_Path(Name, ext, count+1)     # If it exists already, +1 to the file number, restart this function with new input
    else:
        return Name + str(count) + ext

def Value_Map(value, fLow, fHigh, toLow, toHigh):          #pretty much the map() function in arduino, used 4 times so far
    return toLow + (toHigh - toLow) * ((value - fLow) / (fHigh - fLow))

#### End Little Tools ####

def GPS_Start():                                                 # Updates the GPS info on the main display
    global Stop_GPS, Record_Lap, GPS_Thread, GPS_Found, Arduino_Thread       # Has to be external so you can reset vars
                                                                #    and eventually stop threads. 
    GPS_Found  = False
    Stop_GPS   = True
    Record_Lap = False
    
    GPS_Thread     = threading.Thread(target=GPSHandler_Thread )
    GPS_Thread.start()                                          # Start the GPS thread
    Arduino_Thread = threading.Thread(target=Arduino_TPS )      # Start the Arduino thread
    Arduino_Thread.start()
    
    
root = Tk()
root.minsize(width=480, height=290)
"""
# make it cover the entire screen, it works but commented out for testing
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
#root.overrideredirect(1)
root.geometry("%dx%d+0+0" % (w, h))
root.attributes('-zoomed', True)
"""
app = Application(master=root)
GPS_Start()    # Starts GPS thread in the background
app.mainloop()

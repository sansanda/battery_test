'''
Created on 2 jul. 2019

@author: mespower
'''
# if __name__ == '__main__':
#     pass


# POWER CYCLING SCRIPT
import threading
from tkinter import messagebox

import visa
import sys

# DEFINING MINS FOR PARAMETERS
from Main import csv_connection

from threading import Timer


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


TOTAL_TIME_MIN = 0
MEASURE_PERIOD_MIN = 1
CURRENT_MIN = 0
CURRENT_MAX = 60
GPIB_ADDR_MIN = 1
GPIB_ADDR_MAX = 30

# OPEN THE FILE THAT CONTAINS THE INITIALS VALUES
initial_values_f = open('.\config_files\initial_values_file.txt',
                        "r")  # Opening the file with a relative path, as readers ('r')
initial_values = initial_values_f.readlines()  # Read the file: Array of strings

for line in initial_values:  # line: each string in the previous array
    # Define the file variables in the script
    # The file configuration is: VARIABLE=VALUE
    # In order to find the values, we memorize all the characters after the index of the '='
    if line.startswith("*"):  # To comment something in the file write: *
        print('Skipping comment:')
        continue
    if 'Current' in line:  # Search where is curr in the file, just in case the order of the values changes
        curr = float(line[line.index('=') + 1:])  # Impose the value of the low current level
        print('Current is: ', curr, 'A')
    if 'Slew Rate' in line:
        sr = float(line[line.index('=') + 1:])  # Slew rate
        print('Slew Rate is:', sr)
    if 'total_time' in line:
        total_time = float(line[line.index('=') + 1:])  # Set up the seconds when the electronic load is conducting
        print('total_time:', total_time, 's')
    if 'measure_period' in line:
        measure_period = float(line[line.index(
            '=') + 1:])  # The seconds elapsed from the electronic load starts conducting till the multimeter measures.
        print('measure_period is:', measure_period, 's')
    if 'Voltage channel' in line:
        voltage_channel = float(line[line.index('=') + 1:])
        print('Voltage channel:',
              voltage_channel)  # .replace because the split introduce a new line after the match
    if 'Current Range' in line:
        curr_rang = float(line[line.index('=') + 1:])  # Set the desired current range (LOW (0-6A) or HIGH(0-60A))
        print('Current Rang:', curr_rang, 'A')
    if 'Csv file path' in line:
        csv_file_path = line[line.index('=') + 1:]  # Relative Path to the CSV file (results)
        print('File path:', csv_file_path)
    if 'Electronic Load GPIBAddr' in line:
        electronic_load_GPIBAddr = int(line[line.index('=') + 1:])  # Electronic load GPIB address
        print('Electronic Load GPIBAddr:', electronic_load_GPIBAddr)
    if 'Keithley 3706 GPIBAddr' in line:
        multimeter_GPIBAddr = int(line[line.index('=') + 1:])  # Keithley multimeter GPIB address
        print('Keithley 3706 GPIBAddr:', multimeter_GPIBAddr)

initial_values_f.close()  # In order to avoid errors, the file is closed
print('\n---------------------------------------------------------------')


def check_parameters(_total_time,
                     _measure_period,
                     _current_range,
                     _current):
    """
    This function checks whether the parameters are coherent. It returns an error if any of the
    following sentences happen, as well as a reporting message.
    """
    error = False  # Initial error status=False

    if _total_time < TOTAL_TIME_MIN:
        error = True
        messagebox.showerror(message="total_time must be bigger than " + str(TOTAL_TIME_MIN) + " minutes.",
                             title="Time Definition Error")

    if _measure_period < MEASURE_PERIOD_MIN:
        error = True
        messagebox.showerror(message="measure period must be bigger than " + str(MEASURE_PERIOD_MIN) + " seconds.",
                             title="Time Definition Error")

    if _current < CURRENT_MIN or _current > CURRENT_MAX:
        error = True
        messagebox.showerror(
            message="current must be between valors [" + str(CURRENT_MIN) + "," + str(CURRENT_MAX) + "]"
            , title="Current Definition Error")

    if _current_range < CURRENT_MIN or _current_range > CURRENT_MAX:
        error = True
        messagebox.showerror(
            message="current range must be between valors [" + str(CURRENT_MIN) + "," + str(CURRENT_MAX) + "]"
            , title="Current Definition Error")

    return error


# Check if all the times are OK
if check_parameters(total_time,
                    measure_period,
                    curr_rang,
                    curr):
    exit()  # If any mentioned fact has happened, the program exits.

# Define the total number of channels
nChannels = 2

# CREATE AND OPEN THE CSV FILE TO TRANSFR THE ACQUIRED DATA
field_names = ['Time (seconds)', 'Battery Voltage', 'Battery Current']  # Create an array of constant headers

csv_connection.create_csv_file(csv_file_path, field_names)  # Open the csv file and write the array of headers

# ---------------------------------------------------------------------------------------------


# STOP BUTTON
stop = 0  # Boolean in order to stop the electronic load whenever necessary.

# OPENING THE RESOURCE MANAGER
rm = visa.ResourceManager()

# COMMUTICATE WITH THE ELECTRONIC LOAD
electronic_load = rm.open_resource(
    'GPIB0::' + str(electronic_load_GPIBAddr) + '::INSTR')  # Assign a variable to the Electronic load by its address

# COMMUTICATE WITH KEITHLEY MULTIMETER
multimeter = rm.open_resource(
    'GPIB0::' + str(multimeter_GPIBAddr) + '::INSTR')  # Assign a variable to the multimeter by its address

# SENDING THE FIRST COMMANDS TO CONFIGURE THE ELECTRONIC LOAD
electronic_load.write('*CLS')  # Clear Status Command
electronic_load.write('*RST')  # Reset Command
electronic_load.write('TRIG:SOUR BUS')  # Source triggeR will be send via bus
electronic_load.write('MODE:CURR')  # Set the operating mode: Current Mode (CC)
electronic_load.write('CURR:RANG {}'.format(curr_rang))  # Low range current (0A-6A), High range current (0A-60A)
electronic_load.write('CURR:SLEW {}'.format(sr))  # The value of the Slew Rate in the file is imposed on the instrument
electronic_load.write('CURR {}'.format(curr))  # The value of the current is established on the instrument
electronic_load.write('INPUT ON')  # Switch on electronic load

# SENDING THE FIRST COMMANDS TO CONFIGURE KEITHLEY MULTIMETER
multimeter.write('reset()')  # Reset
multimeter.write('localnode.prompts = 0')  # The command messages do not generate prompts in console
multimeter.write('localnode.prompts4882 = 0')  # Disable the prompts for the GPIB

# Set voltage configuration
multimeter.write('dmm.func = dmm.DC_VOLTS')  # Set measurement function: Voltage
multimeter.write('dmm.nplc=1')  # The integration rate in line cycles for the DMM for the function selected by dmm.func.
multimeter.write('dmm.range=20')  # Set Range

try:
    # DEFINING PRINCIPAL FUNCTION

    def measure(_voltage_channel):
        """
        Measures the voltage on the multimeter dmm
        """
        #aqui medimos tanto corriente de la carga electronica como voltage del multimetro


        #acto seguido escribimos en el fichero de resultados

        if stop == 1:  # Someone has pressed the stop button

            print("CANCELLING THE PROCESS!!!!!!!")
            print("CANCELLING THE PROCESS!!!!!!!")
            print("CANCELLING THE PROCESS!!!!!!!")

            # Timers are closed in order to avoid errors
            timer.cancel()


    def emergency_stop():
        """
        Detects the space bar key pressed on the console, and stops the electronic load, 
        setting the current value to zero immediately.
        """
        if sys.stdin.read(1) == ' ':  # Detects when the space bar is pressed

            print('STOP!!!')
            global stop  # Stop is converted to a global variable
            stop = 1  # 'trg_up'and'trg_down' will stop executing

            electronic_load.write('CURR:TRIG 0')  # Intensity value ZERO on memory, Preset
            electronic_load.write('*TRG')  # Send the trigger

            electronic_load.write('INPUT OFF')  # Impose that the instrument switch its input off
            multimeter.write('reset()')

            global rm
            rm.close()
            rm = None
            # gc.collect()

        # To stop the program 'space bar' and then 'enter' must be pressed in the console!


    # TIMER
    timer = RepeatedTimer(measure_period, measure, voltage_channel)
    timer.start()  # The timer is started

    # OPEN A THREAD TO ALLOW THE STOP BUTTON TO RUN IN PARALEL THE CODE
    stop_thread = threading.Thread(target=emergency_stop())
    # It is continually running independently the other code, so whenever the space bar is pressed, it will be registered
    stop_thread.start()  # The thread is initialized

except visa.VisaIOError as e:
    # except SomeException:
    print(e.args)
    print(rm.last_status)
    print(rm.visalib.last_status)

    if rm.last_status == visa.constants.StatusCode.error_resource_busy:
        print("The port is busy!")

    print('holiiiiiiiiiiiiiiiiiiiiii')
    electronic_load.write('INPUT OFF')

'''
Created on 28 Nov. 2022

@author: david_sanchez (sansanda)
'''

# BATTERY TEST SCRIPT
import atexit
import time
from tkinter import messagebox

import pyvisa
import sys
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
MEASURE_PERIOD_MIN = 0.1
CURRENT_MIN = 0
CURRENT_MAX = 60
GPIB_ADDR_MIN = 1
GPIB_ADDR_MAX = 30


def readConfigFile(file_path):
    parameters = dict()
    config_file = open('..\config_files\initial_values_file.txt',
                       "r")  # Opening the file with a relative path, as readers ('r')
    config_file_lines = config_file.readlines()  # Read the file: Array of strings

    for line in config_file_lines:  # line: each string in the previous array
        # Define the file variables in the script
        # The file configuration is: VARIABLE=VALUE
        # In order to find the values, we memorize all the characters after the index of the '='
        if line.startswith("*"):  # To comment something in the file write: *
            print('Skipping comment:')
            continue
        if 'Current' in line:  # Search where is curr in the file, just in case the order of the values changes
            parameters["current"] = float(line[line.index('=') + 1:])  # Impose the value of the low current level
            print('Current is: ', parameters["current"], ' Amps')
        if 'Slew Rate' in line:
            parameters["slew_rate"] = float(line[line.index('=') + 1:])  # Slew rate
            print('Slew Rate is:', parameters["slew_rate"])
        if 'total_time' in line:
            parameters["total_time"] = float(
                line[line.index('=') + 1:])  # Set up the seconds when the electronic load is conducting
            print('total_time:', parameters["total_time"], 's')
        if 'measure_period' in line:
            parameters["measure_period"] = float(line[line.index(
                '=') + 1:])  # The seconds elapsed from the electronic load starts conducting till the multimeter measures.
            print('measure_period is:', parameters["measure_period"], 's')
        if 'Voltage channel' in line:
            parameters["voltage_channel"] = float(line[line.index('=') + 1:])
            print('Voltage channel:',
                  parameters["voltage_channel"])  # .replace because the split introduce a new line after the match
        if 'Current Range' in line:
            parameters["current_range"] = float(
                line[line.index('=') + 1:])  # Set the desired current range (LOW (0-6A) or HIGH(0-60A))
            print('Current Rang:', parameters["current_range"], 'A')
        if 'Csv file path' in line:
            parameters["results_file_rel_path"] = line[line.index('=') + 1:]  # Relative Path to the CSV file (results)
            print('File path:', parameters["results_file_rel_path"])
        if 'Electronic Load GPIBAddr' in line:
            parameters["electronic_load_gpib_addr"] = int(line[line.index('=') + 1:])  # Electronic load GPIB address
            print('Electronic Load GPIBAddr:', parameters["electronic_load_gpib_addr"])
        if 'Keithley 3706 GPIBAddr' in line:
            parameters["multimeter_gpib_addr"] = int(line[line.index('=') + 1:])  # Keithley multimeter GPIB address
            print('Keithley 3706 GPIBAddr:', parameters["multimeter_gpib_addr"])

    config_file.close()  # In order to avoid errors, the file is closed

    return parameters


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


def get_instruments(electronic_load_gpib_addr,
                    multimeter_gpib_addr):
    # OPENING THE RESOURCE MANAGER
    rm = pyvisa.ResourceManager()

    # COMMUTICATE WITH THE ELECTRONIC LOAD
    _electronic_load = rm.open_resource(
        'GPIB0::' + str(
            electronic_load_gpib_addr) + '::INSTR')  # Assign a variable to the Electronic load by its address

    # COMMUTICATE WITH KEITHLEY MULTIMETER
    _multimeter = rm.open_resource(
        'GPIB0::' + str(multimeter_gpib_addr) + '::INSTR')  # Assign a variable to the multimeter by its address

    return _electronic_load, _multimeter


# ---------------------------------------------------------------------------------------------


def configure_multimeter(_multimeter, channel):
    # SENDING THE FIRST COMMANDS TO CONFIGURE KEITHLEY MULTIMETER
    _multimeter.write('reset()')  # Reset
    _multimeter.write('localnode.prompts = 0')  # The command messages do not generate prompts in console
    _multimeter.write('localnode.prompts4882 = 0')  # Disable the prompts for the GPIB

    # Set voltage configuration
    _multimeter.write('dmm.func = dmm.DC_VOLTS')  # Set measurement function: Voltage
    _multimeter.write(
        'dmm.nplc=1')  # The integration rate in line cycles for the DMM for the function selected by dmm.func.
    _multimeter.write('dmm.range=20')  # Set Range
    _multimeter.write("dmm.configure.set('mydcvolts')")  # Save Configuration
    _multimeter.write("dmm.setconfig('" + str(channel) + "','mydcvolts')")


def configure_electronic_load(_electronic_load, current, current_range, slew_rate):
    # SENDING THE FIRST COMMANDS TO CONFIGURE THE ELECTRONIC LOAD
    _electronic_load.write('*CLS')  # Clear Status Command
    _electronic_load.write('*RST')  # Reset Command
    _electronic_load.write('TRIG:SOUR BUS')  # Source triggeR will be send via bus
    _electronic_load.write('MODE:CURR')  # Set the operating mode: Current Mode (CC)
    _electronic_load.write(
        'CURR:RANG {}'.format(current_range))  # Low range current (0A-6A), High range current (0A-60A)
    _electronic_load.write(
        'CURR:SLEW {}'.format(slew_rate))  # The value of the Slew Rate in the file is imposed on the instrument
    _electronic_load.write('CURR {}'.format(current))  # The value of the current is established on the instrument
    time.sleep(1)
    _electronic_load.write('INPUT ON')  # Switch on electronic load


# DEFINING PRINCIPAL FUNCTION

def measure(_electronic_load, _multimeter, results_file_rel_path):
    """
    Measures the voltage on the multimeter dmm
    """
    # aqui medimos tanto corriente de la carga electronica como voltage del multimetro

    # start_scan_multimeter()
    actual_electronic_load_curr = _electronic_load.query('MEASure:CURRent:DC?')
    _multimeter.write("dmm.close('1001')")
    # actual_multimeter_voltage = _multimeter.query("print(dmm.measure())")
    actual_multimeter_voltage, seconds, fraction = _multimeter("print(dmm.measurewithtime())")
    # acto seguido escribimos en el fichero de resultados
    csv_connection.insertRowInCSV(results_file_rel_path,
                                  [time.time(), actual_multimeter_voltage, actual_electronic_load_curr])
    _multimeter.write("dmm.open('1001')")
    print(f"multimeter voltage: {actual_multimeter_voltage.strip()} Volts.\n"
          f"load current: {actual_electronic_load_curr.strip()} Amps.\n")


# STOP BUTTON
stop = 0  # Boolean in order to stop the electronic load whenever necessary.


def measure_x_times(_electronic_load, _multimeter, results_file_rel_path, interval, times):
    past_time_ref = 0
    elapsed_time = 0

    for i in range(0, times, 1):
        time.sleep(interval - elapsed_time)
        past_time_ref = time.time()
        measure(_electronic_load, _multimeter, results_file_rel_path)
        elapsed_time = time.time() - past_time_ref

    return 0


def measure_forever(_electronic_load, _multimeter, results_file_rel_path, interval):
    past_time_ref = 0
    elapsed_time = 0

    while True:
        time.sleep(interval - elapsed_time)
        past_time_ref = time.time()
        measure(_electronic_load, _multimeter, results_file_rel_path)
        elapsed_time = time.time() - past_time_ref


def exit_function(_electronic_load):
    print("EXITINGGG!!!")
    _electronic_load.write('INPUT OFF')  # Switch on electronic load


def main(_electronic_load, _multimeter, _parameters) -> int:
    # Check if all the times are OK
    if check_parameters(_parameters["total_time"],
                        _parameters["measure_period"],
                        _parameters["current_range"],
                        _parameters["current"]):
        sys.exit(-1)  # If any mentioned fact has happened, the program exits.

    # CREATE AND OPEN THE CSV FILE TO TRANSFR THE ACQUIRED DATA
    field_names = ['Time Stamp (seconds)', 'Battery Voltage', 'Battery Current']  # Create an array of constant headers

    csv_connection.create_csv_file(_parameters["results_file_rel_path"],
                                   field_names)  # Open the csv file and write the array of headers

    configure_multimeter(_multimeter, 1001)
    configure_electronic_load(_electronic_load,
                              _parameters["current"],
                              _parameters["current_range"],
                              _parameters["slew_rate"])

    measure_forever(_electronic_load,
                    _multimeter,
                    _parameters["results_file_rel_path"],
                    _parameters["measure_period"],)

    return 0


if __name__ == '__main__':
    config_file_rel_path = '..\config_files\initial_values_file.txt'
    parameters = readConfigFile(config_file_rel_path)

    electronic_load, multimeter = get_instruments(parameters["electronic_load_gpib_addr"],
                                                  parameters["multimeter_gpib_addr"])

    atexit.register(exit_function,
                    electronic_load)

    sys.exit(main(electronic_load, multimeter, parameters))  # next section explains the use of sys.exit

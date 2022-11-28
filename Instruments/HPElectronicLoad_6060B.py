'''
Created on 19 jul. 2019

@author: mespower
'''

instrument = None

def sendTrigger():
    instrument.write('*TRG')    #Send trigger signal

def reset():
    instrument.write('*RST')    #Send reset command    

def clear():
    instrument.write('*CLS')    #Send clear command
    
def openInstrument (_resourceManager,gpibAddr):
    instrument = _resourceManager.open_resource('GPIB0::'+str(gpibAddr)+'::INSTR')   #Assign a variable to the Electronic load by its address

def setInCurrentMode():
    instrument.write('MODE:CURR')    #Set the operating mode: Current Mode (CC)

def configTriggerSource(_source):
    instrument.write('TRIG:SOUR '+_source+'')
    
def configTriggerSourceAsBus():
    configTriggerSource("BUS")

def configCurrentRange(_curr_range):
    instrument.write('CURR:RANG {}'.format(_curr_range))    #Low range current (0A-6A), High range current (0A-60A)
    
def configureCurrentSlewRate(_sr):
    instrument.write('CURR:SLEW {}'.format(_sr))    #The value of the Slew Rate in the file is imposed on the instrument 
    
def setCurrent(_curr):
    instrument.write('CURR {}'.format(_curr))    #The value of the low current is established on the instrument
def enableInput(_enable):
    if (_enable):
        instrument.write('INPUT ON')    #Switch on electronic load
    if (not _enable):
        instrument.write('INPUT OFF')    #Switch off electronic load 
    
def setDefaultConfiguration(_curr_rang,_sr,_curr):
    reset()
    clear()
    configTriggerSourceAsBus()
    setInCurrentMode()
    configCurrentRange(_curr_rang)
    configureCurrentSlewRate(_sr)
    setCurrent(_curr)
    enableInput(True)

    
    
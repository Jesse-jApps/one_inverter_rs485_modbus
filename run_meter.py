# -*- coding: utf-8 -*-

import os
from datetime import datetime
from time import sleep
import pandas as pd
import minimalmodbus


SERIAL_PORT = '/dev/ttyUSB0'

BASE_FOLDERPATH = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDERPATH = os.path.join(BASE_FOLDERPATH, 'data_meter')

# Function to read input registers
def read_input_registers(instrument, start_address, count):
    try:
        # Read input registers. Registers are 16 bits.
        registers = instrument.read_registers(start_address, count, 3)
        return registers
    except minimalmodbus.NoResponseError as e:
        print(f"No response from device: {e}")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus error: {e}")
    except Exception as e:
        print(f"Error: {e}")


# Configure the serial connection
instrument = minimalmodbus.Instrument(SERIAL_PORT, 2)  # Port name, Slave address (in decimal)
instrument.serial.baudrate = 9600  # Baud
instrument.serial.bytesize = 8
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1.5  # seconds

while True:
    filepath = os.path.join(DATA_FOLDERPATH, f'results_{datetime.now().date()}.csv')
    result = read_input_registers(instrument, 0, 70)
    if result is not None:
        result.append(datetime.now().timestamp())
        df = pd.DataFrame([result])
        df.to_csv(filepath, mode='a', index=False, header=not os.path.exists(filepath))
    sleep(4)

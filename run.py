# -*- coding: utf-8 -*-

import os, random
from datetime import datetime
from time import sleep
import pandas as pd
import minimalmodbus


SERIAL_PORT = '/dev/cu.usbserial-110'

# Function to read input registers
def read_input_registers(instrument, start_address, count):
    try:
        # Read input registers. Registers are 16 bits.
        registers = instrument.read_registers(start_address, count, 4)  # Function code 4
        return registers
    except minimalmodbus.NoResponseError as e:
        print(f"No response from device: {e}")
    except minimalmodbus.ModbusException as e:
        print(f"Modbus error: {e}")
    except Exception as e:
        print(f"Error: {e}")


# Configure the serial connection
instrument = minimalmodbus.Instrument(SERIAL_PORT, 1)  # Port name, Slave address (in decimal)
instrument.serial.baudrate = 9600  # Baud
instrument.serial.bytesize = 8
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1  # seconds
instrument = None

while True:
    filepath = os.path.join('data', f'results_{datetime.now().date()}.csv')
    result = read_input_registers(instrument, 0, 27)
    if result is not None:
        result.append(datetime.now().timestamp())
        df = pd.DataFrame([result])
        df.to_csv(filepath, mode='a', index=False, header=not os.path.exists(filepath))
    sleep(3)

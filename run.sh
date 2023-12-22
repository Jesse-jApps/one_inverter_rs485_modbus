#!/bin/bash
# Run as /home/pi/one_inverter_rs485_modbus/run.sh
source /home/pi/inverter_env/bin/activate
python /home/pi/one_inverter_rs485_modbus/run.py > run.log  2>&1 &
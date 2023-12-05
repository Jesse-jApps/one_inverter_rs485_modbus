# -*- coding: utf-8 -*-

import time, os
from datetime import datetime

import pandas as pd 
import streamlit as st


APP_FOLDERPATH = os.path.dirname(os.path.abspath(__file__))
BASE_FOLDERPATH = os.path.dirname(APP_FOLDERPATH)
DATA_FOLDERPATH = os.path.join(BASE_FOLDERPATH, 'data')

RESPONSE_MAPPING = {
    0: {'id': 0, 'name': 'AC input voltage', 'unit': 'V', 'is_decimal':True},
    1: {'id': 1, 'name': 'Input frequency', 'unit': 'Hz', 'is_decimal':True},
    2: {'id': 2, 'name': 'Output voltage', 'unit': 'V', 'is_decimal':True},
    3: {'id': 3, 'name': 'Output frequency', 'unit': 'Hz', 'is_decimal':True},
    4: {'id': 4, 'name': 'Output current', 'unit': 'A'},
    6: {'id': 6, 'name': 'Output load rate', 'unit': '%'},
    7: {'id': 7, 'name': 'Battery voltage', 'unit': 'V', 'is_decimal':True},
    9: {'id': 9, 'name': 'Battery capacity rate', 'unit': '%'},
    12: {'id': 12, 'name': 'DC bus current', 'unit': 'A'},
    13: {'id': 13, 'name': 'Internal temperature', 'unit': '°C'},
    14: {'id': 14, 'name': 'Ambient temperature', 'unit': '°C'},
    15: {'id': 15, 'name': 'PV input voltage', 'unit': 'V', 'is_decimal':True},
    17: {'id': 17, 'name': 'Controller battery', 'unit': 'V', 'is_decimal':True},
    18: {'id': 18, 'name': 'Controller charging', 'unit': 'A', 'is_decimal':True},
    20: {'id': 20, 'name': 'Controller internal', 'unit': '°C'},
    21: {'id': 21, 'name': 'Controller internal', 'unit': '°C'},
    22: {'id': 22, 'name': 'Controller external', 'unit': '°C'},
    24: {'id': 24, 'name': 'High daily power', 'unit': 'Wh'},
    23: {'id': 23, 'name': 'Low daily power', 'unit': 'Wh'},
    26: {'id': 26, 'name': 'High total power', 'unit': 'Wh'},
    25: {'id': 25, 'name': 'Low total power', 'unit': 'Wh'},
    27: {'id': 27, 'name': 'Timestamp', 'unit': 'ms'},
}

st.set_page_config(
    page_title="Inverter Live and Historical Data",
    layout="wide",
)

st.markdown('## Live Metrics')

placeholder = st.empty()

st.markdown('## Daily Metrics')


while True:
    today_filepath = os.path.join(DATA_FOLDERPATH, f'results_{datetime.now().date()}.csv')

    df_today = pd.read_csv(today_filepath)

    output_load_rate = df_today['6'].iloc[-1]
    output_current = df_today['4'].iloc[-1]

    battery_capacity_rate = df_today['9'].iloc[-1]
    battery_voltage = round(df_today['7'].iloc[-1]/10, 1)

    input_current = round(df_today['18'].iloc[-1]/10, 1)
    input_voltage = round(df_today['15'].iloc[-1]/10, 1)

    current_power = round(input_current*input_voltage)
    previous_mean_power = (df_today.tail(20)['18'] * df_today.tail(20)['15'].map(lambda x: round(x/10, 1))).mean()
    current_power_delta = 100
    if previous_mean_power != 0:
        current_power_delta = round((current_power - previous_mean_power) / previous_mean_power * 100)

    with placeholder.container():
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        kpi1.metric(
            label="Current Load",
            value=f'{output_load_rate} %',
            delta=f'{output_current} A',
            delta_color="off"
        )
        kpi2.metric(
            label="Battery Capacity",
            value=f'{battery_capacity_rate} %',
            delta=f'{battery_voltage} V',
            delta_color="off"
        )
        kpi3.metric(
            label="PV Input",
            value=f'{input_current} A',
            delta=f'{input_voltage} V',
            delta_color="off"
        )
        kpi4.metric(
            label="Electricity production",
            value=f'{current_power} W',
            delta=f'{current_power_delta} %'
        )
        time.sleep(2)



# -*- coding: utf-8 -*-

import time, os, pytz, glob
from datetime import datetime, timedelta

import pandas as pd 
import streamlit as st
import altair as alt

from scipy.signal import savgol_filter 


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

def prepare_df(df):
    df['battery_voltage'] = df['7'].map(lambda x: round(x/10, 1))
    df['time'] = df['datetime'].map(lambda x: x.strftime('%H:%M'))
    df['power'] = (df['18'] * df['15']).map(lambda x: round(x/100, 1))

    return df

def prepare_df_minute(df):
    df_minute = df.groupby(['date', 'time'], as_index=False).mean(numeric_only=True)
    df_minute['datetime'] = df_minute.apply(
        lambda x: datetime.strptime(f"{x['date']} {x['time']}", '%Y-%m-%d %H:%M'),
        axis=1
    )
    df_minute['x'] = df_minute['datetime'].map(
        lambda x: (x.hour-17)*60+x.minute if x.hour >= 17 else (x.hour+7)*60+x.minute
    )
    df_minute['night'] = df_minute.apply(
        lambda x: f"{x['date']} - {x['date']+timedelta(days=1)}" if x['hour'] >= 17 else f"{x['date']-timedelta(days=1)} - {x['date']}" ,
        axis=1
    )
    df_minute = df_minute.sort_values('x')

    dfs = []
    for i, df_sub in df_minute.groupby('night'):
        if df_sub.shape[0] < 60:
            continue
        df_sub['load'] = df_sub['4'].cumsum()
        df_sub['battery_voltage_smooth'] = df_sub[['battery_voltage']].apply(savgol_filter,  window_length=60, polyorder=2)
        dfs.append(df_sub)
    df_minute = pd.concat(dfs)
    df_minute = df_minute[df_minute['night'] > df_minute['night'].min()]

    return df_minute

st.set_page_config(
    page_title="Inverter Live and Historical Data",
    layout="wide",
)

dfs = []
for f in glob.glob(os.path.join(DATA_FOLDERPATH, '*.csv')):
    if '.csv' not in f:
        continue
    file_date = datetime.strptime(f.split('/')[-1], 'results_%Y-%m-%d.csv')
    if file_date < datetime.now()-timedelta(days=6):
        continue
    df = pd.read_csv(f)
    df['filepath'] = f
    df['datetime'] = df['27'].map(lambda x: datetime.fromtimestamp(x, pytz.timezone("Asia/Manila")))
    df['date'] = df['datetime'].map(lambda x: x.date())
    df['hour'] = df['datetime'].map(lambda x: x.hour)
    df['seconds'] = df['datetime'].map(lambda x: (x - x.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())
    df['Wh'] = df['4']*(df['seconds'] - df['seconds'].shift(1)).fillna(df['seconds'])/3600*220
    #df['Wh_cumsum'] = df['Wh'].cumsum()
    dfs.append(df)
df_all = prepare_df(pd.concat(dfs))
df_all['x'] = df_all['datetime'].map(
    lambda x: (x.hour-17)*60+x.minute if x.hour >= 17 else (x.hour+7)*60+x.minute
)
df_all['night'] = df_all.apply(
    lambda x: f"{x['date']} - {x['date']+timedelta(days=1)}" if x['hour'] >= 17 else f"{x['date']-timedelta(days=1)} - {x['date']}" ,
    axis=1
)
df_all_max = df_all.groupby('date', as_index=False).max()
#df_minute = prepare_df_minute(df_all)
#df_minute = df_minute[df_minute['power'] == 0]

st.markdown('## Live Metrics')
placeholder = st.empty()

st.markdown('## Battery infos')
c1, c2 = st.columns(2)
c1.markdown('### Total consumption during night')
df_sonsumption_night = df_all[df_all['power'] == 0].groupby('night')[['Wh']].sum()
df_sonsumption_night['kWh'] = df_sonsumption_night['Wh'].map(lambda x: round(x/1000, 2))
c1.dataframe(df_sonsumption_night[['kWh']])

#c1, c2, c3, c4 = st.columns(4)
#for d, df_sub in df_all[df_all['power'] == 0].groupby('date'):
#chart = alt.Chart(df_all[df_all['power'] == 0]).mark_line().transform_window(
#    # Sort the data chronologically
#    sort=[{'field': 'x'}],
#    # Include all previous records before the current record and none after
#    # (This is the default value so you could skip it and it would still work.)
#    frame=[None, 0],
#    # What to add up as you go
#    cumulative_wh='sum(Wh)',
#    groupby=['night'],
#).encode(
#    x='x',
#    y=alt.Y('cumulative_wh:Q'),
#    color=alt.Color("night:O")
#)

#st.altair_chart(chart, use_container_width=True)

#
#st.markdown('## Daily Metrics')
#c1, c2, c3 = st.columns(3)
#
#chart_total_production = alt.Chart(df_all_max).mark_bar().encode(
#    x = alt.X("date", title='Date'),
#    y=alt.Y("24", title='Total Electricity Production in Wh'),
#)
#c1.altair_chart(chart_total_production, use_container_width=True)

#chart_production = alt.Chart(df_all[df_all['power'] != 0]).mark_boxplot(extent="min-max").encode(
#    x=alt.X("date:T", axis=alt.Axis(tickCount="day"), title='Date'),
#    y=alt.Y("power:Q", title='Electricity Production in W'),
#    color=alt.Color("date:O", legend=None)
#)
#c2.altair_chart(chart_production, use_container_width=True)

#chart_load = alt.Chart(df_all).mark_boxplot(extent="min-max").encode(
#    x=alt.X("date:T", axis=alt.Axis(tickCount="day"), title='Date'),
#    y=alt.Y("6:Q", title='Load in %'),
#    color=alt.Color("date:O", legend=None)
#)
#c3.altair_chart(chart_load, use_container_width=True)

#st.markdown('## Battery breakdown')
#b1, b2, b3 = st.columns(3)
#chart_voltage_time = alt.Chart(df_minute).mark_line().encode(
#    x=alt.X('x', axis=alt.Axis(
#        labelExpr="format((datum.value/60+17 <= 24) ? round(datum.value/60 + 17) : round(datum.value/60 - 6), '~s')+':00'"
#    )),
#    y=alt.Y('battery_voltage_smooth', scale=alt.Scale(zero=False)),
#    color=alt.Color("night:O", scale=alt.Scale(scheme='dark2'))
#)
#
#b1.altair_chart(alt.layer(chart_voltage_time), use_container_width=True)
#
#chart_load_time = alt.Chart(df_minute).mark_line().encode(
#    x=alt.X('x', axis=alt.Axis(
#        labelExpr="format((datum.value/60+17 <= 24) ? round(datum.value/60 + 17) : round(datum.value/60 - 6), '~s')+':00'"
#    )),
#    y=alt.Y('load', scale=alt.Scale(zero=False)),
#    color=alt.Color("night:O", scale=alt.Scale(scheme='dark2'))
#)
#
#b2.altair_chart(chart_load_time, use_container_width=True)
#
#
#chart_voltage_load = alt.Chart(df_minute).mark_line().encode(
#    x='load:Q',
#    y=alt.Y('battery_voltage_smooth', scale=alt.Scale(zero=False)),
#    color=alt.Color("night:O", scale=alt.Scale(scheme='dark2'))
#)
#
#b3.altair_chart(chart_voltage_load, use_container_width=True)



daily_refresh = 0
while True:
    today_filepath = os.path.join(DATA_FOLDERPATH, f'results_{datetime.now().date()}.csv')

    df_today = pd.read_csv(today_filepath)
    df_today['filepath'] = today_filepath

    #if daily_refresh == 10:
    #    df_all = df_all[df_all['filepath'] != today_filepath]
    #    df_all = prepare_df(pd.concat([df_all, df_today]))
    #    df_all_max = df_all.groupby('date', as_index=False).max()
    #    df_minute = prepare_df_minute(df_all)
    #    daily_refresh = 0


    output_load_rate = df_today['6'].iloc[-1]
    output_current = df_today['4'].iloc[-1]

    battery_capacity_rate = df_today['9'].iloc[-1]
    battery_voltage = round(df_today['7'].iloc[-1]/10, 1)

    input_current = round(df_today['18'].iloc[-1]/10, 1)
    input_voltage = round(df_today['15'].iloc[-1]/10, 1)

    production_today = df_today['24'].max()
    production_daily_mean = df_all_max['24'].mean()
    production_today_delta = round((production_today - production_daily_mean) / production_daily_mean * 100)

    current_power = round(input_current*input_voltage)
    previous_mean_power = (df_today.tail(20)['18'].map(lambda x: round(x/10, 1)) * df_today.tail(20)['15'].map(lambda x: round(x/10, 1))).mean()
    current_power_delta = 100
    if previous_mean_power != 0:
        current_power_delta = round((current_power - previous_mean_power) / previous_mean_power * 100)
    if previous_mean_power == 0 and current_power == 0:
        current_power_delta = 0

    with placeholder.container():
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

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
        kpi5.metric(
            label="Production today",
            value=f'{round(production_today/1000, 1)} kWh',
            delta=f'{production_today_delta} %'
        )
    continue

    time.sleep(2)
    daily_refresh += 1



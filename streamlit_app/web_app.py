import streamlit as st
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

from datetime import date, timedelta
import plotly.graph_objs as go
import plotly.express as px
from data_preparation import df_combined, tr, end

st.title('Stock dashboard')

# mothly transaction overview
mt = (
    tr.groupby(by=[pd.Grouper(key="Time", freq="M"), "action"])["action"]
    .count()
    .rename("transactions")
    .reset_index()
)  # montly transaction

fig = go.Figure()

# reformat the date_time to provide a monthly summary (do not show the date)
mt['mnth_yr'] = mt['Time'].apply(lambda x: x.strftime('%b-%Y'))

for action in ['buy', 'sell']:
    mt_ = mt.loc[mt['action'] == action]
    fig.add_trace(go.Bar(
        x=mt_.mnth_yr,
        y=mt_.transactions,
        name=action,
    ))

fig.update_layout(barmode='group', xaxis_tickangle=-45, title_text='monthly transactions overview',
                  yaxis=dict(
                      title='transaction counts',
                  ))
st.plotly_chart(fig)

# pie chart of portofolio composition
df_ = df_combined.loc[(df_combined['time_ts'] == end -
                       timedelta(1)) & (df_combined['no_shares'] > 0.25)]

fig = px.pie(df_, values='values', names='ticker')
st.plotly_chart(fig)

# line plot for portofolio time history
df_ = df_combined.pivot_table(index='time_ts', values=[
                                 'values', 'invested'], aggfunc='sum').reset_index()
df = px.data.stocks()

fig = px.line(df_, x="time_ts", y= ['values','invested'],
              hover_data={"time_ts": "|%B %d, %Y"},
              title='Overview'
             )

fig.update_xaxes(
    dtick="M1",
    tickformat="%b\n%Y")

st.plotly_chart(fig)

import streamlit as st
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

from datetime import date, timedelta
import plotly.graph_objs as go
import plotly.express as px
from data_preparation import data_preprocessing
import plotly.io as pio

pio.templates.default = 'plotly_white'
st.set_page_config(layout="wide")

# row0
row0_1, row0_spacer2, row0_2, row0_spacer3 = st.beta_columns(
    ( 2, .2, 1, .1))
row0_1.title('A stock portofolio dashboard')
st.markdown("This web app visulizes the personal transaction records on the trading platform [**Trading 212**](https://www.trading212.com). The charts in this dashboard are created to help a investor to better understand his/her portofile, at the same time gaining insights into personal investment style. To download transaction data from the trading platform, please refer to this [post](https://community.trading212.com/t/new-feature-export-your-investing-history/35612) for the instructions.")
st.markdown("**Disclaimner**: the uploaded file is not stored, nor shared. Should there be any concerns, it is adviced to first review the [scripts](https://github.com/jinchao-chen/portfolio-dashboard) before running the app. Alternatively, one can excecute this app locally.")

# upload the file
uploaded_file = st.file_uploader("Please select a csv file to upload. ")
if uploaded_file is not None:
    fln = uploaded_file
else:
    fln = "../data/dummy_transactions.csv"

# data pre-processing
df_combined, tr, start, end, data = data_preprocessing(fln)

df_agg = df_combined.pivot_table(index='time_ts', values=[
                                 'value', 'cum_total_eur', 'profit_eur'], aggfunc='sum').reset_index()
df_agg['realized_profit'] = df_agg['profit_eur'].cumsum()
df_agg['floating_profit'] = df_agg['value'] - df_agg['cum_total_eur']
last_row = df_agg.tail(1)

# row1
st.write('')
row1_space1, row1_1, row1_space2, row1_2, row1_space3 = st.beta_columns(
    (.1, 1, .1, 1, .1))
# line plot for portofolio time history
with row1_1:
    df = px.data.stocks()
    fig11 = px.line(df_agg, x="time_ts", y=['value', 'cum_total_eur'],
                    hover_data={"time_ts": "|%B %d, %Y"},
                    title='overview'
                    )

    fig11.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y")

    fig11.update_layout(hovermode="x")
    st.plotly_chart(fig11)
    st.write('')
    st.markdown("Up to {:}, you've invested **{:,.1f}** EUR on Trading 212.".format(
        end.strftime("%b %d, %Y"),
        last_row.cum_total_eur.values[0]))

with row1_2:
    fig12 = px.line(df_agg, x="time_ts", y=['floating_profit', 'realized_profit'],
                    hover_data={"time_ts": "|%B %d, %Y"},
                    title='profit and loss'
                    )

    fig12.add_trace(go.Scatter(
        name="total",
        x=df_agg["time_ts"], y=df_agg['floating_profit'] +
        df_agg['realized_profit'],
    ))

    fig12.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y")

    fig12.update_layout(hovermode="x")
    st.plotly_chart(fig12)

    st.write('')
    st.markdown("Up to {:}, you've invested **{:,.1f}** EUR on this platform. The total profit amounts to **{:,.1f}** EUR: the realized profit is **{:,.1f}** EUR while the floating profit is **{:,.1f}** EUR".format(
        end.strftime("%b %d, %Y"),
        last_row.cum_total_eur.values[0],
        last_row.floating_profit.values[0] + last_row.realized_profit.values[0],
        last_row.floating_profit.values[0],
        last_row.realized_profit.values[0]))
    if last_row.cum_total_eur.values[0]>0:
        st.markdown('Congratulations! Well done! :clap:')
    else:
        st.markdown('Not bad!')

# row2
st.write('')
row2_space1, row2_1, row2_space2, row2_2, row2_space3 = st.beta_columns(
    (.1, 1, .1, 1, .1))
# fig_1-1, mothly transaction overview
with row2_1:
    mt = (
        tr.groupby(by=[pd.Grouper(key="Time", freq="M"), "Action"])["Action"]
        .count()
        .rename("transactions")
        .reset_index()
    )  # montly transaction

    fig21 = go.Figure()
    mt['mnth_yr'] = mt['Time'].apply(lambda x: x.strftime('%b-%Y'))

    for action in ['buy', 'sell']:
        mt_ = mt.loc[mt['Action'] == action]
        fig21.add_trace(go.Bar(
            x=mt_.mnth_yr,
            y=mt_.transactions,
            name=action,
        ))

    fig21.update_layout(template='plotly_white',
                        barmode='group', xaxis_tickangle=-45, title_text='monthly transactions overview',
                        yaxis=dict(
                            title='transaction counts',
                        )
                        )
    st.plotly_chart(fig21)

# pie chart of portofolio composition
with row2_2:
    df_ = df_combined.loc[(df_combined['time_ts'] == (end -
                           timedelta(1)).floor('1d'))  & (df_combined['cum_shares'] > 0.25)]
    df_ = df_.drop_duplicates(
        subset=['time_ts', 'Ticker'], keep='last', inplace=False, ignore_index=False)

    fig22 = px.pie(df_, values='value', names='Ticker',
                   title='portofolio composition')
    st.plotly_chart(fig22)
    # fig22.update_layout(title='portofolio composition')

# row3
st.write('')
row3_space1, row3_1, row3_space2, row3_2, row3_space3 = st.beta_columns(
    (.1, 1, .1, 1, .1))

with row3_1:
    retscomp = data['Adj Close'].pct_change()
    corr = retscomp.corr()
    cols = df_.Ticker.dropna().unique()
    retscomp = data.loc[:, ('Adj Close', cols)].droplevel(0, axis=1)
    retscomp = retscomp.pct_change()
    corr = retscomp.corr()
    fig31 = go.Figure(data=go.Heatmap(
        z=corr,
        x=cols,
        y=cols,
        colorscale='Hot',
        reversescale=True,
        zmax=1.0,
        zmin=0.0))

    fig31.update_layout(title_text='stock correlation analysis',)

    st.plotly_chart(fig31)

with row3_2:
    fig32 = px.scatter(x=retscomp.mean(), y=retscomp.std(), text=cols)
    fig32.update_traces(textposition='top center')
    fig32.update_layout(
        #     height=800,
        title_text='return and Risk',
        xaxis_title="Return",
        yaxis_title="Risk",
    )
    st.plotly_chart(fig32)

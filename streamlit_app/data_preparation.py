import plotly.express as px
import plotly.graph_objs as go
from datetime import date, timedelta
from scr.utility import (
    plot_transactions,
    plot_transactions_2,
    read_ticker_ts,
    read_transactions,
)
from altair import datum
import yfinance as yf
import panel as pn
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta


def ticker_price_history(data, ticker):
    """filter time history of the specifed ticker, history of ticker close price """
    tts_sub = data[[('Close', ticker)]]  # ticker time series
    tts_sub = tts_sub.reset_index()
    tts_sub.columns = tts_sub.columns.droplevel()
    tts_sub.columns = ['time_ts', 'close_price']

    return tts_sub


def merge_histories(tr_sub, tts_sub, ticker):
    """merge dataframe based on date and time

    note: invested amount is determined based on the market price at close, rather than the transaction record
    """
    merged = tts_sub.merge(right=tr_sub, left_on='time_ts',
                           right_on='Time', how="outer")
    merged['cum_shares'] = merged['cum_shares'].fillna(method='ffill')
    merged['value'] = merged['close_price']*merged['cum_shares']
    merged['ticker'] = ticker
    merged['cum_total_eur'] = merged['cum_total_eur'].fillna(
        method='ffill')
    merged['value'] = merged['value'].fillna(
        method='ffill')
    return merged


def calculate_average_price(group):
    '''calculate the average price based on the invested value and floating number of shares'''

    # cumulative total in euro (buy price*share - average_price*sell)
    group['cum_total_eur'] = group['invested_eur'].cumsum()
    group['ave_price_eur'] = group['cum_total_eur']/group['cum_shares']

    return group


def calculate_return(group):
    """Update transaction time history, include calculation of average price
    """

    mask_buy = group["Action"] == 'buy'
    mask_sell = group["Action"] == 'sell'

    # determine the accumulated number of shares
    group.loc[mask_buy, 'action_sign'] = 1
    group.loc[mask_sell, 'action_sign'] = -1

    group['cum_shares'] = (group['No. of shares'] *
                           group['action_sign']).cumsum()

    # average price, treating all actions as buy
    group['pps_eur'] = group['Price / share'] / \
        group['Exchange rate'].astype('float')  # price per share in eur
    group['invested_eur'] = group['No. of shares']*group['pps_eur']
    group = calculate_average_price(group)

    # update the ave_price whenever a sell event occurs
    for idx, row in group[mask_sell].iterrows():
        group.loc[idx, 'invested_eur'] = -group.loc[idx,
                                                    'No. of shares']*group.loc[idx-1, 'ave_price_eur']
        group.loc[idx, 'ave_price_eur'] = group.loc[idx-1, 'ave_price_eur']
        group = calculate_average_price(group)

    # determine the return for each sell event
    group.loc[mask_sell, 'profit_eur'] = group.loc[mask_sell, 'pps_eur']*group.loc[mask_sell, 'No. of shares'] + \
        group.loc[mask_sell, 'invested_eur']

    return group


"""import and clean transaction data"""
fln = "../data/trasaction_history_18022021.csv"
tr = read_transactions(fln)

# keep only the most relavent columns
col_to_keep = ['Action', 'Time', 'Ticker', 'No. of shares', 'Price / share', 'Exchange rate',
               'Result (EUR)']
tr = tr[col_to_keep]
tr.loc[tr['Action'].str.contains("buy"), 'Action'] = 'buy'
tr.loc[tr['Action'].str.contains("sell"), 'Action'] = 'sell'
# tr_pivoted = tr.pivot_table(index=['Ticker', 'Time'],
#                             columns='action', values='No. of shares', dropna=False)

tr = tr.loc[tr['Action'].isin(['buy', 'sell'])]
grouped = tr.groupby(by='Ticker')

# feature engineering
groups = []

for name, group in grouped:
    group.reset_index(inplace=True, drop=True)
    group = calculate_return(group)
    groups.append(group)

tr = pd.concat(groups).reset_index(drop=True)

"""request time history from yahoo finance"""

# download the ts
tickers = tr.Ticker.dropna().unique()
tickers = tickers.tolist()
start = tr.Time.min()
end = tr.Time.max() + timedelta(1)
data = yf.download(tickers, start, end)

#  identify tickers not downloaded
ts_tickers = data.columns.droplevel(0).values
mask = data['Adj Close'].isna().mean() == 1.0
tickers_to_drop = mask.loc[mask].keys().values

# loop it through for all the tickers:
# loop it through for all the tickers:
dfs = []
groups = tr.groupby(by='Ticker')
ts_tickers = data.columns.droplevel(0).values

for ticker in tickers:
    if ticker not in tickers_to_drop:
        # share_no_history(tr_pivoted,ticker)
        tr_sub = groups.get_group(
            ticker)[['Time', 'Ticker', 'cum_shares', 'cum_total_eur', 'profit_eur']]
        tts_sub = ticker_price_history(data, ticker)
        df = merge_histories(tr_sub, tts_sub, ticker)

        dfs.append(df)
    else:
        print(f'{ticker} not in the database')

df_combined = pd.concat(dfs)
df_combined = df_combined.drop_duplicates(
    subset=['time_ts', 'ticker'], keep='last', inplace=False, ignore_index=False)
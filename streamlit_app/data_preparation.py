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


# determine number of shares for each day
def share_no_history(tr_pivoted, ticker):
    """determine the share no of each ticker through pivoting the transaction history
    """
    tr_sub = tr_pivoted.loc[ticker].dropna(
        subset=['buy', 'sell'], how='all').reset_index()
    tr_sub = tr_sub.sort_values('Time')
    tr_sub.rename({'Time': 'time_tr'}, axis=1, inplace=True)
    tr_sub.drop(['Deposit', 'Dividend (Ordinary)',
                 'Withdrawal'], axis=1, inplace=True)
    return tr_sub


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
                           right_on='time_tr', how="outer")
    # , inplace=True, subset = ['buy', 'sell'], how = 'all')
    merged[['buy', 'sell']] = merged[['buy', 'sell']].fillna(0)
    merged['no_shares'] = (merged['buy']-merged['sell']).cumsum()
    merged['invested'] = (merged['close_price'] *
                          (merged['buy']-merged['sell'])).cumsum()
    merged['values'] = merged['close_price']*merged['no_shares']
    merged['ticker'] = ticker
    return merged


"""import transaction data"""
fln = "../data/trasaction_history_18022021.csv"
tr = read_transactions(fln)
tr_pivoted = tr.pivot_table(index=['Ticker', 'Time'],
                            columns='action', values='No. of shares', dropna=False)

"""request time history from yahoo finance"""
tickers = tr.Ticker.dropna().unique()
tickers = tickers.tolist()

start = tr.Time.min()
end = tr.Time.max() + timedelta(1)

data = yf.download(tickers, start, end)
# loop it through for all the tickers:

dfs = []

for ticker in tickers:
    tr_sub = share_no_history(tr_pivoted, ticker)
    tts_sub = ticker_price_history(data, ticker)
    df = merge_histories(tr_sub, tts_sub, ticker)

    dfs.append(df)

df_combined = pd.concat(dfs)

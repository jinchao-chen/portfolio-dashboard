from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import panel as pn
import yfinance as yf
from altair import datum
import sys

from scr.utility import plot_transactions, read_ticker_ts
from scr.utility import plot_transactions_2
from scr.utility import read_transactions

def get_figures():
    
    alt.renderers.enable("default")
    pn.extension("vega")

    fln = "./data/trasaction_history_18022021.csv"
    transactions = read_transactions(fln)
    transactions.Ticker.unique()
    
    ticker = 'DIS'
    subset = transactions[transactions["Ticker"] == ticker]
    ts = read_ticker_ts(ticker=ticker, start= '2020-5-1', end='2021-03-01')


    chart_1 = plot_transactions(subset, ts)
    chart_2 = plot_transactions_2(subset, ts)
    chart_3 = plot_transactions(subset, ts)
    chart_4 = plot_transactions_2(subset, ts)
    chart_5 = plot_transactions(subset, ts)
    
    return [chart.to_json() for chart in [chart_1, chart_2, chart_3, chart_4]]


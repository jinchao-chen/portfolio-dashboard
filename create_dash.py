from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import panel as pn
import yfinance as yf
from altair import datum
from utility import *
import sys
alt.renderers.enable("default")
pn.extension("vega")

fln = "trasaction_history_18022021.csv"
transactions = read_transactions(fln)

# hide
title = '# Trading Dashboard'
subtitle = 'A personalized visualization tool for **Trading 212** trading transactions and market data'

companies = transactions["Ticker"].dropna().unique().tolist()
ticker = pn.widgets.Select(name="Company", options=companies)
style = pn.widgets.Select(name="Plot Style", options=[
                            "Candelstick", "Line"])

# this creates the date range slider
date_range_slider = pn.widgets.DateRangeSlider(
    name="Date Range",
    start=datetime(2020, 1, 1),
    end=datetime.today(),
    value=(datetime(2020, 1, 1), datetime.today()),
)

# tell Panel what your plot "depends" on.
@pn.depends(ticker.param.value, date_range_slider.param.value, style.param.value)
def get_plots(ticker, date_range, style):  # start function

    # filter based on ticker
    subset = transactions[transactions["Ticker"] == ticker]

    start_date = date_range_slider.value[
        0
    ]  # store the first date range slider value in a var
    end_date = date_range_slider.value[1]  # store the end date in a var

    ts = read_ticker_ts(ticker=ticker, start=start_date, end=end_date)

    if style == "Candelstick":
        chart = plot_transactions(subset, ts)
    else:
        chart = plot_transactions_2(subset, ts)

    return chart

dashboard = pn.Row(
    pn.Column(title, subtitle, ticker, style, date_range_slider),
    get_plots,  # draw chart function!
)
# print('ss')
dashboard.servable()

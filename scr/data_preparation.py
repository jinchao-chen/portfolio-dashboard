from datetime import date, datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import panel as pn
import plotly.express as px
import plotly.graph_objs as go
import yfinance as yf
from altair import datum

from scr.utility import read_ticker_ts, read_transactions

def ticker_price_history(data, ticker):
    """filter time history of the specifed ticker, history of ticker close price """
    tts_sub = data[[("Close", ticker)]]  # ticker time series
    tts_sub = tts_sub.reset_index()
    tts_sub.columns = tts_sub.columns.droplevel()
    tts_sub.columns = ["time_ts", "close_price"]

    return tts_sub


def merge_histories(tr_sub, tts_sub, ticker, df_forex):
    """merge dataframe based on date and time

    note: invested amount is determined based on the market price at close, rather than the transaction record
    """
    merged = tts_sub.merge(
        right=tr_sub, left_on="time_ts", right_on="Time", how="outer"
    )
    merged = merged.merge(df_forex, left_on="time_ts", right_on="date")
    merged["cum_shares"] = merged["cum_shares"].fillna(method="ffill")
    merged["value"] = merged["close_price"] * merged["cum_shares"] * merged["rate"]
    merged["ticker"] = ticker
    merged["cum_total_eur"] = merged["cum_total_eur"].fillna(method="ffill")
    merged["value"] = merged["value"].fillna(method="ffill")
    return merged


def calculate_average_price(group):
    """calculate the average price based on the invested amount and number of shares"""

    # cumulative total in euro (buy price*share - average_price*sell)
    group["cum_total_eur"] = group["invested_amount_eur"].cumsum()
    group["ave_price_eur"] = group["cum_total_eur"] / group["cum_shares"]

    return group


def calculate_return(group):
    """Update transaction time history, include calculation of average price
    """

    mask_buy = group["Action"] == "buy"
    mask_sell = group["Action"] == "sell"

    # determine the accumulated number of shares
    group.loc[mask_buy, "action_sign"] = 1
    group.loc[mask_sell, "action_sign"] = -1
    group["cum_shares"] = (group["No. of shares"] * group["action_sign"]).cumsum()

    # average price, treating all actions as buy
    group["pirce_per_share_eur"] = group["Price / share"] / group["Exchange rate"].astype(
        "float"
    )  # price per share in eur
    group["invested_amount_eur"] = group["No. of shares"] * group["pirce_per_share_eur"]
    group = calculate_average_price(group)

    # update the ave_price whenever a sell event occurs
    for idx, row in group[mask_sell].iterrows():
        group.loc[idx, "invested_amount_eur"] = (
            -group.loc[idx, "No. of shares"] * group.loc[idx - 1, "ave_price_eur"]
        )
        group.loc[idx, "ave_price_eur"] = group.loc[idx - 1, "ave_price_eur"]
        group = calculate_average_price(group)

    # determine the return for each sell event
    group.loc[mask_sell, "profit_eur"] = (
        group.loc[mask_sell, "pirce_per_share_eur"] * group.loc[mask_sell, "No. of shares"]
        + group.loc[mask_sell, "invested_amount_eur"]
    )

    return group

def feature_engineering(tr): 
    # feature engineering, calcuate return for each ticker
    tr_grouped = tr.groupby(by="Ticker")
    groups = []

    for name, group in tr_grouped:
        group.reset_index(inplace=True, drop=True)
        group = calculate_return(group)
        groups.append(group)

    tr = pd.concat(groups).reset_index(drop=True)
    
    return tr

def data_preprocessing(fln):
    # import and clean transaction data
    tr = read_transactions(fln)
    tr = feature_engineering(tr)
    # download the ts for the tickers from yahoo finance
    tickers = tr.Ticker.dropna().unique()
    tickers = tickers.tolist()
    start = tr.Time.min()
    end = tr.Time.max() + timedelta(1)
    data = yf.download(tickers, start, end)

    # download forex data
    df_forex = yf.download(["USDEUR%3DX"], start, end)[["Adj Close"]]
    df_forex = df_forex.reset_index()
    df_forex.rename({"Date": "date", "Adj Close": "rate"}, axis=1, inplace=1)

    #  identify tickers not downloaded
    ts_tickers = data.columns.droplevel(0).values
    mask = data["Adj Close"].isna().mean() == 1.0
    tickers_to_drop = mask.loc[mask].keys().values

    # loop through all the tickers:
    dfs = []
    groups = tr.groupby(by="Ticker")
    ts_tickers = data.columns.droplevel(0).values

    for ticker in tickers:
        if ticker not in tickers_to_drop:
            # share_no_history(tr_pivoted,ticker)
            tr_sub = groups.get_group(ticker).copy()[
                [
                    "Time",
                    "Ticker",
                    "Action",
                    "No. of shares",
                    "cum_shares",
                    "cum_total_eur",
                    "profit_eur",
                ]
            ]
            tr_sub["Time"] = tr_sub["Time"].dt.floor("d")
            tts_sub = ticker_price_history(data, ticker)
            df = merge_histories(tr_sub, tts_sub, ticker, df_forex)

            dfs.append(df)
        else:
            print(f"{ticker} not in the database")

    df_combined = pd.concat(dfs)
    df_combined = df_combined.drop_duplicates(
        subset=["time_ts", "ticker"], keep="last", inplace=False, ignore_index=False
    )

    return df_combined, tr, start, end, data

if __name__ =='__main__':
    data_preprocessing("./data/dummy_transactions.csv")
    print('voila')

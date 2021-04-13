from datetime import datetime, timedelta

import altair as alt
import numpy as np
import pandas as pd
import panel as pn
import yfinance as yf
from altair import datum


def action_direction(action):
    """To simplify the modelling, I wont't differentiate 'market sell/buy' or  'limit sell/buy'

    Args:
        action (str): trading activity, possible values ('market sell', 'limit sell', ect.)

    Returns:
        (str): actions renamed, strip off non-necessary information
    """
    if "buy" in action:
        return "buy"
    elif "sell" in action:
        return "sell"
    else:
        return action
    
def read_transactions(fln):
    """Read transaction *csv file downloaded from trading212.com. 

    how to download the transaction history is available here: https://community.trading212.com/t/new-feature-export-your-investing-history/35612


    Args:
        fln (str): csv file name 

    Returns:
        transaction (pd.Dataframe): 
    """
    # dateparse = lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M")
    transactions = pd.read_csv(
        fln, parse_dates=["Time"]
    )
    # transactions["textof"] = "➟"
    # transactions["Time"] = transactions["Time"].dt.floor("d")
    transactions["action"] = transactions["Action"].apply(lambda x: action_direction(x))

    return transactions

def read_ticker_ts(ticker, start, end):
    """Read the trading history through yfinance API, for the specified ticker. Note that the time history is provided for timezone (GMT)

    Args:
        ticker ([type]): [name of the stock, eg apple: APPL]
        start ([type]): [description]
        end ([type]): [description]

    Returns:
        [type]: [description]
    """
    ticker = yf.Ticker(ticker)
    ts = ticker.history(start=start, end=end, interval="1d", tz="GMT")
    ts.reset_index(inplace=True)
    ts.columns = [x.lower() for x in ts.columns]  # Rename the columns using lower case

    if not ts.empty:
        ts["date"] = ts["date"].dt.floor("d")
    return ts

# base plot

def plot_transactions(subset, ts):
    """[summary]

    Args:
        subset ([type]): [description]
        ts ([type]): [description]
    """
    open_close_color = alt.condition(
        "datum.open <= datum.close", alt.value("#06982d"), alt.value("#ae1325")
    )

    base = (
        alt.Chart(ts).encode(
            alt.X(
                "date:T", axis=alt.Axis(format="%y/%m/%d", labelAngle=-45, title="Date")
            ),
            color=open_close_color,
        ).properties(width=400, height=300)
    )

    rule = base.mark_rule().encode(
        alt.Y("low:Q", title="Price", scale=alt.Scale(zero=False),), alt.Y2("high:Q")
    )

    bar = base.mark_bar(size=2).encode(alt.Y("open:Q"), alt.Y2("close:Q")).interactive()

    # add annotation for action undertook
    annotation = (
        alt.Chart(subset)
        .mark_text(align="left", baseline="middle", fontSize=10, dx=7)
        .encode(
            x=alt.X(
                "Time",
                axis=alt.Axis(
                    format="%y/%m/%d",
                    labelAngle=0,
                    #               title='Date'
                ),
            ),
            y="Price / share",
            text="label:N",
            color="action",
        )
        .transform_calculate(label='datum.action + " " + datum["No. of shares"]')
    )

    # add the markers
    text = (
        alt.Chart(subset)
        .mark_text(dx=0, dy=0, angle=90, fontSize=14)
        .encode(
            x=alt.X(
                "Time",
                axis=alt.Axis(
                    format="%y/%m/%d",
                    labelAngle=-45,
                    #               title='Date'
                ),
            ),
            y="Price / share",
            text="textof",
            color="action",
        )
    )

    return rule + bar + annotation + text

def plot_transactions_2(subset, ts):

    # Add selection bar
    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["date"], empty="none"
    )

    # The basic line
    line = (
        alt.Chart(ts)
        .mark_line(interpolate="basis")
        .encode(
            x=alt.X(
                "date:T",
                axis=alt.Axis(
                    format="%y/%m/%d",
                    labelAngle=0,
                    #               title='Date'
                ),
            ),
            y="close:Q",
        ).properties(width=400, height=300)
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = (
        alt.Chart(ts)
        .mark_point()
        .encode(x="date:T", opacity=alt.value(0),)
        .add_selection(nearest)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text_close = line.mark_text(align="left", dx=5, dy=-5).encode(
        text=alt.condition(nearest, "close:Q", alt.value(""), format=",.2f")
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(ts)
        .mark_rule(color="gray")
        .encode(x="date:T",)
        .transform_filter(nearest)
    )

    # add marker for the actions undertook
    markers = (
        alt.Chart(subset)
        .mark_circle(color="action", filled=True)
        .encode(x="Time:T", y="Price / share:Q")
    )

    # add annotation for action undertook
    annotation = (
        alt.Chart(subset)
        .mark_text(align="left", baseline="middle", fontSize=10, dx=7)
        .encode(
            x=alt.X(
                "Time",
                axis=alt.Axis(
                    format="%y/%m/%d",
                    labelAngle=-45,
                    #               title='Date'
                ),
            ),
            y="Price / share",
            text="label:N",
            color="action",
        )
        .transform_calculate(label='datum["No. of shares"]')
    )

    return line + selectors + points + text_close + rules + annotation + markers
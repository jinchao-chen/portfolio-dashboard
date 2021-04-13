import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots

from scr.data_preparation import data_preprocessing

pio.templates.default = "plotly_white"
st.set_page_config(layout="wide")

# row0
row0_1, row0_spacer2, row0_2, row0_spacer3 = st.beta_columns((2, 0.2, 1, 0.1))
row0_1.title("A stock portfolio dashboard")
st.markdown(
    "This web application works to visualize the personal transactions executed on the trading platform [**Trading 212**](https://www.trading212.com). The charts are created to help you better understand your portfolio, and at the same time gain some insights into your personal investment style. To download transaction data from the trading platform, please refer to this [post](https://community.trading212.com/t/new-feature-export-your-investing-history/35612) for the instructions."
)
st.markdown(
    "**Disclaimer**: the uploaded file is not stored, nor shared. Should there be any concerns, it is advised to first review the [scripts](https://github.com/jinchao-chen/portfolio-dashboard) before running the app. Alternatively, you can set it up and execute this app locally on your own computer."
)


#"""data pre-processing"""

uploaded_file = st.file_uploader("Please select a csv file to upload. ")
if uploaded_file is not None:
    fln = uploaded_file
else:
    fln = "./data/dummy_transactions.csv"

df_combined, tr, start, end, data = data_preprocessing(fln)
df_combined = df_combined.rename(
    {"time_ts": "time", "value": "open position",
        "cum_total_eur": "invested amount", },
    axis=1,
)
df_agg = df_combined.pivot_table(
    index="time",
    values=["open position", "invested amount", "profit_eur"],
    aggfunc="sum",
).reset_index()
df_agg["realized profit"] = df_agg["profit_eur"].cumsum()
df_agg["floating profit"] = df_agg["open position"] - df_agg["invested amount"]
last_row = df_agg.tail(1)

# row1
st.write("")
row1_space1, row1_1, row1_space2, row1_2, row1_space3 = st.beta_columns(
    (0.1, 1, 0.1, 1, 0.1)
)

# line plot for portfolio time history
with row1_1:
    fig = px.line(
        df_agg,
        x="time",
        y=["open position", "invested amount",
            "floating profit", "realized profit"],
        hover_data={"time": "|%B %d, %Y"},
        title="profit and loss",
    )

    fig.update_xaxes(dtick="M1", tickformat="%b\n%Y")
    fig.update_yaxes(title_text="EUR")

    fig.update_layout(hovermode="x")
    st.plotly_chart(fig)

    st.write("")
    st.markdown(
        "Up to {:}, you've invested **{:,.1f}** EUR on this platform. The total profit amounts to **{:,.1f}** EUR: the realized profit is **{:,.1f}** EUR while the floating profit is **{:,.1f}** EUR".format(
            (end).strftime("%b %d, %Y"),
            last_row["invested amount"].values[0],
            last_row["floating profit"].values[0]
            + last_row["realized profit"].values[0],
            last_row["realized profit"].values[0],
            last_row["floating profit"].values[0],
        )
    )
    if last_row["realized profit"].values[0] > 0:
        st.markdown("Congratulations! Well done! :clap:")
    else:
        st.markdown("Not bad!")
    st.markdown(
        "*note: profit and loss calculation includes only US listed stock. Your actual profit/loss may vary, depending on the portion of non-US listed*"
    )

with row1_2:
    df_ = df_combined.loc[
        (df_combined["time"] == (end - timedelta(1)).floor("1d"))
        & (df_combined["cum_shares"] > 0.25)
    ]
    df_ = df_.drop_duplicates(
        subset=["time", "ticker"], keep="last", inplace=False, ignore_index=False
    )

    fig = px.pie(
        df_, values="open position", names="ticker", title="portfolio composition"
    )
    st.plotly_chart(fig)

    tickers_sorted = df_.sort_values(
        by="open position", ascending=False).ticker.values
    st.markdown(
        "**{:}** has the heaviest weight in your current portfolio, followed by {:} ".format(
            tickers_sorted[0], ", ".join(tickers_sorted[1:5])
        )
    )

# row2
st.write("")
row2_space1, row2_1, row2_space2, row2_2, row2_space3 = st.beta_columns(
    (0.1, 1, 0.1, 1, 0.1)
)

# fig_2-1, monthly transaction overview
with row2_1:
    mt = (
        tr.groupby(by=[pd.Grouper(key="Time", freq="M"), "Action"])["Action"]
        .count()
        .rename("transactions")
        .reset_index()
    )  # monthly transaction

    fig = go.Figure()
    mt["mnth_yr"] = mt["Time"].apply(lambda x: x.strftime("%b-%Y"))

    for action in ["buy", "sell"]:
        mt_ = mt.loc[mt["Action"] == action]
        fig.add_trace(go.Bar(x=mt_.mnth_yr, y=mt_.transactions, name=action,))

    fig.update_layout(
        template="plotly_white",
        barmode="group",
        xaxis_tickangle=-45,
        title_text="monthly transactions overview",
        yaxis=dict(title="transaction counts",),
    )
    st.plotly_chart(fig)

    # include some statistics about the transactions
    start_date = tr.Time.min().strftime("%b %d, %Y")
    end_date = tr.Time.max().strftime("%b %d, %Y")
    total_orders = mt.transactions.sum()
    buy_orders = mt.loc[mt["Action"] == "buy"].transactions.sum()
    sell_orders = mt.loc[mt["Action"] == "sell"].transactions.sum()
    most_frequent_month = mt.groupby(
        by="mnth_yr")["transactions"].sum().idxmax()
    most_frequent_count = mt.groupby(by="mnth_yr")["transactions"].sum().max()

    def diff_month(d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    diff_month = diff_month(tr.Time.max(), tr.Time.min())
    monthly_orders = total_orders / (diff_month + 1)
    # st.markdown('During the selected period, in total ')
    st.markdown(
        f"Between {start_date:} and {end_date:}, you executed in total **{total_orders:0.0f}** orders: {buy_orders:0.0f} buying and {sell_orders:0.0f} selling orders. In average, you sell and buy **{monthly_orders:0.1f}** times each month. {most_frequent_month:} is the month with the most frequent transactions, reaching {most_frequent_count:} orders."
    )  #

# fig_2-2 chart of distribution over the day and week
with row2_2:
    day_names = tr.Time.dt.day_name()
    hours = tr.Time.round("1h").dt.time

    fig = go.Figure()

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["distribution over the day",
                        "distribution over the week"],
    )

    m = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    fig.add_trace(go.Histogram(
        x=sorted(day_names, key=m.index),), row=1, col=1)
    fig.update_xaxes(title_text="day of a week", row=1,
                     col=1, tickformat="%H-%M-%S")
    fig.update_yaxes(title_text="counts", row=1, col=1)

    fig.add_trace(go.Histogram(x=sorted(hours),), row=1, col=2)
    fig.update_xaxes(title_text="time of day", row=1,
                     col=2, tickformat="%H:%M")
    fig.update_yaxes(title_text="counts", row=1, col=2)

    fig.update_layout(bargap=0.2)
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig)

    st.markdown(
        f"You are more likely to trade on **{day_names.value_counts().idxmax()}** than the rest of the week. When looking at the distribution over the day, **{hours.value_counts().idxmax():%H} o'clock(GMT)** is the peak hour for you to place an order."
    )


# row3
st.write("")
row3_space1, row3_1, row3_space2, row3_2, row3_space3 = st.beta_columns(
    (0.1, 1, 0.1, 1, 0.1)
)

with row3_1:
    retscomp = data["Adj Close"].pct_change()
    corr = retscomp.corr()
    cols = df_.ticker.dropna().unique()
    retscomp = data.loc[:, ("Adj Close", cols)].droplevel(0, axis=1)
    retscomp = retscomp.pct_change()
    corr = retscomp.corr()
    fig31 = go.Figure(
        data=go.Heatmap(
            z=corr,
            x=cols,
            y=cols,
            colorscale="Hot",
            reversescale=True,
            zmax=1.0,
            zmin=0.0,
        )
    )

    fig31.update_layout(title_text="stock correlation analysis",)

    st.plotly_chart(fig31)

    most_correlated = corr.unstack().sort_values(
        ascending=False).drop_duplicates().index[1]
# print(*most_correlated)
    st.markdown('The correlation measures how the price of one stock moves in relation to the other. Knowing the correlation will help us understand whether the return of one stock is affected by other stocks. In the chart, the darker the color the more correlated are the two stocks, i.e. the pair is more likely to move in the same direction. In your portfolio, {:} and {:} is the most correlated pair.'.format(
        *most_correlated))
    st.markdown(
        'If you are interested in the technical background, please refer to this [post](https://towardsdatascience.com/in-12-minutes-stocks-analysis-with-pandas-and-scikit-learn-a8d8a7b50ee7)')

with row3_2:
    fig32 = px.scatter(x=retscomp.mean(), y=retscomp.std(), text=cols)
    fig32.update_traces(textposition="top center")
    fig32.update_layout(
        #     height=800,
        title_text="return and Risk",
        xaxis_title="Return",
        yaxis_title="Risk",
    )
    st.plotly_chart(fig32)
    max_ratio = (retscomp.mean()/retscomp.std()).index[0]
    st.markdown(
        'In this chart, the stocks are measured in two dimensions: return and risk. In your portfolio, {:} has the largest return and risk ratio. If interested in the technical details, please refer to this [post](https://towardsdatascience.com/in-12-minutes-stocks-analysis-with-pandas-and-scikit-learn-a8d8a7b50ee7).'.format(max_ratio))

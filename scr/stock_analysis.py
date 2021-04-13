from data_preparation import data


# correlation analysis
st.plotly_chart(fig22)
retscomp = data['Adj Close'].pct_change()
corr = retscomp.corr()
cols = df_end.Ticker.dropna().unique()
retscomp = data.loc[:, ('Adj Close', cols)].droplevel(0, axis =1)
retscomp = retscomp.pct_change()
corr = retscomp.corr()
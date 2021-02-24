[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jinchao-chen/portfolio-dashboard/HEAD)

# portfolio-dashboard

This packages creates a dashboard for trading212 trading activities. 

## how to set up


- download the transaction history from Trading212. It is explained in this [post](https://community.trading212.com/t/new-feature-export-your-investing-history/35612) on how to download it in 'csv' format.
- replace <code>fln = "dummy_transactions.csv"</code> in 'main.py' with the name of your downloaded file
- deploy locally from command line by running <code>panel serve main.py</code>

You could as well have a try of the dashboard through [binder](https://mybinder.org/v2/gh/jinchao-chen/portfolio-dashboard/HEAD)

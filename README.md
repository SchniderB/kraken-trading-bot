# Instructions to use a Python trading bot with Kraken

## Aim of the project
This project presents how to make and run a trading bot coded fully in Python based on Kraken's API. The trading bot should 
be able to buy and sell a predefined list of cryptocurrencies for you on your Kraken's account. The trading bot should 
buy cryptocurrencies when the price is low and sell them when it is high. The trading algorithm is simply based on the price 
history and does not include external indicators. The trading is based on a single base currency fiat, such as the Euro, 
and does not swap directly coins between each other.

## Disclaimer
This is an educational project, not a real investment strategy or advice, and I will not take any responsibility for any 
money loss or deviant use of my code. If you decide to use my code, please make sure you never share your API keys with 
anyone and never activate the fund withdrawal option. Please note that the algorithm only performs well during bullish 
times because of the high daily price fluctuations, which it can exploit on a regular basis, I strongly advise not to use 
it at the end of a bull run as it will likely buy overpriced cryptocurrencies.

## Dependencies
### Requirements
- Python 3.6 or Higher
- Kraken's Python API client `krakenex` (set-up described below)
- Kraken's API key with balance reading permission
- Kraken's API key with the permission to create, modify and delete buy and sell orders
- Script `crypto_wrapper.py`
- Folder `data`
- Configuration file `config.txt` in the folder `data`

### First set-up
1. Download `virtualenv` if you do not alread have it
```bash
pip install virtualenv
```
2. Create virtual environment in your folder of interest
```bash
virtualenv krakenex
```
3. Activate the virtual environment
```bash
source krakenex/bin/activate
```
4. Install the libraries of interest in the virtual environment based on the `requirements.txt` file
```bash
pip install -r requirements.txt
```

### Re-activate virtual environment every time you need to extract data
```bash
source krakenex/bin/activate
```

## Account permission
### Balance reading API key
You will need a first API key from your Kraken account with ONLY (!IMPORTANT!) balance reading permission. The public and 
secret keys should be stored each on one line in a local file called `balance_query.key`. The process to generate the key can 
be found directly in Kraken's FAQs and tutorials which are quite clear and simple.

### Order API key
You will need a second API key from your Kraken account with ONLY (!IMPORTANT!) the permissions to create, modify and 
delete buy and sell orders. The public and secret keys should be stored each on one line in a local file called `order.key`. 

## Settings and requirements
### Fiat base currency selection
You will need to specify the fiat base currency as the value of the variable `base_currency` in the script `crypto_wrapper.py` 
which is set to `ZEUR` by default which stands for the Euro.

### List of cryptocurrencies
You can define the list of cryptocurrencies you want the trading bot to speculate on with the variable `currencies` in the 
script `crypto_wrapper.py`.

### Minimal balance
The trading bot my not work if your dedicated total balance is inferior to 100 EUR / USD.

### Configuration file
The configuration file can be used with different parameters. The parameters should be separated from their values with a 
tab. Here is how the parameters can be used:
* `RECOVER`: If the value is set to `YES`, the script will look into the folder `data` to recover your trading history and 
continue to trade based on this history. Any other value, will be considered as a no, and will ignore the files in the folder 
`data`, but the trading bot will not delete the data in this folder and will not override these files either
* `DECISION`: If you want to manually affect the decision of the trading bot, you can choose two options:
  * `PREVENT_BUY_ADA`: Prevent the trading bot from buying the cryptocurrency with the symbol `ADA` as long as the parameter 
  value is given in the config file
  * `COND_BUY_ADA`: Prevent the trading bot from buying the cryptocurrency with the symbol `ADA` except if its price drops 
  of more than 10% of the median price of the cryptocurrency

The default content of the file `config.txt` is the following:
```bash
RECOVER	YES
DECISION	NONE
```

### Default algorithm settings
The following settings were optimized based on a programmatic algorithm training on the historical data of several cryptocurrencies:
- `drop_rate`: Price drop percentage value over a `drop_time_frame` that will trigger a buy order. Default 0.02 (i.e. 2%)
- `drop_time_frame`: Time frame on which the price drop is assessed, e.g. a `drop_rate` of 2% will trigger the buy condition 
only if the price dropped of at least 2% on this specified period of time. Default 120 (i.e. 2 hours)
- `end_tendency`: A price dropping tendency will be considered over after the price raised of this specific percentage. 
Default 2%. E.g. if the price drops for a while and then increases of 2%, the dropping tendency will be considered as finished. 
- `min_benef`: The trading bot will only sell a cryptocurrency if it made this percentage of benefit. Default 1.08 (i.e. 8%)
- `history_regression`: Time frame on which the price trend and direction is assessed, default 120 (i.e. 2 hours)
- `emergency_drop`: Defines the emergency drop rate, this parameter is only relevant if the manual instruction `COND_BUY_`
  (describe above) is used


## Launch the cryptocurrency trading bot
A simple Python command will launch the trading bot:
```bash
python3 crypto_wrapper.py
```
As the trading bot will run indefinitely, we recommend you run it in a detached terminal state. You can use the terminal 
multiplexer `Screen` for this purpose.


## Results
### Output files
- `$symbol_records.txt`: The file with every decision, i.e. `WAIT`, `buy` or `sell`, and price statistics for each individual 
cryptocurrency symbol will be stored in the folder `data`
- `$symbol_last_activity.txt`: The last buy or sell trade of the concerned cryptocurrency symbol will be stored in this file

### Performances
The algorithm generated a benefit superior to +100% during the last bull run, by regularly buying and selling. It then remained 
stuck with cryptocurrencies bought at very high prices at the end of the bull run. The optimal strategy for this algorithm 
would be to launch it 1 year after the end of the bull run and to stop it before the end of the bull run and manually sell 
all the remaining cryptocurrencies.

## Project Timeline
- Start Date: July 2020
- Completion Date: December 2020
- Maintenance status: Inactive
# -*- coding: utf-8 -*-
"""
This script is a wrapper that runs all the functions that constitute the trading
bot.

Created on Sat Jul 20 15:28:53 2020

@author: boris
"""

#### Import built-in and third-party modules and packages ####
import krakenex
import os
import decimal
import time
import datetime
import statistics
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
####

#### Import home-made modules and packages ####
from tradingbot import *
# import API.update_database  # Module to write the trading results into a local database
####

#### Function that computes linear regression ####
def compute_linear_regression(t, price, tstime):
    """
    Function that computes the slope, the mean squared error and the coefficient of
    determination of a linear regression fitted on the evolution of the price in function
    of the time.
    """
    t = np.array(t).reshape((-1, 1))
    price = np.array(price)
    future_time = np.array([tstime, tstime+60]).reshape((-1, 1))  # Need a list for the price prediction but using only the first element
    # Create linear regression object
    regr = linear_model.LinearRegression()

    # Train the model using the training sets
    regr.fit(t, price)

    # Make predictions using the testing set
    future_prices = regr.predict(future_time)

    # Return the results of the statistics
    return future_prices[0]  # regr.coef_  # mean_squared_error(future_time, future_prices), r2_score(future_time, future_prices)
####

#### Pre-defined parameters based on the benchmark results ####
drop_rate = 0.02
drop_time_frame = 120
end_tendency = 1.02
min_benef = 1.08
history_regression = 120
emergency_drop = 0.1
####

#### Define base variables and instanciate classes ####
currencies = ["XXBT", "XETH", "XMLN", "ADA", "XXLM", "DOT"]
base_currency = "ZEUR"
sum_to_invest = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20]  # Fraction of the total balance to invest per crypto
price_last_decision = {currency:[] for currency in currencies}  # simple memory of the last price and volume, contains ["decision", closing, volume, fee]
history = {currency:[] for currency in currencies}  # operation history
funds = dict()
distrib_info = {currency:[False, 10**7, 0] for currency in currencies}  # Will respectively replace the variables isDropping, min_price, max_price to store each value per crypto
k = krakenex.API()
get_info = query_public_info.Query_public_info()
query_rate = currency_rates.Query_price()
perform_order = order_close.Make_order()
utilities = utilities.Utilities()
# update = API.update_database.Update_DB()  # Module to write the trading results into a local database
####

#### Recovery system and write output file ####
list_data = os.listdir("data/")
with open("data/config.txt", "r") as config:
    recover = config.readline().rstrip("\n").rstrip("\r").split("\t")[1].lower()
if recover == "yes":  # If recovery mode is activated by specifying YES in the config file
    for file in list_data:
        if "last_activity" in file:
            currency = file.split("_")[0]
            with open("data/{}".format(file), "r") as f:
                price_last_decision[currency] = f.readline().rstrip("\n").split("\t")[:4]  # Time is not included
                price_last_decision[currency][1] = float(price_last_decision[currency][1])
                price_last_decision[currency][2] = float(price_last_decision[currency][2])
                price_last_decision[currency][3] = float(price_last_decision[currency][3])
else:  # If recovery mode is not activated
    list_data.remove("config.txt")
    if not list_data:  # Only write if no files are present to avoid overwriting
        for currency in currencies:
            with open("data/{}_records.txt".format(currency), "w") as balance_file:
                balance_file.write("round\ttime\toperation\torder_price\tdecimal\tfee\tmin_order_volume\tvolume_to_invest\t{0}_balance\t{1}_balance\t{1}_rate\tbenefit\tclosed_order_name\n".format(base_currency, currency))
    else:
        print("ERROR: data folder not empty. Please empty the folder or add the file recovery.txt to start in recovery mode.")
        exit()
####

#### Get all the currency pair names ####
all_pairs = get_info.get_all_info_assetPairs()["result"].keys()
####

#### Generate history for all currencies ####
for i, currency in enumerate(currencies):
    pair = "{}{}".format(currency, base_currency)  # Define currency pair
    if pair not in all_pairs:  # if pair does not exist, try something different
        pair = "{}{}".format(currency, base_currency.lstrip("Z"))
    OHLC = k.query_public("OHLC", data = {'pair': pair, 'since': time.time()-(history_regression-10)*60, 'interval': 1})
    if utilities.is_error(OHLC, currency):  # If error occurs while querying info, write it
        continue  # Cannot start the investment loop if an error occurred here
    else:
        for data_point in OHLC["result"][pair]:
            history[currency].append([0, datetime.datetime.fromtimestamp(float(data_point[0])), "WAIT", float(data_point[4]), "NA", "NA", "NA", "NA", "NA", "NA", float(data_point[4]), "NA", float(data_point[0]), "NA"])
####

#### Start investment loop ####
loop_nb = 0
while True:

    loop_nb += 1  # Start at loop #1

    for i, currency in enumerate(currencies):

        #### Define variables that are reset at each new loop ####
        canceled = False
        closed_txid = ["NA"]
        benefit = "NA"
        base_volume = 0.0
        invest = False
        decision = "WAIT"
        order_status = ""
        pair = "{}{}".format(currency, base_currency)  # Define currency pair
        if pair not in all_pairs:  # if pair does not exist, try something different
            pair = "{}{}".format(currency, base_currency.lstrip("Z"))
        ####

        #### Full code into try to avoid crashes if Kraken platform does not respond ####
        try:
        ####

            #### Update account balance and store it to history file with summary per currency ####
            time.sleep(15)  # Wait after first private request to avoid issues with API rate limit
            current_balance = account_balance.balance_query()
            if utilities.is_error(current_balance, currency):  # If error occurred during balance query, report it
                continue  # Cannot start the investment loop if an error occurred here
            else:
                funds = current_balance["result"]
                base_volume = sum_to_invest[i]*float(funds[base_currency])  # base volume available for investment
            ####

            #### Extract fee per purchase per currency pair + decimal limit + min volume order ####
            time.sleep(0.1)  # Wait after first public request to avoid issues with API rate limit

            gen_info = get_info.get_all_info_assetPairs(currency_pair = pair)
            if utilities.is_error(gen_info, currency):  # If error occurs while querying info, write it
                continue  # Cannot start the investment loop if an error occurred here
            else:
                decimal = gen_info["result"][pair]["pair_decimals"]  # decimal of rouding allowed for crypto
                min_vol_order = gen_info["result"][pair]["ordermin"]  # minimal volume of crypto per order
                fees = gen_info["result"][pair]["fees"]  # fees applied depending on the volume ordered
            ####

            #### Evaluate the fee applied to the current volume ####
            final_fee = utilities.eval_fee(fees, base_volume)
            ####

            #### Extract OHLC for currencies and store it to price history file ####
            time.sleep(0.1)
            tstime = time.time()
            current_time = datetime.datetime.fromtimestamp(tstime)
            OHLC = k.query_public("OHLC", data = {'pair': pair, 'since': tstime})
            if utilities.is_error(OHLC, currency):  # If error occurs while querying info, write it
                continue  # Cannot start the investment loop if an error occurred here
            else:
                closing = OHLC["result"][pair][0][4]  # Extract closing price for pair
            ####

            #### Define decimal ceiling value ####
            sum_decimal = utilities.decimal_round(decimal)
            ####

            #### Extraction of the manual decisions ####
            with open("data/config.txt", "r") as config:
                config.readline()  # Skip recovery line
                man_decision = config.readline().rstrip("\n").rstrip("\r").split("\t")[1]
            ####

            #### Estimation of the investment amount per crypto #### Algorithm is here ####
            if not price_last_decision[currency] or price_last_decision[currency][0] == "sell":
                order_price = round(float(closing) + sum_decimal, decimal)  # Define order price for buying higher than closing, and round to avoid weird decimals
                volume_to_invest = utilities.volume_round(base_volume/order_price, order_price)  # Define volume to be invested in function of the order price and round it to avoid an excess of decimals due to python's poor handling of te floats
                if len(history[currency]) > history_regression:  # look at history size to avoid errors
                    last_closing = [float(i[3]) for i in history[currency][-history_regression:]]
                    frame_prices = [float(i[3]) for i in history[currency][-drop_time_frame:]]
                    if not "prevent_buy_{}".format(currency) in man_decision:
                        if not "cond_buy_{}".format(currency) in man_decision or order_price < (1-emergency_drop)*statistics.median(frame_prices):
                            if order_price < (1-drop_rate)*statistics.median(frame_prices):  # BUY TRIGGER  # Median is appropriate to distinguish valleys from peaks as the median is robust to outliers, so its value will remain high in case of valley , but low in case of a drop from a peak
                                time_history = [i[12] for i in history[currency][-history_regression:]]
                                expected_price = compute_linear_regression(time_history, last_closing, tstime)  # based on a linear regression, compute the expected price based on the data of the whole day / half day => to make sure we are actually not on a relatively large peak that will crash without return
                                if order_price < expected_price*(1-final_fee):  # if the order price is lower than expected, then it is not just caused by a recent peak that's returning to normal, but it is actually much lower than usual
                                    if not distrib_info[currency][0]:
                                        distrib_info[currency][1] = order_price
                                        distrib_info[currency][0] = True
                                    elif order_price < distrib_info[currency][1]:
                                        distrib_info[currency][1] = order_price
                                    elif order_price > end_tendency*distrib_info[currency][1]:  # If growth starts again after valley
                                        decision = "buy"
                                        invest = True
                                        distrib_info[currency][0] = False
                                        distrib_info[currency][2] = 0

            elif price_last_decision[currency][0] == "buy":  # selling algo
                order_price = round(float(closing) - sum_decimal, decimal)  # Define order price for selling lower than closing, and round to avoid weird decimals
                volume_to_invest = price_last_decision[currency][2]
                last_closing = [float(i[3]) for i in history[currency][-history_regression:]]
                if price_last_decision[currency][1]*price_last_decision[currency][2]*(1+price_last_decision[currency][3])*min_benef < order_price*price_last_decision[currency][2]*(1-final_fee):  # If previous buy was 10% lower than current sell when accounting for fees, sell
                    if not distrib_info[currency][0]:
                        distrib_info[currency][2] = order_price
                        distrib_info[currency][0] = True
                    elif order_price > distrib_info[currency][2]:
                        distrib_info[currency][2] = order_price
                    elif order_price*end_tendency < distrib_info[currency][2]:  # If growth starts again after valley
                        decision = "sell"
                        invest = True
                        distrib_info[currency][0] = False
                        distrib_info[currency][1] = 10**7
            ####

            #### Evaluate if minimum volume is reached ####
            if not utilities.is_min_vol(volume_to_invest, min_vol_order, currency):
                continue
            ####

            #### Make decision whether to make order or wait ####
            if invest:
                transaction = perform_order.order(currency_pair = pair, order_type = decision, price = order_price, volume = volume_to_invest)
                if utilities.is_error(transaction, currency):  # If error occurs while performing order, write it
                    continue  # Cannot start the investment loop if an error occurred here
                else:
                    txids = transaction["result"]["txid"]  # Extract !!LIST!! of txids

                time.sleep(0.1)  # buffer for max API rate
                closed_txid = []
                for txid in txids:
                    is_closed = 0
                    for i in range(5):
                        transaction_info = perform_order.query_order(order_txid = txid)
                        if utilities.is_error(transaction_info, currency):  # If error occurs while query info order, write it
                          continue
                        else:
                            if transaction_info["result"][txid]["status"] == "closed" or "artial" in transaction_info["result"][txid]["status"]:  # artial is for Partial fill trades
                                closed_txid.append(txid)  # Append the closed txid to the list of closed txids
                                order_status = transaction_info["result"][txid]["status"]
                                order_price = float(transaction_info["result"][txid]["price"])  # Override the limit set by the real price of the closed order
                                if decision == "sell":  # estimate benefit
                                    benefit = float(transaction_info["result"][txid]["cost"]) - float(transaction_info["result"][txid]["fee"]) - price_last_decision[currency][1]*price_last_decision[currency][2]*(1+price_last_decision[currency][3])
                                time.sleep(1)  # Wait after first private request to avoid issues with API rate limit
                                # Update balance
                                current_balance = account_balance.balance_query()
                                if utilities.is_error(current_balance, currency):  # If error occurred during balance query, report it
                                    continue  # Cannot start the investment loop if an error occurred here
                                else:
                                    funds = current_balance["result"]
                                is_closed = 1
                                break  # Break loop once order was closed
                            else:
                                time.sleep(10)
                    if not is_closed:  # If after 5 rounds order was not closed, cancel it
                        time.sleep(0.1)  # Buffer for platform request
                        cancelation = perform_order.cancel_order(order_txid = txid)
                        if utilities.is_error(cancelation, currency):  # If error occurs while performing order, write it
                            continue  # Cannot start the investment loop if an error occurred here
                        else:
                            canceled = True
                            decision = "WAIT"
                            closed_txid.append("Canceled order: {}\n".format(txid))
                if not canceled:  # Write last activity only if actually something happened
                    price_last_decision[currency] = [decision, order_price, volume_to_invest, final_fee]
                    with open("data/{}_last_activity.txt".format(currency), "w") as last_activity:
                        last_activity.write("{}\t{}\n".format("\t".join([str(i) for i in price_last_decision[currency]]), current_time))
            ####

            #### Write results in each respective file ####
            amount_currency = utilities.is_zero_funds(funds, currency)
            history[currency].append([loop_nb, current_time, decision, order_price, decimal, final_fee, min_vol_order, volume_to_invest, funds[base_currency], amount_currency, closing, benefit, tstime, ",".join(closed_txid)])
            with open("data/{}_records.txt".format(currency), "a") as balance_file:
                balance_file.write("{}\n".format("\t".join([str(i) for i in history[currency][-1]])))
            ####

        #### Redirect any exception into output files to have follow-up cycle by cycle ####
        except Exception as excpt:
            with open("data/{}_records.txt".format(currency), "a") as balance_file:
                balance_file.write("ERROR: {}\n".format(excpt))
        ####


    #### Define wait time based on benchmark ####
    time.sleep(1)
    # The code below is to store the trading results in a local database
    # try:
    #     update.update_trades("data")
    #     update.update_prices("data")
    # except Exception as E:
    #     print("ERROR with the DB update: {}".format(str(E)))
    ####

#### End investment loop ####

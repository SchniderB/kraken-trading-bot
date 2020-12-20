# -*- coding: utf-8 -*-
"""
This file contains methods to perform buy and sell orders, and order cancellation
using Kraken python API. It also allows to query the open and closed orders.

This file is part of krakenex. Licensed under the Simplified BSD license.

Created on Mon Jul 14 22:28:53 2020

@author: boris
"""

import krakenex

class Make_order:
    """
    Make_order is a class that allows to perform buy and sell orders, as well as
    order cancellation, using Kraken python API.  It also allows to query the open
    and closed orders.
    """
    def __init__(self):
        self.k = krakenex.API()  # Load class from krakenex API
        self.k.load_key('order.key')  # Load key at instanciation point

    def order(self, currency_pair = "", order_type = "", price = "", volume = ""):
        """
        Method that performs a currency buy / sell order via Kraken platform.

        currency_pair : pair of currencies of interest in the following format:
            X + first currency ID + Z + second currency
        order_type : type of order to be addressed to Kraken, i.e. either 'buy' or
            'sell'
        price : rate of the first currency of the pair of currencies relatively to
            the other currency.
        volume : number of currencies to be bought / sold with the order.
        """
        response = self.k.query_private('AddOrder',
                                        {'pair': currency_pair,
                                         'type': order_type,
                                         'ordertype': 'limit',
                                         'price': price,
                                         'volume': volume
                                         # `ordertype`, `price`, `price2` are valid
                                         # 'close[ordertype]': 'limit',
                                         # 'close[price]': '0.165'
                                         # these will be ignored!
                                         # 'close[pair]': 'XXBTZEUR',
                                         # 'close[type]': 'sell',
                                         # 'close[volume]': '1'
                                         })
        return response

    def cancel_order(self, order_txid = ""):
        """
        Method that cancels an order currently pending on Kraken platform.

        order_txid : ID of the order to be cancelled
        """
        response = self.k.query_private('CancelOrder', {'txid': order_txid})
        return response

    def query_order(self, order_txid = ""):
        """
        Method that queries information about an order.

        order_txid : ID of the queried order
        """
        response = self.k.query_private('QueryOrders', {'txid': order_txid})
        return response


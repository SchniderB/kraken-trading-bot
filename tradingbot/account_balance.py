# -*- coding: utf-8 -*-
"""
This file is part of krakenex

Licensed under the Simplified BSD license.
Returns the account balance.
"""

import krakenex

def balance_query():
    k = krakenex.API()
    k.load_key('balance_query.key')
    return k.query_private('Balance')

#  Drakkar-Software OctoBot-Websockets
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from enum import Enum

PROJECT_NAME = "OctoBot-Websockets"
VERSION = "1.1.2"  # major.minor.patch

BUY = 'buy'
SELL = 'sell'

BID = 'bid'
ASK = 'ask'
BIDS = 'bids'
ASKS = 'asks'
UND = 'undefined'

CONFIG_EXCHANGE_WEB_SOCKET = "web-socket"


class Feeds(Enum):
    L2_BOOK = 'l2_book'
    L3_BOOK = 'l3_book'
    BOOK_DELTA = 'book_delta'
    TRADES = 'trades'
    TICKER = 'ticker'
    CANDLE = 'candle'
    KLINE = 'kline'
    FUNDING = 'funding'
    ORDERS = 'orders'
    PORTFOLIO = 'portfolio'
    POSITION = 'position'
    TRADE = 'trade'
    UNSUPPORTED = 'unsupported'

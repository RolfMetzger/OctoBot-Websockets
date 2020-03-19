# cython: language_level=3
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
from time import time


class Ticker:
    def __init__(self):
        self.timestamp = 0

        """
        Last prices
        """
        self.ask_price = 0
        self.bid_price = 0
        self.last_price = 0

        """
        24h data
        """
        self.high_24 = 0
        self.low_24 = 0
        self.open_24 = 0
        self.volume_24 = 0

        """
        Future
        """
        self.mark_price = 0
        self.funding_rate = 0
        self.next_funding_time = 0

    def handle_quote(self, bid_price, ask_price):
        should_refresh: int = False

        if bid_price and self.bid_price != bid_price:
            self.bid_price = bid_price
            self.timestamp = time()
            should_refresh = True

        if ask_price and self.ask_price != ask_price:
            self.ask_price = ask_price
            self.timestamp = time()
            should_refresh = True

        return should_refresh

    def handle_last_price(self, last_price):
        if self.last_price != last_price:
            self.timestamp = time()
            self.last_price = last_price
            return True
        return False

    def handle_24_ticker(self, high_24, low_24, open_24, volume_24):
        if high_24 and self.high_24 != high_24:
            self.high_24 = high_24
        if low_24 and self.low_24 != low_24:
            self.low_24 = low_24
        if open_24 and self.open_24 != open_24:
            self.open_24 = open_24
        if volume_24 and self.volume_24 != volume_24:
            self.volume_24 = volume_24

    def handle_mark_price(self, mark_price):
        if self.mark_price != mark_price:
            self.mark_price = mark_price
            return True
        return False

    def handle_funding(self, funding_rate, next_funding_time):
        if self.funding_rate != funding_rate or self.next_funding_time != next_funding_time:
            self.funding_rate = funding_rate
            self.next_funding_time = next_funding_time
            return True
        return False

    def to_dict(self):
        return {
            "open": self.open_24,
            "high": self.high_24,
            "low": self.low_24,
            "last": self.last_price,
            "ask": self.ask_price,
            "bid": self.bid_price,
            "timestamp": self.timestamp
        }

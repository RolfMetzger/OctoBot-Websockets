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
from octobot_websockets.constants import TICKER

from octobot_websockets.data.ticker import Ticker
from octobot_websockets.feeds.feed import Feed


class TickerConstructor:
    def __init__(self, feed: Feed, symbol: str):
        self.feed = feed
        self.ticker = Ticker()
        self.symbol = symbol

    async def handle_quote(self, bid_price: float, ask_price: float):
        if self.ticker.handle_quote(bid_price, ask_price):
            await self.__handle_refresh()

    async def handle_recent_trade(self, last_price: float):
        if self.ticker.handle_recent_trade(last_price):
            await self.__handle_refresh()

    async def __handle_refresh(self):
        if self.ticker.is_ready():
            await self.feed.callbacks[TICKER](feed=self.feed.get_name(),
                                              symbol=self.symbol,
                                              bid=self.ticker.bid_price,
                                              ask=self.ticker.ask_price,
                                              last=self.ticker.last_price,
                                              timestamp=self.ticker.timestamp)

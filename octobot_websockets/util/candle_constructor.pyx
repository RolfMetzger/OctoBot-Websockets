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
from octobot_websockets.feed import Feed

from octobot_websockets import CANDLE, TimeFrames
from octobot_websockets.util.candle import Candle


cdef class CandleConstructor:
    cdef object feed
    cdef str symbol
    cdef object time_frame
    cdef object candle

    def __init__(self, feed: Feed, symbol: str, time_frame: TimeFrames):
        self.feed = feed
        self.symbol = symbol
        self.candle = None
        self.time_frame = time_frame

    async def handle_recent_trade(self, price: float, vol: float):
        if self.candle is None:
            self.candle = Candle(price, 1)

        self.candle.handle_candle_update(price, vol)

        if self.candle.is_closed:
            await self.feed.callbacks[CANDLE](feed=self.feed.get_name(),
                                              symbol=self.symbol,
                                              timestamp=self.candle.close_timestamp,
                                              time_frame=self.time_frame,
                                              close=self.candle.close,
                                              volume=self.candle.vol,
                                              high=self.candle.high,
                                              low=self.candle.low,
                                              opn=self.candle.opn)
            self.candle = None

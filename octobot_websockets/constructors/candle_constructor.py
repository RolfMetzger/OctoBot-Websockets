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
import asyncio
from time import time

from octobot_websockets.constants import CANDLE, TimeFrames, TimeFramesMinutes, KLINE, \
    MINUTE_TO_SECONDS

from octobot_websockets.data.candle import Candle
from octobot_websockets.feeds.feed import Feed


class CandleConstructor:
    def __init__(self, feed: Feed, symbol: str, time_frame: TimeFrames, started_candle: list):
        self.should_stop = False
        self.feed = feed
        self.symbol = symbol
        self.candle = None
        self.time_frame = time_frame

        # recover started candle
        self.candle = Candle(0)
        self.candle.start_timestamp, \
        self.candle.opn, self.candle.high, self.candle.low, self.candle.close, self.candle.vol = started_candle

        self.time_frame_seconds = TimeFramesMinutes[self.time_frame] * MINUTE_TO_SECONDS
        self.time_frame_delta = self.time_frame_seconds - (time() - started_candle[0])
        self.candle_task = asyncio.create_task(self.release_candle())

    async def handle_recent_trade(self, price: float, vol: float):
        if self.candle is None:
            self.candle = Candle(price)

        self.candle.handle_candle_update(price, vol)

        await self.feed.callbacks[KLINE](feed=self.feed.get_name(),
                                         symbol=self.symbol,
                                         timestamp=self.candle.close_timestamp,
                                         time_frame=self.time_frame,
                                         close=self.candle.close,
                                         volume=self.candle.vol,
                                         high=self.candle.high,
                                         low=self.candle.low,
                                         opn=self.candle.opn)

    async def release_candle(self):
        await asyncio.sleep(self.time_frame_delta)
        while not self.should_stop:
            if self.candle is not None:
                self.candle.on_close()
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
            await asyncio.sleep(self.time_frame_seconds)

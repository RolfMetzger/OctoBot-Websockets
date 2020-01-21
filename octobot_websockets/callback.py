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
from octobot_commons.enums import TimeFrames


class Callback(object):
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, *args, **kwargs):
        raise NotImplemented


class TradeCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       side: str,
                       amount: float,
                       price: float,
                       timestamp: int):
        await self.callback(feed, pair=symbol, timestamp=timestamp, side=side, amount=amount, price=price)


class TickerCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       bid: float,
                       ask: float,
                       last: float,
                       timestamp: int):
        await self.callback(feed, pair=symbol, bid=bid, ask=ask, last=last, timestamp=timestamp)


class CandleCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       timestamp: int,
                       time_frame: TimeFrames,
                       close: float,
                       volume: float,
                       high: float,
                       low: float,
                       opn: float):
        await self.callback(feed, pair=symbol, timestamp=timestamp, time_frame=time_frame,
                            close=close, volume=volume, high=high, low=low, opn=opn)


class KlineCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       timestamp: int,
                       time_frame: TimeFrames,
                       close: float,
                       volume: float,
                       high: float,
                       low: float,
                       opn: float):
        await self.callback(feed, pair=symbol, timestamp=timestamp, time_frame=time_frame,
                            close=close, volume=volume, high=high, low=low, opn=opn)


class BookCallback(Callback):
    """
    For full L2/L3 book updates
    """

    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       asks: list,
                       bids: list,
                       timestamp: int):
        await self.callback(feed, pair=symbol, asks=asks, bids=bids, timestamp=timestamp)


class OrdersCallback(Callback):
    """
    For orders updates
    """

    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       price: float,
                       quantity: float,
                       order_id: int,
                       is_canceled: bool,
                       is_filled: bool):
        await self.callback(feed, pair=symbol, price=price, quantity=quantity,
                            order_id=order_id, is_canceled=is_canceled, is_filled=is_filled)


class PositionCallback(Callback):
    """
    For position updates
    """

    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       entry_price: float,
                       cost: float,
                       quantity: float,
                       pnl_percent: float,
                       mark_price: float,
                       liquidation_price: float,
                       timestamp: int):
        await self.callback(feed,
                            pair=symbol,
                            entry_price=entry_price,
                            cost=cost,
                            quantity=quantity,
                            pnl_percent=pnl_percent,
                            mark_price=mark_price,
                            liquidation_price=liquidation_price,
                            timestamp=timestamp)


class UpdatedBookCallback(Callback):
    """
    For Book Deltas
    """

    # NOT SUPPORTED
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       delta: dict):
        """
        Delta is in format of:
        {
            BID: {
                ADD: [(price, size), (price, size), ...],
                DEL: [price, price, price, ...]
                UPD: [(price, size), (price, size), ...]
            },
            ASK: {
                ADD: [(price, size), (price, size), ...],
                DEL: [price, price, price, ...]
                UPD: [(price, size), (price, size), ...]
            }
        }

        ADD - these tuples should simply be inserted.
        DEL - price levels should be deleted
        UPD - prices should have the quantity set to size (these are not price deltas)
        """
        await self.callback(feed, pair=symbol, delta=delta)


class FundingCallback(Callback):
    pass


class PortfolioCallback(Callback):
    pass

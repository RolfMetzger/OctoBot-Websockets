"""
Copyright (C) 2017-2019  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
"""
from asyncio import get_event_loop
from decimal import Decimal


class Callback:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, *args, **kwargs):
        raise NotImplemented


class TradeCallback(Callback):
    async def __call__(self, *, feed: str, symbol: str, side: str, amount: Decimal, price: Decimal, timestamp=None):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, timestamp, side, amount, price)


class TickerCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       bid: Decimal,
                       ask: Decimal,
                       close: Decimal,
                       volume: Decimal,
                       high: Decimal,
                       low: Decimal,
                       opn: Decimal):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, bid, ask, close, volume, high, low, opn)


class CandleCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       timestamp: Decimal,
                       close: Decimal,
                       volume: Decimal,
                       high: Decimal,
                       low: Decimal,
                       opn: Decimal):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, timestamp, close, volume, high, low, opn)


class BookCallback(Callback):
    """
    For full L2/L3 book updates
    """

    async def __call__(self, *, feed: str, symbol: str, asks: dict, bids: dict, timestamp):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, asks, bids, timestamp)


class BookUpdateCallback(Callback):
    """
    For Book Deltas
    """

    async def __call__(self, *, feed: str, pair: str, delta: dict, timestamp):
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
        await get_event_loop().run_in_executor(None, self.callback, feed, pair, delta, timestamp)


class VolumeCallback(Callback):
    pass


class FundingCallback(Callback):
    pass

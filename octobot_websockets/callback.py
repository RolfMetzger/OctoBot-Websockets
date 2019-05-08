from asyncio import get_event_loop
import asyncio


class Callback:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, *args, **kwargs):
        raise NotImplemented


class TradeCallback(Callback):
    async def __call__(self, *, feed: str, symbol: str, side: str, amount: int, price: int, timestamp=None):
        asyncio.run_coroutine_threadsafe(self.callback(feed, symbol, timestamp, side, amount, price), get_event_loop())


class TickerCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       bid: int,
                       ask: int,
                       last: int):
        asyncio.run_coroutine_threadsafe(self.callback(feed, symbol, bid, ask, last), get_event_loop())


class CandleCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       timestamp: int,
                       close: int,
                       volume: int,
                       high: int,
                       low: int,
                       opn: int):
        asyncio.run_coroutine_threadsafe(get_event_loop(),
                                         self.callback(feed, symbol, timestamp, close, volume, high, low, opn), get_event_loop())


class BookCallback(Callback):
    """
    For full L2/L3 book updates
    """

    async def __call__(self, *, feed: str, symbol: str, asks: dict, bids: dict):
        asyncio.run_coroutine_threadsafe(self.callback(feed, symbol, asks, bids), get_event_loop())


class UpdatedBookCallback(Callback):
    """
    For Book Deltas
    """

    async def __call__(self, *, feed: str, symbol: str, asks: dict, bids: dict):
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
        asyncio.run_coroutine_threadsafe(self.callback(feed, symbol, asks, bids), get_event_loop())


class VolumeCallback(Callback):
    pass


class FundingCallback(Callback):
    pass

from asyncio import get_event_loop


class Callback:
    def __init__(self, callback):
        self.callback = callback

    async def __call__(self, *args, **kwargs):
        raise NotImplemented


class TradeCallback(Callback):
    async def __call__(self, *, feed: str, symbol: str, side: str, amount: int, price: int, timestamp=None):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, timestamp, side, amount, price)


class TickerCallback(Callback):
    async def __call__(self, *,
                       feed: str,
                       symbol: str,
                       bid: int,
                       ask: int,
                       last: int):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, bid, ask, last)


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
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, timestamp, close, volume, high, low, opn)


class BookCallback(Callback):
    """
    For full L2/L3 book updates
    """

    async def __call__(self, *, feed: str, symbol: str, asks: dict, bids: dict):
        await get_event_loop().run_in_executor(None, self.callback, feed, symbol, asks, bids)


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
        await get_event_loop().run_in_executor(None, self.callback, feed, pair, delta, timestamp)


class VolumeCallback(Callback):
    pass


class FundingCallback(Callback):
    pass

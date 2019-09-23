from logging import DEBUG

from octobot_commons.enums import TimeFrames
from octobot_commons.logging.logging_util import get_logger, set_global_logger_level

from octobot_websockets.callback import TradeCallback, TickerCallback, BookCallback, CandleCallback, KlineCallback
from octobot_websockets.constants import Feeds
from tentacles.Websockets.feeds.bitmex import Bitmex

logger = get_logger("DEMO")


async def ticker(feed, symbol, bid, ask, last, timestamp):
    print(f'[{timestamp}][TICKER] Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask} Last : {last}')


async def trade(feed, symbol, timestamp, side, amount, price):
    print(
        f"[{timestamp}][TRADE] Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")


async def book(feed, symbol, asks, bids, timestamp):
    print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Bids are {bids}')
    print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Asks are {asks}')


async def candle(feed, symbol, timestamp, time_frame, close, volume, high, low, opn):
    print(
        f'[{timestamp}][CANDLE] Feed: {feed} TimeFrame: {time_frame} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def kline(feed, symbol, timestamp, time_frame, close, volume, high, low, opn):
    print(
        f'[{timestamp}][KLINE] Feed: {feed} TimeFrame: {time_frame} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def funding(**kwargs):
    # print(f"Funding Update for {kwargs['feed']}")
    # print(kwargs)
    pass


def main():
    set_global_logger_level(DEBUG)
    b = Bitmex(pairs=["BTC/USD", "ETH/USD"], channels=[Feeds.TRADES, Feeds.TICKER, Feeds.L2_BOOK, Feeds.CANDLE], callbacks={
        Feeds.TRADES: TradeCallback(trade),
        Feeds.TICKER: TickerCallback(ticker),
        Feeds.L2_BOOK: BookCallback(book),
        Feeds.CANDLE: CandleCallback(candle),
        Feeds.KLINE: KlineCallback(kline)
    }, time_frames=[TimeFrames.ONE_MINUTE])
    b.start()


if __name__ == '__main__':
    main()

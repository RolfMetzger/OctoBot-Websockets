from logging import DEBUG

from octobot_commons.logging.logging_util import get_logger, set_global_logger_level

from octobot_websockets.callback import TradeCallback, TickerCallback, BookCallback, CandleCallback, KlineCallback
from octobot_websockets.constants import TRADES, TICKER, L2_BOOK, CANDLE, TimeFrames, KLINE
from octobot_websockets.feeds.bitmex import Bitmex

logger = get_logger("DEMO")


async def ticker(feed, symbol, bid, ask, last, timestamp):
    logger.info(f'[{timestamp}][TICKER] Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask} Last : {last}')


async def trade(feed, symbol, timestamp, side, amount, price):
    logger.info(
        f"[{timestamp}][TRADE] Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")


async def book(feed, symbol, asks, bids, timestamp):
    logger.info(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Bids are {bids}')
    logger.info(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Asks are {asks}')


async def candle(feed, symbol, timestamp, time_frame, close, volume, high, low, opn):
    logger.info(
        f'[{timestamp}][CANDLE] Feed: {feed} TimeFrame: {time_frame} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def kline(feed, symbol, timestamp, time_frame, close, volume, high, low, opn):
    logger.info(
        f'[{timestamp}][KLINE] Feed: {feed} TimeFrame: {time_frame} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def funding(**kwargs):
    # logger.info(f"Funding Update for {kwargs['feed']}")
    # logger.info(kwargs)
    pass


def main():
    set_global_logger_level(DEBUG)
    b = Bitmex(pairs=["BTC/USD", "ETH/USD"], channels=[TRADES, TICKER, L2_BOOK, CANDLE], callbacks={
        TRADES: TradeCallback(trade),
        TICKER: TickerCallback(ticker),
        L2_BOOK: BookCallback(book),
        CANDLE: CandleCallback(candle),
        KLINE: KlineCallback(kline)
    }, time_frames=[TimeFrames.ONE_MINUTE])
    b.start()


if __name__ == '__main__':
    main()

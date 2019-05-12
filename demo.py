from octobot_websockets.constants import TRADES, TICKER, L2_BOOK, CANDLE, TimeFrames, KLINE
from octobot_websockets.feeds.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, TickerCallback, BookCallback, CandleCallback, KlineCallback


async def ticker(feed, symbol, bid, ask, last, timestamp):
    # print(f'[{timestamp}][TICKER] Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask} Last : {last}')
    pass


async def trade(feed, symbol, timestamp, side, amount, price):
    # print(
    #     f"[{timestamp}][TRADE] Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")
    pass


async def book(feed, symbol, asks, bids, timestamp):
    # print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Bids are {bids}')
    # print(f'[{timestamp}][ORDER BOOK] Feed: {feed} Pair: {symbol} Book Asks are {asks}')
    pass


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
    b = Bitmex(pairs=['BTC/USD', 'ETH/USD'], channels=[TRADES, TICKER, L2_BOOK, CANDLE], callbacks={
        TRADES: TradeCallback(trade),
        TICKER: TickerCallback(ticker),
        L2_BOOK: BookCallback(book),
        CANDLE: CandleCallback(candle),
        KLINE: KlineCallback(kline)
    }, time_frames=[TimeFrames.ONE_MINUTE])
    b.start()


if __name__ == '__main__':
    main()

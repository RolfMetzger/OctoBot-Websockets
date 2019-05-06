from octobot_websockets import TRADES, L2_BOOK
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, BookCallback
from octobot_websockets.feedhandler import FeedHandler


def ticker(feed, symbol, bid, ask, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {symbol} Bid: {bid} Ask: {ask}')


def trade(feed, symbol, timestamp, side, amount, price):
    print(
        f"Timestamp: {timestamp} Feed: {feed} Pair: {symbol} Side: {side} Amount: {amount} Price: {price}")


def book(feed, symbol, asks, bids, timestamp):
    print(f'Timestamp: {timestamp} Feed: {feed} Pair: {symbol} '
          f'Book Bid Size is {len(bids)} '
          f'Ask Size is {len(asks)}')


def candle(feed, symbol, timestamp, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {symbol} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


def funding(**kwargs):
    print(f"Funding Update for {kwargs['feed']}")
    print(kwargs)


def main():
    f = FeedHandler()
    f.add_feed(Bitmex(pairs=['BTC/USD'], channels=[TRADES, L2_BOOK], callbacks={
        TRADES: TradeCallback(trade),
        L2_BOOK: BookCallback(book)
    }))
    f.run()


if __name__ == '__main__':
    main()

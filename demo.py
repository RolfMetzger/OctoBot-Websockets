from octobot_websockets import BID, ASK, TRADES, L2_BOOK
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, BookCallback
from octobot_websockets.feedhandler import FeedHandler


async def ticker(feed, pair, bid, ask, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {pair} Bid: {bid} Ask: {ask}')


async def trade(feed, pair, order_id, timestamp, side, amount, price):
    print(
        f"Timestamp: {timestamp} Feed: {feed} Pair: {pair} ID: {order_id} Side: {side} Amount: {amount} Price: {price}")


async def book(feed, pair, book, timestamp):
    print(f'Timestamp: {timestamp} Feed: {feed} Pair: {pair} Book Bid Size is {len(book[BID])} Ask Size is {len(book[ASK])}')


async def candle(feed, pair, timestamp, close, volume, high, low, opn):
    print(f'Feed: {feed} Pair: {pair} Close: {close} Volume: {volume} High: {high} Low: {low} Open: {opn}')


async def funding(**kwargs):
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

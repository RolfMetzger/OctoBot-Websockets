import asyncio

import pytest

from octobot_websockets import L2_BOOK, TRADES
from octobot_websockets.bitmex.bitmex import Bitmex
from octobot_websockets.callback import TradeCallback, BookCallback
from octobot_websockets.feedhandler import FeedHandler

pytestmark = pytest.mark.asyncio

test_book = False
test_trade = False


async def book(feed, pair, book, timestamp):
    global test_book
    test_book = True


async def trade(feed, pair, order_id, timestamp, side, amount, price):
    global test_trade
    test_trade = True


async def test_bitmex_ticker():
    f = FeedHandler()
    f.add_feed(Bitmex(pairs=['BTC/USD'], channels=[TRADES, L2_BOOK], callbacks={
        TRADES: TradeCallback(trade),
        L2_BOOK: BookCallback(book)
    }))
    f.run()
    await asyncio.sleep(5)
    assert test_book
    assert test_trade
    f.stop()

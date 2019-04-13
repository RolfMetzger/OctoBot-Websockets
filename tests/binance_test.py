import asyncio

import pytest

from octobot_websockets import TICKER
from octobot_websockets.binance.binance import Binance
from octobot_websockets.callback import TickerCallback
from octobot_websockets.feedhandler import FeedHandler

pytestmark = pytest.mark.asyncio

test_ticker = False


async def ticker(feed, pair, bid, ask, close, volume, high, low, opn):
    global test_ticker
    test_ticker = True


async def test_binance_ticker():
    f = FeedHandler()
    f.add_feed(Binance(pairs=['BTC/USDT'], channels=[TICKER], callbacks={TICKER: TickerCallback(ticker)}))
    f.run()
    await asyncio.sleep(5)
    assert test_ticker
    f.stop()

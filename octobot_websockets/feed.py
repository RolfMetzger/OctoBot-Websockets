"""
Copyright (C) 2017-2019  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
"""
import logging
from abc import abstractmethod
import ccxt

from octobot_websockets import TRADES, TICKER, L2_BOOK, L3_BOOK, VOLUME, BOOK_DELTA, UNSUPPORTED, FUNDING
from octobot_websockets.callback import Callback


class Feed:
    def __init__(self, address, pairs=None, channels=None, config=None, callbacks=None, book_interval=1000):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = {}
        self.address = address
        self.book_update_interval = book_interval
        self.updates = 0
        self.do_deltas = False
        self.pairs = []
        self.channels = []

        self.ccxt_client = getattr(ccxt, self.get_name())()
        self.ccxt_client.load_markets()

        if config is not None and (pairs is not None or channels is not None):
            raise ValueError("Use config, or channels and pairs, not both")

        if config is not None:
            for channel in config:
                chan = self.feed_to_exchange(channel)
                self.config[chan] = [self.get_exchange_pair(pair) for pair in config[channel]]

        if pairs:
            self.pairs = [self.get_exchange_pair(pair) for pair in pairs]

        if channels:
            self.channels = [self.feed_to_exchange(chan) for chan in channels]

        self.l3_book = {}
        self.l2_book = {}
        self.callbacks = {TRADES: Callback(None),
                          TICKER: Callback(None),
                          L2_BOOK: Callback(None),
                          L3_BOOK: Callback(None),
                          VOLUME: Callback(None)}

        if callbacks:
            for cb_type, cb_func in callbacks.items():
                self.callbacks[cb_type] = cb_func
                if cb_type == BOOK_DELTA:
                    self.do_deltas = True

    async def book_callback(self, pair, book_type, forced, delta, timestamp):
        if self.do_deltas and self.updates < self.book_update_interval and not forced:
            self.updates += 1
            await self.callbacks[BOOK_DELTA](feed=self.get_name(), pair=pair, delta=delta, timestamp=timestamp)

        if self.updates >= self.book_update_interval or forced or not self.do_deltas:
            self.updates = 0
            if book_type == L2_BOOK:
                await self.callbacks[L2_BOOK](feed=self.get_name(),
                                              pair=pair,
                                              book=self.l2_book[pair],
                                              timestamp=timestamp)
            else:
                await self.callbacks[L3_BOOK](feed=self.get_name(),
                                              pair=pair,
                                              book=self.l3_book[pair],
                                              timestamp=timestamp)

    async def message_handler(self, msg):
        raise NotImplementedError

    @classmethod
    def get_name(cls):
        raise NotImplemented("get_name is not implemented")

    @classmethod
    def get_ccxt(cls):
        getattr(ccxt, cls.get_name())

    @classmethod
    @abstractmethod
    def get_L2_book_feed(cls):
        raise NotImplemented("get_L2_book_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_L3_book_feed(cls):
        raise NotImplemented("get_L3_book_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_trades_feed(cls):
        raise NotImplemented("get_trades_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_ticker_feed(cls):
        raise NotImplemented("get_ticker_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_volume_feed(cls):
        raise NotImplemented("get_volume_feed is not implemented")

    @classmethod
    @abstractmethod
    def get_funding_feed(cls):
        raise NotImplemented("get_funding_feed is not implemented")

    def get_pairs(self):
        return self.ccxt_client.symbols

    @staticmethod
    def timestamp_normalize(ts):
        return ts

    @classmethod
    def get_feeds(cls):
        return {
            FUNDING: cls.get_funding_feed(),
            L2_BOOK: cls.get_L2_book_feed(),
            L3_BOOK: cls.get_L3_book_feed(),
            TRADES: cls.get_trades_feed(),
            TICKER: cls.get_ticker_feed(),
            VOLUME: cls.get_volume_feed()
        }

    def get_pair_from_exchange(self, pair):
        return self.ccxt_client.find_market(pair)["symbol"]

    def get_exchange_pair(self, pair):
        if pair in self.ccxt_client.symbols:
            try:
                return self.ccxt_client.find_market(pair)["id"]
            except KeyError:
                raise KeyError(f'{pair} is not supported on {self.get_name()}')
        else:
            raise ValueError(f'{pair} is not supported on {self.get_name()}')

    def feed_to_exchange(self, feed):
        ret = self.get_feeds()[feed]
        if ret == UNSUPPORTED:
            self.logger.error("{} is not supported on {}".format(feed, self.get_name()))
            raise ValueError(f"{feed} is not supported on {self.get_name()}")
        return ret

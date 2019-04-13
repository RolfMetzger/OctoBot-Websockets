"""
Copyright (C) 2017-2019  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
"""
import calendar
import json
from collections import defaultdict
from datetime import datetime as dt
from decimal import Decimal

from sortedcontainers import SortedDict as sd

from octobot_websockets import TRADES, BUY, SELL, BID, ASK, L2_BOOK, L3_BOOK, FUNDING, UNSUPPORTED
from octobot_websockets.feed import Feed


class Bitmex(Feed):
    api = 'https://www.bitmex.com/api/v1/'

    def __init__(self, pairs=None, channels=None, callbacks=None, **kwargs):
        super().__init__('wss://www.bitmex.com/realtime', pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self._reset()

    def _reset(self):
        self.partial_received = False
        self.order_id = {}
        for pair in self.pairs:
            self.l3_book[pair] = {BID: sd(), ASK: sd()}
            self.l2_book[pair] = {BID: sd(), ASK: sd()}
            self.order_id[pair] = defaultdict(dict)

    async def _trade(self, msg):
        """
        trade msg example

        {
            'timestamp': '2018-05-19T12:25:26.632Z',
            'symbol': 'XBTUSD',
            'side': 'Buy',
            'size': 40,
            'price': 8335,
            'tickDirection': 'PlusTick',
            'trdMatchID': '5f4ecd49-f87f-41c0-06e3-4a9405b9cdde',
            'grossValue': 479920,
            'homeNotional': Decimal('0.0047992'),
            'foreignNotional': 40
        }
        """
        for data in msg['data']:
            await self.callbacks[TRADES](feed=self.get_name(),
                                         pair=data['symbol'],
                                         side=BUY if data['side'] == 'Buy' else SELL,
                                         amount=Decimal(data['size']),
                                         price=Decimal(data['price']),
                                         order_id=data['trdMatchID'],
                                         timestamp=data['timestamp'])

    async def _book(self, msg):
        """
        the Full bitmex book
        """
        timestamp = dt.utcnow()
        timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        pair = None
        delta = {BID: [], ASK: []}
        # if we reset the book, force a full update
        forced = False
        if not self.partial_received:
            # per bitmex documentation messages received before partial
            # should be discarded
            if msg['action'] != 'partial':
                return
            self.partial_received = True
            forced = True

        if msg['action'] == 'partial' or msg['action'] == 'insert':
            for data in msg['data']:
                side = BID if data['side'] == 'Buy' else ASK
                price = Decimal(data['price'])
                pair = data['symbol']
                size = Decimal(data['size'])
                order_id = data['id']

                if price in self.l3_book[pair][side]:
                    self.l3_book[pair][side][price][order_id] = size
                else:
                    self.l3_book[pair][side][price] = {order_id: size}
                self.order_id[pair][side][order_id] = (price, size)
                delta[side].append((order_id, price, size))
        elif msg['action'] == 'update':
            for data in msg['data']:
                side = BID if data['side'] == 'Buy' else ASK
                pair = data['symbol']
                update_size = Decimal(data['size'])
                order_id = data['id']

                price, _ = self.order_id[pair][side][order_id]

                self.l3_book[pair][side][price][order_id] = update_size
                self.order_id[pair][side][order_id] = (price, update_size)
                delta[side].append((order_id, price, update_size))
        elif msg['action'] == 'delete':
            for data in msg['data']:
                pair = data['symbol']
                side = BID if data['side'] == 'Buy' else ASK
                order_id = data['id']

                delete_price, _ = self.order_id[pair][side][order_id]
                del self.order_id[pair][side][order_id]
                del self.l3_book[pair][side][delete_price][order_id]

                if len(self.l3_book[pair][side][delete_price]) == 0:
                    del self.l3_book[pair][side][delete_price]

                delta[side].append((order_id, delete_price, 0))

        else:
            self.logger.warning("%s: Unexpected L3 Book message %s", self.get_name(), msg)
            return

        await self.book_callback(pair, L3_BOOK, forced, delta, timestamp)

    async def _l2_book(self, msg):
        """
        top 10 orders from each side
        """
        timestamp = msg['data'][0]['timestamp']
        pair = None

        for update in msg['data']:
            pair = update['symbol']
            self.l2_book[pair][BID] = sd({
                Decimal(price): Decimal(amount)
                for price, amount in update['bids']
            })
            self.l2_book[pair][ASK] = sd({
                Decimal(price): Decimal(amount)
                for price, amount in update['asks']
            })

        await self.callbacks[L2_BOOK](feed=self.get_name(), pair=pair, book=self.l2_book[pair], timestamp=timestamp)

    async def _funding(self, msg):
        """
        {'table': 'funding',
         'action': 'partial',
         'keys': ['timestamp', 'symbol'],
         'types': {
             'timestamp': 'timestamp',
             'symbol': 'symbol',
             'fundingInterval': 'timespan',
             'fundingRate': 'float',
             'fundingRateDaily': 'float'
            },
         'foreignKeys': {
             'symbol': 'instrument'
            },
         'attributes': {
             'timestamp': 'sorted',
             'symbol': 'grouped'
            },
         'filter': {'symbol': 'XBTUSD'},
         'data': [{
             'timestamp': '2018-08-21T20:00:00.000Z',
             'symbol': 'XBTUSD',
             'fundingInterval': '2000-01-01T08:00:00.000Z',
             'fundingRate': Decimal('-0.000561'),
             'fundingRateDaily': Decimal('-0.001683')
            }]
        }
        """
        for data in msg['data']:
            await self.callbacks[FUNDING](feed=self.get_name(),
                                          pair=data['symbol'],
                                          timestamp=data['timestamp'],
                                          interval=data['fundingInterval'],
                                          rate=data['fundingRate'],
                                          rate_daily=data['fundingRateDaily']
                                          )

    async def message_handler(self, msg):
        msg = json.loads(msg, parse_float=Decimal)
        if 'info' in msg:
            self.logger.info("%s - info message: %s", self.get_name(), msg)
        elif 'subscribe' in msg:
            if not msg['success']:
                self.logger.error("%s: subscribe failed: %s", self.get_name(), msg)
        elif 'error' in msg:
            self.logger.error("%s: Error message from exchange: %s", self.get_name(), msg)
        else:
            if msg['table'] == 'trade':
                await self._trade(msg)
            elif msg['table'] == 'orderBookL2':
                await self._book(msg)
            elif msg['table'] == 'funding':
                await self._funding(msg)
            elif msg['table'] == 'orderBook10':
                await self._l2_book(msg)
            else:
                self.logger.warning("%s: Unhandled message %s", self.get_name(), msg)

    async def subscribe(self, websocket):
        self._reset()
        chans = []
        for channel in self.channels if not self.config else self.config:
            for pair in self.pairs if not self.config else self.config[channel]:
                chans.append("{}:{}".format(channel, pair))

        await websocket.send(json.dumps({"op": "subscribe",
                                         "args": chans}))

    @classmethod
    def get_name(cls):
        return 'bitmex'

    @classmethod
    def get_L2_book_feed(cls):
        return 'orderBook10'

    @classmethod
    def get_L3_book_feed(cls):
        return 'orderBookL2'

    @classmethod
    def get_trades_feed(cls):
        return 'trade'

    @classmethod
    def get_ticker_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_volume_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_funding_feed(cls):
        return 'funding'

    @staticmethod
    def timestamp_normalize(ts):
        return calendar.timegm(dt.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").utctimetuple())

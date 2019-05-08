import calendar
import json
from collections import defaultdict
from datetime import datetime as dt
from sortedcontainers import SortedDict as sd

from octobot_websockets import TRADES, BUY, SELL, BID, ASK, L2_BOOK, FUNDING, UNSUPPORTED, TICKER, ASKS, BIDS, L3_BOOK
from octobot_websockets.bitmex.api_key import generate_signature, generate_nonce
from octobot_websockets.feed import Feed


class Bitmex(Feed):
    api = 'https://www.bitmex.com/api/v1'
    MAX_TABLE_LEN = 200

    def __init__(self, pairs=None, channels=None, callbacks=None, **kwargs):
        super().__init__('wss://www.bitmex.com/realtime', pairs=pairs, channels=channels, callbacks=callbacks, **kwargs)
        self.last_trade = None
        self._reset()

    def _reset(self):
        self.partial_received = False
        self.order_id = {}
        self.l3_book = {}
        for pair in self.pairs:
            self.l3_book[pair] = {BID: sd(), ASK: sd()}
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
                                         symbol=self.get_pair_from_exchange(data['symbol']),
                                         side=BUY if data['side'] == 'Buy' else SELL,
                                         amount=data['size'],
                                         price=data['price'],
                                         timestamp=data['timestamp'])
            self.last_trade = data

    async def _l2_book(self, msg):
        await self.callbacks[L2_BOOK](feed=self.get_name(),
                                      symbol=self.get_pair_from_exchange(msg['data'][0]['symbol']),
                                      asks=msg['data'][0]['asks'],
                                      bids=msg['data'][0]['bids'])

    async def _quote(self, msg):
        """Return a ticker object. Generated from quote and trade."""
        try:
            data = msg['data'][0]
            await self.callbacks[TICKER](feed=self.get_name(),
                                         symbol=self.get_pair_from_exchange(data['symbol']),
                                         bid=data['bidPrice'],
                                         ask=data['askPrice'],
                                         last=self.last_trade['price'])
        except TypeError:
            pass

    async def _margin(self, msg):
        pass

    async def _position(self, msg):
        pass

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
                                          symbol=self.get_pair_from_exchange(data['symbol']),
                                          timestamp=data['timestamp'],
                                          interval=data['fundingInterval'],
                                          rate=data['fundingRate'],
                                          rate_daily=data['fundingRateDaily'])

    async def on_message(self, message):
        """Handler for parsing WS messages."""
        message = json.loads(message)

        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None

        try:
            if 'info' in message:
                self.logger.info(f"{self.get_name()}: info message : {message}")
            elif 'subscribe' in message:
                if not message['success']:
                    self.logger.error(f"{self.get_name()}: subscribed failed : {message}")
            elif 'status' in message:
                if message['status'] == 400:
                    self.logger.error(message['error'])
                if message['status'] == 401:
                    self.logger.error("API Key incorrect, please check and restart.")
            elif 'error' in message:
                self.logger.error(f"{self.get_name()}: Error message from exchange: {message}")
            elif action:
                if table == self.get_trades_feed():
                    await self._trade(message)

                elif table == self.get_funding_feed():
                    await self._funding(message)

                elif table == self.get_ticker_feed():
                    await self._quote(message)

                elif table == self.get_margin_feed():
                    await self._margin(message)

                elif table == self.get_position_feed():
                    await self._position(message)

                elif table == self.get_L3_book_feed():
                    await self.handle_book_update(message)

                elif table == self.get_L2_book_feed():
                    await self._l2_book(message)
                else:
                    raise Exception(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error when handling message {e}")
            raise e

    async def handle_book_update(self, msg):
        delta = {BID: [], ASK: []}
        pair = None
        # if we reset the book, force a full update
        forced = False
        is_partial = msg['action'] == 'partial'
        if not self.partial_received:
            # per bitmex documentation messages received before partial
            # should be discarded
            if not is_partial:
                print("return")
                return
            else:
                self.partial_received = True
            forced = True

        if is_partial or msg['action'] == 'insert':
            for data in msg['data']:
                side = BID if data['side'] == 'Buy' else ASK
                price = data['price']
                pair = data['symbol']
                size = data['size']
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
                update_size = data['size']
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
            self.logger.warning(f"{self.get_nane()}: Unexpected L3 Book message {msg}")
            return

        await self.callbacks[L3_BOOK](feed=self.get_name(),
                                      symbol=self.get_pair_from_exchange(pair),
                                      asks=self.l3_book[pair][ASK],
                                      bids=self.l3_book[pair][BID],
                                      forced=forced)

    async def subscribe(self):
        chans = []
        for channel in self.channels:
            for pair in self.pairs:
                chans.append("{}:{}".format(channel, pair))

        await self.__send_command("subscribe", chans)

    async def __send_command(self, command, args):
        await self.websocket.send(json.dumps({"op": command, "args": args or []}))

    def get_auth(self):
        """Return auth headers. Will use API Keys if present in settings."""
        if self.api_key:
            self.logger.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            expires = generate_nonce()
            return [
                "api-expires: " + str(expires),
                "api-signature: " + generate_signature(self.api_secret, 'GET', '/realtime', expires, ''),
                "api-key:" + self.api_key
            ]
        else:
            self.logger.info("Not authenticating.")
            return []

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
        return 'quote'

    @classmethod
    def get_volume_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_candle_feed(cls):
        return UNSUPPORTED

    @classmethod
    def get_funding_feed(cls):
        return 'funding'

    @classmethod
    def get_margin_feed(cls):
        return 'margin'

    @classmethod
    def get_position_feed(cls):
        return 'position'

    @staticmethod
    def timestamp_normalize(ts):
        return calendar.timegm(dt.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").utctimetuple())

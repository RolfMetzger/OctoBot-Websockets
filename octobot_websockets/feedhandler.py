"""
Copyright (C) 2017-2019  Bryant Moscon - bmoscon@gmail.com

Please see the LICENSE file for the terms and conditions
associated with this software.
"""
import asyncio
import logging
from asyncio import CancelledError
from datetime import datetime as dt
from datetime import timedelta
from socket import error as socket_error

import websockets
from websockets import ConnectionClosed

from octobot_websockets.feed import Feed


class FeedHandler:
    def __init__(self, retries=10, timeout_interval=5):
        """
        retries: int
            number of times the connection will be retried (in the event of a disconnect or other failure)
        timeout_interval: int
            number of seconds between checks to see if a feed has timed out
        """
        self.feeds = []
        self.retries = retries
        self.timeout = {}
        self.last_msg = {}
        self.timeout_interval = timeout_interval
        self.exchanges = {feed.get_name(): feed for feed in Feed.__subclasses__()}

        self.loop = asyncio.get_event_loop()
        self.feed_tasks = []

        self.logger = logging.getLogger(self.__class__.__name__)

    def add_feed(self, feed, timeout=120, **kwargs):
        """
        feed: str or class
            the feed (exchange) to add to the handler
        timeout: int
            number of seconds without a message before the feed is considered
            to be timed out. The connection will be closed, and if retries
            have not been exhausted, the connection will be restablished
        kwargs: dict
            if a string is used for the feed, kwargs will be passed to the
            newly instantiated object
        """
        if isinstance(feed, str):
            if feed in self.exchanges:
                self.feeds.append(self.exchanges[feed](**kwargs))
                feed = self.exchanges[feed]
            else:
                raise ValueError("Invalid feed specified")
        else:
            self.feeds.append(feed)
        self.last_msg[feed.get_name()] = None
        self.timeout[feed.get_name()] = timeout

    def run(self):
        if not self.feeds:
            self.logger.error('No feeds specified')
            raise ValueError("No feeds specified")

        try:
            for feed in self.feeds:
                self.feed_tasks.append(self.loop.create_task(self._connect(feed)))

            # asyncio.gather(*asyncio.all_tasks())
            self.loop.run_until_complete(asyncio.gather(*self.feed_tasks))
        except KeyboardInterrupt:
            self.logger.info("Keyboard Interrupt received - shutting down")
        except Exception as e:
            self.logger.error(f"Unhandled exception : {e}")

    def stop(self):
        for task in self.feed_tasks:
            task.cancel()

    async def _watch(self, feed_id, websocket):
        while websocket.open:
            if self.last_msg[feed_id]:
                if dt.utcnow() - timedelta(seconds=self.timeout[feed_id]) > self.last_msg[feed_id]:
                    self.logger.warning("%s: received no messages within timeout, restarting connection", feed_id)
                    await websocket.close()
                    break
            await asyncio.sleep(self.timeout_interval)

    async def _connect(self, feed):
        """
        Connect to websocket feeds
        """
        retries = 0
        delay = 1
        watch_task = None
        while retries <= self.retries:
            self.last_msg[feed.get_name()] = None
            try:
                async with websockets.connect(feed.address) as websocket:
                    watch_task = asyncio.create_task(self._watch(feed.get_name(), websocket))
                    # connection was successful, reset retry count and delay
                    retries = 0
                    delay = 1
                    await feed.subscribe(websocket)
                    await self._handler(websocket, feed.message_handler, feed.get_name())
            except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError, socket_error) as e:
                self.logger.warning("%s: encountered connection issue %s - reconnecting...", feed.get_name(), str(e))
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2
            except Exception:
                self.logger.error("%s: encountered an exception, reconnecting", feed.get_name(), exc_info=True)
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2
        try:
            watch_task.cancel()
        except Exception:
            self.logger.error("Failed to cancel watch task")

        self.logger.error("%s: failed to reconnect after %d retries - exiting", feed.get_name(), retries)

    async def _handler(self, websocket, handler, feed_id):
        async for message in websocket:
            self.last_msg[feed_id] = dt.utcnow()
            try:
                await handler(message)
            except Exception:
                self.logger.error("%s: error handling message %s", feed_id, message)
                # exception will be logged with traceback when connection handler
                # retries the connection
                raise

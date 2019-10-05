#  Drakkar-Software OctoBot-Websockets
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from octobot_websockets.data.book import Book


def test_create_book():
    book = Book()
    assert not book.asks
    assert not book.bids
    assert book.timestamp == 0


def test_update_book():
    book = Book()
    book.handle_book_update([[100.3, 0.112504], [100.5, 0.484882], [100.1, 2.0]],
                            [[100.5, 0.126516], [101.01, 0.49906]])
    assert book.timestamp != 0
    assert book.asks
    assert book.bids

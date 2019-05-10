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
import operator
from time import time

cdef class Book:
    cdef public timestamp
    cdef public list bids
    cdef public list asks

    def __init__(self):
        self.asks = []
        self.bids = []
        self.timestamp = 0

    cpdef handle_book_update(self, list bids, list asks):
        self.bids = sorted(bids, key=operator.itemgetter(0), reverse=True)
        self.asks = sorted(asks, key=operator.itemgetter(0))
        self.timestamp = time()

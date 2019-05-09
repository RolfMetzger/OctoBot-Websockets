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
from time import time

cdef class Candle:
    cdef double start_timestamp
    cdef int time_frame_size
    cdef public double close_timestamp
    cdef public float high
    cdef public float low
    cdef public float opn
    cdef public float close
    cdef public float vol
    cdef public int is_closed

    def __init__(self, float price, int time_frame_size):
        self.is_closed = False
        self.opn = price
        self.high = price
        self.low = price
        self.close = price
        self.vol = 0
        self.start_timestamp = time()
        self.time_frame_size = time_frame_size
        self.close_timestamp = 0


    cpdef handle_candle_update(self, float price, float vol):
        if self.high < price:
            self.high = price
    
        if self.low > price:
            self.low = price
    
        self.close = price
        self.vol += vol
    
        if time() - self.start_timestamp >= self.time_frame_size:
            self.is_closed = True
            self.close_timestamp = time()


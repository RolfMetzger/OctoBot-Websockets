# cython: language_level=3
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

cdef class Candle:
    cdef double time_frame_size
    cdef public double start_timestamp
    cdef public double close_timestamp
    cdef public double high
    cdef public double low
    cdef public double opn
    cdef public double close
    cdef public double vol
    cdef public bint is_closed

    cpdef handle_candle_update(self, double price, double vol)
    cpdef on_close(self)

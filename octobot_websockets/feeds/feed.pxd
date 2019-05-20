#cython: language_level=2
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

cdef class Feed:
    cdef str api_key
    cdef str api_secret
    cdef str address

    cdef int timeout
    cdef int timeout_interval
    cdef int book_update_interval
    cdef int updates

    cdef bint create_loop
    cdef bint is_connected
    cdef bint do_deltas
    cdef bint should_stop

    cdef list pairs
    cdef list time_frames
    cdef list channels

    cdef public dict callbacks

    # objects
    cdef object loop
    cdef object logger
    cdef object websocket
    cdef object ccxt_client
    cdef object async_ccxt_client
    cdef object _watch_task
    cdef object _websocket_task
    cdef object last_msg

    cdef __initialize(self, list pairs, list channels, dict callbacks)
    cpdef start(self)
    cdef on_close(self)
    cpdef stop(self)
    cpdef close(self)
    cdef list get_auth(self)
    cdef list get_pairs(self)
    cdef double fix_timestamp(self, double ts)
    cdef double timestamp_normalize(self, double ts)
    cdef str get_pair_from_exchange(self, str pair)
    cdef str get_exchange_pair(self, str pair)
    cdef str feed_to_exchange(self, feed)
    cdef float safe_float(self, dict dictionary, key, default_value)

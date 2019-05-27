# cython: language_level=3

cdef class Callback(object):
    cdef object callback

cdef class TradeCallback(Callback):
    pass

cdef class TickerCallback(Callback):
    pass

cdef class CandleCallback(Callback):
    pass

cdef class KlineCallback(Callback):
    pass

cdef class BookCallback(Callback):
    pass

cdef class OrdersCallback(Callback):
    pass

cdef class PositionCallback(Callback):
    pass

cdef class UpdatedBookCallback(Callback):
    pass

cdef class FundingCallback(Callback):
    pass

cdef class PortfolioCallback(Callback):
    pass

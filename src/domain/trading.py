from heapq import heappush, heappop
from enum import Enum
from decimal import Decimal, getcontext, ROUND_UP

from config import VWAP


getcontext().rounding = ROUND_UP


class TradingPair(Enum):
    BTC_USD = 'BTC-USD'
    ETH_USD = 'ETH-USD'
    ETH_BTC = 'ETH-BTC'


class MessageType(Enum):
    ERROR = 'error'
    SUBSCRIPTIONS = 'subscriptions'
    MATCH = 'match'


class Processor:
    def __init__(self, trading_pair: TradingPair):
        self._trading_pair = trading_pair
        self._trades = []

        # helper properties
        self._cumulative_value = Decimal(0)
        self._cumulative_volume = Decimal(0)

    def add_trade(self, trade):
        self._cumulative_value += trade['price']*trade['size']
        self._cumulative_volume += trade['size']
        heappush(self._trades, (trade['sequence'], trade))

        if len(self._trades) > VWAP.DATA_POINTS_COUNT:
            _, oldest_trade = heappop(self._trades)
            self._cumulative_value -= oldest_trade['price'] * trade['size']
            self._cumulative_volume -= oldest_trade['size']

    @property
    def trades(self):
        return self._trades

    @trades.setter
    def trades(self, trades):
        self._trades = trades

    @property
    def vwap(self):
        value = self._cumulative_value / self._cumulative_volume
        return value.quantize(Decimal('.00000001'))

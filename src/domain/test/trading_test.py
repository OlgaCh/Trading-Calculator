import random

from unittest import TestCase
from copy import deepcopy
from decimal import Decimal
from datetime import datetime

from config import VWAP
from domain.trading import (
    TradingPair,
    MessageType,
    Processor,
)


def create_deserialized_trade(**kwargs):
    return dict({
        'type': MessageType.MATCH,
        'price': Decimal(10),
        'size': Decimal(1),
        'sequence': random.randint(10000, 90000),
        'time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
    }, **kwargs)


class TradingTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        VWAP.DATA_POINTS_COUNT = 5

    def setUp(self):
        super().setUp()

        self.processor = Processor(TradingPair.BTC_USD)

    def test_should_add_trades_based_on_sequence(self):
        for i in range(5):
            t = create_deserialized_trade(sequence=(i+1)*10 if i % 2 == 0 else i)
            self.processor.add_trade(t)

        self.assertEqual(len(self.processor.trades), 5)

        # Next attempt to add trade should remove trade with minimal sequence (i.e. 1) from the trades
        self.processor.add_trade(create_deserialized_trade(sequence=1000))

        sequences = [t[0] for t in self.processor.trades]
        self.assertEqual(len(self.processor.trades), 5)
        self.assertNotIn(1, sequences)

        # Attempt to add trade with sequence lower than minimal should not update trades list
        old_trades = deepcopy(self.processor.trades)
        self.processor.add_trade(create_deserialized_trade(sequence=2))

        self.assertEqual(old_trades, self.processor.trades)

    def test_should_calculate_vwap(self):
        expected_vwap = Decimal(3)

        for i in range(5):
            t = create_deserialized_trade(price=Decimal(i+1), size=Decimal(1))
            self.processor.add_trade(t)

        vwap = self.processor.vwap

        self.assertEqual(expected_vwap, vwap)

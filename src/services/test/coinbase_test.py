import websockets

from unittest import TestCase, IsolatedAsyncioTestCase
from parameterized import parameterized

from copy import deepcopy
from decimal import Decimal
from datetime import datetime
from marshmallow.exceptions import ValidationError

from config import Coinbase
from domain.trading import TradingPair
from services.coinbase import SubscribeSchema, ConsumeSchema, subscribe, consume


class SubscribeSerializeTestCase(TestCase):
    def test_should_serialize_subscribe_message(self):
        expected_message = {
            'type': 'subscribe',
            'channels': [Coinbase.CHANNEL],
            'product_ids': [TradingPair.BTC_USD.value]
        }

        message = SubscribeSchema().dump(dict(channels=[Coinbase.CHANNEL], product_ids=[TradingPair.BTC_USD.value]))

        self.assertEqual(message, expected_message)


class ConsumeDeserializeTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.message = {
            'type': 'match',
            'trade_id': 151784501,
            'maker_order_id': 'e397d156-1134-43ff-a0b7-8b6109321033',
            'taker_order_id': 'a7963b81-7b29-4fb6-85c3-333d215fb219',
            'side': 'sell',
            'size': '0.0241',
            'price': '58050.02',
            'product_id': 'BTC-USD',
            'sequence': 23369758602,
            'time': '2021-04-01T18:19:16.243055Z'
        }

    def test_should_deserialize_message_ok(self):
        expected_message = {
            'type': 'match',
            'size': Decimal('0.0241'),
            'price': Decimal('58050.02'),
            'product_id': 'BTC-USD',
            'sequence': 23369758602,
            'time': datetime.strptime('2021-04-01T18:19:16.243055Z', '%Y-%m-%dT%H:%M:%S.%f%z')
        }

        deserialized = ConsumeSchema().load(self.message)

        self.assertEqual(deserialized, expected_message)

    @parameterized.expand([
        ['type'], ['size'], ['price'], ['product_id'], ['sequence'], ['time']
    ])
    def test_should_raise_validation_error_on_missing_data(self, p_missing):
        message = deepcopy(self.message)
        message.pop(p_missing)

        with self.assertRaises(ValidationError):
            ConsumeSchema().load(message)

    @parameterized.expand([
        ['type'], ['size'], ['price'], ['product_id'], ['sequence'], ['time']
    ])
    def test_should_raise_validation_error_on_null_data(self, p_empty):
        message = deepcopy(self.message)
        message[p_empty] = None

        with self.assertRaises(ValidationError):
            ConsumeSchema().load(message)

    @parameterized.expand([
        ['size'], ['price']
    ])
    def test_should_raise_validation_error_on_wrong_numeric_data(self, p_field):
        message = deepcopy(self.message)
        message[p_field] = 0

        with self.assertRaises(ValidationError):
            ConsumeSchema().load(message)

    @parameterized.expand([
        ['type', 'last_match'],
        ['product_id', 'EUR-USD']
    ])
    def test_should_raise_validation_error_on_data_mismatch(self, p_field, p_value):
        message = deepcopy(self.message)
        message[p_field] = p_value

        with self.assertRaises(ValidationError):
            ConsumeSchema().load(message)


async def wait():
    import time
    time.sleep(1)


class EventLoopTestCase(IsolatedAsyncioTestCase):
    async def test_connect_ok_and_process_messages(self):
        async with websockets.connect(Coinbase.URL, ssl=True) as websocket:
            with self.assertLogs(level='INFO') as logs:
                await subscribe(websocket)
                await wait()  # trick to collect some messages from websocket
                await websocket.close()   # should gracefully close connection to not start consuming too many messages
                await consume(websocket)

            self.assertTrue(f"Successfully connected to {Coinbase.CHANNEL} channel." in ' '.join(logs.output))
            # Do not process messages with type other than "match"
            self.assertTrue("Skip processing message. Error: {'type': ['Must be one of: match.']}"
                            in ' '.join(logs.output))
            # Calculate indicators based on ws data
            self.assertTrue("[VWAP]" in ' '.join(logs.output))

    async def test_connection_error(self):
        async with websockets.connect(Coinbase.URL, ssl=True) as websocket:
            with self.assertLogs(level='WARNING') as logs:
                await websocket.send('{"a": "b"}')
                await consume(websocket)
            self.assertTrue(f"Error connecting to {Coinbase.CHANNEL} channel. "
                            f"Closing connection" in ' '.join(logs.output))

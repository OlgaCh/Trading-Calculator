import sys
import json
import logging
import websockets

from marshmallow import Schema, EXCLUDE, fields, validate
from marshmallow.exceptions import ValidationError
from logging import getLogger

from config import Coinbase
from domain.trading import TradingPair, MessageType, Processor


logger = getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


TRADING_PAIRS = [tp.value for tp in TradingPair]
TRADES = {tp: Processor(tp) for tp in TRADING_PAIRS}


class SubscribeSchema(Schema):
    type = fields.Constant('subscribe')
    channels = fields.List(fields.String(), required=True)
    product_ids = fields.List(fields.String(), required=True)


class ConsumeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.String(required=True, allow_none=False, validate=validate.OneOf([MessageType.MATCH.value]))
    product_id = fields.String(required=True, allow_none=False, validate=validate.OneOf(TRADING_PAIRS))
    price = fields.Decimal(required=True, allow_none=False, validate=validate.Range(min=1e-8))
    size = fields.Decimal(required=True, allow_none=False, validate=validate.Range(min=1e-8))
    sequence = fields.Int(required=True, allow_none=False)
    time = fields.DateTime(required=True, allow_none=False)


async def event_loop():
    async with websockets.connect(Coinbase.URL, ssl=True) as websocket:
        await subscribe(websocket)
        await consume(websocket)


async def subscribe(websocket):
    await websocket.send(json.dumps(
        SubscribeSchema().dump(dict(channels=[Coinbase.CHANNEL],
                                    product_ids=TRADING_PAIRS))
    ))


async def consume(websocket):
    async for message in websocket:
        message = json.loads(message)

        if message['type'] == MessageType.SUBSCRIPTIONS.value:
            logger.info(f"Successfully connected to {Coinbase.CHANNEL} channel.")
        elif message['type'] == MessageType.ERROR.value:
            logger.warning(f"Error connecting to {Coinbase.CHANNEL} channel. Closing connection")
            await websocket.close()
        else:
            process(message)


def process(message):
    try:
        data = ConsumeSchema().load(message)
    except ValidationError as e:
        logger.warning(f"Skip processing message. Error: {str(e)}")
        return

    processor = TRADES.get(data['product_id'])
    processor.add_trade(data)

    logger.info(f"[VWAP][{data['product_id']}] {processor.vwap}")

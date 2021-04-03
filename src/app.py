import asyncio

from services.coinbase import event_loop


if __name__ == '__main__':
    asyncio.run(event_loop())

# Trading Calculator

**Trading Calculator** allows getting various indicators based on real-time data from the [Coinbase feed](https://docs.pro.coinbase.com/#the-matches-channel).

Current version supports [VWAP](https://en.wikipedia.org/wiki/Volume-weighted_average_price) indicator only. It is calculated based on `N`(configurable) most recent trades.

## Prerequisites

Project running using `docker-compose`. Make sure you have `docker-compose` of version 1.27.4 or greater installed.

## Building Trading Calculator

To build docker images, run:

```
docker-compose build
```

It will create images for the application and the test suite.

## Using Trading Calculator

### Application

To run the application:

```
docker-compose run app
```

Sample output will look like:
```
[INFO] Successfully connected to matches channel.
[INFO] [VWAP][ETH-BTC] 0.03563000
[INFO] [VWAP][BTC-USD] 59347.18000000
[INFO] [VWAP][ETH-USD] 2114.25000000
[INFO] [VWAP][BTC-USD] 59347.18000000
[INFO] [VWAP][ETH-USD] 2114.25000000
```

Each line has information about the indicator, trading pair, and the calculated value.

To stop application use `Ctrl+C`.

### Tests

To execute tests:

```
docker-compose run test
```

## Implementation Notes

The current version using [heapq](https://docs.python.org/3/library/heapq.html) to keep in the memory last `N` trades and
use those for the indicators calculations. It does allow to push/pop trades in `O(log n)` but won't be sufficient if we
need to calculate indicators based on 10^k trades per each pair. 

Another limitation is related to the data persistence. Since all data kept in memory there is no way to reconcile the 
calculated indicators vs trades, same as recover current calculation if app exit unexpectedly.

As a mitigation for this we can dump real-time data into file (CSV or HDF5 format). An async process can then pull data 
from the files and run data-aggregation logic using [Pandas](https://pandas.pydata.org/).

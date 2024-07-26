import datetime
import time
import numpy as np
import pandas as pd
import urllib.request
import urllib.error
from .utils import create_null_logger

def url_exists(url):
    try:
        time.sleep(1)
        res = urllib.request.urlopen(url)
        if res.getcode() == 200:
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} for URL: {url}")
    except Exception as e:
        print(f"Error: {str(e)} for URL: {url}")
    return False

def url_read_csv(url):
    try:
        time.sleep(1)
        df = pd.read_csv(url)
        df = df.rename(columns={
            'symbol': 'market',
        })
        df['price'] = df['price'].astype('float64')
        df['size'] = df['size'].astype('float64')
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df['side'] = np.where(df['side'] == 'BUY', 1, -1).astype('int8')
        return df
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} for URL: {url}")
    except Exception as e:
        print(f"Error: {str(e)} for URL: {url}")
    return None

class GmoFetcher:
    def __init__(self, market, logger=None, ccxt_client=None, memory=None):
        self.market = market
        self.logger = logger if logger is not None else create_null_logger()
        self.ccxt_client = ccxt_client
        self.memory = memory

        if memory is None:
            self._url_exists = url_exists
            self._url_read_csv = url_read_csv
        else:
            url_exists_cached = memory.cache(url_exists)
            self._url_exists = url_exists_cached
            url_read_csv_cached = memory.cache(url_read_csv)
            self._url_read_csv = url_read_csv_cached

    def fetch_ohlcv(self, interval_sec=None, market=None):
        return self.fetch_trades(market=market, interval_sec=interval_sec)

    def fetch_trades(self, market=None, interval_sec=None):
        if interval_sec is not None:
            if 3600 % interval_sec != 0:
                raise Exception('3600 % interval_sec must be 0')
        today = datetime.datetime.now().date()
        start_year, start_month, start_day = self._find_start_year_month(market)
        date = datetime.date(start_year, start_month, start_day)
        dfs = []
        date_range = pd.date_range(start=date, end=today - datetime.timedelta(days=1), freq='D')
        for date in date_range:
            url = 'https://api.coin.z.com/data/trades/{}/{}/{:02}/{}{:02}{:02}_{}.csv.gz'.format(
                market,
                date.year,
                date.month,
                date.year,
                date.month,
                date.day,
                market,
            )
            self.logger.debug(f"Accessing URL: {url}")
            df = self._url_read_csv(url)
            if df is not None:
                if interval_sec is not None:
                    df['timestamp'] = df['timestamp'].dt.floor(f'{interval_sec}S')
                    df = df.groupby('timestamp').agg({
                        'price': ['first', 'max', 'min', 'last'],
                        'size': 'sum'
                    })
                    df.columns = ['op', 'hi', 'lo', 'cl', 'volume']
                dfs.append(df)

        if len(dfs) == 0:
            self.logger.debug("No data found for the specified period and market.")
            return pd.DataFrame()

        df = pd.concat(dfs)

        if interval_sec is None:
            df.reset_index(drop=True, inplace=True)

        return df

    def _find_start_year_month(self, market):
        today = datetime.datetime.now().date()
        start_year = None
        start_month = None
        start_day = None

        for year in range(2018, today.year + 1):
            for month in range(1, 13):
                url = f'https://api.coin.z.com/data/trades/{market}/{year}/{month:02}/'
                if self._url_exists(url):
                    start_year = year
                    start_month = month
                    for day in range(1, 32):
                        test_url = f'https://api.coin.z.com/data/trades/{market}/{year}/{month:02}/{year}{month:02}{day:02}_{market}.csv.gz'
                        if self._url_exists(test_url):
                            start_day = day
                            return start_year, start_month, start_day
        return start_year, start_month, start_day


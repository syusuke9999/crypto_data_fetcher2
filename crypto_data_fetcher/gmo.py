import datetime
import time
import numpy as np
import pandas as pd
import urllib.request
import urllib.error
from .utils import create_null_logger
from tqdm import tqdm


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

    def fetch_ohlcv(self, interval_sec=900, market=None):
        if market is None:
            market = self.market
        return self.fetch_trades(market, interval_sec)

    def fetch_trades(self, market, interval_sec, start_year=None, start_month=None,start_day=None):
        today = datetime.datetime.now().date()
        if start_year is None:
            start_year = 2018
            start_month = 9
            start_day = 5
        date = datetime.date(start_year, start_month, start_day)
        dfs = []
        date_range = pd.date_range(start=date, end=today - datetime.timedelta(days=1), freq='D')
        for date in tqdm(date_range):
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
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', drop=True, inplace=True)
                ohlcv = df.resample(f'{interval_sec}S').agg({
                    'price': ['first', 'max', 'min', 'last'],
                    'size': 'sum'
                })
                ohlcv.columns = ['op', 'hi', 'lo', 'cl', 'volume']  # 列名をリネーム
                dfs.append(ohlcv)
        if len(dfs) == 0:
            self.logger.debug("No data found for the specified period and market.")
            return pd.DataFrame()
        df = pd.concat(dfs)
        return df

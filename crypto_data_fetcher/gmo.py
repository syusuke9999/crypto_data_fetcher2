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
    def __init__(self, logger=None, ccxt_client=None, memory=None):
        self.logger = create_null_logger() if logger is None else logger
        self.ccxt_client = ccxt_client

        if memory is None:
            self._url_exists = url_exists
            self._url_read_csv = url_read_csv
        else:
            url_exists_cached = memory.cache(url_exists)
            self._url_exists = url_exists_cached

            url_read_csv_cached = memory.cache(url_read_csv)
            self._url_read_csv = url_read_csv_cached

    def generate_url(self, year, month, day):
        date_str = f"{year}{month:02d}{day:02d}"
        url = f"https://api.coin.z.com/data/trades/{self.market}/{year}/{month:02}/{date_str}_{self.market}.csv.gz"
        return url

    def fetch_ohlcv(self, interval_sec=None, market=None):
        return self.fetch_trades(market=market, interval_sec=interval_sec)

    def fetch_trades(self, market=None, interval_sec=None):
        if interval_sec is not None:
            if 3600 % interval_sec != 0:
                raise Exception('3600 % interval_sec must be 0')

        today = datetime.datetime.now().date()
        start_year, start_month = self._find_start_year_month(market)
        date = datetime.date(start_year, start_month, 1)

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
                    df['timestamp'] = df['timestamp'].dt.floor('{}S'.format(interval_sec))
                    df = pd.concat([
                        df.groupby('timestamp')['price'].nth(0).rename('op'),
                        df.groupby('timestamp')['price'].max().rename('hi'),
                        df.groupby('timestamp')['price'].min().rename('lo'),
                        df.groupby('timestamp')['price'].nth(-1).rename('cl'),
                        df.groupby('timestamp')['size'].sum().rename('volume'),
                    ], axis=1)
                dfs.append(df)

        if len(dfs) == 0:
            self.logger.debug("No data found for the specified period and market.")
            return pd.DataFrame()  # 空のデータフレームを返す

        df = pd.concat(dfs)

        if interval_sec is None:
            df.reset_index(drop=True, inplace=True)

        return df

    def _find_start_year_month(self, market):
        today = datetime.datetime.now().date()

        for year in range(2018, today.year + 1):
            url = 'https://api.coin.z.com/data/trades/{}/{}/'.format(market, year)
            self.logger.debug(f"Checking URL: {url}")
            if self._url_exists(url):
                start_year = year
                break

        for month in range(1, 13):
            url = 'https://api.coin.z.com/data/trades/{}/{}/{:02}/'.format(market, start_year, month)
            self.logger.debug(f"Checking URL: {url}")
            if self._url_exists(url):
                start_month = month
                break

        return start_year, start_month

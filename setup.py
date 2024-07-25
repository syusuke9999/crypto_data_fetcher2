#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="crypto_data_fetcher",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "ccxt==4.3.67",
        "lightgbm==4.4.0",
        "TA-Lib==0.4.21",
        "pandas",
        "numpy",
        "joblib",
    ]
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="crypto_data_fetcher",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "ccxt==1.60.0",
        "lightgbm==3.2.1",
        "TA-Lib==0.4.21"
    ]
)


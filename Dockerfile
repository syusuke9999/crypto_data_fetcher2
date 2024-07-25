FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    libtool \
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && make && make install

COPY . /app

RUN pip install pipenv
RUN pipenv lock
RUN pipenv install --deploy --ignore-pipfile

# アプリケーションを実行（必要に応じて変更）
CMD ["pipenv", "run", "python", "crypto_data_fetcher/gmo.py"]

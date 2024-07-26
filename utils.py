import logging


def create_null_logger():
    # ロガーを取得し、最低限のログレベルを設定
    logger = logging.getLogger("GmoFetcher")
    logger.setLevel(logging.CRITICAL)  # CRITICAL以上のログのみ出力（実質的に何も出力しない）

    return logger


def create_url_logger():
    logger = logging.getLogger("URLLogger")
    logger.setLevel(logging.DEBUG)  # デバッグレベルのログを設定

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
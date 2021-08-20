"""logging.Loggerのインスタンスを作成する

"""
from logging import DEBUG, INFO, FileHandler, Formatter, StreamHandler, getLogger


def set_logger(logpath=None, is_debug=False, modname=''):
    """logging.Loggerのインスタンスを作成する

    Args:
        logpath (str, opt): ログファイルの作成先. Defaults to None.
        is_debug (bool, opt): デバッグ実行フラグ. Defaults to False.
        modname (str, bool): ログの出力に使うプログラム名. Defaults to 'sawara'.

    Returns:
        logging.Loggerのインスタンス

    Note:
        logpathを設定しない場合は標準出力のみ行われる
    """
    logger = getLogger(modname)
    logger.setLevel(DEBUG)

    # Stream: ログの標準出力
    sh = StreamHandler()
    if not is_debug:
        sh.setLevel(INFO)
    sh_formatter = Formatter('[%(levelname)s] %(message)s')
    sh.setFormatter(sh_formatter)
    logger.addHandler(sh)

    # File: ログのファイル出力
    if logpath:
        fh = FileHandler(logpath)
        fh.setLevel(INFO)
        fh_formatter = Formatter(
            '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
            '%y-%m-%d %H:%M:%S',
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

    return logger

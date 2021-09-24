"""TODO

encoding: http://www.yamamo10.jp/yamamoto/comp/latex/run/inline_frame/char_code.php

"""
from datetime import datetime
import glob
import os
import re
import shutil
import subprocess
import sys

# 起動元によって対応
try:
    from set_logger import set_logger
except ImportError:
    from .set_logger import set_logger


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, '_log')
WORK_DIR = os.path.join(BASE_DIR, '_work')
SAVE_DIR = os.path.join(BASE_DIR, '_result')


def _initialize():
    logname = datetime.now().strftime('%Y%m%d_%H%M%S.txt')
    logpath = os.path.join(LOG_DIR, logname)
    return set_logger(logpath=logpath)


def _output_error(logger, log_text_l):
    """LaTeXコンパイルのエラーと警告をログに出力する
    詳細は以下のリファレンスを参照
    https://texwiki.texjp.org/?LaTeX%20のエラーメッセージ
    """
    pattern_dict = {
        # groups(): (error position, match_type, message)
        'error': re.compile(r'(.+:(?:\d+): |! )(LaTeX Error: )?(.+)'),
        'warning': re.compile(r'(.+\..+:(?:\d+): )?(LaTeX (?:.* )?Warning: )(.+)'),
    }
    for row in range(len(log_text_l)):
        text = log_text_l[row].strip()
        for key, pattern in pattern_dict.items():
            # エラーと警告のログを出力する
            res = pattern.match(text)
            if res is None:
                # マッチしていなければスキップ
                continue

            # print(res.groups())
            content = 'TeX Compile: ' + res.group(3)
            indent_cnt = 0
            for i in range(1, 3):
                if res.group(i) is not None:
                    indent_cnt += len(res.group(i))
            while len(log_text_l[row + 1].strip()) > 0:
                text = log_text_l[row + 1].strip()
                # 複数行の出力は1行にまとめる
                if len(text) > indent_cnt:
                    # インデントがある場合は除く
                    content += ' ' + text[indent_cnt:]
                else:
                    # インデントがない場合
                    content += text
                row += 1

            # エラーポジションがあれば追記する
            if res.group(1) is not None:
                content += ' at ' + res.group(1)
            if key == 'error':
                logger.error(content)
            elif key == 'warning':
                logger.warning(content)
            break

    return


def compile_tex(src_dir, dst_dir=SAVE_DIR, logger=None):
    """TeXファイルをコンパイルする

    Args:
        src_dir (str): ソースファイルのディレクトリ
        dst_dir (:obj:`str`, optional): ファイルを出力するディレクトリ
        logger (:obj:`logging.Logger`, optional): ロガー(なければ作る)

    Returns:
        dict:
            `'filename'`: 出力ファイル名
            `'content'`: 出力PDFのバイナリデータ
    """
    if logger is None:
        logger = set_logger()

    # TeXファイルが1つだけ存在することを確認する
    tex_list = glob.glob(os.path.join(src_dir, '**', '*.tex'), recursive=True)
    if len(tex_list) == 0:
        logger.critical('TeXファイルが見つかりません。')
        return None
    if len(tex_list) > 1:
        logger.critical('TeXファイルが複数存在し、一意に特定できません。')
        return None

    # まず作業ディレクトリにファイルをコピーする
    if os.path.isdir(WORK_DIR):
        shutil.rmtree(WORK_DIR)

    shutil.copytree(src_dir, WORK_DIR)
    logger.debug('ソースデータを複製')

    # 次にカレントディレクトリを作業ディレクトリに変更
    current_dir = os.getcwd()
    os.chdir(WORK_DIR)
    src_path = glob.glob(os.path.join(WORK_DIR, '**', '*.tex'), recursive=True)[0]

    # dviファイルの生成
    command = [
        'platex',
        # '-halt-on-error',
        src_path,
        # TODO: encoding
    ]
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    cnt = 0
    while cnt < 1000:
        # エラーが出るたびにEnter入力して強制進行する
        proc.stdin.write('\n'.encode())
        proc.stdin.flush()
        cnt += 1
        text = proc.stdout.read().decode().strip()
        if 'Transcript written' in text:
            # 処理完了を検知したら出る
            break

    # ログの出力
    tex_log_path = src_path[:-3] + 'log'
    if os.path.isfile(tex_log_path):
        with open(tex_log_path) as f:
            log_text = f.readlines()
        _output_error(logger, log_text)
    else:
        logger.warning('TeXのコンパイルログがありません。')

    dvi_path = src_path[:-3] + 'dvi'
    if not os.path.isfile(dvi_path):
        logger.error('tex -> dvi: 失敗')
        return None

    logger.info('tex -> dvi: 成功')

    # pdfの生成
    command = ['dvipdfmx', dvi_path]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_path = src_path[:-3] + 'pdf'
    if not os.path.isfile(pdf_path):
        logger.error('dvi -> pdf: 失敗')
        return None

    logger.info('dvi -> pdf: 成功')
    # pdfのバイナリを返す
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    # キャッシュを削除する
    shutil.rmtree(WORK_DIR)
    filename = os.path.basename(pdf_path)
    os.chdir(current_dir)
    return {'filename': filename, 'content': pdf_data}


def main(args):
    logger = _initialize()
    if len(args) == 1:
        logger.critical('コンパイルする作業フォルダを指定してください')
        return

    src_dir = args[1]
    if not (src_dir[0] == '/' or src_dir[1:3] == ':\\'):
        src_dir = os.path.join(BASE_DIR, src_dir)

    if not os.path.isdir(src_dir):
        logger.critical('無効なフォルダです')
        return

    # コンパイル処理
    response = compile_tex(src_dir, logger=logger)
    if response is None:
        logger.info('処理を中止しました')
        return

    # pdf生成に成功した場合
    os.makedirs(SAVE_DIR, exist_ok=True)
    save_pdf_path = os.path.join(SAVE_DIR, response['filename'])
    if os.path.isfile(save_pdf_path):
        logger.warning('既に同名のファイルが存在するため、上書き保存します。')

    with open(save_pdf_path, 'wb') as f:
        f.write(response['content'])

    logger.info('PDFファイル生成完了')
    return


if __name__ == '__main__':
    main(sys.argv)

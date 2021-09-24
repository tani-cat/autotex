# autoTeX
TeXファイルを自動でコンパイルしPDFを生成するモジュール

## 前準備
以下のTeX環境を用意してください。

- pLaTeX
- dvipdfmx

## 手元で実行する場合
```sh
# shell
python autotex.py ソースディレクトリ
```

### 結果

## モジュールとして利用する場合
```python
# python
from autotex import compile_tex
compile_tex('src_dir', dst_dir='dst_dir', logger=logger)
```

# QRコード生成ツール

Flaskで動く最小構成のQRコード生成Webアプリです。フォームに入力したテキストからPNGのQRコードをインメモリ生成し、画面にプレビュー表示してダウンロードできます。

## ファイル構成

- `app.py`: アプリ本体
- `requirements.txt`: 依存関係
- `.gitignore`: Git除外設定

## ローカル実行

```bash
python -m venv env && source env/bin/activate
```

Windows:

```powershell
env\Scripts\activate
```

依存をインストールして起動します。

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで `http://localhost:8000` を開いてください。

## Render公開

1. GitHubへこのプロジェクトをプッシュします。
2. Renderで `New` → `Web Service` を選びます。
3. GitHubリポジトリを接続します。
4. 設定を以下にします。

- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`

### よくある失敗

- `PORT` に未対応だとRender上で起動失敗します。
- `127.0.0.1` 待受だと外部公開されません。`0.0.0.0` で待受してください。
- `ModuleNotFoundError` は `requirements.txt` 未コミットや依存不足で起きやすいです。

## 使い方

1. テキストを入力します。
2. `QRコードを生成` を押します。
3. 画面にQRプレビュー（PNG）が表示されます。
4. 必要なら `PNGをダウンロード` を押します。

任意で以下も指定できます。

- サイズ（px）
- 余白（border）
- 誤り訂正レベル（L / M / Q / H）

## セキュリティ / 制限

- 入力テキストは最大500文字までです。
- 空文字は拒否します。
- 画像サイズは 128px から 1024px までに制限しています。
- 余白は 0 から 20 までに制限しています。
- 画像ファイルは保存せず、`io.BytesIO` でインメモリ生成します。

## 失敗時ヒント

- 依存エラーが出る場合は `pip install -r requirements.txt` を再実行してください。
- ポート競合時は `PORT=8001` などを設定して起動してください。
- 文字数超過やサイズ超過の場合は、入力値を制限内に収めてください。

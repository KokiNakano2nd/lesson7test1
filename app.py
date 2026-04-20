import base64
import io
import os

from flask import Flask, Response, render_template_string, request
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
from PIL import Image


app = Flask(__name__)

MAX_TEXT_LENGTH = 500
MIN_SIZE = 128
MAX_SIZE = 1024
MIN_BORDER = 0
MAX_BORDER = 20
DEFAULT_SIZE = 320
DEFAULT_BORDER = 4
DEFAULT_LEVEL = "M"

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>QRコード生成ツール</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f4ee;
      --panel: #fffdf8;
      --line: #d7cfc0;
      --text: #1f1a14;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --error: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Yu Gothic UI", "Hiragino Sans", sans-serif;
      background:
        radial-gradient(circle at top left, #fff3d8 0, transparent 28%),
        linear-gradient(180deg, #f5efe4 0%, var(--bg) 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 920px;
      margin: 0 auto;
      padding: 32px 16px 56px;
    }
    .card {
      background: rgba(255, 253, 248, 0.96);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 12px 30px rgba(31, 26, 20, 0.08);
      overflow: hidden;
    }
    .hero {
      padding: 28px 28px 18px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(135deg, #fff7ea 0%, #f7fffd 100%);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 30px;
    }
    p {
      margin: 0;
      line-height: 1.7;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
    }
    .section {
      padding: 24px 28px 28px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 700;
    }
    textarea, input, select, button {
      width: 100%;
      border-radius: 12px;
      border: 1px solid #c9bfaf;
      padding: 12px 14px;
      font: inherit;
      background: #fff;
    }
    textarea {
      min-height: 144px;
      resize: vertical;
    }
    .row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 16px;
    }
    .help {
      margin-top: 6px;
      font-size: 13px;
      color: #655b4f;
    }
    .actions {
      margin-top: 20px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    button, .download {
      width: auto;
      min-width: 150px;
      border: none;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 12px 18px;
    }
    button:hover, .download:hover {
      background: var(--accent-dark);
    }
    .error {
      margin-bottom: 16px;
      padding: 12px 14px;
      border-radius: 12px;
      background: #fef3f2;
      color: var(--error);
      border: 1px solid #fecdca;
    }
    .preview {
      background: #fcfaf5;
      min-height: 100%;
    }
    .preview-box {
      margin-top: 18px;
      padding: 18px;
      border: 1px dashed #c9bfaf;
      border-radius: 16px;
      background: #fff;
      text-align: center;
    }
    .preview-box img {
      max-width: 100%;
      height: auto;
      border-radius: 12px;
      border: 1px solid #ece5d8;
      background: #fff;
    }
    .meta {
      margin-top: 12px;
      color: #655b4f;
      font-size: 14px;
      line-height: 1.6;
      word-break: break-word;
    }
    .placeholder {
      margin-top: 18px;
      padding: 22px;
      border-radius: 16px;
      background: #fffbf3;
      border: 1px dashed var(--line);
      color: #655b4f;
    }
    @media (max-width: 760px) {
      .grid, .row {
        grid-template-columns: 1fr;
      }
      .hero, .section {
        padding: 22px 18px;
      }
      h1 {
        font-size: 26px;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="hero">
        <h1>QRコード生成ツール</h1>
        <p>入力したテキストからPNGのQRコードを生成し、その場で表示してダウンロードできます。</p>
      </div>
      <div class="grid">
        <section class="section">
          {% if error %}
          <div class="error">{{ error }}</div>
          {% endif %}
          <form method="post" accept-charset="utf-8">
            <label for="text">テキスト</label>
            <textarea id="text" name="text" required maxlength="{{ max_text_length }}" placeholder="URL、メモ、連絡先などを入力">{{ values.text }}</textarea>
            <div class="help">最大 {{ max_text_length }} 文字。空文字は不可です。</div>

            <div class="row">
              <div>
                <label for="size">サイズ（px）</label>
                <input id="size" name="size" type="number" min="{{ min_size }}" max="{{ max_size }}" value="{{ values.size }}">
              </div>
              <div>
                <label for="border">余白（border）</label>
                <input id="border" name="border" type="number" min="{{ min_border }}" max="{{ max_border }}" value="{{ values.border }}">
              </div>
              <div>
                <label for="level">誤り訂正</label>
                <select id="level" name="level">
                  {% for option in levels %}
                  <option value="{{ option }}" {% if values.level == option %}selected{% endif %}>{{ option }}</option>
                  {% endfor %}
                </select>
              </div>
            </div>

            <div class="actions">
              <button type="submit">QRコードを生成</button>
            </div>
          </form>
        </section>

        <aside class="section preview">
          <label>プレビュー</label>
          {% if image_data_url %}
          <div class="preview-box">
            <img src="{{ image_data_url }}" alt="生成されたQRコード">
            <div class="actions" style="justify-content:center;">
              <a class="download" href="{{ image_data_url }}" download="qr-code.png">PNGをダウンロード</a>
            </div>
            <div class="meta">
              サイズ: {{ values.size }}px / 余白: {{ values.border }} / 誤り訂正: {{ values.level }}
            </div>
          </div>
          {% else %}
          <div class="placeholder">
            左のフォームにテキストを入力して生成すると、ここにQRコードが表示されます。
          </div>
          {% endif %}
        </aside>
      </div>
    </div>
  </div>
</body>
</html>
"""


def parse_int(name, default_value, minimum, maximum):
    raw_value = request.form.get(name, "").strip()
    if not raw_value:
        return default_value
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} は整数で入力してください。") from exc
    if value < minimum or value > maximum:
        raise ValueError(f"{name} は {minimum} から {maximum} の範囲で指定してください。")
    return value


def build_qr_png(text, size, border, level):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_LEVELS[level],
        box_size=10,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    image = image.resize((size, size), Image.Resampling.NEAREST)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_page(values, image_data_url=None, error=None):
    html = render_template_string(
        HTML,
        values=values,
        image_data_url=image_data_url,
        error=error,
        max_text_length=MAX_TEXT_LENGTH,
        min_size=MIN_SIZE,
        max_size=MAX_SIZE,
        min_border=MIN_BORDER,
        max_border=MAX_BORDER,
        levels=["L", "M", "Q", "H"],
    )
    return Response(html, content_type="text/html; charset=utf-8")


@app.route("/", methods=["GET", "POST"])
def index():
    values = {
        "text": "",
        "size": DEFAULT_SIZE,
        "border": DEFAULT_BORDER,
        "level": DEFAULT_LEVEL,
    }

    if request.method == "GET":
        return render_page(values)

    try:
        text = request.form.get("text", "").strip()
        size = parse_int("size", DEFAULT_SIZE, MIN_SIZE, MAX_SIZE)
        border = parse_int("border", DEFAULT_BORDER, MIN_BORDER, MAX_BORDER)
        level = request.form.get("level", DEFAULT_LEVEL).strip().upper() or DEFAULT_LEVEL

        values.update({"text": text, "size": size, "border": border, "level": level})

        if not text:
            raise ValueError("テキストを入力してください。")
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"テキストは {MAX_TEXT_LENGTH} 文字以内で入力してください。")
        if level not in ERROR_LEVELS:
            raise ValueError("誤り訂正レベルは L / M / Q / H のいずれかを指定してください。")

        png_bytes = build_qr_png(text, size, border, level)
        image_data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
        return render_page(values, image_data_url=image_data_url)
    except Exception as exc:
        return render_page(values, error=f"QRコードを生成できませんでした: {exc}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=port, debug=debug)

import os  # ✅ これを先頭に追加

from flask import Flask, render_template, request, abort
import whisper
import difflib
import urllib.parse

# ✅ 追加：ベースディレクトリ設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
TEXTS_FOLDER = "texts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = whisper.load_model("base")

# 運営用ホーム画面
@app.route("/")
def home():
    return """
    <h1>音読AIアプリへようこそ</h1>
    <p>【ご利用目的】<br>このアプリは音読力向上を支援するためのものです。</p>
    <p>【単元選択】<br><a href='/white-hat'>教育出版 4年生 白いぼうし（単元選択へ）</a></p>
    """

# 白いぼうし一覧ページ
@app.route("/white-hat")
def white_hat_list():
    scenes = ["1", "2", "3", "4"]
    html = "<h1>白いぼうし 音読課題一覧</h1><ul>"
    for scene_number in scenes:
        url = f"/scene/教育出版/４年生/白いぼうし/{scene_number}"
        html += f'<li><a href="{url}">白いぼうし - {scene_number}</a></li>'
    html += "</ul>"
    return html

# 課題画面
@app.route("/scene/<publisher>/<grade>/<unit>/<scene_number>")
def scene(publisher, grade, unit, scene_number):
    path = f"{TEXTS_FOLDER}/{publisher}/{grade}/{unit}/{unit}-{scene_number}.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            question = f.read().strip()
    except FileNotFoundError:
        abort(404, description="指定された課題が見つかりませんでした。")

    breadcrumbs_html = f"""
    <div style='margin-bottom: 10px;'>
      <a href='/'>ホーム</a> &gt;
      <a href='/white-hat'>白いぼうし一覧</a> &gt;
      <span>{scene_number}</span>
    </div>
    """

    return render_template("index.html", question=question, breadcrumbs=breadcrumbs_html)

# 録音提出処理
@app.route("/upload", methods=["POST"])
def upload():
    audio = request.files["audio_data"]
    filename_parts = audio.filename.replace("_recording.webm", "").split("_")

    if len(filename_parts) != 5:
        return "<h1>提出情報が不足しています。（想定：出版社_学年_単元_場面_児童ID）</h1>"

    publisher, grade, unit, scene_number, student_id = filename_parts

    publisher = urllib.parse.unquote(publisher)
    grade = urllib.parse.unquote(grade)
    unit = urllib.parse.unquote(unit)
    scene_number = urllib.parse.unquote(scene_number)

    audio_path = os.path.join(UPLOAD_FOLDER, audio.filename)
    audio.save(audio_path)

    result = model.transcribe(audio_path, language="ja")
    student_text = result["text"]

    correct_path = os.path.join(BASE_DIR, TEXTS_FOLDER, publisher, grade, unit, f"{unit}-{scene_number}_correct.txt")
    print("=== 正解ファイルを探しているパス ===")
    print(correct_path)
    print("=== 実際に存在するか確認 ===")
    print(os.path.exists(correct_path))
    with open(correct_path, "r", encoding="utf-8") as f:
        correct_text = f.read().strip()

    seq = difflib.SequenceMatcher(None, correct_text, student_text)
    similarity = round(seq.ratio() * 100, 2)
    diffs = []
    for opcode, a0, a1, b0, b1 in seq.get_opcodes():
        if opcode == 'replace':
            diffs.append(f"間違い: {correct_text[a0:a1]} → {student_text[b0:b1]}")
        elif opcode == 'delete':
            diffs.append(f"抜け: {correct_text[a0:a1]}")
        elif opcode == 'insert':
            diffs.append(f"追加: {student_text[b0:b1]}")

    diff_html = "<br>".join(diffs) if diffs else "特に誤りはありませんでした。"

    next_scene_number = str(int(scene_number) + 1)
    next_scene_url = f"/scene/{publisher}/{grade}/{unit}/{next_scene_number}"
    next_path = os.path.join(TEXTS_FOLDER, publisher, grade, unit, f"{unit}-{next_scene_number}.txt")
    next_button_html = (f"<button onclick=\"location.href='{next_scene_url}'\">次の課題に進む</button>"
                        if os.path.exists(next_path) else
                        "<button onclick=\"location.href='/white-hat'\">一覧に戻る</button>")

    return f"""
    <h1>提出が完了しました！</h1>
    <h2>{student_id}さんの音読結果：</h2>
    <p>{student_text}</p>
    <h2>一致率：{similarity}%</h2>
    <h2>誤りリスト：</h2>
    <p>{diff_html}</p>
    <h2>次の行動を選んでください</h2>
    <button onclick="location.href='/scene/{publisher}/{grade}/{unit}/{scene_number}'">もう一度挑戦する</button>
    {next_button_html}
    <button onclick="location.href='/white-hat'">一覧に戻る</button>
    """

if __name__ == "__main__":
    app.run(debug=True)
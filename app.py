import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
from itertools import combinations
from collections import Counter
import os
import yaml
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

st.set_page_config(page_title="LOTO6 知的予測AIシステム", layout="centered")

# base64で背景GIFを埋め込み
with open("matrix_scroll_background.gif", "rb") as f:
    gif_data = f.read()
    gif_base64 = base64.b64encode(gif_data).decode("utf-8")

st.markdown(f"""
<style>
html, body, .stApp {{
    background-color: black !important;
    background-image: url("data:image/gif;base64,{gif_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    color: white;
    font-family: 'Oswald', sans-serif !important;
}}
</style>
""", unsafe_allow_html=True)

font_path = os.path.join(os.path.dirname(__file__), "fonts", "ipaexg.ttf")
pdfmetrics.registerFont(TTFont("IPAexGothic", font_path))

rule_path = os.path.join(os.path.dirname(__file__), "rules.yaml")
with open(rule_path, "r", encoding="utf-8") as f:
    rules = yaml.safe_load(f)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&display=swap');

.stButton>button {
    background-color: #b30000;
    color: white;
    font-size: 20px;
    padding: 12px 30px;
    border-radius: 12px;
    border: 2px solid white;
    box-shadow: 0 0 12px #ff1a1a;
    transition: all 0.3s ease-in-out;
}
.stButton>button:hover {
    background-color: white;
    color: #b30000;
    border: 2px solid #b30000;
}
.title-glow {
    font-size: 56px;
    font-weight: 700;
    text-align: center;
    color: #ffffff;
    text-shadow: 0 0 10px #ff0000, 0 0 30px #ff0000;
    padding-top: 20px;
}
.subtitle {
    text-align: center;
    color: #dddddd;
    font-size: 20px;
    margin-bottom: 30px;
    font-weight: 300;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-glow">LOTO6知的予測AIシステム</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">— 勝つための数字は、知性が導き出す —</div>', unsafe_allow_html=True)

st.markdown("## 💼 データアップロード")
data_file = st.file_uploader("CSVファイルをアップロードしてください", type=["csv"])

if data_file is not None:
    df = pd.read_csv(data_file, encoding="shift_jis")
    df_cleaned = df[["日付", "第1数字", "第2数字", "第3数字", "第4数字", "第5数字", "第6数字"]].copy()
    df_cleaned.columns = ["date", "number1", "number2", "number3", "number4", "number5", "number6"]

    if st.button("🎯 予測スタート"):
        numbers = df_cleaned.iloc[:, 1:].values.flatten()
        freq = pd.Series(numbers).value_counts().sort_index()

        latest_numbers = df_cleaned.iloc[0, 1:].tolist()
        selected = []
        if rules.get("use_previous_numbers"):
            selected += latest_numbers[:rules.get("previous_number_count", 2)]

        if rules.get("use_common_pairs"):
            all_pairs = []
            for _, row in df_cleaned.iterrows():
                nums = row[1:].tolist()
                pairs = list(combinations(sorted(nums), 2))
                all_pairs.extend(pairs)
            pair_counts = Counter(all_pairs)
            common_pairs = [pair for pair, count in pair_counts.most_common(rules.get("common_pair_limit", 20))]
            flat_common_numbers = list(set(num for pair in common_pairs for num in pair))
            selected += flat_common_numbers

        zone_picks = []
        if rules.get("use_zone_distribution"):
            for z in rules.get("zones", []):
                zone_range = list(range(z[0], z[1] + 1))
                zone_picks.append(np.random.choice(zone_range, 1)[0])
                selected += zone_picks

        avoid_numbers = []
        if rules.get("exclude_hot_numbers"):
            avoid_numbers = freq.sort_values(ascending=False).head(rules.get("hot_count", 3)).index.tolist()

        candidates = set(selected)
        filtered_candidates = list(candidates - set(avoid_numbers))
        predicted = sorted(np.random.choice(filtered_candidates, 6, replace=False).tolist())

        st.markdown("## 🔻 予測結果")
        st.success(f"🎲 予測数字: {predicted}")

        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        c.setFont("IPAexGothic", 14)
        top = 280 * mm
        line_height = 10 * mm

        c.drawString(30 * mm, top, "LOTO6予測レポート")
        c.setFont("IPAexGothic", 12)
        c.drawString(30 * mm, top - line_height * 2, "■ 予測数字")
        c.drawString(40 * mm, top - line_height * 3, f"→ {predicted}")
        c.drawString(30 * mm, top - line_height * 5, "■ 前回の数字")
        c.drawString(40 * mm, top - line_height * 6, f"→ {list(map(int, latest_numbers))}")
        c.drawString(30 * mm, top - line_height * 8, "■ ゾーン分散")
        c.drawString(40 * mm, top - line_height * 9, f"→ {list(map(int, zone_picks))}")
        c.drawString(30 * mm, top - line_height * 11, "■ 除外（ホット数字）")
        c.drawString(40 * mm, top - line_height * 12, f"→ {list(map(int, avoid_numbers))}")
        c.showPage()
        c.save()

        st.download_button(
            label="📄 PDFレポートをダウンロード",
            data=pdf_buffer.getvalue(),
            file_name="loto6_gambler_report.pdf",
            mime="application/pdf"
        )

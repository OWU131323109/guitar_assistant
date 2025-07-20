import streamlit as st
import pandas as pd
import google.generativeai as genai
import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
font_path = "assets/NotoSansJP-VariableFont_wght.ttf"
font_prop = font_manager.FontProperties(fname=font_path)

plt.rcParams["font.family"] = font_prop.get_name()
from pathlib import Path
import requests

#st.set_page_config(layout="wide")


#ユーザー登録
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "goal_time" not in st.session_state:
    st.session_state.goal_time = 30  

#ログイン画面
if not st.session_state.logged_in:
    st.title("🐼PandaJam🎸")
    st.caption("〜 パンダくんのギター教室 〜")

    st.image("assets/panda-kun.png", width = 350)
    IMG_PATH = Path("assets/panda-kun.png").as_posix()
    name = st.text_input("ニックネームを入力してね")
    if st.button("ログイン") and name:
        st.session_state.logged_in = True
        # ユーザー名が変わったらgoal_timeリセット
        if st.session_state.user_name != name:
            st.session_state.goal_time = 30
        st.session_state.user_name = name
        st.success(f"{name}さん、ようこそ！")
        st.balloons()
    st.stop()

# ログイン後の画面
DATA_PATH = f"data/practice_log_{st.session_state.user_name}.csv"
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_PATH):
    pd.DataFrame(columns=["date", "practice_item", "duration_min"]).to_csv(DATA_PATH, index=False)

st.title("PandaJam🎸")
# サイドバー：ユーザー情報表示
with st.sidebar:
    st.image("assets/panda-kun.png", width=100)
    st.markdown("## 🐼PandaJam")
    st.markdown(f"👤 **{st.session_state.user_name}** さん")
    st.markdown("🎸いつも応援してるよ！")
    st.markdown("---")

    if st.sidebar.button("🔚 ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

st.caption("〜 パンダくんのギター教室 〜")
st.subheader(f"{st.session_state.user_name}さん！今日も一緒にがんばろうね🐼🎶")
st.markdown("---")

#Gemini API設定
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")
IMG_PATH = Path("assets/panda-kun.png").as_posix()



# 練習記録セクション

st.header("📅 今日の練習目標を立てよう")
st.session_state.goal_time = st.slider(
    "今日の練習時間（分）",
    10, 120,value=st.session_state.goal_time,step=5
)

if "today_menu" not in st.session_state:
    st.session_state.today_menu = None

if st.button("パンダくんからの今日の練習メニュー"):
    with st.spinner("パンダくん考え中..."):
        prompt = f"""
あなたは「パンダくん」という優しいギターの先生です。
第一人称は「僕」です。
ユーザーが今日 {st.session_state.goal_time} 分間練習したいと言っています。
以下のように、今日の練習メニューを初心者向けにやさしく短く提案してください。

・項目を3つ程度に絞る
・優しく励ます言葉
・各項目の時間も割り振って書く
・大事なところは太文字にする
・見やすい表示にする
例：
- コードチェンジ練習（10分）: C→G→Am をゆっくり繰り返そう
- リズム練習（10分）: メトロノームに合わせてストロークしよう
- 好きな曲を弾いてみよう（10分）: 気楽にチャレンジ！

ユーザーの希望時間：{st.session_state.goal_time} 分
"""
        response = model.generate_content(prompt)
        st.session_state.today_menu = response.text

if st.session_state.today_menu:
    st.markdown("### 🐼 今日のおすすめ練習メニュー")
    st.image("assets/panda-kun.png", width=150) 
    st.write(st.session_state.today_menu)  # response.text ではなく session_state.today_menu を使う

def search_youtube_url(query: str, api_key: str):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "key": api_key,
        "maxResults": 1
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        items = response.json().get("items")
        if items:
            video_id = items[0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
    return None

if st.button("♫ パンダくんおすすめの練習曲を教えて"):
    with st.spinner("パンダくん 曲を探し中・・・"):
        prompt = f"""
あなたは「パンダくん」という優しいギターの先生です。
第一人称は「僕」です。

ユーザーが今日、{st.session_state.goal_time}分ギターを練習する予定です。
初心者でも楽しんで練習できるギターの曲を、**2曲** 提案してください。

- 日本のJ-POPや洋楽を含んでOKです
- 曲名とアーティスト名を含めてください
- それぞれの曲がなぜ練習しやすいかの理由（簡単なコード構成など）も添えてください
- 最後に「がんばってね！」などの励ましの一言も加えてください
- 大事なところは 太字 にしてください
- 見やすい表示にする
"""
        response = model.generate_content(prompt)
        song_text = response.text
        st.markdown("### 🎶 パンダくんのおすすめ曲")
        st.image(IMG_PATH, width=120)
        st.write(song_text)

        # 曲名抽出と自動検索
        YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]  
        lines = song_text.splitlines()
        for line in lines:
            if "/" in line:
                song_title = line.split("/")[0].strip().lstrip("1.").lstrip("2.").strip()
                youtube_url = search_youtube_url(song_title + " ギター", YOUTUBE_API_KEY)
                if youtube_url:
                    st.video(youtube_url)


# アドバイス
st.header("🎸パンダくんに質問しよう")
user_question = st.text_input("ギターに関する質問を入力してね（例：Fコードが上手く弾けません）")

if st.button("パンダくんに聞いてみる") and user_question:
    with st.spinner("パンダくん考え中..."):
        prompt = f"""
あなたは「パンダくん」という優しいギターの先生です。
第一人称は、「僕」です。
以下の初心者の悩みに対して、優しく、親しみやすく、わかりやすく答えてください。
初心者に安心感を与える語り口調でお願いします。また、大事なところは太文字にし、見やすい表示にしてください。

悩み:{user_question}
"""
        response = model.generate_content(prompt)
        st.markdown("### 🐾 パンダくんからのアドバイス")
        st.image("assets/panda-kun.png", width=120)  
        st.write(response.text)

st.markdown("---")


st.header("📝 練習記録をつけよう")

with st.form("log_form"):
    date = st.date_input("日付を選んでね", value=datetime.date.today())
    practice_item = st.text_input("練習した内容（例：パワーコード、アルペジオ）")
    duration = st.number_input("練習時間（分）", min_value=1, max_value=300, step=5)
    submitted = st.form_submit_button("記録する")

if submitted:
    new_data = pd.DataFrame({
        "date": [date.strftime("%Y-%m-%d")],
        "practice_item": [practice_item],
        "duration_min": [duration]
    })
    df = pd.read_csv(DATA_PATH)
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    st.success("✅ 練習が記録されました！")
    st.balloons()

# 練習グラフ表示
st.markdown("---")
st.header("📊 練習時間グラフ")

df = pd.read_csv(DATA_PATH)
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    df_grouped = df.groupby("date")["duration_min"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(8, 6))

    # 横棒グラフは日付をY軸にするので、文字列に変換すると見やすい
    df_grouped["date_str"] = df_grouped["date"].dt.strftime("%Y-%m-%d")

    # 横棒グラフの描画
    ax.barh(df_grouped["date_str"], df_grouped["duration_min"], color="skyblue")

    # タイトル・ラベル
    ax.set_title("これまでの練習時間")
    ax.set_xlabel("練習時間（分）")
    ax.set_ylabel("日付")

    # グラフ表示
    st.pyplot(fig)

else:
    st.info("まだ練習記録がありません")

# 応援メッセージ
st.markdown("---")
st.header("🌟 今日のパンダくんからの一言")

with st.expander("クリックして励ましをもらおう！"):
    encouragements = [
        "大丈夫、一歩ずつでOKだよ！🐼",
        "Fコードも必ず弾けるようになるよ！",
        "続けることが一番の上達のコツ！",
        "ギターを楽しもうね🎸",
        "今日もよくがんばったね！"
    ]
    st.write(f"🐼「{encouragements[datetime.date.today().day % len(encouragements)]}」")

st.markdown("---")
st.header("🗑️ 練習記録を削除する")

if st.button("全ての練習記録を削除する（注意！元に戻せません）"):
    pd.DataFrame(columns=["date", "practice_item", "duration_min"]).to_csv(DATA_PATH, index=False)
    st.success("練習記録を全て削除しました。")

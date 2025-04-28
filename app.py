import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time
from io import BytesIO
from PIL import Image

# ====== Streamlitアプリ設定 ======
st.set_page_config(page_title="4セット配置版アニメーション (完全版)", layout="wide")
st.title("🖥️ 4方向カラー帯＋ラインアニメーション（距離mm単位・Rainbow・温度範囲40〜50℃）")

# ====== ファイルアップロード ======
st.sidebar.header("ファイルアップロード")

top_file = st.sidebar.file_uploader("⬆️ 上セットファイル", type=["csv"])
bottom_file = st.sidebar.file_uploader("⬇️ 下セットファイル", type=["csv"])
left_file = st.sidebar.file_uploader("⬅️ 左セットファイル", type=["csv"])
right_file = st.sidebar.file_uploader("➡️ 右セットファイル", type=["csv"])

# ====== データ読み込み ======
def load_csv(file):
    df = pd.read_csv(file)
    times = df['time'].values
    distance_columns = df.columns[1:]
    distance = np.array([float(col.replace('mm', '')) for col in distance_columns])
    temperature_data = df.drop('time', axis=1).values
    return times, distance, temperature_data

# ====== メインロジック ======
if top_file and bottom_file and left_file and right_file:
    times_top, dist_top, temp_top = load_csv(top_file)
    times_bottom, dist_bottom, temp_bottom = load_csv(bottom_file)
    times_left, dist_left, temp_left = load_csv(left_file)
    times_right, dist_right, temp_right = load_csv(right_file)

    # 時間軸は4ファイル共通前提
    times = times_top

    # サイドバー設定
    st.sidebar.header("アニメーション設定")

    start_time = st.sidebar.slider(
        "再生開始時間を指定",
        float(times.min()), float(times.max()),
        float(times.min()), step=0.1
    )

    animation_speed = st.sidebar.slider("再生速度（秒/フレーム）", 0.05, 1.0, 0.2)

    time_step = st.sidebar.selectbox(
        "時間ステップ幅を選択",
        options=[0.1, 0.2, 0.5, 1.0],
        index=0
    )

    # 再生・停止ボタン
    if 'playing' not in st.session_state:
        st.session_state.playing = False

    play_col, stop_col = st.sidebar.columns(2)
    if play_col.button("▶️ Play"):
        st.session_state.playing = True
    if stop_col.button("⏹️ Stop"):
        st.session_state.playing = False

    generate_gif = st.sidebar.button("🎞️ GIFアニメーションを保存する")

    # ====== プロット関数 ======
    def plot_4views(t_idx, title_text=None):
        fig = plt.figure(figsize=(8, 8))
        fig.patch.set_facecolor('white')

        gs = fig.add_gridspec(3, 3, width_ratios=[1,2,1], height_ratios=[1,2,1], wspace=0.2, hspace=0.2)

        # 上
        ax_top = fig.add_subplot(gs[0,1])
        ax_top.set_facecolor('black')
        dist_fine = np.linspace(dist_top.min(), dist_top.max(), 500)
        temp_fine = np.interp(dist_fine, dist_top, temp_top[t_idx])
        img = np.expand_dims(temp_fine, axis=0)
        ax_top.imshow(img, aspect='auto', extent=[dist_top.min(), dist_top.max(), 0, 1], cmap='rainbow', vmin=40, vmax=50, origin='lower')
        ax_top.plot(dist_top, np.ones_like(dist_top)*0.5, color='yellow', marker='o', markersize=4, linestyle='-')
        ax_top.axis('off')

        # 下
        ax_bottom = fig.add_subplot(gs[2,1])
        ax_bottom.set_facecolor('black')
        dist_fine = np.linspace(dist_bottom.min(), dist_bottom.max(), 500)
        temp_fine = np.interp(dist_fine, dist_bottom, temp_bottom[t_idx])
        img = np.expand_dims(temp_fine, axis=0)
        ax_bottom.imshow(img, aspect='auto', extent=[dist_bottom.min(), dist_bottom.max(), 0, 1], cmap='rainbow', vmin=40, vmax=50, origin='lower')
        ax_bottom.plot(dist_bottom, np.ones_like(dist_bottom)*0.5, color='yellow', marker='o', markersize=4, linestyle='-')
        ax_bottom.axis('off')

        # 左
        ax_left = fig.add_subplot(gs[1,0])
        ax_left.set_facecolor('black')
        dist_fine = np.linspace(dist_left.min(), dist_left.max(), 500)
        temp_fine = np.interp(dist_fine, dist_left, temp_left[t_idx])
        img = np.expand_dims(temp_fine, axis=1)
        ax_left.imshow(img, aspect='auto', extent=[0, 1, dist_left.min(), dist_left.max()], cmap='rainbow', vmin=40, vmax=50, origin='lower')
        ax_left.plot(np.ones_like(dist_left)*0.5, dist_left, color='yellow', marker='o', markersize=4, linestyle='-')
        ax_left.axis('off')

        # 右
        ax_right = fig.add_subplot(gs[1,2])
        ax_right.set_facecolor('black')
        dist_fine = np.linspace(dist_right.min(), dist_right.max(), 500)
        temp_fine = np.interp(dist_fine, dist_right, temp_right[t_idx])
        img = np.expand_dims(temp_fine, axis=1)
        ax_right.imshow(img, aspect='auto', extent=[0, 1, dist_right.min(), dist_right.max()], cmap='rainbow', vmin=40, vmax=50, origin='lower')
        ax_right.plot(np.ones_like(dist_right)*0.5, dist_right, color='yellow', marker='o', markersize=4, linestyle='-')
        ax_right.axis('off')

        # ====== 中央に時刻を大きく表示 ======
        fig.text(0.5, 0.5, title_text, fontsize=28, ha='center', va='center', color='black')

        return fig

    # ====== メイン表示部 ======
    placeholder = st.empty()
    current_time = start_time

    if generate_gif:
        st.info("GIF生成中...お待ちください！")

        frames = []
        gif_time = start_time

        while gif_time <= times.max():
            t_idx = np.argmin(np.abs(times - gif_time))

            fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            buf.seek(0)
            img = Image.open(buf)
            frames.append(img)

            gif_time += time_step

        gif_buf = BytesIO()
        frames[0].save(
            gif_buf, format='GIF', save_all=True, append_images=frames[1:], duration=int(animation_speed*1000), loop=0
        )
        gif_buf.seek(0)

        st.download_button(
            label="📥 GIFをダウンロードする",
            data=gif_buf,
            file_name="4view_animation.gif",
            mime="image/gif"
        )

    if st.session_state.playing:
        while current_time <= times.max():
            t_idx = np.argmin(np.abs(times - current_time))

            fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
            placeholder.pyplot(fig)
            time.sleep(animation_speed)

            current_time += time_step
    else:
        selected_time = st.slider(
            "時間を手動選択",
            float(times.min()), float(times.max()),
            start_time, step=0.1, key="manual_slider"
        )
        t_idx = np.argmin(np.abs(times - selected_time))
        fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
        placeholder.pyplot(fig)

else:
    st.info("4つのCSVファイルをアップロードしてください。")

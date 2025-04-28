import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time
from io import BytesIO
from PIL import Image

# ====== Streamlitアプリ設定 ======
st.set_page_config(page_title="1Dカラーストリップアニメーション (完全版)", layout="wide")
st.title("🎥 1Dカラーストリップ（距離mm単位・ファイルアップロード・アニメーションコントロール対応＋GIF保存）")

# ====== ファイルアップロード ======
uploaded_file = st.file_uploader("📄 CSVファイルをアップロードしてください", type=["csv"])

if uploaded_file is not None:
    # データ読み込み
    df = pd.read_csv(uploaded_file)

    # 時間と距離の情報取得
    times = df['time'].values
    distance_columns = df.columns[1:]
    distance = np.array([float(col.replace('mm', '')) for col in distance_columns])

    # 温度データ
    temperature_data = df.drop('time', axis=1).values

    # ----- サイドバー設定 -----
    st.sidebar.header("操作パネル")

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

    colormap = st.sidebar.selectbox(
        "カラーマップを選択",
        options=["plasma", "viridis", "inferno", "magma", "cividis", "jet", "rainbow", "seismic"],
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

    # ====== グラフ描画関数 ======
    def plot_color_strip(temperature, title_text):
        distance_fine = np.linspace(distance.min(), distance.max(), 500)
        temperature_fine = np.interp(distance_fine, distance, temperature)

        fig, ax = plt.subplots(figsize=(10, 2))
        img = np.expand_dims(temperature_fine, axis=0)

        extent = [distance.min(), distance.max(), 0, 1]
        ax.imshow(img, aspect='auto', extent=extent, cmap=colormap, origin='lower', vmin=35, vmax=60)

        ax.set_xlim(distance.min(), distance.max())
        ax.set_ylim(0, 1)
        ax.set_xlabel('Distance [mm]')
        ax.set_yticks([])
        ax.set_title(title_text)

        norm = plt.Normalize(vmin=35, vmax=60)
        sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.2)
        cbar.set_label('Temperature (°C)')

        return fig

    # ====== 表示プレースホルダ ======
    placeholder = st.empty()

    # 再生モード or 手動モード
    current_time = start_time

    if generate_gif:
        st.info("GIF生成中...少しお待ちください！")

        frames = []
        gif_time = start_time

        while gif_time <= times.max():
            idx = np.argmin(np.abs(times - gif_time))

            distance_fine = np.linspace(distance.min(), distance.max(), 500)
            temperature_fine = np.interp(distance_fine, distance, temperature_data[idx])

            fig, ax = plt.subplots(figsize=(6, 1.2))
            img = np.expand_dims(temperature_fine, axis=0)
            extent = [distance.min(), distance.max(), 0, 1]
            ax.imshow(img, aspect='auto', extent=extent, cmap=colormap, origin='lower', vmin=35, vmax=60)
            ax.axis('off')

            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            buf.seek(0)
            img = Image.open(buf)
            frames.append(img)

            gif_time += time_step

        # GIF保存
        gif_buf = BytesIO()
        frames[0].save(
            gif_buf, format='GIF', save_all=True, append_images=frames[1:],
            duration=int(animation_speed * 1000), loop=0
        )
        gif_buf.seek(0)

        st.download_button(
            label="📥 GIFをダウンロードする",
            data=gif_buf,
            file_name="animation.gif",
            mime="image/gif"
        )

    if st.session_state.playing:
        while current_time <= times.max():
            idx = np.argmin(np.abs(times - current_time))

            fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {times[idx]:.1f} 秒")
            placeholder.pyplot(fig)
            time.sleep(animation_speed)

            current_time += time_step
    else:
        selected_time = st.slider(
            "時間を手動選択",
            float(times.min()), float(times.max()),
            start_time, step=0.1, key="manual_slider"
        )
        idx = np.argmin(np.abs(times - selected_time))
        fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {selected_time:.1f} 秒")
        placeholder.pyplot(fig)

else:
    st.info("まずCSVファイルをアップロードしてください。")

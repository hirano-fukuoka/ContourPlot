import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time

# ====== Streamlitアプリ設定 ======
st.set_page_config(page_title="1Dカラーストリップアニメーション (完全版)", layout="wide")
st.title("🎥 1Dカラーストリップ（距離mm単位・ファイルアップロード・アニメーション対応）")

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

    play_animation = st.sidebar.checkbox("アニメーション再生", value=False)

    animation_speed = st.sidebar.slider("再生速度（秒/フレーム）", 0.05, 1.0, 0.2)

    # 時間ステップ幅選択
    time_step = st.sidebar.selectbox(
        "時間ステップ幅を選択",
        options=[0.1, 0.2, 0.5, 1.0],
        index=0
    )

    # 手動時間スライダー
    selected_time = st.sidebar.slider(
        "時間を選択",
        float(times.min()), float(times.max()),
        float(times.min()), step=0.1
    )

    # カラーマップ選択
    colormap = st.sidebar.selectbox(
        "カラーマップを選択",
        options=["plasma", "viridis", "inferno", "magma", "cividis", "jet", "rainbow", "seismic"],
        index=0
    )

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

        # ★ カラーバーも35〜60固定
        norm = plt.Normalize(vmin=35, vmax=60)
        sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.2)
        cbar.set_label('Temperature (°C)')

        return fig

    # ====== 表示プレースホルダ ======
    placeholder = st.empty()

    # 再生モード/手動モード
    if play_animation:
        current_time = times.min()
        while current_time <= times.max():
            idx = np.argmin(np.abs(times - current_time))

            fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {times[idx]:.1f} 秒")
            placeholder.pyplot(fig)
            time.sleep(animation_speed)

            current_time += time_step
    else:
        idx = np.where(times == selected_time)[0][0]
        fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {selected_time:.1f} 秒")
        placeholder.pyplot(fig)

else:
    st.info("まずCSVファイルをアップロードしてください。")

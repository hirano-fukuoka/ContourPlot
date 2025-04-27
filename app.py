import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time

# ====== データ読み込み ======
df = pd.read_csv('data.csv')

# 時間と距離配列
times = df['time'].values
distance_columns = df.columns[1:]
distance = np.array([float(col.replace('mm', '')) for col in distance_columns])

# 温度データ
temperature_data = df.drop('time', axis=1).values

# ====== Streamlitアプリ ======
st.set_page_config(page_title="1Dカラーストリップアニメーション (mm対応)", layout="wide")
st.title("🎥 1Dカラーストリップ（距離mm単位・時間変化アニメーション）")

# サイドバー
st.sidebar.header("操作パネル")
play_animation = st.sidebar.checkbox("アニメーション再生", value=False)
animation_speed = st.sidebar.slider("再生速度（秒/フレーム）", 0.05, 1.0, 0.2)

selected_time = st.sidebar.slider(
    "時間を選択",
    float(times.min()), float(times.max()),
    float(times.min()), step=0.1
)

# グラフ描画関数
def plot_color_strip(temperature, title_text):
    distance_fine = np.linspace(distance.min(), distance.max(), 500)
    temperature_fine = np.interp(distance_fine, distance, temperature)

    fig, ax = plt.subplots(figsize=(10, 2))
    img = np.expand_dims(temperature_fine, axis=0)

    extent = [distance.min(), distance.max(), 0, 1]
    ax.imshow(img, aspect='auto', extent=extent, cmap='plasma', origin='lower')

    ax.set_xlim(distance.min(), distance.max())
    ax.set_ylim(0, 1)
    ax.set_xlabel('Distance [mm]')
    ax.set_yticks([])
    ax.set_title(title_text)

    norm = plt.Normalize(temperature_data.min(), temperature_data.max())
    sm = plt.cm.ScalarMappable(cmap='plasma', norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', pad=0.2)
    cbar.set_label('Temperature (°C)')

    return fig

# 表示場所
placeholder = st.empty()

# 再生モード
if play_animation:
    for idx, t in enumerate(times):
        fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {t:.1f} 秒")
        placeholder.pyplot(fig)
        time.sleep(animation_speed)
else:
    idx = np.where(times == selected_time)[0][0]
    fig = plot_color_strip(temperature_data[idx], title_text=f"Time = {selected_time:.1f} 秒")
    placeholder.pyplot(fig)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time
from io import BytesIO
from PIL import Image

# ====== Streamlitアプリ設定 ======
st.set_page_config(page_title="4方向配置版アニメーション (超最適化版)", layout="wide")
st.title("🖥️ 4方向カラー帯＋ラインアニメーション＋カラーバー＋進捗バー付き")

# ====== ファイル一括アップロード ======
st.sidebar.header("ファイルアップロード")

uploaded_files = st.sidebar.file_uploader(
    "📄 4ファイルをまとめてアップロードしてください (top.csv, bottom.csv, left.csv, right.csv)",
    type=["csv"],
    accept_multiple_files=True
)

# ====== データ読み込み関数 ======
def load_csv(file):
    df = pd.read_csv(file)
    times = df['time'].values
    distance_columns = df.columns[1:]
    distance = np.array([float(col.replace('mm', '')) for col in distance_columns])
    temperature_data = df.drop('time', axis=1).values
    return times, distance, temperature_data

# ====== メインロジック ======
if uploaded_files and len(uploaded_files) == 4:
    # ファイル名で分類
    file_dict = {file.name: file for file in uploaded_files}

    top_file = file_dict.get('top.csv')
    bottom_file = file_dict.get('bottom.csv')
    left_file = file_dict.get('left.csv')
    right_file = file_dict.get('right.csv')

    if top_file and bottom_file and left_file and right_file:
        times_top, dist_top, temp_top = load_csv(top_file)
        times_bottom, dist_bottom, temp_bottom = load_csv(bottom_file)
        times_left, dist_left, temp_left = load_csv(left_file)
        times_right, dist_right, temp_right = load_csv(right_file)

        times = times_top  # 時間軸共通前提

        # ====== サイドバー設定 ======
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
            fig = plt.figure(figsize=(15, 13))
            fig.patch.set_facecolor('white')

            gs = fig.add_gridspec(5, 6,
                      width_ratios=[0.25, 0.25, 0.8, 0.25, 0.25, 0.05],  # 横方向：ライン/コンター交互配置
                      height_ratios=[0.3, 0.3, 0.8, 0.3, 0.3],      # 縦方向：ライン/コンター交互配置
                      wspace=0.05, hspace=0.05)

            cmap = 'rainbow'
            norm = plt.Normalize(vmin=40, vmax=50)

            # 上セット
            ax_top_line = fig.add_subplot(gs[0,2])
            ax_top_line.set_facecolor('black')
            ax_top_line.plot(dist_top, temp_top[t_idx], color='yellow', marker='o')
            ax_top_line.set_xlim(dist_top.min(), dist_top.max())
            ax_top_line.set_ylim(40, 50)
            ax_top_line.set_xticks([])
            ax_top_line.set_yticks([])

            ax_top_contour = fig.add_subplot(gs[1,2])
            ax_top_contour.set_facecolor('black')
            dist_fine = np.linspace(dist_top.min(), dist_top.max(), 500)
            temp_fine = np.interp(dist_fine, dist_top, temp_top[t_idx])
            img = np.expand_dims(temp_fine, axis=0)
            ax_top_contour.imshow(img, aspect='auto', extent=[dist_top.min(), dist_top.max(), 0, 1], cmap=cmap, norm=norm, origin='lower')
            ax_top_contour.axis('off')

            # 下セット
            ax_bottom_contour = fig.add_subplot(gs[3,2])
            ax_bottom_contour.set_facecolor('black')
            dist_fine = np.linspace(dist_bottom.min(), dist_bottom.max(), 500)
            temp_fine = np.interp(dist_fine, dist_bottom, temp_bottom[t_idx])
            img = np.expand_dims(temp_fine, axis=0)
            ax_bottom_contour.imshow(img, aspect='auto', extent=[dist_bottom.min(), dist_bottom.max(), 0, 1], cmap=cmap, norm=norm, origin='lower')
            ax_bottom_contour.axis('off')

            ax_bottom_line = fig.add_subplot(gs[4,2])
            ax_bottom_line.set_facecolor('black')
            ax_bottom_line.plot(dist_bottom, temp_bottom[t_idx], color='yellow', marker='o')
            ax_bottom_line.set_xlim(dist_bottom.min(), dist_bottom.max())
            ax_bottom_line.set_ylim(40, 50)
            ax_bottom_line.set_xticks([])
            ax_bottom_line.set_yticks([])

            # 左セット
            ax_left_line = fig.add_subplot(gs[2,0])
            ax_left_line.set_facecolor('black')
            ax_left_line.plot(temp_left[t_idx], dist_left, color='yellow', marker='o')
            ax_left_line.set_xlim(40, 50)
            ax_left_line.set_ylim(dist_left.min(), dist_left.max())
            ax_left_line.invert_xaxis()
            ax_left_line.set_xticks([])
            ax_left_line.set_yticks([])

            ax_left_contour = fig.add_subplot(gs[2,1])
            ax_left_contour.set_facecolor('black')
            dist_fine = np.linspace(dist_left.min(), dist_left.max(), 500)
            temp_fine = np.interp(dist_fine, dist_left, temp_left[t_idx])
            img = np.expand_dims(temp_fine, axis=1)
            ax_left_contour.imshow(img, aspect='auto', extent=[0, 1, dist_left.min(), dist_left.max()], cmap=cmap, norm=norm, origin='lower')
            ax_left_contour.axis('off')

            # 右セット
            ax_right_contour = fig.add_subplot(gs[2,3])
            ax_right_contour.set_facecolor('black')
            dist_fine = np.linspace(dist_right.min(), dist_right.max(), 500)
            temp_fine = np.interp(dist_fine, dist_right, temp_right[t_idx])
            img = np.expand_dims(temp_fine, axis=1)
            ax_right_contour.imshow(img, aspect='auto', extent=[0, 1, dist_right.min(), dist_right.max()], cmap=cmap, norm=norm, origin='lower')
            ax_right_contour.axis('off')

            ax_right_line = fig.add_subplot(gs[2,4])
            ax_right_line.set_facecolor('black')
            ax_right_line.plot(temp_right[t_idx], dist_right, color='yellow', marker='o')
            ax_right_line.set_xlim(40, 50)
            ax_right_line.set_ylim(dist_right.min(), dist_right.max())
            ax_right_line.set_xticks([])
            ax_right_line.set_yticks([])

            # カラーバー独立配置
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar_ax = fig.add_axes([0.92, 0.2, 0.02, 0.6])
            cbar = fig.colorbar(sm, cax=cbar_ax)
            cbar.set_label('Temperature (°C)', fontsize=12)
            cbar.set_ticks([40, 42, 44, 46, 48, 50])
            cbar.ax.tick_params(labelsize=10, colors='black')

            # 中央時刻
            if title_text:
                fig.text(0.5, 0.5, title_text, fontsize=28, ha='center', va='center', color='black')

            return fig


        # ====== メイン表示部 ======
        placeholder = st.empty()
        current_time = start_time

        if generate_gif:
            st.info("GIF生成中...お待ちください！")

            frames = []
            gif_time = start_time
            n_total_frames = int((times.max() - gif_time) / time_step) + 1
            progress_bar = st.progress(0)

            current_frame = 0
            while gif_time <= times.max():
                t_idx = np.argmin(np.abs(times - gif_time))

                fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
                buf = BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
                plt.close(fig)  # メモリ解放
                buf.seek(0)
                img = Image.open(buf)
                frames.append(img)

                gif_time += time_step
                current_frame += 1
                progress_bar.progress(min(current_frame / n_total_frames, 1.0))

            gif_buf = BytesIO()
            frames[0].save(
                gif_buf, format='GIF', save_all=True, append_images=frames[1:], duration=int(animation_speed * 1000), loop=0
            )
            gif_buf.seek(0)

            st.download_button(
                label="📥 GIFをダウンロードする",
                data=gif_buf,
                file_name="4view_animation.gif",
                mime="image/gif"
            )

            progress_bar.empty()  # 進捗バー消去

        if st.session_state.playing:
            n_total_frames = int((times.max() - current_time) / time_step) + 1
            progress_bar = st.progress(0)

            frame_counter = 0
            while current_time <= times.max():
                t_idx = np.argmin(np.abs(times - current_time))

                fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
                placeholder.pyplot(fig, clear_figure=True)
                plt.close(fig)
                time.sleep(animation_speed)

                current_time += time_step
                frame_counter += 1
                progress_bar.progress(min(frame_counter / n_total_frames, 1.0))

            progress_bar.empty()  # 再生後、進捗バー消去
        else:
            selected_time = st.slider(
                "時間を手動選択",
                float(times.min()), float(times.max()),
                start_time, step=0.1, key="manual_slider"
            )
            t_idx = np.argmin(np.abs(times - selected_time))
            fig = plot_4views(t_idx, title_text=f"{times[t_idx]:.1f} sec")
            placeholder.pyplot(fig, clear_figure=True)
            plt.close(fig)

    else:
        st.warning("top.csv, bottom.csv, left.csv, right.csv の4ファイルを必ずアップロードしてください。")
else:
    st.info("4つのCSVファイルをアップロードしてください。")



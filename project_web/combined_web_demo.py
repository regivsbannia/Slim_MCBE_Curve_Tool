import gradio as gr
import zipfile
import tempfile
import os
import shutil
from pathlib import Path
import threading
import time
from datetime import datetime, timedelta

from file_fill import fill_from_file
from region_input import fill_region

from angle_straight import plot_full_track
from circle_vision_simple import draw_quarter_circle_image

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import zhplot

# === 全局配置 ===
MAX_CONCURRENT_USERS = 5  # 最大同时访问人数
current_users = 0
current_users_lock = threading.Lock()

# === 临时文件管理器 ===
class TempFileManager:
    def __init__(self):
        self.temp_files = []
        self.lock = threading.Lock()
        
    def add_file(self, file_path):
        with self.lock:
            self.temp_files.append({
                'path': file_path,
                'created_at': datetime.now()
            })
            
    def cleanup_old_files(self, max_age_minutes=30):
        """清理超过指定时间的临时文件"""
        with self.lock:
            now = datetime.now()
            to_remove = []
            for file_info in self.temp_files:
                if os.path.exists(file_info['path']):
                    file_age = now - file_info['created_at']
                    if file_age > timedelta(minutes=max_age_minutes):
                        try:
                            os.unlink(file_info['path'])
                            to_remove.append(file_info)
                        except:
                            pass
            for file_info in to_remove:
                self.temp_files.remove(file_info)
                
    def cleanup_all(self):
        """清理所有临时文件"""
        with self.lock:
            for file_info in self.temp_files:
                if os.path.exists(file_info['path']):
                    try:
                        os.unlink(file_info['path'])
                    except:
                        pass
            self.temp_files.clear()

temp_manager = TempFileManager()

# 启动后台清理线程
def cleanup_daemon():
    while True:
        time.sleep(300)  # 每5分钟清理一次
        temp_manager.cleanup_old_files()

cleanup_thread = threading.Thread(target=cleanup_daemon, daemon=True)
cleanup_thread.start()

# === 用户访问控制 ===
def check_user_limit():
    """检查是否超过用户限制"""
    global current_users
    with current_users_lock:
        if current_users >= MAX_CONCURRENT_USERS:
            return False, "当前服务器访问人数过多，请稍后再试。\n建议下载本地版本使用：https://github.com/regivsbannia/Slim_MCBE_Curve_Tool"
        current_users += 1
        return True, f"欢迎使用！当前在线用户：{current_users}/{MAX_CONCURRENT_USERS}"

def release_user():
    """释放用户计数"""
    global current_users
    with current_users_lock:
        if current_users > 0:
            current_users -= 1

# === 火车轨道设计 & 像素圆功能 ===

def generate_track_design(mode, x0, y0, x1, y1, k1, k2,
                          track_width, curvature, ground_height,
                          use_mid_point, xm, ym, k_mid):
    # 检查用户限制
    allowed, msg = check_user_limit()
    if not allowed:
        raise gr.Error(msg)
    
    try:
        html_file = None
        plotly_fig = None
        coords = pd.DataFrame(columns=['X', 'Height', 'Y'])

        def safe_convert(s):
            try:
                return float('inf') if str(s).lower() == "inf" else float(s)
            except:
                return 0.0

        use_line = (mode == "直线模式")
        k1 = 0.0 if use_line else safe_convert(k1)
        k2 = 0.0 if use_line else safe_convert(k2)

        k_mid_converted = None
        if use_mid_point:
            if use_line:
                k_mid_converted = 0.0
            elif k_mid is not None and str(k_mid).strip():
                k_mid_converted = safe_convert(k_mid)

        via = (xm, ym) if use_mid_point else None
        k_via = k_mid_converted if use_mid_point else None
        effective_curvature = 3.0 if use_line else curvature

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111)

        plot_full_track(
            (x0, y0), (x1, y1),
            k1, k2,
            track_width,
            effective_curvature,
            via=via,
            k_via=k_via,
            ground_height=ground_height,
            use_line=use_line
        )

        static_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        plt.savefig(static_img.name, bbox_inches='tight', dpi=100)
        plt.close(fig)
        temp_manager.add_file(static_img.name)

        coord_file = "rail_output.txt"
        if os.path.exists(coord_file):
            coords = pd.read_csv(coord_file, sep=' ', header=None, names=['X', 'Height', 'Y'])
            shapes, hover_x, hover_y, hover_text = [], [], [], []
            for row in coords.itertuples(index=False):
                x, height, y = row
                shapes.append(dict(
                    type="rect",
                    x0=x - 0.5, x1=x + 0.5,
                    y0=y - 0.5, y1=y + 0.5,
                    line=dict(color="blue", width=0.5),
                    fillcolor="lightblue"
                ))
                hover_x.append(x)
                hover_y.append(y)
                hover_text.append(f"X: {x}, Y: {y}, 高度: {height}")

            plotly_fig = go.Figure()
            plotly_fig.add_trace(go.Scatter(
                x=hover_x,
                y=hover_y,
                mode='markers',
                marker=dict(size=8, color='rgba(0,0,0,0)'),
                hoverinfo='text',
                text=hover_text,
                showlegend=False
            ))
            plotly_fig.update_layout(
                title="轨道像素图（交互）",
                xaxis=dict(title="X 坐标", gridcolor='lightgray', scaleanchor="y", scaleratio=1),
                yaxis=dict(title="Y 坐标", gridcolor='lightgray'),
                shapes=shapes,
                height=600,
                hovermode='closest'
            )

            html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            plotly_fig.write_html(html_file.name)
            html_file.close()
            temp_manager.add_file(html_file.name)

        temp_coord_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        coords.to_csv(temp_coord_file.name, sep=' ', index=False, header=False)
        temp_coord_file.close()
        temp_manager.add_file(temp_coord_file.name)

        return static_img.name, temp_coord_file.name, html_file.name if html_file else None, coords.round(2).values.tolist(), plotly_fig

    except Exception as e:
        release_user()  # 出错时释放用户计数
        raise gr.Error(f"生成轨道设计时出错: {str(e)}")

def gradio_draw_quarter_circle(r):
    allowed, msg = check_user_limit()
    if not allowed:
        raise gr.Error(msg)
    try:
        return draw_quarter_circle_image(r)
    finally:
        release_user()

# === Gradio 界面整合 ===

with gr.Blocks(theme=gr.themes.Soft(), title="Slim MCBE Curve Tool ") as demo:
    gr.Markdown("# Slim MCBE Curve Tool  |  轻量级MCBE曲线工具")
    gr.Markdown("*Thanks to [Amulet](https://www.amuletmc.com/)*")
    gr.Markdown("""
    ⚠️ **重要提示**：
    1. 临时文件会在30分钟后自动清理，请及时下载需要的文件
    2. 关闭或刷新页面后，生成的文件将无法再次访问
    3. 建议下载本地版本以获得更好的性能和稳定性
    """)
    
    # 用户计数器显示
    user_counter = gr.Markdown(f"当前在线用户：{current_users}/{MAX_CONCURRENT_USERS}")
    
    with gr.Tabs():

        # —— Tab1：Minecraft 像素曲线工具 —— 
        with gr.TabItem("🖌️ 曲线与圆设计工具"):

            with gr.Tabs():
                with gr.TabItem("复杂 曲线 设计"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            mode = gr.Radio(choices=["曲线模式", "直线模式"], value="曲线模式", label="生成 模式")
                            x0 = gr.Number(label="起点 X 坐标", value=0.0)
                            y0 = gr.Number(label="起点 Z 坐标", value=0.0)
                            k1 = gr.Textbox(label="起点 斜率 (数字 或 'inf')", value="0.0")
                            x1 = gr.Number(label="终点 X 坐标", value=100.0)
                            y1 = gr.Number(label="终点 Z 坐标", value=50.0)
                            k2 = gr.Textbox(label="终点 斜率 (数字 或 'inf')", value="0.0")
                            track_width = gr.Slider(label="宽度 (像素)", minimum=1, maximum=10, step=1, value=3)
                            curvature = gr.Slider(label="曲率 (建议 3)", minimum=1, maximum=6, step=0.1, value=3)
                            ground_height = gr.Number(label="高度", value=0.0)
                            use_mid_point = gr.Checkbox(label="使用 中间点", value=False)
                            with gr.Column(visible=False) as mid_col:
                                xm = gr.Number(label="中间点 X", value=50.0)
                                ym = gr.Number(label="中间点 Z", value=30.0)
                                k_mid = gr.Textbox(label="中间点 斜率", value=None)
                            use_mid_point.change(fn=lambda x: gr.update(visible=x), inputs=use_mid_point, outputs=mid_col)
                            submit_btn = gr.Button("生成 轨道 图", variant="primary")
                        with gr.Column(scale=2):
                            output_plot = gr.Image(label="轨道 静态 图")
                            gr.Markdown("### 下载txt坐标文件后上传至本地版本进行世界编辑")
                            gr.Markdown("⚠️ **注意：文件将在30分钟后自动删除，请及时下载**")
                            with gr.Tabs():
                                with gr.TabItem("交互式 可视化"):
                                    plotly_output = gr.Plot(label="交互式 轨道 图")
                                    coord_table = gr.Dataframe(label="轨道 坐标", headers=["X","高度","Z"],
                                                               datatype=["number","number","number"], col_count=3)
                                with gr.TabItem("下载 区域"):
                                    download_coords = gr.File(label="下载 坐标 文件 (.txt)")
                                    download_html = gr.File(label="下载 HTML 可视化")

                    # 动态显示/隐藏曲线相关参数
                    def update_mode_ui(mode):
                        is_curve = mode == "曲线模式"
                        return [
                            gr.update(visible=is_curve),  # k1
                            gr.update(visible=is_curve),  # k2
                            gr.update(visible=is_curve),  # curvature
                            gr.update(visible=is_curve),  # k_mid
                        ]
                    
                    mode.change(
                        fn=update_mode_ui,
                        inputs=mode,
                        outputs=[k1, k2, curvature, k_mid]
                    )

                    # 示例数据
                    gr.Examples(
                        examples=[
                            ["曲线模式", 0, 0, 100, 50, "0.0", "0.0", 1, 3, 0.0, False, 0, 0, None],
                            ["曲线模式", 0, 0, 100, 100, "inf", "0.0", 3, 3, 0.0, False, 0, 0, None],
                            ["直线模式", 0, 0, 100, 100, None, None, 3, None, 0.0, False, 0, 0, None],
                            ["曲线模式", 0, 0, 100, 100, "0.0", "3.0", 4, 3, 40, True, 50, 70, None],
                            ["曲线模式", 0, 50, 150, 0, "-1.0", "0.5", 4, 3, 80, True, 80, 30, "0.0"]
                        ],
                        inputs=[mode, x0, y0, x1, y1, k1, k2, track_width, curvature, ground_height, 
                            use_mid_point, xm, ym, k_mid],
                        outputs=[output_plot, download_coords, download_html, coord_table, plotly_output],
                        fn=generate_track_design,
                        cache_examples=False
                    )
                    
                    def generate_and_release(*args, **kwargs):
                        try:
                            result = generate_track_design(*args, **kwargs)
                            return result
                        finally:
                            release_user()
                    
                    submit_btn.click(
                        fn=generate_and_release,
                        inputs=[mode, x0, y0, x1, y1, k1, k2, track_width,
                                curvature, ground_height, use_mid_point, xm, ym, k_mid],
                        outputs=[output_plot, download_coords, download_html, coord_table, plotly_output]
                    )

                with gr.TabItem("🔵 像素圆"):
                    radius_input = gr.Number(label="半径", value=50, precision=0)
                    run_button = gr.Button("绘制", variant="primary")
                    text_output = gr.Textbox(label="线段 信息")                    
                    image_output = gr.Image(type="pil", label="四分之 一 圆 图像")
                    run_button.click(fn=gradio_draw_quarter_circle, inputs=radius_input, outputs=[image_output, text_output])

        # —— Tab2：本地版本指引 —— 
        with gr.TabItem("🌐 自动放置工具"):
            gr.Markdown("""
            # 🚀 自动放置仅本地版本可以使用
            
            ## 为什么使用本地版本？
            
            1. **性能更好**：本地运行，无需网络传输
            2. **功能完整**：包含完整的世界编辑功能
            
            ## 📥 下载与安装
            
            ### 方式一：下载打包好的 EXE（推荐）
            
            **GitHub 项目地址**：[https://github.com/regivsbannia/Slim_MCBE_Curve_Tool](https://github.com/regivsbannia/Slim_MCBE_Curve_Tool)
            
            1. 访问上面的 GitHub 链接
            2. 在 Releases 页面下载最新版本的 EXE 文件
            3. 双击运行即可，无需安装 Python 环境
            
            ### 方式二：自行部署 Python 版本
            

            ```bash
            # 1. 克隆项目或下载 Python 版本
            # 方式 A：克隆项目（需要 git）
            git clone https://github.com/regivsbannia/Slim_MCBE_Curve_Tool.git
            cd Slim_MCBE_Curve_Tool/project_self

            # 方式 B：下载 Release 中的 Python 版本（推荐）
            # 从 GitHub Releases 页面下载 "XXX_python_zip" 压缩包
            # 解压后进入解压目录

            # 2. 安装依赖
            pip install -r requirements.txt

            # 3. 运行程序
            python combined_demo.py
            ```
            
            ## ❓ 常见问题
            
            **Q: 本地版本有病毒吗？**  
            A: 没有。代码完全开源，可以在 GitHub 上查看所有源代码。请允许windows运行本exe文件。
            
            **Q: 需要安装 Minecraft 吗？**  
            A: 不需要。本工具只处理 Minecraft 世界文件，不需要游戏本体。
            
            **Q: 支持哪些 Minecraft 版本？**  
            A: 支持 Minecraft Bedrock Edition 最新版本。
            
            **Q: 遇到问题怎么办？**  
            A: 自行部署python版本
            """)
            
            gr.Markdown("---")
            gr.Markdown("""
            ⚠️ **安全提示**：网页版已移除存档编辑功能，以防止恶意文件攻击服务器。  
            ✅ **建议所有用户都使用本地版本以获得最佳体验和完整功能。**
            """)

    gr.Markdown("---\nMCBE Curve Tool，欢迎体验！")
    
    # 页面关闭时清理用户计数
    demo.unload(release_user)
    
if __name__ == "__main__":
    demo.queue(max_size=MAX_CONCURRENT_USERS).launch(
        server_name="0.0.0.0", 
        server_port=7861,
        show_error=True
    )
    # 程序退出时清理所有临时文件
    temp_manager.cleanup_all()
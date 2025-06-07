import gradio as gr
import zipfile
import tempfile
import os
import shutil
from pathlib import Path

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

# === 火车轨道设计 & 像素圆功能 ===

def generate_track_design(mode, x0, y0, x1, y1, k1, k2,
                          track_width, curvature, ground_height,
                          use_mid_point, xm, ym, k_mid):
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

        temp_coord_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        coords.to_csv(temp_coord_file.name, sep=' ', index=False, header=False)
        temp_coord_file.close()

        return static_img.name, temp_coord_file.name, html_file.name if html_file else None, coords.round(2).values.tolist(), plotly_fig

    except Exception as e:
        raise gr.Error(f"生成轨道设计时出错: {str(e)}")


def gradio_draw_quarter_circle(r):
    return draw_quarter_circle_image(r)

# === Minecraft 世界多步骤编辑功能 ===

def unzip_world(zip_file):
    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file.name, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    # 如果解压后没有直接的 level.dat，则进入第一层子目录
    if not (Path(tmp_dir) / "level.dat").exists():
        subdirs = [f for f in Path(tmp_dir).iterdir() if f.is_dir()]
        if subdirs:
            return str(subdirs[0])
    return tmp_dir

def zip_world_folder(world_folder):
    zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(zip_path.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(world_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, world_folder)
                zipf.write(file_path, arcname)
    return zip_path.name

def start_session(world_zip):
    try:
        world_path = unzip_world(world_zip)
        return world_path, "✅ 世界上传并解压成功。"
    except Exception as e:
        return None, f"❌ 上传失败：{e}"

def run_file_fill_ui(session_path, coords_file, block_name, slab_option):
    if not session_path:
        return "⚠️ 请先上传世界文件。"
    slab = slab_option if slab_option in ("top", "bottom") else None
    try:
        result = fill_from_file(session_path, coords_file.name, block_name, slab)
        return result
    except Exception as e:
        return f"❌ 操作失败：{e}"

def run_region_fill_ui(session_path, x1, y1, z1, x2, y2, z2, block_name, slab_option):
    if not session_path:
        return "⚠️ 请先上传世界文件。"
    slab = slab_option if slab_option in ("top", "bottom") else None
    try:
        coord1 = (int(x1), int(y1), int(z1))
        coord2 = (int(x2), int(y2), int(z2))
        result = fill_region(session_path, coord1, coord2, block_name, slab)
        return result
    except Exception as e:
        return f"❌ 操作失败：{e}"

def export_final_world(session_path):
    if not session_path:
        return None
    return zip_world_folder(session_path)


# === Gradio 界面整合 ===

with gr.Blocks(theme=gr.themes.Soft(), title="Slim MCBE Curve Tool ") as demo:
    gr.Markdown("# Slim MCBE Curve Tool  |  轻量级MCBE曲线工具")
    gr.Markdown("*Thanks to [Amulet](https://www.amuletmc.com/)*")
    
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
                            gr.Markdown("### 下载txt坐标文件后上传至‘世界编辑工具’页面自动填充")                            
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
                    
                    submit_btn.click(
                        fn=generate_track_design,
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

        # —— Tab2：Minecraft 多步骤编辑 —— 
        with gr.TabItem("🌐 世界编辑工具"):
            gr.Markdown("###步骤： 1. 上传世界 → 2. 多次操作 → 3. 导出最终世界###")

            session_world = gr.State(value=None)

            with gr.Row():
                world_zip = gr.File(label="上传 世界 压缩包 (.zip)")
                upload_btn = gr.Button("上传并解压", variant="primary")
                upload_output = gr.Textbox(label="上传状态")
            upload_btn.click(fn=start_session, inputs=[world_zip], outputs=[session_world, upload_output])

            with gr.Tabs():
                with gr.TabItem("坐标文件填充"):
                    coords_file = gr.File(label="上传 坐标文件 (.txt 每行 x y z)")
                    file_block = gr.Textbox(label="方块 名称 (如 stone 或 normal_stone_slab)")
                    file_slab = gr.Radio(["none", "top", "bottom"], label="半砖 选项", value="none")
                    btn1 = gr.Button("执行 坐标填充", variant="primary")
                    output1 = gr.Textbox(label="执行 结果")
                    btn1.click(fn=run_file_fill_ui,
                               inputs=[session_world, coords_file, file_block, file_slab],
                               outputs=[output1])

                with gr.TabItem("区域 坐标 填充"):
                    x1 = gr.Number(label="X1")
                    y1 = gr.Number(label="Y1")
                    z1 = gr.Number(label="Z1")
                    x2 = gr.Number(label="X2")
                    y2 = gr.Number(label="Y2")
                    z2 = gr.Number(label="Z2")
                    region_block = gr.Textbox(label="方块 名称 (如 stone 或 normal_stone_slab)")
                    region_slab = gr.Radio(["none", "top", "bottom"], label="半砖 选项", value="none")
                    btn2 = gr.Button("执行 区域 填充", variant="primary")
                    output2 = gr.Textbox(label="执行 结果")
                    btn2.click(fn=run_region_fill_ui,
                               inputs=[session_world, x1, y1, z1, x2, y2, z2, region_block, region_slab],
                               outputs=[output2])

            with gr.Row():
                export_btn = gr.Button("📦 导出 最终 世界", variant="primary")
                download_world = gr.File(label="下载 世界 (.zip)", interactive=False)
            export_btn.click(fn=export_final_world, inputs=[session_world], outputs=[download_world])

    gr.Markdown("---\nMCBE Curve Tool，欢迎体验！")
    
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)


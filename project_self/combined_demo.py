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

def run_file_fill(world_path, coords_file, block_name, slab_choice):
    """
    Gradio 调用：从文件填充
    slab_choice: 三个选项 "none"/"top"/"bottom"
    """
    # 如果用户选择 none，就把 slab_choice 设为 None
    block_half = slab_choice if slab_choice in ("top", "bottom") else None

    try:
        result = fill_from_file(world_path, coords_file.name, block_name, block_half)
    except Exception as e:
        result = f"❌ 运行时发生错误：{e}"
    return result


def run_region_fill(
    world_path,
    x1, y1, z1,
    x2, y2, z2,
    block_name,
    slab_choice
):
    """
    Gradio 调用：按区域填充
    slab_choice: 三个选项 "none"/"top"/"bottom"
    """
    block_half = slab_choice if slab_choice in ("top", "bottom") else None
    coord1 = (int(x1), int(y1), int(z1))
    coord2 = (int(x2), int(y2), int(z2))

    try:
        result = fill_region(world_path, coord1, coord2, block_name, block_half)
    except Exception as e:
        result = f"❌ 运行时发生错误：{e}"
    return result


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

            tabs = gr.Tabs()

            # —— Tab1：从文件坐标批量放置 —— 
            with tabs:
                with gr.TabItem("从文件坐标填充"):
                    gr.Markdown("**说明：** 上传一个文本文件，里面每行是 `x y z`，程序会将所有这些点设置成指定方块。")
                    file_world = gr.Textbox(label="世界文件夹路径", placeholder="例如：E:/my_mc_world")
                    coords_file = gr.File(label="坐标文件 (*.txt)，每行格式：x y z")
                    file_block = gr.Textbox(label="方块名称", placeholder="例如：stone 或 normal_stone_slab")
                    file_slab = gr.Radio(
                        choices=["none", "top", "bottom"],
                        label="如果是半砖，选择‘top’或‘bottom’，否则选‘none’",
                        value="none"
                    )
                    file_btn = gr.Button("开始从文件放置")
                    file_output = gr.Textbox(label="运行结果")

                    file_btn.click(
                        run_file_fill,
                        inputs=[file_world, coords_file, file_block, file_slab],
                        outputs=[file_output]
                    )

                # —— Tab2：按区域填充 —— 
                with gr.TabItem("按区域填充"):
                    gr.Markdown("**说明：** 输入两个对角点坐标，程序会填充此区域。")
                    region_world = gr.Textbox(label="世界文件夹路径", placeholder="例如：E:/my_mc_world")
                    x1_in = gr.Number(label="第一个对角点 X1", value=0)
                    y1_in = gr.Number(label="第一个对角点 Y1", value=0)
                    z1_in = gr.Number(label="第一个对角点 Z1", value=0)

                    x2_in = gr.Number(label="第二个对角点 X2", value=0)
                    y2_in = gr.Number(label="第二个对角点 Y2", value=0)
                    z2_in = gr.Number(label="第二个对角点 Z2", value=0)

                    region_block = gr.Textbox(label="方块名称", placeholder="例如：stone 或 normal_stone_slab")
                    region_slab = gr.Radio(
                        choices=["none", "top", "bottom"],
                        label="如果是半砖，选择‘top’或‘bottom’，否则选‘none’",
                        value="none"
                    )
                    region_btn = gr.Button("开始区域填充")
                    region_output = gr.Textbox(label="运行结果")

                    region_btn.click(
                        run_region_fill,
                        inputs=[region_world, x1_in, y1_in, z1_in, x2_in, y2_in, z2_in, region_block, region_slab],
                        outputs=[region_output]
                    )

    gr.Markdown("---\nMCBE Curve Tool，欢迎体验！")
    
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)


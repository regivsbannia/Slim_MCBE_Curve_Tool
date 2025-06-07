import gradio as gr
from project.angle_straight import plot_full_track
from circle_vision_simple import draw_quarter_circle_image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tempfile
import os
import pandas as pd
import plotly.express as px
import json
import zhplot
import plotly.graph_objects as go
import numpy as np
import io
from PIL import Image

# 火车轨道设计功能
def generate_track_design(mode, x0, y0, x1, y1, k1, k2, track_width, curvature, ground_height, use_mid_point, xm, ym, k_mid):
    if mode == "直线模式":
        use_line = True
    else:
        use_line = False

    """生成轨道设计的主函数"""
    try:
        # 防止变量未定义异常
        html_file = None
        plotly_fig = None
        table_data = []
        coords = pd.DataFrame(columns=['X', 'Height', 'Y'])

        # 处理斜率输入
        def safe_convert(s):
            try:
                return float('inf') if str(s).lower() == "inf" else float(s)
            except:
                return 0.0
        
        k1 = 0.0 if use_line else safe_convert(k1)
        k2 = 0.0 if use_line else safe_convert(k2)

        k_mid_converted = None
        if use_mid_point:
            if use_line:
                k_mid_converted = 0.0  # 直线模式下中间点斜率设为0
            elif k_mid is not None and str(k_mid).strip():  # 非空输入
                k_mid_converted = safe_convert(k_mid)
        
        # 处理中间点
        via = (xm, ym) if use_mid_point else None
        k_via = k_mid_converted if use_mid_point else None
        
        # 直线模式下不使用曲率参数
        effective_curvature = 3.0 if use_line else curvature

        # 创建 Matplotlib 图形
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111)

        # 调用绘图函数
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

        # 保存 Matplotlib 图像为 PNG
        static_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        plt.savefig(static_img.name, bbox_inches='tight', dpi=100)
        plt.close(fig)

        # 读取 rail_output.txt 文件
        coord_file = "rail_output.txt"
        if os.path.exists(coord_file):
            coords = pd.read_csv(coord_file, sep=' ', header=None, names=['X', 'Height', 'Y'])

            # ========== 构造 Plotly 图 ==========
            shapes = []
            hover_x, hover_y, hover_text = [], [], []

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
                title="轨道像素图（带交互）",
                xaxis=dict(title="X 坐标", gridcolor='lightgray', scaleanchor="y", scaleratio=1),
                yaxis=dict(title="Y 坐标", gridcolor='lightgray'),
                shapes=shapes,
                height=600,
                hovermode='closest'
            )

            # 保存交互式 HTML 文件
            html_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
            plotly_fig.write_html(html_file.name)
            html_file.close()

            # 表格数据输出
            table_data = coords.round(2).values.tolist()

        # 坐标文本文件另存
        temp_coord_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        coords.to_csv(temp_coord_file.name, sep=' ', index=False, header=False)
        temp_coord_file.close()

        return (
            static_img.name,
            temp_coord_file.name,
            html_file.name if html_file else None,
            table_data,
            plotly_fig
        )

    except Exception as e:
        raise gr.Error(f"生成轨道设计时出错: {str(e)}")

# 四分之一圆功能

def gradio_draw_quarter_circle(r):
    return draw_quarter_circle_image(r)
   

# 创建统一的应用界面
with gr.Blocks(theme=gr.themes.Soft(), title="Minecraft像素曲线工具") as app:
    gr.Markdown("# Minecraft像素曲线工具")
    gr.Markdown("整合的几何设计工具，包含复杂曲线设计和像素圆可视化功能")
    
    with gr.Tabs():
        # 火车轨道设计标签页
        with gr.TabItem("复杂曲线设计"):
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.Markdown("## 模式选择")
                        mode = gr.Radio(
                            choices=["曲线模式", "直线模式"],
                            value="曲线模式",
                            label="选择生成模式",
                            interactive=True
                        )
                    
                    with gr.Group():
                        gr.Markdown("## 起点参数")
                        x0 = gr.Number(label="起点 X 坐标", value=0.0)
                        y0 = gr.Number(label="起点 Z 坐标", value=0.0)
                        k1 = gr.Textbox(
                            label="起点切线斜率 (输入数字或'inf'表示垂直)", 
                            value="0.0",
                            visible=True
                        )
                    
                    with gr.Group():
                        gr.Markdown("## 终点参数")
                        x1 = gr.Number(label="终点 X 坐标", value=100.0)
                        y1 = gr.Number(label="终点 Z 坐标", value=50.0)
                        k2 = gr.Textbox(
                            label="终点切线斜率 (输入数字或'inf'表示垂直)", 
                            value="0.0",
                            visible=True
                        )
                    
                    with gr.Group():
                        gr.Markdown("## 轨道参数")
                        track_width = gr.Slider(label="宽度 (像素)", minimum=1, maximum=10, step=1, value=3)
                        curvature = gr.Slider(
                            label="曲率参数（越小越弯，越大越直，建议为3）", 
                            minimum=1, 
                            maximum=6, 
                            step=0.1, 
                            value=3,
                            visible=True
                        )
                        ground_height = gr.Number(label="高度", value=0.0)
                    
                    with gr.Group():
                        gr.Markdown("## 中间点设置")
                        use_mid_point = gr.Checkbox(label="使用中间点", value=False)
                        with gr.Column(visible=False) as mid_col:
                            xm = gr.Number(label="中间点 X 坐标", value=50.0)
                            ym = gr.Number(label="中间点 Z 坐标", value=30.0)
                            k_mid = gr.Textbox(
                                label="中间点切线斜率 (输入数字或'inf'表示垂直)，默认为均值", 
                                value=None,
                                visible=True
                            )
                        
                        use_mid_point.change(
                            fn=lambda x: gr.update(visible=x),
                            inputs=use_mid_point,
                            outputs=mid_col
                        )
                    
                    submit_btn = gr.Button("生成轨道设计", variant="primary")
                
                with gr.Column(scale=2):
                    with gr.Tabs():
                        with gr.TabItem("静态图像"):
                            output_plot = gr.Image(label="轨道设计图", interactive=False)
                        with gr.TabItem("交互式可视化"):
                            plotly_output = gr.Plot(label="交互式轨道可视化")
                            coord_table = gr.Dataframe(
                                label="轨道坐标数据", 
                                headers=["X坐标", "高度", "Z坐标"],
                                datatype=["number", "number", "number"],
                                col_count=3
                            )
                    
                    with gr.Row():
                        download_coords = gr.File(label="下载坐标文件(TXT)")
                        download_html = gr.File(label="下载交互式可视化(HTML)")
            
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
                inputs=[mode, x0, y0, x1, y1, k1, k2, track_width, curvature, ground_height, 
                       use_mid_point, xm, ym, k_mid],
                outputs=[output_plot, download_coords, download_html, coord_table, plotly_output]
            )
        
        # 四分之一圆标签页
        with gr.TabItem("🔵 像素圆可视化"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## 四分之一圆可视化")
                    gr.Markdown("输入半径生成1/4圆及其线段分组")
                    radius_input = gr.Number(label="半径", value=50, precision=0)
                    run_button = gr.Button("绘制", variant="primary")
                    text_output = gr.Textbox(label="线段信息")
                
                with gr.Column(scale=2):
                    image_output = gr.Image(type="pil", label="四分之一圆可视化")
            
            run_button.click(
                fn=gradio_draw_quarter_circle, 
                inputs=radius_input, 
                outputs=[image_output, text_output]
            )
    
    # 页脚
    gr.Markdown("---")
    gr.Markdown("Minecraft像素曲线工具")

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
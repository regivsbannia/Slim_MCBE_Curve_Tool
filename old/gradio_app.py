import gradio as gr
from angle_width_hight_bigtu_gradio import plot_full_track
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

def generate_track_design(x0, y0, x1, y1, k1, k2, track_width, ground_height, use_mid_point, xm, ym):
    """生成轨道设计的主函数"""
    try:
        # 防止变量未定义异常
        html_file = None
        plotly_fig = None
        table_data = []
        coords = pd.DataFrame(columns=['X', 'Height', 'Y'])

        # 处理斜率输入
        k1 = float('inf') if k1.lower() == "inf" else float(k1)
        k2 = float('inf') if k2.lower() == "inf" else float(k2)

        # 处理中间点
        via_point = (float(xm), float(ym)) if use_mid_point else None

        # 创建 Matplotlib 图形
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111)

        # 调用轨道绘制函数
        plot_full_track(
            (float(x0), float(y0)),
            (float(x1), float(y1)),
            k1, k2,
            int(track_width),
            via_point,
            float(ground_height)
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

# 创建Gradio界面
with gr.Blocks(theme=gr.themes.Soft(), title="火车轨道设计工具") as demo:
    gr.Markdown("# 🚂 火车轨道设计工具")
    gr.Markdown("使用此工具设计火车轨道，可视化结果并导出坐标数据")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("## 起点参数")
                x0 = gr.Number(label="起点 X 坐标", value=0.0)
                y0 = gr.Number(label="起点 Y 坐标", value=0.0)
                k1 = gr.Textbox(label="起点切线斜率 (输入数字或'inf'表示垂直)", value="0.0")
            
            with gr.Group():
                gr.Markdown("## 终点参数")
                x1 = gr.Number(label="终点 X 坐标", value=100.0)
                y1 = gr.Number(label="终点 Y 坐标", value=50.0)
                k2 = gr.Textbox(label="终点切线斜率 (输入数字或'inf'表示垂直)", value="0.0")
            
            with gr.Group():
                gr.Markdown("## 轨道参数")
                track_width = gr.Slider(label="轨道宽度 (像素)", minimum=1, maximum=10, step=1, value=3)
                ground_height = gr.Number(label="轨道地面高度", value=0.0)
            
            with gr.Group():
                gr.Markdown("## 中间点设置")
                use_mid_point = gr.Checkbox(label="使用中间点", value=False)
                with gr.Column(visible=False) as mid_col:
                    xm = gr.Number(label="中间点 X 坐标", value=50.0)
                    ym = gr.Number(label="中间点 Y 坐标", value=30.0)
                
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
                        headers=["X坐标", "地面高度", "Y坐标"],
                        datatype=["number", "number", "number"],
                        col_count=3
                    )
            
            with gr.Row():
                download_coords = gr.File(label="下载坐标文件(TXT)")
                download_html = gr.File(label="下载交互式可视化(HTML)")
    
    # 示例数据
    gr.Examples(
        examples=[
            [0, 0, 100, 50, "0.0", "0.0", 3, 0.0, False, 0, 0],
            [0, 0, 100, 100, "inf", "0.0", 3, 0.0, False, 0, 0],
            [0, 0, 100, 100, "0.0", "inf", 4, 0.5, True, 50, 70],
            [0, 50, 150, 0, "-1.0", "0.5", 5, 1.0, True, 80, 30]
        ],
        inputs=[x0, y0, x1, y1, k1, k2, track_width, ground_height, use_mid_point, xm, ym],
        outputs=[output_plot, download_coords, download_html, coord_table, plotly_output],
        fn=generate_track_design,
        cache_examples=False
    )
    
    submit_btn.click(
        fn=generate_track_design,
        inputs=[x0, y0, x1, y1, k1, k2, track_width, ground_height, use_mid_point, xm, ym],
        outputs=[output_plot, download_coords, download_html, coord_table, plotly_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
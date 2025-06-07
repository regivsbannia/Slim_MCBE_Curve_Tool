import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image
import zhplot  # 如果此模块自定义了中文支持或样式，可以保留

def generate_circle_segments(r):
    if r == 0:
        return []
    x = r
    y = 0
    d = 1 - r
    segments = []
    current_segment = 0
    while x >= y:
        current_segment += 1
        if d < 0:
            d += 2 * y + 3
        else:
            d += 2 * (y - x) + 5
            segments.append(current_segment)
            current_segment = 0
            x -= 1
        y += 1
    if current_segment > 0:
        segments.append(current_segment)
    mirrored = segments[::-1]
    full_segments = segments + mirrored
    return full_segments

def generate_quarter_circle_points(r):
    points = []
    if r == 0:
        return points
    
    x = r
    y = 0
    d = 1 - r
    
    while x >= y:
        points.append((x, y))
        if d < 0:
            d += 2 * y + 3
        else:
            d += 2 * (y - x) + 5
            x -= 1
        y += 1
    
    return points

def draw_quarter_circle_image(r):
    if r > 999:
        return None, "错误：半径过大，建议不超过999。"
    if r <= 0:
        return None, "错误：请输入正整数半径。"
        
    quarter_points = generate_quarter_circle_points(r)
    segments = generate_circle_segments(r)
    
    fig, ax = plt.subplots(figsize=(20, 20))  # 固定画布大小
    ax.set_xlim(-0.5, r + 0.5)
    ax.set_ylim(-0.5, r + 0.5)
    ax.set_xticks(np.arange(0, r + 1, max(1, r // 10)))
    ax.set_yticks(np.arange(0, r + 1, max(1, r // 10)))
    ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
    ax.set_aspect('equal')
    ax.set_title(f'1/4直角圆周（半径={r}）')

    all_points = set()
    for x, y in quarter_points:
        all_points.add((x, y))
        all_points.add((y, x))

    for x, y in all_points:
        rect = plt.Rectangle((x - 0.5, y - 0.5), 1, 1,
                             edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)

    # 动态字体大小
    font_size = max(16, 3000 // r)

    # 标注段长度
    start_idx = 0
    for seg_num, seg_length in enumerate(segments, 1):
        if start_idx >= len(quarter_points):
            break
        end_idx = min(start_idx + seg_length - 1, len(quarter_points) - 1)
        mid_x = (quarter_points[start_idx][0] + quarter_points[end_idx][0]) / 2
        mid_y = (quarter_points[start_idx][1] + quarter_points[end_idx][1]) / 2
        ax.text(mid_x - 1, mid_y - 0.3, str(seg_length),
                ha='center', va='center', color='red', fontsize=font_size)
        start_idx = end_idx + 1

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image = Image.open(buf)

    segment_str = ' '.join(map(str, segments))
    segment_info = f"线段组（共{len(segments)}段）:\n{segment_str}"
    return image, segment_info


# Gradio 界面构建
with gr.Blocks(title="四分之一圆可视化") as demo:
    gr.Markdown("## 输入半径并绘制1/4圆及其线段分组")
    radius_input = gr.Number(label="半径", value=5, precision=0)
    image_output = gr.Image(type="pil", label="绘制图像")
    text_output = gr.Textbox(label="线段信息")
    run_button = gr.Button("绘制")
    
    run_button.click(fn=draw_quarter_circle_image, 
                     inputs=radius_input, 
                     outputs=[image_output, text_output])

demo.launch()


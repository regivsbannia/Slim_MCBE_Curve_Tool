# circle_vision_neo.py
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

def generate_circle_segments(r):
    """
    生成整数半径 r 对应的圆周离散化后在第一象限上的“线段组”长度序列。
    """
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
    """
    生成整数半径 r 对应的第一象限扇形（x>=0,y>=0）上
    所有离散化后的圆周坐标 (x,y) 列表。
    """
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
    """
    根据半径 r，绘制一张“1/4 直角圆”的像素化示意图，并在图上标注每段
    的长度（线段组长度）。返回一个 PIL.Image.Image 对象（用于 Gradio 显示），
    以及一段文字说明（线段组的信息）。
    """
    if r > 999:
        return None, "错误：半径过大，建议不超过 999。"
    if r <= 0:
        return None, "错误：请输入正整数半径。"
    
    quarter_points = generate_quarter_circle_points(r)
    segments = generate_circle_segments(r)

    # 整体画布设置
    fig, ax = plt.subplots(figsize=(min(20, r + 2), min(20, r + 2)))
    ax.set_xlim(-0.5, r + 0.5)
    ax.set_ylim(-0.5, r + 0.5)
    # 只在重要刻度上画网格，避免过密
    step = max(1, r // 10)
    ax.set_xticks(np.arange(0, r + 1, step))
    ax.set_yticks(np.arange(0, r + 1, step))
    ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
    ax.set_aspect('equal')
    ax.set_title(f'1/4 直角圆（半径={r}）', fontsize=16)

    # 把第一象限的 (x,y) 和 (y,x) 都画上，构成完整的扇形
    all_points = set()
    for x, y in quarter_points:
        all_points.add((x, y))
        all_points.add((y, x))

    for x, y in all_points:
        rect = plt.Rectangle((x - 0.5, y - 0.5), 1, 1,
                             edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)

    # 动态字体：r 越大，字体越小；但不小于 16
    font_size = max(16, 3000 // r)

    # 标注“线段组”编号（实际上只在第一象限轮廓上标记）
    start_idx = 0
    for seg_length in segments:
        if start_idx >= len(quarter_points):
            break
        end_idx = min(start_idx + seg_length - 1, len(quarter_points) - 1)
        mid_x = (quarter_points[start_idx][0] + quarter_points[end_idx][0]) / 2
        mid_y = (quarter_points[start_idx][1] + quarter_points[end_idx][1]) / 2
        ax.text(mid_x - 1, mid_y - 0.3, str(seg_length),
                ha='center', va='center', color='red', fontsize=font_size)
        start_idx = end_idx + 1

    # 把图存到内存 buffer，再由 PIL 读取，以便 Gradio 直接显示
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image = Image.open(buf)

    # 生成文字说明：线段组长度序列
    segment_str = ' '.join(map(str, segments))
    segment_info = f"线段组（共{len(segments)}段）：\n{segment_str}"
    return image, segment_info

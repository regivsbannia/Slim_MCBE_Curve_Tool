import matplotlib.pyplot as plt
import numpy as np
import zhplot

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

def draw_quarter_circle(r):
    quarter_points = generate_quarter_circle_points(r)
    segments = generate_circle_segments(r)
    
    if not quarter_points:
        print("半径为0，无图形。")
        return
    
    fig, ax = plt.subplots(figsize=(r+2, r+2))
    ax.set_xlim(-0.5, r+0.5)
    ax.set_ylim(-0.5, r+0.5)
    ax.set_xticks(np.arange(0, r+1))
    ax.set_yticks(np.arange(0, r+1))
    ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
    ax.set_aspect('equal')
    ax.set_title(f'1/4直角圆周（半径={r}）')
    
    # 绘制1/4圆的轮廓点（不填充）
    all_points = set()
    
    # 第一象限 (x >= 0, y >= 0)
    for x, y in quarter_points:
        all_points.add((x, y))
        all_points.add((y, x))
    
    # 绘制所有轮廓点
    for x, y in all_points:
        rect = plt.Rectangle((x-0.5, y-0.5), 1, 1, 
                           edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)
    
    # 生成线段组信息
    segment_info = []
    current_segment = 1
    prev_x = quarter_points[0][0]
    
    for i in range(1, len(quarter_points)):
        if quarter_points[i][0] == prev_x:
            current_segment += 1
        else:
            segment_info.append(current_segment)
            current_segment = 1
            prev_x = quarter_points[i][0]
    segment_info.append(current_segment)
    
    # 标注线段组编号（在第一象限的线段上）
    start_idx = 0
    for seg_num, seg_length in enumerate(segments, 1):
        if start_idx >= len(quarter_points):
            break
        
        end_idx = start_idx + seg_length - 1
        if end_idx >= len(quarter_points):
            end_idx = len(quarter_points) - 1
        
        # 计算线段中点坐标
        mid_x = (quarter_points[start_idx][0] + quarter_points[end_idx][0]) / 2
        mid_y = (quarter_points[start_idx][1] + quarter_points[end_idx][1]) / 2
        
        # 标注位置调整
        ax.text(mid_x - 1, mid_y - 0.3, str(seg_length), 
               ha='center', va='center', color='red', fontsize=16)
        
        start_idx = end_idx + 1
    plt.tight_layout()
    plt.show()

radius = int(input("请输入半径: "))
segments = generate_circle_segments(radius)
# 逐个数字用空格分隔
segment_str = ' '.join(map(str, segments))
print(f"线段组（共{len(segments)}段）: {segment_str}")
draw_quarter_circle(radius)
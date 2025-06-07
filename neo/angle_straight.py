import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import zhplot

def unit_vector(k):
    if k == float('inf') or abs(k) > 1e6:
        return (0.0, 1.0)
    norm = math.sqrt(1 + k**2)
    return (1.0 / norm, k / norm)

def remove_duplicates(pts):
    seen = set()
    out = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out

def enforce_4connectivity(raw_pixels):
    if not raw_pixels:
        return []
    new_path = [raw_pixels[0]]
    def step_towards(x0, y0, tx, ty):
        dx = tx - x0
        dy = ty - y0
        if dx != 0:
            return (x0 + (1 if dx > 0 else -1), y0)
        if dy != 0:
            return (x0, y0 + (1 if dy > 0 else -1))
        return (x0, y0)

    for (px, py) in raw_pixels[1:]:
        cx, cy = new_path[-1]
        while (cx, cy) != (px, py):
            nx, ny = step_towards(cx, cy, px, py)
            new_path.append((nx, ny))
            cx, cy = nx, ny

    deduped = []
    prev = None
    for p in new_path:
        if p != prev:
            deduped.append(p)
            prev = p
    return deduped

def generate_line(P0, P1, samples_per_unit=1.0):
    x0, y0 = P0
    x1, y1 = P1
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    N = max(int(length * samples_per_unit), 2)
    
    pixel_coords = []
    for i in range(N + 1):
        t = i / N
        x = x0 + t * dx
        y = y0 + t * dy
        ix, iy = int(x + 0.5), int(y + 0.5)
        pixel_coords.append((ix, iy))
    
    raw = remove_duplicates(pixel_coords)
    consistent = enforce_4connectivity(raw)
    return consistent, [(x0 + t * dx, y0 + t * dy) for t in [i/N for i in range(N+1)]]

def generate_bezier(P0, P3, k1, k2, curvature, samples_per_unit=1.5):
    d = math.hypot(P3[0] - P0[0], P3[1] - P0[1])
    d1 = d / curvature
    d2 = d / curvature

    ux1, uy1 = unit_vector(k1)
    ux2, uy2 = unit_vector(k2)

    P1 = (P0[0] + d1 * ux1, P0[1] + d1 * uy1)
    P2 = (P3[0] - d2 * ux2, P3[1] - d2 * uy2)

    N = max(int(d * samples_per_unit), 4)
    curve_points = []
    pixel_coords = []
    for i in range(N + 1):
        t = i / N
        b0 = (1 - t)**3
        b1 = 3 * (1 - t)**2 * t
        b2 = 3 * (1 - t) * t**2
        b3 = t**3

        ux = b0*P0[0] + b1*P1[0] + b2*P2[0] + b3*P3[0]
        vy = b0*P0[1] + b1*P1[1] + b2*P2[1] + b3*P3[1]
        curve_points.append((ux, vy))

        ix, iy = int(ux + 0.5), int(vy + 0.5)
        pixel_coords.append((ix, iy))

    raw = remove_duplicates(pixel_coords)
    consistent = enforce_4connectivity(raw)
    return consistent, curve_points, (P0, P1, P2, P3)

def draw_arrow(ax, point, k, length=8, color='green'):
    ux, uy = unit_vector(k)
    ax.arrow(point[0], point[1], ux*length, uy*length, head_width=2, head_length=4, fc=color, ec=color)

def plot_full_track(a, b, k1, k2, track_width=1.0, curvature=3.0, via=None, k_via=None, ground_height=0.0, use_line=False):
    all_points = []
    curves = []
    
    if use_line:
        # 使用直线模式
        if via:
            pix1, curve1 = generate_line(a, via)
            pix2, curve2 = generate_line(via, b)
            all_points += pix1 + pix2
            curves = [(curve1, None), (curve2, None)]
        else:
            pix, curve = generate_line(a, b)
            all_points += pix
            curves = [(curve, None)]
    else:
        # 使用贝塞尔曲线模式
        if via:
            mid = via
            if k_via is not None:
                k_mid = k_via
                pix1, curve1, ctrl1 = generate_bezier(a, mid, k1, k_mid, curvature)
                pix2, curve2, ctrl2 = generate_bezier(mid, b, k_mid, k2, curvature)
                all_points += pix1 + pix2
                curves = [(curve1, ctrl1), (curve2, ctrl2)]
            else:
                k_mid = (k1+k2)/2
                pix1, curve1, ctrl1 = generate_bezier(a, mid, k1, k_mid, curvature)
                pix2, curve2, ctrl2 = generate_bezier(mid, b, k_mid, k2, curvature)
                all_points += pix1 + pix2
                curves = [(curve1, ctrl1), (curve2, ctrl2)]
        else:
            pix, curve, ctrl = generate_bezier(a, b, k1, k2, curvature)
            all_points += pix
            curves = [(curve, ctrl)]

    drawn_pixels = set()
    for (cx, cy) in remove_duplicates(all_points):
        half = int(track_width // 2)
        for dx in range(-half, half + 1):
            for dy in range(-half, half + 1):
                drawn_pixels.add((cx + dx, cy + dy))

    if drawn_pixels:
        all_x, all_y = zip(*drawn_pixels)
        xmin, xmax = min(all_x), max(all_x)
        ymin, ymax = min(all_y), max(all_y)
        width = xmax - xmin + 1
        height = ymax - ymin + 1
        figsize = (max(6, width / 5), max(5, height / 5))
    else:
        figsize = (10, 8)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.set_title("Rail Track with Intermediate Point & Width")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    for curve, ctrl in curves:
        cx, cy = zip(*curve)
        ax.plot(cx, cy, '-', color='black', linewidth=1)
        if ctrl:  # 只有贝塞尔曲线有控制点
            P0, P1, P2, P3 = ctrl
            ax.plot(*zip(P0, P1), '--', color='gray', linewidth=1)
            ax.plot(*zip(P2, P3), '--', color='gray', linewidth=1)
            ax.plot(P1[0], P1[1], 'o', color='purple')
            ax.plot(P2[0], P2[1], 'o', color='purple')

    if not use_line:  # 只有曲线模式显示箭头
        draw_arrow(ax, a, k1, color='green')
        draw_arrow(ax, b, k2, color='green')

    if via:
        ax.plot(via[0], via[1], 'ro', label='经过点')
        ax.text(via[0], via[1] + 3, '中间点', ha='center', color='red')

    for (px, py) in drawn_pixels:
        rect = patches.Rectangle(
            (px - 0.5, py - 0.5), 1, 1,
            edgecolor='blue',
            facecolor='lightblue'
        )
        ax.add_patch(rect)

    margin = 5
    ax.set_xlim(xmin - margin, xmax + margin)
    ax.set_ylim(ymin - margin, ymax + margin)
    ax.set_xticks(range(int(xmin - margin), int(xmax + margin + 1)))
    ax.set_yticks(range(int(ymin - margin), int(ymax + margin + 1)))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.legend()

    with open("rail_output.txt", "w") as f:
        for (x, y) in sorted(drawn_pixels):
            f.write(f"{x} {ground_height} {y}\n")

    ax.legend()
    plt.tight_layout()
    plt.show()
    
if __name__ == "__main__":
    print("请输入起点坐标 a(x0, y0)：")
    x0 = float(input("x0 = "))
    y0 = float(input("y0 = "))
    print("请输入终点坐标 b(x1, y1)：")
    x1 = float(input("x1 = "))
    y1 = float(input("y1 = "))
    
    print("请选择模式：1-直线模式，2-曲线模式（默认）")
    mode = input("模式选择 (1/2): ").strip()
    use_line = mode == '1'
    
    if not use_line:
        print("请输入起点切线斜率 k1（可输入 inf 表示垂直）:")
        k1_str = input("k1 = ")
        k1 = float(k1_str) if k1_str != "inf" else float('inf')
        print("请输入终点切线斜率 k2（可输入 inf 表示垂直）:")
        k2_str = input("k2 = ")
        k2 = float(k2_str) if k2_str != "inf" else float('inf')
        print("请输入轨道曲率参数curvature：（建议3，直接回车默认为3）")
        user_input = input("curvature = ")
        curvature = float(user_input) if user_input else 3.0
    else:
        k1 = k2 = 0  # 直线模式下不使用这些参数
        curvature = 3.0  # 直线模式下不使用这个参数

    print("请输入铁路线路宽度（像素）:")
    track_width = int(input("track_width = "))
    print("请输入铁路地面高度：")
    ground_height = float(input("ground_height = "))

    print("是否要添加一个必须经过的点？(y/n)")
    use_mid = input().strip().lower()
    if use_mid == 'y':
        print("请输入必须经过的点坐标 (xm, ym)：")
        xm = float(input("xm = "))
        ym = float(input("ym = "))

        if not use_line:
            print("必过点切线斜率k_mid:（直接回车默认为k1和k2的平均值，输入 'inf' 表示垂直切线）")
            user_input = input("k_mid = ")
            if not user_input:
                k_mid = (k1 + k2) / 2
            elif user_input.strip().lower() == "inf":
                k_mid = float('inf')
            else:
                try:
                    k_mid = float(user_input)
                except ValueError:
                    print("输入无效，将使用默认值（k1和k2的平均值）")
                    k_mid = (k1 + k2) / 2
        else:
            k_mid = None

        plot_full_track((x0, y0), (x1, y1), k1, k2, track_width, curvature, 
                       via=(xm, ym), k_via=k_mid, ground_height=ground_height, use_line=use_line)
    else:
        plot_full_track((x0, y0), (x1, y1), k1, k2, track_width, curvature, 
                       ground_height=ground_height, use_line=use_line)
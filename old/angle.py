import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import zhplot

def unit_vector(k):
    if k == float('inf') or abs(k) > 1e6:
        return (0.0, 1.0)
    norm = math.sqrt(1 + k**2)
    return (1.0 / norm, k / norm)

def generate_smooth_track(x0, y0, x1, y1, k1, k2, d1=None, d2=None, samples_per_unit=1.5):
    P0 = (x0, y0)
    P3 = (x1, y1)

    d = math.hypot(x1 - x0, y1 - y0)
    if d1 is None:
        d1 = d / 3.0
    if d2 is None:
        d2 = d / 3.0

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

    return remove_duplicates(pixel_coords), curve_points, (P0, P1, P2, P3)

def remove_duplicates(pts):
    seen = set()
    out = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out

def plot_track(x0, y0, x1, y1, k1, k2, d1=None, d2=None):
    pixel_track, curve, control_points = generate_smooth_track(x0, y0, x1, y1, k1, k2, d1, d2)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.set_title("Smooth Railway in World Coordinates")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    margin = 10
    all_x, all_y = zip(*pixel_track)
    xmin, xmax = min(all_x) - margin, max(all_x) + margin
    ymin, ymax = min(all_y) - margin, max(all_y) + margin
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_xticks(range(int(xmin), int(xmax) + 1))
    ax.set_yticks(range(int(ymin), int(ymax) + 1))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    for (ix, iy) in pixel_track:
        rect = patches.Rectangle(
            (ix - 0.5, iy - 0.5), 1, 1,
            edgecolor='blue',
            facecolor='lightblue'
        )
        ax.add_patch(rect)

    cx, cy = zip(*curve)
    ax.plot(cx, cy, '-', color='black', linewidth=1, alpha=0.5, label='Bezier Curve')

    P0, P1, P2, P3 = control_points
    ax.plot(*zip(P0, P1, P2, P3), 'o--', color='gray', label='Control Polygon')

    ax.arrow(P0[0], P0[1], P1[0]-P0[0], P1[1]-P0[1], head_width=3, color='red')
    ax.arrow(P3[0], P3[1], P3[0]-P2[0], P3[1]-P2[1], head_width=3, color='green')
    ax.text(P0[0], P0[1]-5, 'Start', ha='center')
    ax.text(P3[0], P3[1]+5, 'End', ha='center')

    ax.legend()
    plt.show()

if __name__ == "__main__":
    print("请输入起点坐标 a(x0, y0)：")
    x0 = float(input("x0 = "))
    y0 = float(input("y0 = "))

    print("请输入终点坐标 b(x1, y1)：")
    x1 = float(input("x1 = "))
    y1 = float(input("y1 = "))

    print("请输入起点切线斜率 k1（可输入 inf 表示垂直）:")
    k1_str = input("k1 = ")
    k1 = float(k1_str) if k1_str != "inf" else float('inf')

    print("请输入终点切线斜率 k2（可输入 inf 表示垂直）:")
    k2_str = input("k2 = ")
    k2 = float(k2_str) if k2_str != "inf" else float('inf')

    d1_input = input("可选：起点控制长度 d1（默认自动估计）：")
    d2_input = input("可选：终点控制长度 d2（默认自动估计）：")
    d1 = float(d1_input) if d1_input.strip() else None
    d2 = float(d2_input) if d2_input.strip() else None

    plot_track(x0, y0, x1, y1, k1, k2, d1, d2)

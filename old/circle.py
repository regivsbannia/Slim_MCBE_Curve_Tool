def generate_circle_segments(r):
    if r == 0:
        return ''
    x = r
    y = 0
    d = 1 - r
    segments = []
    current_segment = 0
    while x >= y:
        current_segment += 1
        if d < 0:
            # 选择E方向，仅y增加
            d += 2 * y + 3
        else:
            # 选择SE方向，x减少，y增加
            d += 2 * (y - x) + 5
            segments.append(current_segment)
            current_segment = 0
            x -= 1
        y += 1
    if current_segment > 0:
        segments.append(current_segment)
    # 镜像线段以形成完整的1/4圆
    mirrored = segments[::-1]
    full_segments = segments + mirrored
    return ''.join(map(str, full_segments))

# 示例输入
radius = input("请输入半径: ")
print(generate_circle_segments(int(radius)))
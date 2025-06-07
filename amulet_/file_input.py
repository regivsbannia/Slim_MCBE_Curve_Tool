import amulet
from amulet.api.block import Block
from amulet.utils.world_utils import block_coords_to_chunk_coords

# === 1. 加载世界 ===
world_path = r"E:\Locak_Repositories\RoyalBunny\minec\transfer_folder\NuyqpysO9kw=\NuyqpysO9kw="  # 请替换为你的世界路径
level = amulet.load_level(world_path)

dimension = "minecraft:overworld"  # 通常为主世界

# === 2. 读取坐标文件 ===
coords = []
with open("rail_output.txt", "r") as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) == 3:
            x, y, z = map(int, parts)
            coords.append((x, y, z))

# === 3. 获取通用方块对象 ===
# 创建一个代表 'minecraft:rail' 的方块对象
rail_block = Block("minecraft", "stone")

# 将方块转换为通用格式
universal_block, block_entity, _ = level.translation_manager.get_version("bedrock", (1, 21, 81)).block.to_universal(rail_block)

# 注册方块到调色板以获取运行时 ID
block_id = level.block_palette.get_add_block(universal_block)

# === 4. 设置方块 ===
for x, y, z in coords:
    # 计算区块坐标
    cx, cz = block_coords_to_chunk_coords(x, z)
    # 获取对应区块
    chunk = level.get_chunk(cx, cz, dimension)
    # 计算区块内的相对坐标
    offset_x, offset_z = x - 16 * cx, z - 16 * cz
    # 设置方块
    chunk.blocks[offset_x, y, offset_z] = block_id
    # 如果有方块实体，设置它
    if block_entity is not None:
        chunk.block_entities[(x, y, z)] = block_entity
    elif (x, y, z) in chunk.block_entities:
        del chunk.block_entities[(x, y, z)]
    # 标记区块已更改
    chunk.changed = True

# === 5. 保存并关闭世界 ===
level.save()
level.close()

print(f"✅ 已成功放置 {len(coords)} 个方块。")


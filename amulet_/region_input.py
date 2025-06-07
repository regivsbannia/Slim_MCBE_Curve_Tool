import amulet
from amulet.api.block import Block
from amulet.utils.world_utils import block_coords_to_chunk_coords
from amulet_nbt import StringTag


def fill_region(world_path: str,
                coord1: tuple[int, int, int],
                coord2: tuple[int, int, int],
                block_name: str,
                block_half: str | None = None,
                dimension: str = "minecraft:overworld",
                version: tuple[int, int, int] = (1, 21, 81)):

    x1, y1, z1 = coord1
    x2, y2, z2 = coord2

    # === 构造方块对象 ===
    if block_half in ("top", "bottom"):
        properties = {"minecraft:vertical_half": StringTag(block_half)}
    else:
        properties = {}

    block = Block("minecraft", block_name, properties)

    # === 加载世界 ===
    level = amulet.load_level(world_path)

    # === 通用方块转换 ===
    version_obj = level.translation_manager.get_version("bedrock", version)
    universal_block, block_entity, _ = version_obj.block.to_universal(block)
    block_id = level.block_palette.get_add_block(universal_block)

    # === 范围排序 ===
    xmin, xmax = sorted([x1, x2])
    ymin, ymax = sorted([y1, y2])
    zmin, zmax = sorted([z1, z2])

    # === 填充区域 ===
    count = 0
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            for z in range(zmin, zmax + 1):
                cx, cz = block_coords_to_chunk_coords(x, z)
                chunk = level.get_chunk(cx, cz, dimension)
                offset_x, offset_z = x - 16 * cx, z - 16 * cz
                chunk.blocks[offset_x, y, offset_z] = block_id
                if block_entity is not None:
                    chunk.block_entities[(x, y, z)] = block_entity
                elif (x, y, z) in chunk.block_entities:
                    del chunk.block_entities[(x, y, z)]
                chunk.changed = True
                count += 1

    level.save()
    level.close()
    print(f"✅ 成功填充 {count} 个 '{block_name}' 方块（属性：{properties}）")


if __name__ == "__main__":
    print("=== Minecraft 区域方块填充器 ===")

    # 世界路径
    world_path = input("请输入你的世界文件夹路径（如 E:/path/to/world）：").strip()

    # 输入坐标
    x1, y1, z1 = map(int, input("请输入第一个对角点坐标 x y z：").strip().split())
    x2, y2, z2 = map(int, input("请输入第二个对角点坐标 x y z：").strip().split())

    # 输入方块名
    block_name = input("请输入方块名称（如 stone 或 normal_stone_slab）：").strip()

    # 输入 slab 属性（可选）
    block_half_raw = input("如果是半砖，请输入 top 或 bottom，否则直接回车：").strip().lower()
    block_half = block_half_raw if block_half_raw in ("top", "bottom") else None

    fill_region(world_path, (x1, y1, z1), (x2, y2, z2), block_name, block_half)

import amulet
from amulet.api.block import Block
from amulet.utils.world_utils import block_coords_to_chunk_coords
from amulet_nbt import StringTag

def fill_region(
    world_path: str,
    coord1: tuple[int, int, int],
    coord2: tuple[int, int, int],
    block_name: str,
    block_half: str | None = None,
    dimension: str = "minecraft:overworld",
    version: tuple[int, int, int] = (1, 21, 81),
) -> str:
    """
    根据两个对角点 coord1、coord2，填充此长方体区域内的方块为指定类型。
    block_name: 方块 ID，比如 "stone"、"normal_stone_slab" 等。
    block_half: 如果是半砖，传 "top" 或 "bottom"；否则传 None。
    返回：操作结果的提示字符串。
    """

    x1, y1, z1 = coord1
    x2, y2, z2 = coord2

    # === 构造方块对象 ===
    if block_half in ("top", "bottom"):
        props = {"minecraft:vertical_half": StringTag(block_half)}
    else:
        props = {}

    block = Block(namespace="minecraft", base_name=block_name, properties=props)

    # === 打开世界 ===
    level = amulet.load_level(world_path)

    # === 转换成通用方块，并在调色板中注册 ===
    version_obj = level.translation_manager.get_version("bedrock", version)
    universal_block, block_entity, _ = version_obj.block.to_universal(block)
    block_id = level.block_palette.get_add_block(universal_block)

    # === 坐标范围排序 ===
    xmin, xmax = sorted([x1, x2])
    ymin, ymax = sorted([y1, y2])
    zmin, zmax = sorted([z1, z2])

    # === 遍历填充区域 ===
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
                else:
                    if (x, y, z) in chunk.block_entities:
                        del chunk.block_entities[(x, y, z)]

                chunk.changed = True
                count += 1

    level.save()
    level.close()

    return f"✅ 成功填充 {count} 个“{block_name}”（属性：{props}）。"

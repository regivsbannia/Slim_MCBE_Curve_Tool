import amulet
from amulet.api.block import Block
from amulet.utils.world_utils import block_coords_to_chunk_coords
from amulet_nbt import StringTag

def fill_from_file(
    world_path: str,
    coords_file: str,
    block_name: str,
    block_half: str | None = None,
    dimension: str = "minecraft:overworld",
    version: tuple[int, int, int] = (1, 21, 81),
) -> str:
    """
    从 coords_file 中读取所有 x y z 坐标，批量将这些位置设置为指定方块。
    block_name: 方块 ID，比如 "stone"、"normal_stone_slab" 等。
    block_half: 如果是半砖，传 "top" 或 "bottom"；否则传 None。
    返回：操作结果的提示字符串。
    """
    # === 构造方块对象 ===
    if block_half in ("top", "bottom"):
        # 半砖需要 vertical_half 属性
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

    # === 从文件里读取所有坐标 ===
    coords: list[tuple[int, int, int]] = []
    try:
        with open(coords_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3:
                    x, y, z = map(int, parts)
                    coords.append((x, y, z))
    except Exception as e:
        level.close()
        return f"❌ 无法读取坐标文件：{e}"

    if not coords:
        level.close()
        return "⚠️ 坐标文件中没有有效的 x y z 数值。"

    # === 遍历坐标，逐块写入 ===
    count = 0
    for x, y, z in coords:
        cx, cz = block_coords_to_chunk_coords(x, z)
        chunk = level.get_chunk(cx, cz, dimension)
        offset_x, offset_z = x - 16 * cx, z - 16 * cz

        chunk.blocks[offset_x, y, offset_z] = block_id

        if block_entity is not None:
            # 如果方块有方块实体（slab 可能没有）
            chunk.block_entities[(x, y, z)] = block_entity
        else:
            # 否则如果当前位置有旧方块实体，也要清除
            if (x, y, z) in chunk.block_entities:
                del chunk.block_entities[(x, y, z)]

        chunk.changed = True
        count += 1

    # === 保存并关闭世界 ===
    level.save()
    level.close()

    return f"✅ 成功从文件放置 {count} 个方块（{block_name}，属性 {props}）。"

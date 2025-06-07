import gradio as gr
from file_fill import fill_from_file
from region_input import fill_region


def run_file_fill(world_path, coords_file, block_name, slab_choice):
    """
    Gradio 调用：从文件填充
    slab_choice: 三个选项 "none"/"top"/"bottom"
    """
    # 如果用户选择 none，就把 slab_choice 设为 None
    block_half = slab_choice if slab_choice in ("top", "bottom") else None

    try:
        result = fill_from_file(world_path, coords_file.name, block_name, block_half)
    except Exception as e:
        result = f"❌ 运行时发生错误：{e}"
    return result


def run_region_fill(
    world_path,
    x1, y1, z1,
    x2, y2, z2,
    block_name,
    slab_choice
):
    """
    Gradio 调用：按区域填充
    slab_choice: 三个选项 "none"/"top"/"bottom"
    """
    block_half = slab_choice if slab_choice in ("top", "bottom") else None
    coord1 = (int(x1), int(y1), int(z1))
    coord2 = (int(x2), int(y2), int(z2))

    try:
        result = fill_region(world_path, coord1, coord2, block_name, block_half)
    except Exception as e:
        result = f"❌ 运行时发生错误：{e}"
    return result


# === Gradio UI ===
with gr.Blocks() as demo:
    gr.Markdown("## Minecraft 批量放置方块工具")

    tabs = gr.Tabs()

    # —— Tab1：从文件坐标批量放置 —— 
    with tabs:
        with gr.TabItem("从文件坐标填充"):
            gr.Markdown("**说明：** 上传一个文本文件，里面每行是 `x y z`，程序会将所有这些点设置成指定方块。")
            file_world = gr.Textbox(label="世界文件夹路径", placeholder="例如：E:/my_mc_world")
            coords_file = gr.File(label="坐标文件 (*.txt)，每行格式：x y z")
            file_block = gr.Textbox(label="方块名称", placeholder="例如：stone 或 normal_stone_slab")
            file_slab = gr.Radio(
                choices=["none", "top", "bottom"],
                label="如果是半砖，选择‘top’或‘bottom’，否则选‘none’",
                value="none"
            )
            file_btn = gr.Button("开始从文件放置")
            file_output = gr.Textbox(label="运行结果")

            file_btn.click(
                run_file_fill,
                inputs=[file_world, coords_file, file_block, file_slab],
                outputs=[file_output]
            )

        # —— Tab2：按区域填充 —— 
        with gr.TabItem("按区域填充"):
            gr.Markdown("**说明：** 输入两个对角点坐标，程序会填充此区域。")
            region_world = gr.Textbox(label="世界文件夹路径", placeholder="例如：E:/my_mc_world")
            x1_in = gr.Number(label="第一个对角点 X1", value=0)
            y1_in = gr.Number(label="第一个对角点 Y1", value=0)
            z1_in = gr.Number(label="第一个对角点 Z1", value=0)

            x2_in = gr.Number(label="第二个对角点 X2", value=0)
            y2_in = gr.Number(label="第二个对角点 Y2", value=0)
            z2_in = gr.Number(label="第二个对角点 Z2", value=0)

            region_block = gr.Textbox(label="方块名称", placeholder="例如：stone 或 normal_stone_slab")
            region_slab = gr.Radio(
                choices=["none", "top", "bottom"],
                label="如果是半砖，选择‘top’或‘bottom’，否则选‘none’",
                value="none"
            )
            region_btn = gr.Button("开始区域填充")
            region_output = gr.Textbox(label="运行结果")

            region_btn.click(
                run_region_fill,
                inputs=[region_world, x1_in, y1_in, z1_in, x2_in, y2_in, z2_in, region_block, region_slab],
                outputs=[region_output]
            )

    # 整体页面 footer
    gr.Markdown("---")
    gr.Markdown("**提示：** 请确保你填写的 `世界文件夹路径` 是一个已经存在并可用的 MCBE / Java 世界文件夹。")

if __name__ == "__main__":
    demo.launch()

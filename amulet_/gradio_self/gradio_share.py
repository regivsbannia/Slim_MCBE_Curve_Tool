import gradio as gr
import zipfile
import tempfile
import os
import shutil
from pathlib import Path
from file_fill import fill_from_file
from region_input import fill_region

def unzip_world(zip_file):
    tmp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file.name, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)

    # 检查是否直接包含 level.dat 或解压后还有一层目录
    if not (Path(tmp_dir) / "level.dat").exists():
        subdirs = [f for f in Path(tmp_dir).iterdir() if f.is_dir()]
        if subdirs:
            return str(subdirs[0])  # 返回第一层目录
    return tmp_dir

def zip_world_folder(world_folder):
    zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(zip_path.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(world_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, world_folder)
                zipf.write(file_path, arcname)
    return zip_path.name

def run_file_fill_ui(world_zip, coords_file, block_name, slab_option):
    try:
        world_path = unzip_world(world_zip)
        slab = slab_option if slab_option in ("top", "bottom") else None
        result = fill_from_file(world_path, coords_file.name, block_name, slab)
        zip_result = zip_world_folder(world_path)
        return result, zip_result
    except Exception as e:
        return f"❌ 出错：{e}", None

def run_region_fill_ui(world_zip, x1, y1, z1, x2, y2, z2, block_name, slab_option):
    try:
        world_path = unzip_world(world_zip)
        coord1 = (int(x1), int(y1), int(z1))
        coord2 = (int(x2), int(y2), int(z2))
        slab = slab_option if slab_option in ("top", "bottom") else None
        result = fill_region(world_path, coord1, coord2, block_name, slab)
        zip_result = zip_world_folder(world_path)
        return result, zip_result
    except Exception as e:
        return f"❌ 出错：{e}", None

with gr.Blocks() as demo:
    gr.Markdown("## Minecraft 云端方块填充工具 - gradio_share")

    with gr.Tabs():
        with gr.TabItem("从坐标文件填充"):
            world_zip1 = gr.File(label="上传 Minecraft 世界压缩包 (.zip)")
            coords_file = gr.File(label="上传坐标文件 (txt，每行格式为 x y z)")
            block_name1 = gr.Textbox(label="方块名称，例如 stone 或 normal_stone_slab")
            slab_option1 = gr.Radio(["none", "top", "bottom"], label="如果是半砖，请选择 top 或 bottom，否则选 none", value="none")
            btn1 = gr.Button("开始填充")
            output1 = gr.Textbox(label="执行结果")
            download1 = gr.File(label="下载修改后的世界 (.zip)", interactive=False)

            btn1.click(fn=run_file_fill_ui,
                      inputs=[world_zip1, coords_file, block_name1, slab_option1],
                      outputs=[output1, download1])

        with gr.TabItem("按区域坐标填充"):
            world_zip2 = gr.File(label="上传 Minecraft 世界压缩包 (.zip)")
            x1 = gr.Number(label="X1")
            y1 = gr.Number(label="Y1")
            z1 = gr.Number(label="Z1")
            x2 = gr.Number(label="X2")
            y2 = gr.Number(label="Y2")
            z2 = gr.Number(label="Z2")
            block_name2 = gr.Textbox(label="方块名称，例如 stone 或 normal_stone_slab")
            slab_option2 = gr.Radio(["none", "top", "bottom"], label="如果是半砖，请选择 top 或 bottom，否则选 none", value="none")
            btn2 = gr.Button("开始填充")
            output2 = gr.Textbox(label="执行结果")
            download2 = gr.File(label="下载修改后的世界 (.zip)", interactive=False)

            btn2.click(fn=run_region_fill_ui,
                      inputs=[world_zip2, x1, y1, z1, x2, y2, z2, block_name2, slab_option2],
                      outputs=[output2, download2])

if __name__ == "__main__":
    demo.launch()

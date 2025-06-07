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

    if not (Path(tmp_dir) / "level.dat").exists():
        subdirs = [f for f in Path(tmp_dir).iterdir() if f.is_dir()]
        if subdirs:
            return str(subdirs[0])
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

def start_session(world_zip):
    try:
        world_path = unzip_world(world_zip)
        return world_path, "✅ 世界上传并解压成功。"
    except Exception as e:
        return None, f"❌ 上传失败：{e}"

def run_file_fill_ui(session_path, coords_file, block_name, slab_option):
    if not session_path:
        return "⚠️ 请先上传世界文件。"
    slab = slab_option if slab_option in ("top", "bottom") else None
    try:
        result = fill_from_file(session_path, coords_file.name, block_name, slab)
        return result
    except Exception as e:
        return f"❌ 操作失败：{e}"

def run_region_fill_ui(session_path, x1, y1, z1, x2, y2, z2, block_name, slab_option):
    if not session_path:
        return "⚠️ 请先上传世界文件。"
    slab = slab_option if slab_option in ("top", "bottom") else None
    try:
        coord1 = (int(x1), int(y1), int(z1))
        coord2 = (int(x2), int(y2), int(z2))
        result = fill_region(session_path, coord1, coord2, block_name, slab)
        return result
    except Exception as e:
        return f"❌ 操作失败：{e}"

def export_final_world(session_path):
    if not session_path:
        return None
    return zip_world_folder(session_path)

with gr.Blocks() as demo:
    gr.Markdown("## Minecraft 多步骤方块填充工具 - gradio_share")

    session_world = gr.State(value=None)

    with gr.Row():
        world_zip = gr.File(label="上传 Minecraft 世界压缩包 (.zip)")
        upload_btn = gr.Button("开始上传并解压")
        upload_output = gr.Textbox(label="上传状态")

    upload_btn.click(fn=start_session, inputs=[world_zip], outputs=[session_world, upload_output])

    with gr.Tabs():
        with gr.TabItem("从坐标文件填充"):
            coords_file = gr.File(label="上传坐标文件 (txt，每行格式为 x y z)")
            block_name1 = gr.Textbox(label="方块名称，例如 stone 或 normal_stone_slab")
            slab_option1 = gr.Radio(["none", "top", "bottom"], label="如果是半砖，请选择 top 或 bottom，否则选 none", value="none")
            btn1 = gr.Button("执行坐标填充")
            output1 = gr.Textbox(label="执行结果")

            btn1.click(fn=run_file_fill_ui, inputs=[session_world, coords_file, block_name1, slab_option1], outputs=[output1])

        with gr.TabItem("按区域坐标填充"):
            x1 = gr.Number(label="X1")
            y1 = gr.Number(label="Y1")
            z1 = gr.Number(label="Z1")
            x2 = gr.Number(label="X2")
            y2 = gr.Number(label="Y2")
            z2 = gr.Number(label="Z2")
            block_name2 = gr.Textbox(label="方块名称，例如 stone 或 normal_stone_slab")
            slab_option2 = gr.Radio(["none", "top", "bottom"], label="如果是半砖，请选择 top 或 bottom，否则选 none", value="none")
            btn2 = gr.Button("执行区域填充")
            output2 = gr.Textbox(label="执行结果")

            btn2.click(fn=run_region_fill_ui,
                      inputs=[session_world, x1, y1, z1, x2, y2, z2, block_name2, slab_option2],
                      outputs=[output2])

    with gr.Row():
        export_btn = gr.Button("📦 导出最终世界文件")
        download_link = gr.File(label="点击下载修改后的世界 (.zip)", interactive=False)

    export_btn.click(fn=export_final_world, inputs=[session_world], outputs=[download_link])

if __name__ == "__main__":
    demo.launch()

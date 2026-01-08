import zipfile
import os

def create_test_zip(filename, size_kb):
    """
    创建指定大小的测试ZIP文件
    filename: 输出文件名
    size_kb: 文件大小（KB）
    """
    temp_file = "temp_data.bin"
    zip_filename = filename
    
    # 生成随机数据文件
    with open(temp_file, 'wb') as f:
        f.write(os.urandom(size_kb * 1024))
    
    # 创建ZIP文件
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(temp_file, 'test_data.bin')
    
    # 清理临时文件
    os.remove(temp_file)
    
    actual_size = os.path.getsize(zip_filename) / 1024
    print(f"已创建: {zip_filename} ({actual_size:.2f} KB)")

# 生成不同大小的文件
sizes = [100, 500, 1000, 5000, 10000, 50000, 100000]  # KB

for size in sizes:
    create_test_zip(f"test_{size//1000}k.zip" if size < 1000 else f"test_{size//1000}m.zip", size)
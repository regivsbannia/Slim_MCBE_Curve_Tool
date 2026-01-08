# Slim MCBE Curve Tool  |  轻量级MCBE曲线工具

*Thanks to [Amulet](https://www.amuletmc.com/)*

### Try | 试用
可以直接访问[(https://curve.yy-li.com)](https://curve.yy-li.com)试用，采用个人云服务器和HuggingFace，计算较慢
Go (https://curve.yy-li.com) to try, it works slowly cause it based on my own VPS or Huggingface

### 部署
**建议具备python运行条件的在自己主机部署，直接输入文件路径更加方便**
**It is recommended to deploy on your own host if you have the python conditions to run it, and it is more convenient to enter the file path directly.**

- 下载project_self内部文件  |  Download files in project_self folder
- 安装requirements.txt中的包  |  Intasll the python packages in requireents.txt
- 运行combined_demo.py  |  Run combined_demo.py
- 浏览器访问https://127.0.0.1:7860

*如果出现空间不足，可以修改临时文件存储位置*
```
$env:TEMP = "D:\gradio_tmp"  
$env:TMP  = "D:\gradio_tmp" 
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
```
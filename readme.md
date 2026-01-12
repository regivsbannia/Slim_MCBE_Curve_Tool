# Slim MCBE Curve Tool  |  轻量级MCBE曲线工具

*Thanks to [Amulet](https://www.amuletmc.com/)*

---

### Try | 试用
可以直接访问[(https://curve.yy-li.com)](https://curve.yy-li.com)试用，采用个人云服务器，计算较慢,==**只能计算曲线，不能自动放置**==
You can directly visit [(https://curve.yy-li.com)](https://curve.yy-li.com) to try it out. It uses a personal cloud server, so the computation is relatively slow. ==**It can only calculate curves and cannot automatically place them**==

---

### Use | 使用
下载release中的exe文件，运行后会自动打开浏览器，在浏览器页面使用即可
Download the exe file from the release, and after running it, the browser will open automatically. You can use it on the browser page.

---

### Deployment | 部署
==**强烈建议具备python运行条件的在自己主机部署，直接输入文件路径更加方便**==
==**It is strongly recommended to deploy on your own host if you have the python conditions to run it, and it is more convenient to enter the file path directly.**==

- 下载release中zip文件  |  Download zip file in release folder
- 安装requirements.txt中的包  |  Intasll the python packages in requireents.txt
- 运行combined_demo.py  |  Run combined_demo.py
- 浏览器访问https://127.0.0.1:7860

*如果出现空间不足，可以修改临时文件存储位置*
```
$env:TEMP = "D:\gradio_tmp"  
$env:TMP  = "D:\gradio_tmp" 
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
```
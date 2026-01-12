# Slim_MCBE_Curve_Tool 打包指南

## 1️⃣ 准备工作

1. 使用虚拟环境（conda 或 venv），确保依赖完整：

```bash
pip install -r requirements.txt
```

2. 卸载可能冲突的旧包（例如 `pathlib` 的过时版本）：

```bash
pip uninstall pathlib
```

---

## 2️⃣ 打包方案

**使用 `onefile` 打包 + `--collect-all`**（最稳定）：

```bash
pyinstaller --onefile --name Slim_MCBE_Curve_Tool --clean --hidden-import matplotlib.backends.backend_agg --hidden-import plotly --hidden-import zhplot --collect-all amulet_core --collect-all safehttpx --collect-all groovy --collect-all gradio entry.py
```

> 说明：
>
> * `--collect-all <package>`：确保依赖库的所有非 Python 文件（模板、txt、yaml）被打包。
> * `--hidden-import`：补充动态导入的模块。

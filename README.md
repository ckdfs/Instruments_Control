# 仪器控制系统

一个基于 PyQt5 和 QFluentWidgets 的现代化仪器控制系统，支持多种实验室仪器的远程控制与数据采集。

> 📚 **[文档导航](DOCS_INDEX.md)** | 🐛 **[故障排除](TROUBLESHOOTING.md)** | 🔧 **[项目结构](PROJECT_STRUCTURE.md)** | ⚙️ **[环境配置](CONDA_SETUP_SUCCESS.md)**

## 功能特性

- 🎨 **现代化界面**: 基于 QFluentWidgets 的 Fluent Design 风格界面
- 📊 **实时数据可视化**: 使用 PyQtGraph 实现高性能实时绘图
- 🔧 **多仪器支持**:
  - 光谱分析仪 (OSA AP2061A)
  - 频谱分析仪 (SA FSV30)
  - 任意函数发生器 (AFG1062)
  - 可编程电源 (E3631A)
- 🌐 **网络通信**: 支持 TCP/IP 远程控制
- 💾 **配置管理**: JSON 配置文件存储仪器参数

## 工程结构

```
Instruments_Control/
├── app/                          # 应用主目录
│   ├── main.py                   # 应用入口
│   ├── ui/                       # UI 相关
│   │   ├── main_window.py        # 主窗口
│   │   ├── pages/                # 各个功能页面
│   │   │   ├── home.py           # 主页
│   │   │   ├── osa_page.py       # OSA 控制页面
│   │   │   ├── sa_page.py        # SA 控制页面
│   │   │   ├── afg_page.py       # AFG 控制页面
│   │   │   └── power_page.py     # 电源控制页面
│   │   └── widgets/              # 自定义组件
│   │       └── plot_widget.py    # 绘图组件
│   └── instruments/              # 仪器控制核心
│       ├── osa_ap2061a.py        # OSA 控制类
│       ├── sa_fsv30.py           # SA 控制类
│       ├── afg_afg1062.py        # AFG 控制类
│       └── power_e3631a.py       # 电源控制类
├── PyApex/                       # PyApex 库
├── config/                       # 配置文件
│   └── settings.json
├── resources/                    # 资源文件
├── requirements.txt              # 依赖清单
└── README.md
```

## 快速开始

### 环境要求

- **Python**: 3.8.8 或更高版本
- **操作系统**: Windows 10/11
- **Conda**: Miniconda 或 Anaconda（推荐）

### 安装步骤

#### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd Instruments_Control
```

#### 2. 创建 Conda 环境（首次安装）

**方式一：使用脚本（推荐）** ✅

双击运行 `conda_install_deps.bat`，脚本会自动：
- 创建名为 `pyqt5.12.2` 的虚拟环境（Python 3.8.8）
- 安装所有依赖包
- 配置 pywin32 DLL 注册

**方式二：手动安装**

```bash
# 创建环境
conda create -n pyqt5.12.2 python=3.8.8 -y

# 激活环境
conda activate pyqt5.12.2

# 安装依赖（使用清华镜像）
pip install PyQt5==5.15.11 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install PyQt-Fluent-Widgets -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyqtgraph numpy RsInstrument pyvisa -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装并注册 pywin32（重要！）
pip install pywin32==305 -i https://pypi.tuna.tsinghua.edu.cn/simple
python %CONDA_PREFIX%\Scripts\pywin32_postinstall.py -install
```

#### 3. 配置仪器参数（可选）

编辑 `config/settings.json` 文件，设置您的仪器 IP 地址和默认参数。

### 运行应用

**方式一：使用脚本（推荐）** ✅

双击运行 `run_conda.bat`

**方式二：手动运行**

```bash
# 1. 激活环境
conda activate pyqt5.12.2

# 2. 进入项目目录
cd D:\code\Instruments_Control

# 3. 运行应用
python -m app.main
```

**⚠️ 重要提示**：
- ✅ 正确：`python -m app.main`
- ❌ 错误：`python app/main.py` 或 `python app\main.py`

## 使用说明

### 光谱分析仪 (OSA)

1. 在左侧导航栏点击「光谱分析仪」
2. 输入仪器 IP 地址和端口
3. 点击「连接」建立通信
4. 配置中心波长、扫描跨度等参数
5. 点击「开始采集」开始实时数据采集
6. 实时光谱图将显示在界面上

### 频谱分析仪 (SA)

1. 在左侧导航栏点击「频谱分析仪」
2. 输入仪器 IP 地址
3. 点击「连接」建立通信
4. 配置中心频率、跨度、RBW、VBW 等参数
5. 点击「开始测量」开始周期性测量
6. 频谱图和标记值将实时更新

### 其他仪器

函数发生器和可编程电源的控制功能正在开发中,界面框架已搭建完成。

## 依赖项

### 核心框架
- **PyQt5 5.15.11**: GUI 框架
- **PyQt-Fluent-Widgets**: Fluent Design 组件库（包名：PyQt-Fluent-Widgets，导入：qfluentwidgets）
- **pyqtgraph 0.13.7**: 高性能实时绘图
- **NumPy**: 数值计算

### 仪器驱动
- **RsInstrument 1.120.1**: 罗德与施瓦茨仪器驱动
- **pyvisa**: VISA 仪器通信
- **PyApex**: Apex 光学仪器驱动（本地库）

### 系统依赖
- **pywin32 305**: Windows API 支持（需要 DLL 注册）

### 镜像源配置（推荐）

为加速包下载，建议使用清华镜像源：

```bash
# 临时使用
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久设置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 故障排除

### 常见问题快速修复

#### 1. Qt 平台插件错误
```
qt.qpa.plugin: Could not load the Qt platform plugin "windows"
```

**解决方案**：
- 重新运行 `conda_install_deps.bat`
- 或手动重装 PyQt5：
```bash
conda activate pyqt5.12.2
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip -y
pip install PyQt5==5.15.11 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 2. pywin32 DLL 加载失败
```
ImportError: DLL load failed while importing win32api
```

**解决方案**：
```bash
conda activate pyqt5.12.2
pip install pywin32==305 -i https://pypi.tuna.tsinghua.edu.cn/simple
python %CONDA_PREFIX%\Scripts\pywin32_postinstall.py -install
```

#### 3. 模块导入错误
```
ModuleNotFoundError: No module named 'app'
```

**解决方案**：
- ✅ 使用正确命令：`python -m app.main`
- ❌ 不要使用：`python app/main.py`

#### 4. QFluentWidgets 未找到
```
ModuleNotFoundError: No module named 'qfluentwidgets'
```

**解决方案**：
```bash
pip install PyQt-Fluent-Widgets -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**注意**：包名是 `PyQt-Fluent-Widgets`（带连字符），导入时用 `import qfluentwidgets`（无连字符）

### 完全重置

如果问题持续，尝试完全重置环境：

```bash
# 1. 删除旧环境
conda env remove -n pyqt5.12.2 -y

# 2. 重新创建（运行安装脚本）
conda_install_deps.bat
```

### 诊断命令

```bash
# 激活环境
conda activate pyqt5.12.2

# 检查 Python 版本
python --version

# 检查已安装包
pip list | findstr "PyQt5 qfluentwidgets pyqtgraph pywin32"

# 测试导入
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
python -c "import qfluentwidgets; print('QFluentWidgets OK')"
python -c "import win32api; print('pywin32 OK')"
```

## 开发路线图

- [x] 工程结构重构
- [x] 基础 UI 框架搭建
- [x] OSA 控制功能实现
- [x] SA 控制功能实现
- [ ] AFG 控制功能实现
- [ ] 电源控制功能实现
- [ ] 数据记录与导出（CSV/Excel）
- [ ] 配置保存与加载
- [ ] 自动化测试脚本
- [ ] 多语言支持
- [ ] 主题切换功能

## 项目文件说明

### 核心文件
- `run_conda.bat` - 启动脚本（Conda 环境）
- `conda_install_deps.bat` - 依赖安装脚本
- `environment.yml` - Conda 环境配置
- `requirements.txt` - Python 依赖清单
- `config/settings.json` - 仪器配置文件

### 文档
- `README.md` - 项目说明（本文档）
- `TROUBLESHOOTING.md` - 故障排除指南
- `CONDA_SETUP_SUCCESS.md` - Conda 环境配置详解

### 应用目录
- `app/main.py` - 应用入口
- `app/ui/` - 用户界面
- `app/instruments/` - 仪器控制
- `PyApex/` - Apex 仪器库
- `resources/` - 资源文件

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

[待定]

## 联系方式

如有问题或建议，请通过 Issue 反馈。

## 更新日志

### v1.0.0 (2025-10-29)
- ✅ 完成项目重构，采用模块化架构
- ✅ 实现 Fluent Design 风格界面
- ✅ 完成 OSA AP2061A 控制功能
- ✅ 完成 SA FSV30 控制功能
- ✅ 配置 Conda 虚拟环境（Python 3.8.8）
- ✅ 解决 Qt 插件和 pywin32 DLL 问题
- ✅ 添加实时绘图功能
- 🚧 AFG1062 和 E3631A 控制功能开发中

---

**最后更新**: 2025-10-29  
**Python 版本**: 3.8.8  
**Conda 环境**: pyqt5.12.2  

**注意事项**: 
- 使用前请确保仪器已正确连接到网络
- 确认防火墙设置允许相应端口的通信
- 推荐使用 Conda 虚拟环境以避免依赖冲突

项目整体说明（INSTRUCTIONS）

目的
- 为开发者和维护者提供项目各模块的实现逻辑、接口契约与谱面格式说明，方便修改、扩展和打包。

包含文件
- chart/INSTRUCTIONS.md — 谱面格式与解析约定。
- player/INSTRUCTIONS.md — 播放器、运行时与 handler 的实现逻辑与接口。
- gui/INSTRUCTIONS.md — GUI 主要组件、事件流与快捷键注册说明。
- shared/INSTRUCTIONS.md — 公共工具、全局热键与会话存储说明。

快速开始
1. 创建并激活虚拟环境；安装依赖（确保包含 `pynput` 用于全局热键）：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pynput
```

2. 运行：

```bash
python main.py
```

3. 运行测试（示例）：

```bash
python -m unittest tests/test_chart_parser.py
```

说明文档位置
- 参见本文档引用的模块下的 `INSTRUCTIONS.md`，每个文件针对该模块的实现细节和扩展点。
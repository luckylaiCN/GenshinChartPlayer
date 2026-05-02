shared 模块说明 — 公共工具与全局热键

目标
- 说明 `shared` 下的工具集合与跨模块契约，特别是全局热键与会话存储的使用方式。

主要工具
- `global_hotkeys.py`
  - 提供全局热键注册/注销接口：`register_hotkey(hotkey, callback, debounce)`、`unregister_hotkey(hotkey)`。
  - 还提供按键按下/释放订阅：`register_key_down(key, cb)`、`register_key_up(key, cb)` 与对应注销接口。
  - 内部使用 `pynput` 监听键盘事件并在回调中执行注册的回调。
  - 注意：在受限平台或无权限时，回退行为存在（当前实现保留对线程/keyboard 的备用处理）。

- `utils.py` 中的 operation lock
  - `is_operation_free()` / `set_operation_state()` / `release_operation()`：用于在 GUI 层协调互斥操作（播放/练习等）。

- `rtjson.py` / 会话存储
  - `session.store` 和 `session.manager` 使用 `RTJSON` 抽象进行配置持久化。请通过 `SessionStore` 接口替换具体实现以便测试。

打包与权限
- `pynput` 依赖底层钩子，Windows 打包成可执行文件时（PyInstaller 或其他）需确认目标环境允许底层输入钩子；或保留回退到 tkinter 绑定以应对无权限环境。

调试建议
- 若出现全局热键监听异常：
  - 检查是否有其他程序抢占低级钩子（杀软、键盘驱动）。
  - 在开发时可在 `global_hotkeys` 层开启日志帮助定位（已按需移除打印）。

gui 模块说明 — 界面组件与事件流

目标
- 说明 GUI 的主要组成（MainFrame、EditorFrame、Sidebar、PlayFunctionalFrame、MenuBar、FloatingChartDisplay）和事件/快捷键流。便于前端维护与快捷键相关改动。

主要组件
- main.py -> `gui.app.run_app()` 启动入口，`MainFrame` 是主容器。
- `MainFrame`：
  - 创建菜单栏（`MenuBar`）、侧边栏与编辑器，并注册会话管理器（`JSONSessionManager`）。
  - 菜单中与播放相关的动作（Play/Stop/Practice/Toggle Floating）会委托给 `PlayFunctionalFrame`。

- `MenuBar` / `Menu`：
  - 子菜单使用 `bind_all` 在窗口内捕获快捷键用于打开菜单项（本地绑定）。
  - 标记 `is_super_command=True` 的项会尝试注册为全局热键（跨焦点），通过 `shared.global_hotkeys.register_hotkey`。失败时回退到线程监听。
  - 为避免重复触发，热键调用会走防抖 `_invoke_command()`。

- `EditorFrame`：
  - 维护当前编辑的谱面文本、调用 parser 生成 runtime，并把 `runtime` 暴露给 `PlayFunctionalFrame`。
  - 当运行时启动后，编辑区设置为不可编辑以避免变更冲突。

- `PlayFunctionalFrame`：
  - 管理 `PlaybackService` 与 `PracticeService`，并通过 `request_play()` / `request_stop()` 等 API 响应菜单或按钮事件。
  - 使用 `shared.utils` 的 operation lock API（`is_operation_free()`、`set_operation_state()`、`release_operation()`）防止并发操作冲突。

热键与快捷键注意事项
- 全局热键（F5、F12 等）默认通过 `shared/global_hotkeys` 注册；确保在打包或运行环境中允许 `pynput` 使用底层钩子（Windows 可能需要权限）。
- UI 层同时有本地 `bind_all` 与全局注册时，防抖和服务端的幂等检查共同保证不会重复触发。

扩展点
- 若需新增窗口级快捷键，仅在 `Menu` 实例中添加 `hotkey` 并决定是否标记 `is_super_command`。
- 若需自定义菜单行为，覆写 `Menu._run_command_and_close` 或 `Menu._invoke_command`。

player 模块说明 — 播放器实现与 handler 协议

目标
- 描述 `player` 目录中运行时（runtime）、调度（PlayerThreadingPool）和服务（PlaybackService、PracticeService）的协作关系，以及 handler 模块需要实现的接口。

主要组件
- ChartRuntime
  - 负责把解析后的谱面（Beat/Note 容器）转为 `playlist`（每个音符的绝对播放时间相对于 runtime 开始时间）。
  - 主要方法：`caculate_playlist()`，返回 playlist 列表。

- PlayerThreadingPool
  - 运行播放循环 `play_loop()`，负责按时间顺序调度 handler 执行真实的按键/音色操作。
  - 暴露方法：`play()`, `stop()`, `set_beat_index()`, `update_handler()` 等。

- PlaybackService
  - 服务封装，负责管理 `PlayerThreadingPool` 的生命周期，提供公共 API：
    - `start(runtime, handler_module, speed_multiplier, beat_index) -> begin_time`
    - `stop()`
    - `set_beat_index(index)`
    - `is_running()`
  - 在 start() 中实现幂等保护，避免重复启动导致双重播放。

- PracticeService / PracticeController
  - PracticeController 负责练习循环（等待按键、校验、回调等）并直接使用键盘监听回调。
  - 已迁移到 `shared/global_hotkeys` 的按键 down/up 订阅接口以统一管理输入监听。

Handler 协议（player/handlers 下模块）
- 每个 handler 模块需导出如下约定函数/接口（示例）：
  - `name() -> str`：显示名称
  - `available() -> bool`：运行时是否可用（驱动存在、权限等）
  - `init(config) -> handler_obj`（可选）：初始化并返回 handler 实例
  - `press(key)` / `release(key)` 或 `play(note)`：执行按键/音频动作

动态发现
- 使用 `player.handlers.iter_handler_modules()` 和 `get_handler_module(name)` 动态加载与选择处理器。
- 新增 handler 文件时请导出上面的函数，并将文件放在 `player/handlers/` 下。

并发与线程模型
- 播放调度在独立线程池中运行（PlayerThreadingPool），UI 通过 `PlaybackService` 发起控制命令。
- UI 层仅持有 `PlaybackService` 引用，不直接操作线程池以避免竞态。

错误与回退
- 如果 handler 报错或不可用，PlaybackService 应优先调用 fallback handler（由 `player.handlers.get_fallback_handler_module()` 提供）。

测试建议
- 为 `PlaybackService` 和 `PlayerThreadingPool` 增加单元测试，使用虚拟或空 handler 模拟按键效果，断言定时调度与停止语义正确。
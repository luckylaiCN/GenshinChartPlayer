chart 模块说明 — 谱面格式与解析约定

目标
- 说明谱面（文本形式）支持的记谱符、词汇表以及解析器（parser.py）对输入的预期格式与边界条件。

核心数据结构
- NOTATION_INDEX_TABLE：记谱符到索引（如 C3..B5）
- KEYBOARD_INDEX_TABLE：键位映射（如 Z, X, C ... U）
- ChartToken：允许的 token 集合（键位、节拍符 '/', 延续符 '_'，以及括号用于和弦/琶音/连音）

文本谱面约定（parser 期望）
- 每一行代表一个逻辑时间序列片段（例如一小节或节拍块），解析器会把文字转换为 Note / Beat 结构。
- 键位字母代表按键（大小写不敏感），例如 `z`、`x`。
- `/` 表示基础节拍分割（BEAT_TOKEN）。
- `_` 表示继续（CONTINUE_TOKEN），用于延长前一音符的时值。
- 括号 `(` `)` 用于和弦，`[` `]` 用于琶音，`{` `}` 用于连音/组块。

示例行
- 单音： `z / x / c /` （每个符号代表相等的时间槽）
- 和弦： `(z x c) /` 表示在同一节拍同时按下 z、x、c
- 延续： `z _ /` 表示 z 在两个时间槽上延续

解析器注意事项
- parser.py 会在遇到非法 token 时抛出或返回解析失败；请保证输入只包含 ALLOWED_TOKENS。
- whitespace 会被规范化；建议预处理（trim / collapse 多空格）。
- 时间计算与 playlist 构建由 `ChartRuntime.caculate_playlist()` 完成，确保在修改节拍或速度计算时同时调整该方法。

扩展指南
- 如果要新增记谱符（例如新增 octave 或符号），请同时更新 `NOTATION_INDEX_TABLE`、`ALLOWED_TOKENS` 并在 parser 中加入对应的处理逻辑。
- 新的 token 请保持与现有 token 向后兼容。

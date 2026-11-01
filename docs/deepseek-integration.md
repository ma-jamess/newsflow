# DeepSeek 接入说明

目标：在现有新闻标题分类系统接入用户指定的 DeepSeek V4.1 Flash 1017。

官方文档与用户账号 `/models` 均确认调用名为 `deepseek-flash`，固定官方地址 `https://api.deepseek.com/chat/completions`。2026-10-24 已验证密钥可用。密钥只写入被排除的 `runtime/deepseek.env`，不进入网页、历史、日志或源码包。

实施清单：

- [x] 新增标准库客户端，采用思考模式、JSON 输出；校验类别、理由与核对状态。信息不足或五类外输入不强制分类。超时与余额、密钥、限流错误明确提示，不自动重复付费请求。
- [x] 接入单条分类和历史、导出。三种本地算法的实验报告和批量处理保持独立。前端提供 DeepSeek 选项与理由，禁用不适用的校准阈值，不显示虚构概率。
- [x] 单元与接口回归测试、实际 API 分类通过；代码复核发现弃权类别持久化丢失，已用失败测试复现并修复。交付不含密钥的新源码包。
- [ ] Edge 操作验收：Computer Use 因无法可靠确认当前浏览器 URL 而停止，未完成；没有切换到其他浏览器绕过。模型选择、阈值切换和结果安全渲染已通过 Node 测试。

验证：`python -m pytest -q`，`node --test tests/*.test.cjs`，实际 API 五类示例、五类外与信息不足案例，Edge 模型选择、结果、理由、历史及本地算法切换。

使用：直接启动 `run.bat` 或 `python run.py`。密钥就绪时单条分类默认选择 DeepSeek。只有选择 DeepSeek 并提交标题时会向官方 API 发送标题并产生按量费用。批量处理使用本地模型。

更换密钥：设置环境变量 `DEEPSEEK_API_KEY`（优先），或修改 `runtime/deepseek.env` 中的 `DEEPSEEK_API_KEY=...`，然后重启服务。发行包不附带密钥。

来源：https://api-docs.deepseek.com/ 和 https://api-docs.deepseek.com/guides/json_mode 。

实测记录：47 项 Python 测试、15 项 Node 测试通过。9 组手写示例与预期一致（含五类新闻、天气、信息不足和两种交叉主题），单次约0.9至2.2秒；这些是功能示例，不是独立准确率评估。结果在 `docs/deepseek-live-verification.json`。原有本地实验报告未改动。依赖 pytz 有一条现有弃用警告，测试无失败。

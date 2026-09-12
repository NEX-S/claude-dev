# Question

怎样组织 Claude Code / Codex 的 prompt、context 与 harness，才能在完整实现需求的前提下减少冗余、过早抽象、重复校验和吞错，并可靠验证实际结果？

调研日期：2026-09-13。已读取项目原有 README、根规范模板及 dev/review 角色；下文将官方来源结论和本项目建议分开。本报告不涉及安装隔离方案，也不选购新的 agent 框架。

# Decision metric

优先级：需求完整与行为正确 > 架构和代码的必要性、可读性 > 维护与上下文成本 > 完成耗时。不能靠减少需求、删除必要错误处理、压缩行数或增加角色数量获得“质量提升”。这些是用户目标的具体化，不是厂商给出的通用排名。

# Constraints

- 保留 Claude Code / Codex 原生执行能力，避免为了编排再造运行时。
- 常驻规则只放持续适用的约束；按任务需要加载工作流与专业知识。
- 开发阶段暴露预期外错误，同时保留需求真正需要的输入拒绝、清理、重试和恢复语义。
- 不把另一项目、旧模型或单次演示的收益当作本项目的性能保证。

# Candidates surveyed

1. 大型常驻 prompt + 每次完整角色流水线：规则集中，但所有任务都支付上下文与流程成本。
2. 短常驻不变量 + 按需 skills/上下文 + 原生 agent：以最小有效配置为基线。
3. 按需规划、分工与独立验证：复杂任务才使用独立角色、明确交接与持久化状态。
4. 自建通用编排框架：将执行顺序、工具调用与状态推进统一交给额外运行时。

# Comparison

表中收益和成本判断均是根据所引来源对本项目作出的推断；“成熟度”指来源是否给出原生支持或实际案例，不表示本项目已测得收益。

| Candidate | Strength on metric | Weakness on metric | Operational cost | Maturity |
|-----------|--------------------|--------------------|------------------|----------|
| 大型常驻 prompt | 统一传递约束，但准确性仍依赖内容质量。[OpenAI 指南](https://learn.chatgpt.com/guides/best-practices) | 过度规定与模糊口号都会损害有效上下文。[Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 常驻内容反复进入上下文，维护成本随重复规则增加。[Claude 扩展机制](https://code.claude.com/docs/en/features-overview) | AGENTS.md / CLAUDE.md 是原生机制；官方建议保持准确、简短。[OpenAI 指南](https://learn.chatgpt.com/guides/best-practices) |
| 短不变量 + 按需加载 | 在保留质量约束的同时让任务拿到相关上下文。[Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 路径、description 或内容过于含糊时，agent 可能找不到所需指导。[Claude 扩展机制](https://code.claude.com/docs/en/features-overview) | 复用原生技能与检索，减少常驻正文；运行时探索仍有成本。[Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 两家均明确推荐可复用指导与按需工作流。[OpenAI 指南](https://learn.chatgpt.com/guides/best-practices)、[Claude 扩展机制](https://code.claude.com/docs/en/features-overview) |
| 按需分工 + 独立验证 | 对复杂任务提供更清晰的交接和外部反馈。[长任务 harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)、[后续 harness 实践](https://www.anthropic.com/engineering/harness-design-long-running-apps) | 评审 agent 也可能宽松；简单任务未必抵偿额外调用。[后续 harness 实践](https://www.anthropic.com/engineering/harness-design-long-running-apps) | 增加角色上下文、协调与验收成本，应按任务启用。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 有实际全栈开发案例，不能外推为普遍质量保证。[后续 harness 实践](https://www.anthropic.com/engineering/harness-design-long-running-apps) |
| 自建通用框架 | 固定工作流可以更明确地控制步骤和检查点。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 额外抽象可能遮蔽实际 prompt/响应并诱发不必要复杂度。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 多维护一套执行、状态与调试机制；本项目尚无对应需求证据。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | 存在生产框架，但官方仍建议从简单组件开始。[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) |

# Recommendation

- **Top pick：短常驻不变量 + 按需 skills + 原生 agent。** 适用于本项目的默认开发配置，符合低复杂度、低常驻成本的目标。
- **Runner-up：按需规划、分工与独立验证。** 当任务存在真实架构决策、可独立执行的工作或跨上下文状态时启用；把流程放入 skill，而非给每次小修改强加完整流水线。
- 暂不引入自建通用运行时；若以后出现原生工具无法实现的确定性调度、恢复或检查需求，再以具体失败案例评估。

## 官方证据与适用边界

1. **Prompt 应具体且适量。** Anthropic 建议使用足够指导行为的高信号信息，避免脆弱的硬编码流程和空泛目标，并根据观察到的失败补充说明、典型例子。[Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
2. **指导与执行分层。** OpenAI 把稳定仓库知识放入 AGENTS.md，把反复出现的工作沉淀为 skills；Claude 文档区分常驻指导、按需内容、独立 worker 与程序性 hooks。[OpenAI 指南](https://learn.chatgpt.com/guides/best-practices)、[Claude 扩展机制](https://code.claude.com/docs/en/features-overview)
3. **让环境给出反馈。** Claude Code 指南要求提供可运行检查和可观察证据；小而明确的修改可直接执行，不必先走完整规划。[Claude Code best practices](https://code.claude.com/docs/en/best-practices)
4. **长期进度不能只靠会话摘要。** Anthropic 的案例通过需求清单、状态记录和真实运行检查改善跨会话推进；其结论主要来自全栈应用任务。[长任务 harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
5. **旧补偿机制需要删除验证。** 后续研究记录了模型升级后删除强制 context reset、sprint 分解，并调整 evaluator 使用方式；作者强调逐项移除、观察结果，避免一口气改掉所有结构。[后续 harness 实践](https://www.anthropic.com/engineering/harness-design-long-running-apps)
6. **评估对象是实际产物。** Anthropic 建议编码任务结合行为测试与质量 rubric，使用隔离环境和多次试验，并校准评审者；严格锁定工具调用顺序容易误判有效解法。[Agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
7. **计划文件是约定，不是产品魔法。** OpenAI cookbook 明确将其 harness、阶段和记录文件描述为可调整的工作流约定；它们不能自行证明功能完成。[Codex workflow cookbook](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)

## 本项目的规则分层

以下是对用户目标的设计建议，不能表述成厂商已证实的最佳代码风格。

| 放置位置 | 内容 | 目的 |
|----------|------|------|
| 根规范常驻 | 先读真实代码和需求；完整解决问题；优先现有结构与依赖；每个新增抽象有当前需求依据 | 避免错误假设与预留式设计 |
| 根规范常驻 | 在信任边界校验；已建立的内部契约不重复防御；预期外失败保留原因；catch/retry/fallback 必须有具体恢复语义 | 减少噪声而不删除必要可靠性 |
| 根规范常驻 | 改动可追溯；不撤销他人修改；验证实际行为；说明证据缺口；简单任务直接执行 | 控制变更范围与虚假完成 |
| 根规范常驻 | 用一段路由说明何时需要研究、架构、计划、实现、评审 | 保持发现入口，不复制完整步骤 |
| 专业角色 | 架构取舍、实施职责、只读评审标准、研究证据规则 | 给独立任务清楚的责任边界 |
| 编排 skill | 依赖、所有权、交接内容、并行条件、集成检查、恢复和完成条件 | 复杂任务才加载执行细节 |
| 质量评估说明或 skill | 具体正反例、错误处理语义、去抽象判据、评估场景 | 把“优雅”变成可讨论的证据 |
| 项目自身检查命令 | 类型、lint、行为回归、真实入口检查 | 让可机械验证的约束由工具执行 |

具体写法应避免两个极端：不能把“少校验”变成信任未校验的外部输入，也不能把“暴露错误”变成删除资源清理或必要恢复。正常输入拒绝是产品行为；不可能状态、程序错误和未知失败才需要保留诊断并停止成功路径。

现有模板建议调整：

- 将“两次失败就停止/重启”改为“重复相同失败且没有新证据时停止同一种修补，重新诊断，再选择新的检查或交接”；次数本身不证明上下文已坏。
- 删除“这一定是上下文问题而不是能力问题”的因果断言；同时检查需求、环境、工具结果、实现假设和上下文缺失。
- 把详细 Session Hygiene、固定流水线和长任务说明移入按需工作流；保留可恢复状态的责任，不强制固定文件族或会话重启。
- 将“每个新 helper 都尝试移除并重跑验证”改为一次有依据的简化审阅；只有实际改变实现才重跑相关验证。
- 保留“最小完整方案”，不要把小 diff、文件少或零 catch 设为独立目标。
- 评审输出指出具体行为、位置、影响与证据缺口；既不能靠作者自评通过，也不能为了显得严格编造问题。

## 如何验证真实效果

这是后续评估方案，本次研究没有执行模型 A/B 实验。

先建立少量有区分度的真实任务；每个任务同时提供正确性检查与质量判据：

| 场景 | 成功证据 | 需要识别的退化 |
|------|----------|----------------|
| 已有模块的小 bug | 复现失败、修复后目标检查与相关回归通过 | 为局部问题新增框架、配置入口或无关重构 |
| 两处形式相似但契约不同的逻辑 | 两种契约均保持正确，设计解释可对应当前调用方 | 为去重合并不相容语义 |
| 外部输入进入受类型约束的内部流程 | 非法外部输入被拒绝，内部流程保持明确契约 | 漏掉边界校验，或每层重复同一校验 |
| 导入/转换中出现未知异常 | 原因可观察，任务不报告成功；必要清理发生 | broad catch、默认空值或 log-and-ignore 掩盖失败 |
| 新功能从真实入口触发 | CLI/API/UI 实际路径可用，结果到达真实存储或输出 | 函数和单测存在，但实际调用没有接通 |
| 可独立实现的两个模块 | 有独立交付，集成后的共同验收通过 | 并行互相覆盖；只验证各分支就宣布整体完成 |
| 恢复时旧笔记与代码不一致 | 读取当前状态修正判断，继续真正剩余工作 | 相信过期状态，重复实现或过早完成 |
| 关键验证环境不可用 | 完成可执行检查并准确记录缺口 | 把未运行、mock 结果或配置校验描述成真实完成 |

新旧配置使用相同仓库快照、任务、模型版本、可用工具和预算，每个任务重复运行，报告个体结果和分布。自动检查验证行为；独立只读评审在不知道配置版本的情况下按相同 rubric 比较必要性、契约、控制流、错误语义和需求完整度，抽样由人校准。

记录成功率、回归、具体质量问题、人工返工、耗时和 token。正确性是先决条件；在同等正确性下比较维护负担与耗时。不能用文档出现了多少关键词、生成代码的行数、角色调用次数，或单次“review ACCEPT”证明效果。每次只调整一个主要策略，保留原始 diff 和检查结果，使收益能追溯到变更。

# Unverified / residual risk

- 官方材料包含经验报告和示例，不构成本项目跨模型、跨语言的因果证据；目前尚未测出质量或速度提升百分比。
- “架构极致优雅”没有单一客观度量，需要任务化 rubric 和人工校准；所有自动评分都可能存在盲点。
- 只有配置/语法检查通过，不能证明原生 agent 实际加载、委派或执行了所写流程；实施阶段仍需验证真实入口。
- 本报告没有对强制重启、固定流水线等策略做消融实验；建议依据官方经验收窄其适用条件，再用本项目任务验证。

# Sources

- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)，2025-09-29。
- [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)，2024-12-19。
- [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)，2025-11-26。
- [Anthropic — Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)，2026-03-24。
- [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)，2026-01-09。
- [Claude Code — Best practices](https://code.claude.com/docs/en/best-practices)，滚动文档。
- [Claude Code — Extend Claude Code](https://code.claude.com/docs/en/features-overview)，滚动文档。
- [OpenAI — Codex best practices](https://learn.chatgpt.com/guides/best-practices)，滚动文档。
- [OpenAI — Iterating development workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)，滚动 cookbook。

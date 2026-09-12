# 问题

计划定稿后，如何用 Claude / Codex 原生能力并行执行开发任务，同时保持可验证的质量、清楚的写入边界和可靠的恢复；相关流程如何写成按需加载的 skills？

查阅日期：2026-09-13。本文的 graph engineering 指开发任务依赖图，不指知识图谱或图框架。以下“工程判断”是针对本仓库的设计建议，不是来源已经证明的性能结论。

# 决策指标

先满足行为正确、无覆盖他人修改、失败可见、验收可复查，再缩短交付时间。比较时同时考虑协调开销、常驻上下文、新增文件和运行依赖。是否减少过早抽象、重复校验和吞错，需要用真实开发任务的结果评估，不能从提示词措辞直接推断。

# 约束

- 保留轻量的开发规范仓库，使用现有原生代理能力，不新增图框架、调度服务或状态数据库。
- 简单任务可以主线程直接完成；并行必须来自真实独立工作。
- Claude 与 Codex 共用流程正文，平台特有配置由安装与启动层处理。
- 普通 `claude` / `codex` 使用默认配置；开发 skills 的安装发现必须服从这个隔离要求，不能无条件污染全局配置。
- 本研究只比较文档与现有模板，不运行性能实验，不证明模型行为提升。

# 候选方案

1. 单会话串行清单：步骤按顺序执行，流程全部放在根提示词。
2. 主线程协调依赖图：一个计划、按依赖就绪派发原生 subagents，skills 承载具体编排和技能编写流程。
3. 原生 agent teams：使用共享任务列表和代理间消息协调执行，skills 承载可复用流程。
4. Claude 原生 Dynamic Workflows：由原生 JavaScript 运行时组织 agent、逐项流水线与并行分组，skills 负责选用和编写流程。
5. Bun + TypeScript 外层程序，调用两端原生 SDK/CLI：适合跨客户端或需要外部进程管理的场景；不是本轮新增组件。

# 比较

表中成本与适用性评价是依据所引文档作出的工程判断；成熟度仅陈述文档覆盖和明确限制。

| 候选 | 对指标的优势 | 对指标的弱点 | 运维成本 | 成熟度证据 |
|---|---|---|---|---|
| 单会话串行清单 | 固定子任务容易按阶段验证；工程判断：协调面最小。[工作流模式](https://www.anthropic.com/engineering/building-effective-agents) | 独立任务无法同时推进；工程判断：把全部流程常驻会浪费上下文。[并行模式](https://www.anthropic.com/engineering/building-effective-agents)、[按需加载规范](https://agentskills.io/specification) | 工程判断：无跨代理状态，最适合小任务。[工作流模式](https://www.anthropic.com/engineering/building-effective-agents) | 官方描述了顺序链和中间检查，但没有证明它对所有开发任务最优。[工作流模式](https://www.anthropic.com/engineering/building-effective-agents) |
| 主线程协调依赖图 | 依赖完成才释放后继，独立节点可并行；主线程接收摘要，控制上下文。[拓扑排序语义](https://docs.python.org/3/library/graphlib.html)、[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 并行写入会冲突，仍需约束所有权；工程判断：协调者要核验结果与维护状态。[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 工程判断：一份计划加原生运行句柄即可表达本项目需求，无须图框架。[拓扑排序语义](https://docs.python.org/3/library/graphlib.html)、[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | Codex 官方文档覆盖原生 subagents；Python 标准库给出 ready / done / cycle 的明确语义。它们不是本仓库编排正确性的运行证明。[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[graphlib](https://docs.python.org/3/library/graphlib.html) |
| 原生 agent teams | 共享任务支持依赖、认领和消息协调，适合需要互相讨论的代理。[Claude agent teams](https://code.claude.com/docs/en/agent-teams) | 文档明确指出同文件写入、顺序任务和密集依赖不适合团队并行；token 成本较高。[Claude agent teams](https://code.claude.com/docs/en/agent-teams) | 工程判断：引入平台特有团队管理；本项目暂时得不到足够收益。[Claude agent teams](https://code.claude.com/docs/en/agent-teams) | 文档仍标为实验功能，列有恢复、任务协调和关闭方面的限制。[Claude agent teams](https://code.claude.com/docs/en/agent-teams) |
| 原生 Dynamic Workflows | 脚本控制后续动作，中间结果留在变量；逐项 pipeline 能独立推进。[Workflows](https://code.claude.com/docs/en/workflows)、[官方 Cookbook](https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows) | 原生受限 JS 环境；恢复可能重跑后续已完成项，需要明确写入与验收语义。[Workflows](https://code.claude.com/docs/en/workflows) | 工程判断：重复流程可减少主线程协调，但本项目尚无需要发布的固定工作流；能力和角色加载需按当前环境确认。 | 官方有脚本保存、失败、恢复和非交互运行文档；本项目未取得实际 workflow 执行证据。[Workflows](https://code.claude.com/docs/en/workflows) |
| Bun 外层调用原生 SDK/CLI | 工程判断：可以统一跨客户端进程与任务入口；仍复用原生 agent loop。[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)、[Codex SDK](https://developers.openai.com/codex/sdk) | 新增适配、进程和恢复责任；Codex TS SDK 文档要求 Node.js 18+，不能直接承诺 Bun 兼容。[Codex SDK](https://developers.openai.com/codex/sdk) | 工程判断：只有已存在跨客户端、外部运行管理需求时才值得增加。 | Bun 提供子进程控制，但本项目未测试两端 SDK 在 Bun 下运行。[Bun 子进程](https://bun.sh/docs/runtime/child-process) |

# 推荐

- 首选：主线程协调依赖图，加窄职责的 `orchestrate` 与 `author-skills`。用于计划已定、存在独立任务或需要跨会话恢复的开发工作；目标是用最少状态换取可控并行。[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Agent Skills 规范](https://agentskills.io/specification)
- 次选：单会话直接执行。用于单文件、单概念或依赖很紧的任务；跳过计划文件和委派仪式。[工作流模式](https://www.anthropic.com/engineering/building-effective-agents)
- 条件备选：原生 agent teams。仅在代理之间需要持续讨论、共享任务认领确有价值且平台能力已核验时采用。[Claude agent teams](https://code.claude.com/docs/en/agent-teams)
- 对稳定、重复、可脚本化的流程，先考虑环境实际提供的原生 Workflows；不要因为已有 Markdown 计划就排除官方脚本运行时。编排者先读取当前原生编写参考，确认角色加载、模型继承和恢复语义，再决定是否采用。[Workflows](https://code.claude.com/docs/en/workflows)
- Bun 是需要外层代码时的运行时偏好，不是创建外层调度器的理由。当前安装器使用 Bun，agent 执行继续复用原生 harness。

## 原生 Workflows 的能力边界

官方 `agent()`、`pipeline()`、`parallel()` 分别承载单 worker、逐项多阶段流程和并行分组。`pipeline(items, stage1, stage2)` 允许某一项进入第二阶段时另一项仍处在第一阶段；因此逐分支即时推进不是自建调度器独有的能力。多前驱汇合、共享资源冲突和集成验收仍需按具体任务安排，不能将 worker 返回等同业务任务完成。[官方 Cookbook](https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows#how-to-read-a-workflow-script)

原生脚本不允许模块加载、直接文件系统访问或 shell 操作；这些工作由 agent 执行。它是 Claude 自身的运行时，普通 Bun 脚本不能直接替代。原生 `/workflow-authoring` 提供当前编写参考，当前环境是否加载该能力需查询工具与技能目录，而非仅检查版本。[Workflows](https://code.claude.com/docs/en/workflows)

停止、不可恢复错误或启动被阻止可能产生 `null`。恢复按启动顺序重放时，失败项之后已完成的任务也可能重跑。工程判断：必需任务不能通过过滤空结果伪装成功；重复执行不能当作文件事务或回滚，写入前必须核对实际产物与旧 worker 状态。[Workflows 恢复](https://code.claude.com/docs/en/workflows#resume-after-a-pause)

本轮官方 Workflows/Cookbook 正文没有建立命名角色参数的完整契约，不能据此认定已安装的六角色正文会自动加载；采用时应根据环境内的原生编写参考与实际启动结果确认。研究已确认官方支持 `claude -p` 路径，但其触发与权限仍受原生规则限制。本地版本为 Claude Code 2.1.268；仅有版本与两端配置加载证据，尚无本 provider 下 Workflow 注册、执行或恢复的证据。[Workflows](https://code.claude.com/docs/en/workflows)、[Subagents](https://code.claude.com/docs/en/sub-agents)

据此，当前默认采用主协调者与原生 subagents；`orchestrate` 增加原生 Workflows 的发现、选用与验收要求，不发布尚未在真实环境验证的通用 workflow 脚本。这是当前任务与证据支持的选择，不是认为自写编排优于官方 harness。

## 依赖图的最小契约

以下是工程判断，采用标准的“前驱完成后节点就绪”语义，不要求实际调用 Python。[graphlib](https://docs.python.org/3/library/graphlib.html)

| 字段 | 必须表达的内容 |
|---|---|
| `id` | 稳定任务标识，供依赖和证据引用 |
| `role` | 执行角色，沿用现有六类职责 |
| `deps` | 必须先完成的任务 ID；空列表即无前驱 |
| `owns` | 允许写入的文件、目录或资源；只读任务明确为空 |
| `acceptance` | 对应需求的可观察结果及实际验证方式 |
| `state` | `pending` / `running` / `blocked` / `done` |

运行时补充实际 agent / session 句柄；使用 worktree 时记录目录和分支。结果记录产物、验证命令与结果，以及可识别的版本或快照。字段可以写在同一个 `plan.md` 中，不需要复制到第二份进度账本。

工程判断：只有主线程更新计划，worker 返回状态与证据。这样不需要为 Markdown 自行实现多写者锁。不要让 worker 自行修改全局完成状态。

## 执行与恢复规则

1. 计划定稿前确认接口、任务边界与验收方式；检查 ID 唯一、依赖存在且无环。原生队列或未来程序化执行器应在计划输入边界完成这些检查。
2. 找出所有 `pending` 且前驱全部 `done` 的任务，再剔除与运行中任务发生写入冲突的候选，形成当前可派发集合。不能只取“第一项未勾选任务”。
3. 有可用代理容量且存在独立工作时并行派发；每条任务交代目标、输入、所有权、依赖产物和验收。任一任务完成就重新计算就绪集合，不等待无关慢任务组成的整批屏障。
4. 共享工作区内，同一资源只允许一个写者。写入重叠时优先拆清边界或串行；确需独立修改时使用独立 worktree。Git worktree 提供独立检出与 index，但共享仓库部分状态，不能视为完整环境隔离。[Git worktree](https://git-scm.com/docs/git-worktree)
5. 使用 worktree 时由主线程串行集成；只有依赖方实际可访问的产物已集成并通过针对性验收，才标记 `done`。独立分支测试通过不能代表组合结果通过。审查绑定稳定快照；被后续修改影响的验证需重跑。
6. 恢复时先读计划、当前 Git / 文件状态和真实运行句柄，再继续工作。计划中的 `running` 只是记录；观察超时也不足以证明进程已经终止。只在确认旧任务终止或句柄不存在后安排替代执行，防止重复写入。
7. 失败时保留具体错误与证据。重新调查根因、必要时修订受影响依赖；阻塞其后继，但继续独立任务。没有就绪任务时，存在运行句柄则等待；否则诊断阻塞或计划错误，不能将“无任务可派发”当作完成。
8. 最终按原始需求核对集成结果、验证证据和审查意见；勾选、worker 自述或 reviewer 的一个 `ACCEPT` 字符串都不能单独证明完成。

第 1–3 条采用标准拓扑就绪语义；第 4–8 条是本项目的工程约束。Anthropic 的长运行实践支持进度产物结合 Git 状态进行交接，并明确记录了未验证就宣称完成的失败模式；该研究也说明多代理是否更优仍是开放问题。[graphlib](https://docs.python.org/3/library/graphlib.html)、[长运行 harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Skills 编写规则

官方共同点是按需加载：先发现名称与描述，相关时才读取正文，支持文件按需加载。Agent Skills 规范建议正文控制在 500 行以内，并给出元数据、正文、资源三层结构；这应是上限参考，不能成为填满篇幅的目标。[Agent Skills 规范](https://agentskills.io/specification)

OpenAI 官方要求聚焦单项工作，描述明确作用域与触发边界，并测试描述是否触发正确。默认用文字指令，只有确定性操作或外部工具需求才加入脚本；步骤要写明输入与输出。Codex 可能缩短初始技能列表中的描述，因此核心用途和触发词应前置。[OpenAI Build skills](https://developers.openai.com/codex/skills)

Anthropic 建议只补充模型缺少的信息；依任务脆弱程度调整约束强度，避免一律机械化。描述写清做什么和何时使用，正文保持简洁，引用避免多层跳转。先从真实失败构建评估，再写最少能解决问题的规则，并用实际使用的模型验证。[Claude skill authoring](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

据此建议：

- `orchestrate` 描述覆盖“执行已定计划、并行依赖任务、恢复中断工作”，排除普通单步修改；正文承载上述执行协议，参考文件仅在具体格式确有复用时增加。
- `author-skills` 描述覆盖“创建、修订、评估技能”，正文包含输入、触发边界、最小流程、输出和验证；不再复制根提示词里的通用代码质量原则。
- 根提示词只保留质量原则、角色路由和进入这些 skills 的条件；角色文件说明专门职责与交付契约。
- 共用正文采用标准 `name` / `description` 和普通相对链接；平台特有 frontmatter、自动执行语法和工具名不混进跨端公共协议。
- 正向触发、邻近但不适用的请求、显式调用、真实任务结果都需要行为评估；仅校验 YAML/TOML 和文件存在不能证明 skill 有效。

最后一条是基于两家官方测试建议的工程细化。Agent 评估应区分轨迹与环境最终结果，重复试验以观察随机性，并按需组合程序判定与人工审查；不要只检查回答包含约定关键词。[Agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## 安装发现边界

Claude 官方列出个人 `~/.claude/skills`、项目 `.claude/skills` 与额外目录等发现入口，支持技能目录符号链接。Codex 官方列出个人 `~/.agents/skills`、项目 `.agents/skills` 等入口，同样支持符号链接。[Claude skills](https://code.claude.com/docs/en/skills)、[OpenAI Build skills](https://developers.openai.com/codex/skills)

工程判断：这些是原生发现能力，不等于应将本项目安装到所有默认会话。`claude-dev` / `codex-dev` 的具体开发配置路径应以启动参数与本地实际发现结果为准；不能仅从 `HOME` 或配置目录名称推断隔离已成立。本研究未验证本地运行，安装实现应保留独立的端到端证据。

## 现有模板中应修正的假设

以下位置是调研开始时的仓库快照，后续实现可能已经修改：

- `templates/agents/plan.md:70` 明确要求按书写顺序执行、禁止隐式并行，与执行依赖图目标冲突。
- `templates/agents/plan.md:12` 将计划文件说成唯一所需状态；应改成计划是协调记录，运行结果必须与实际环境核对。
- `templates/AGENTS.md:64` 的循环取下一条未勾选任务，应改成按依赖与所有权选择就绪任务。
- `templates/AGENTS.md:41` 按两次失败强制重开会话；工程判断：失败次数不等于上下文损坏，应保留根因调查、有效句柄与交接证据，根据停滞证据决定恢复策略。
- `templates/AGENTS.md:42` 另建 `progress.md`，与计划承担的状态容易重复；工程判断：有计划时只维护一份协调记录。
- `templates/agents/plan.md:38` 的 reviewer `ACCEPT` 只能是验收证据的一部分，不能取代需求结果核对。

# 未验证与剩余风险

- 未测量这些修改是否提高代码质量或缩短开发时间；需要与原模板和无技能基线在相同任务、模型与预算下比较。
- 未执行 Claude / Codex 的安装与技能发现测试；具体 CLI 版本、配置路径、权限继承和恢复能力由实现阶段验证。
- 自然语言所有权约束不是操作系统隔离。高冲突任务仍需串行或真实隔离；共享数据库、端口、生成目录也要算入写入资源。
- 文档没有证明一个固定团队规模或“所有角色一律最高推理”能获得最佳质量成本比，本研究不推荐固定并发数或模型参数。
- 跨会话恢复、依赖解锁、失败传播、串行集成和技能误触发应作为后续行为评估用例；静态结构校验只覆盖格式和部分契约。

# 来源

全部读取过官方页面正文，正文引用均指向直接支持相应事实的页面：

- [Anthropic：Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Python：graphlib](https://docs.python.org/3/library/graphlib.html)
- [OpenAI：Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Claude Code：Agent teams](https://code.claude.com/docs/en/agent-teams)
- [Git：git-worktree](https://git-scm.com/docs/git-worktree)
- [Agent Skills：Specification](https://agentskills.io/specification)
- [OpenAI：Build skills](https://developers.openai.com/codex/skills)
- [Claude：Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code：Skills](https://code.claude.com/docs/en/skills)
- [Anthropic：Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic：Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Claude Code：Dynamic Workflows](https://code.claude.com/docs/en/workflows)
- [Anthropic Cookbook：Dynamic Workflows](https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows)
- [Claude Code：Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude：Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [OpenAI：Codex SDK](https://developers.openai.com/codex/sdk)
- [Bun：Child processes](https://bun.sh/docs/runtime/child-process)

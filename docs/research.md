# Harness、loop、graph 与简洁设计调研

核验日期：2026-10-19。本文区分一手来源、用户偏好与本项目取舍。来源中的模型实验不能证明本 profile 的效果；实际检查见 [验证记录](validation.md)。运行时只加载根规则及按需工作流，不要求 agent 每轮阅读本研究。

## 三种常用模型的最新增量（2026-10-19）

本轮重新检查实际工作树与已有轨迹，核读最新官方材料及论文修订。保留根规则表达个人取舍、develop 按需承载协调、五专家按具体问题使用的结构；合并常驻规则里的清理与验收重复。原“已有项目精简直接交 simplify”改成决定委派后的职责安排，小清理可由当前作者完成，整体精简仍须覆盖完整分配范围。不为一个模糊的“极致”继续叠加机制。

本轮粗略阅读清单任务另观察到：模型提出产品问题后仍自行选择浏览器使用方式并增加链接、筛选和删除，180 秒实验限额内未交付。由此把已有“问必要问题”落实为实施依赖：影响功能、使用或数据的答案未收到前，不实施依赖部分，继续独立工作；日常技术选择仍自主完成。这是针对实际轨迹的窄修订，不增加产品规格文件或通用需求流程，原失败与后续范围更正分别记录，见 [验证](validation.md)。

[OpenAI 10 月 14 日维护实践](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)直接覆盖 Sol：建议从 medium 尝试，广域审计有收益再提高投入；同快照、同模型重放单条规则变化比凭感觉累加提示更有判断力。其团队也遇到复杂度超过收益的维护建议。保留完整行为、真实路径与结构必要性的分别验收，不把活动量、测试数或较短提示词当成成品质量证据。

[Opus 5.5 专用提示指南](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)（页面无发布日期，10 月 19 日核读）新增无人值守风险：文本 `end_turn` 可能只是进度汇报，必需后台命令或子任务也可能仍在运行。三端 Completion 因此明确继续可推进的授权工作，交付前收取必需结果；没有复制其额外 checker、自动续跑控制器或固定清单。指南建议从 medium 校准，xhigh/max 先证明额外收益；不改变用户现有模型或挡位。

[Anthropic 10 月 15 日评审实践](https://claude.dev/blog/solving-code-review-at-anthropic/)记录多轮评审制造额外工作：后续被指出的代码约 59% 在首轮就已存在，团队据此收敛复审。现有规则已要求只为具体风险启动 review、只针对修复及受影响路径复验、不凭潜在强化阻塞交付，无需再加固定轮数或 reviewer 链。[7 月 24 日上下文文章](https://claude.dev/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models/)则区分应删除的旧补偿与值得保留的个人意见；其删 prompt 结果来自特定内部评估，不是本项目的压缩配额。标准库优先、why 注释和作者自清理属于用户明确取舍，继续保留。

[Grok 4.7 指南](https://docs.x.ai/developers/grok-4-7)（10 月 10 日更新）与 [Best Practices](https://docs.x.ai/developers/model-capabilities/text/best-practices)（10 月 12 日更新）重点是 Responses API、跨 turn 原样保留加密 reasoning、会话缓存键及记录实际 effort。4.7 的 API 默认是 high；不能把其他模型的 medium 机械迁移过来。这些主要属于原生 harness/API 传输层，不是再写一句“多思考”就能实现的能力。本项目继续沿用原生 CLI，不自建状态传输、重试或缓存系统。

[Mario Zechner 3 月 25 日作者经验](https://mariozechner.at/posts/2026-03-25-thoughts-on-slowing-the-fuck-down/)批评局部决策累积无用类型和抽象，窄评分函数忽略维护复杂度；支持检查完整实际路径，但不是多个 agent 普遍失败的实证，也不采用其个人开发节奏。少防御的实施仍遵循前次一手研究：内部信任合同，错误直接暴露；本轮仅在既有边界句明确不猜测、转换或修复无合同的未支持输入，不要求主动增加拒绝分支或边界测试矩阵。

## 标准库优先与合适的小实现（2026-10-19）

用户补充的依赖偏好已按明确指令落实：标准库和平台能力优先，其次是项目已有合适能力；狭窄当前需求允许直接小实现；第三方只在功能或实现难度上的收益抵消集成与维护成本时引入，小实现不扩成通用框架。三端根规则及十五个角色均携带这条约束，原先 root/arch 中偏向先考虑成熟库的句子已替换，避免相反默认。

[Rob Pike 的 Go at Google §7](https://go.dev/talks/2012/splash.article)支持少量局部实现胜过为一个函数拉入大库；[Russ Cox 的依赖讨论](https://research.swtch.com/deps)说明复用也转移了设计、调试和维护责任。[Casey Muratori 的 Semantic Compression](https://caseymuratori.com/blog_0015)从具体可用代码逐步提炼复用，关注全生命周期的人力成本。它们支持判断实际收益，不构成禁止所有第三方或按重复次数机械抽象的规则。

审美与 [suckless](https://suckless.org/philosophy/) 的简洁、清晰和面向熟练用户相近，但不采用删行指标或复杂即重写；[stb](https://github.com/nothings/stb#faq)提供易集成的小组件，也明确已有等价能力时通常不值得替换。[SQLite](https://www.sqlite.org/selfcontained.html)可借鉴自包含，其[深入测试策略](https://www.sqlite.org/testing.html)与先使用后权衡 bug 的偏好不同。这里比较的是各自部分取舍，不宣称整套哲学相同。

本轮为规则落实和安装检查，未新增云端模型实验；不能仅凭文字载入就宣称所有后续项目都已采用最优依赖。

## 进攻性编程与当前代码偏好（2026-10-19）

结论：吸收“按约定实现、信任已建立的内部保证、让意外失败显现”，适合本用户；当前 harness 已有这些语义，不需要再安装一套哲学 skill、增加专家或普遍添加断言。本轮任务是调研是否引入，只更新研究与判断，不修改或发布运行模板。

“Offensive programming”在一手材料中有不同侧重。[Chris Gonnerman 的作者原文](https://opensource.gonnerman.org/?p=78)（2012-06-22）最接近“先实现当前用途，明显问题之外不穷举，实际出错后处理”：背景是 VBA/Python 能给出有用异常并收到用户反馈，文章明确是 Opinion，不是比较研究。[Johannes Brodwall 原文](https://johannesbrodwall.com/2013/09/25/offensive-programming/)（2013-09-25）反对逐层 catch 后继续、返回空值掩错和蔓延的 null 检查，同时保留资源自动释放，区分环境失败与程序 bug。这两篇浏览工具未能抓取，另经作者站点 HTTPS 直接读取正文核验。

[Tyler Hoffman 的嵌入式文章](https://interrupt.memfault.com/blog/defensive-and-offensive-programming)（2020-12-15）则提倡大量断言、故障记录和复位，也保留外部输入、硬件、持久化等边界。因此只写“使用进攻性编程”可能让 agent 增加另一批检查。采用错误及时可见的目的，不能自动照搬断言、watchdog、重启和诊断基础设施。

[Meyer 的 Applying Design by Contract](https://se.ethz.ch/~meyer/publications/computer/contract.pdf)（1992，pp.41、44）反对调用者与被调用者冗余检查，说明保证前置条件不等于每次重新检测；分工应服务整体架构简洁。[Ledru 讲义](https://lig-membres.imag.fr/ledru/CoursJML/Slides/SFVE_Cours5.pdf)（2013，slides 6–8）也将进攻式描述为方法信任调用者、外部与内部区别处理。可借鉴责任清楚，不需要契约 DSL、专用检查层或每函数断言。

[Armstrong 博士论文](https://erlang.org/download/armstrong_thesis_2003.pdf)（2003，§4.4、§5.3.1、附录 B §3.13–4.1）支持正常路径优先、入口建立保证后内部信任、语言原生错误已经适合时不再自造失败分支；规格已定义且知道如何处理的失败仍可处理。其 worker/supervisor、编译器检查与隔离前提不能直接照搬普通应用，也不能从“let it crash”推出隐藏失败或省略必要资源释放。

架构偏好还需要独立的依据。[Fowler 的 Yagni](https://martinfowler.com/bliki/Yagni.html)（2015）反对为假定未来能力增加复杂度，并明确依赖持续重构和易修改代码。[Metz 的 The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)（2016）支持内联错误抽象、保留尚无共同语义的局部重复。[Ousterhout 的 Designing Abstractions](https://web.stanford.edu/~ouster/CS349W/lectures/abstraction.html)强调隐藏实际复杂度、减少错误条件，而非薄层转发。它们支持按当前收益决定模式和抽象，不能把“最少行数、零 helper、全部塞进一个函数”当作简洁。

[Duffy 的 The Error Model](https://joeduffyblog.com/2016/02/07/the-error-model/)（2016）区分程序 bug 与可恢复错误；这里借鉴分类与错误可见，不迁移 Midori 的整套终止机制。对本用户，文件读取失败可以直接报告并结束本次操作，不必自动创建默认内容或重试；约定标准 JSON 就用标准解析器，不猜格式或修复非约定输入。事务、提交后才报告成功、实际需要的清理是在兑现已有功能，不是为奇怪习惯增加兼容。

“代码自说明、只写非显然 why”是用户明确选择，独立于进攻性编程。[Ousterhout 的注释讲义](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=comments)认可比 why 更广的注释，不能当成严格 why-only 的来源。本项目按用户偏好优先改善名称、类型、控制流；复杂或反直觉之处解释原因，避免复述实现，也不以省行数牺牲可读性。

当前三端核对：root 已约束假想调用者、防御分支、内部重复校验、fallback/retry、原始错误和 why 注释；develop/dev 不预建兼容；arch/simplify 允许取消职责与替换错误抽象；review 不用假想加固阻塞交付。没有发现必须新增的规则。可选的后续消歧是在现有信任边界句中明确“信任已约定使用，不为未支持用法添加猜测、自动转换或兼容”，保留其余错误/清理约束；不另叠新章节。

决策可概括为：只做当前明确需求；按约定走直接、易读的路径；不为臆想用法预建兼容与恢复；已有类型/语言/边界能够暴露错误就不重复检查；只在有具体动作的位置处理失败，禁止吞错或默认值假成功；实际问题出现后按当前支持范围判断修复。这个选择有可解释的一手思想来源，但没有统计证据证明它能让任何模型或项目自动达到全局最简。

## 从实际开发反馈校准循环与验证（2026-10-19）

本轮重新读取官方指南、作者文章与论文正文，并核对 PRISM、Vertex、砚流的原生会话。已有的完整需求、作者自清理、直接设计、真实错误、why 注释及按需专家原则继续保留；主要缺口是“最终独立验收”容易被理解为重新执行作者的全部调查和检查。以下取舍针对这个已观察问题，不表示更长或更短的提示词必然更好。

[OpenAI GPT-6 指南的 Testing and verification](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-sol)明确指出小改动可能过度测试，要求按改动校准检查范围。[Anthropic 长期应用开发实验](https://www.anthropic.com/engineering/harness-design-long-running-apps)（2026-03-24）也在模型能力变化后移除逐 sprint 评估的开销，但保留能力边界外的独立验证。本项目据此明确：主会话核实实际代码和检查输出，复用仍覆盖当前代码、输入和环境的结果，补缺失或失效的检查。受影响行为和明确发布门禁仍须验证；不新增验证缓存、哈希台账或冻结阶段。厂商实验使用不同模型和任务，不能据此保证 Sol 的收益。

[Agent Skills Can Be Harmful](https://arxiv.org/html/2608.11888v1)（2026-08-12，§V）在筛选出的 182 个效率回归案例中，将 114 个归于过重流程，其中 67 个是过度验证、30 个是重型实现流水线。这是选中失败案例的组成，不是所有任务的发生率；环境为 OpenCode/Opus 4.6。它支持检查技能如何增加行动，而非仅数提示词长度。[Agent Skill Evolution](https://arxiv.org/html/2610.04832v1)（2026-10-04，§5–7）进一步区分传递新操作信息与重述旧要求；其小模型、关闭 thinking 等设置不能证明当前 Sol 的效果。本轮只修有证据的语义歧义，并通过真实原生任务观察行为。

[Loop Engineering: Building Blocks, Adoption, and Impact](https://arxiv.org/html/2608.21884v2)（v2，2026-08-26）区分运行内工具循环与跨运行触发循环，报告采用情况，但收益控制实验仍属研究计划。[LangChain 作者的图工程回顾](https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph)（2026-07-22）也区分确定性流程与开放任务，反对将所有代理行为固定成路径；[Graph Engineering 综述](https://arxiv.org/html/2608.21156v2)（v2，2026-08-26，§5.1）要求区分组织结构与额外计算的收益。适合本项目的图思想是明确依赖、写入归属、集成和失败反馈；继续使用原生 goal/子任务，不增加图文件、外层循环或固定五专家链。这是本项目的工程取舍，不是这些材料证明原生循环总优于图框架。

[SlopCodeBench v2](https://arxiv.org/html/2603.24755v2)（2026-05-07，§3.4）观察同一产物连续接收需求后的质量变化：质量提示改善初始结构，却没有阻止后续劣化；只测 Python 和当时模型，不能归因 GPT 通病。本项目借鉴连续需求评估，观察新增需求是否叠加重复表示或机制，保留外部行为验收，不引入其整套运行器或自动复杂度评分。

[OpenAI 的工作流示例](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)（2026-08-03）明确将阶段文档和审批视为可选约定；[Harness-aware evaluation](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)（2026-09-23）说明独立工具或简化循环不能代替原生环境行为验证。本轮复用已有任务、真实 CLI 与独立外验，记录实际生效模型和挡位；分开报告安装/加载、功能、结构与耗时。少量前后运行只作定向观察，不证明普遍提速。

本机旧会话的实际挡位为 ultra，而当前默认值为 medium；记录不足以确定此前 TUI 选择的来源。配置默认值不能替代实际 turn_context。安装器继续不指定默认模型/挡位，只在升级时保留开发 profile 中已有的两个选择，避免发布新规则时抹去个人设置。

## 社区开源实践与选择性借鉴（2026-10-18）

本轮搜索 GitHub 原仓库、作者文章和社区讨论，实际读取规则与提示词源码；搜索摘要只用于发现候选。未安装外部插件或执行其代码。最接近本项目的是原生 agent 上的偏好配置和简化 skills，少数独立运行时提供设计参考。在已检查的项目中，没有核实到把本用户全部偏好原样实现、又有可迁移效果证据的一套完整方案；这不是对所有开源项目的穷尽判断。

- **[Ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)**：以 YAGNI 和减少建设为中心，先追踪实际调用路径，再考虑已有能力、标准库/平台、现有依赖及直接实现；保持合适的原生数据形态，减少包装与转换。借鉴决策顺序，不采用最短 diff 优先、冻结既有层次/所有校验、固定尾注和模式管理。它们会干扰已授权的大范围精简。已核见独立 MIT LICENSE；作者宣传的 LOC/成本数字未复核，不作为本项目收益。
- **[Simplicity Skills](https://github.com/SVS696/simplicity-skills/blob/main/skills/simplicity-code/SKILL.md)**：分设计和代码两个入口，强调作者交付前真正修改可精简的结构，只有诊断不算完成。采用作者自清理并复验，以及设计阶段消除无当前用途的实体/状态；舍弃每元素强制决策表、每次打卡输出、固定复用次数门槛。已核见独立 MIT LICENSE。
- **[steipete/agent-scripts](https://github.com/steipete/agent-scripts/blob/main/AGENTS.MD)**：与本项目定位接近，是原生工具上的个人规则、skills 和脚本。其重构规则要求旧路径有明确现实合同才保留，测试本身不是合同。借鉴这一判断及常驻规则/按需指南分离；不复制作者个人运维、发布和模型路由。已核见 MIT LICENSE，整个配置不能笼统称极简。
- **[Karpathy-inspired guidelines](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/skills/karpathy-guidelines/SKILL.md)**：原 forrestchang 地址现重定向 multica-ai，是借鉴 Karpathy 公开观察的社区项目，并非 Karpathy 本人发布的 harness。反对未请求配置、假想错误处理和不必要抽象，支持清理本次修改残留；过于保守的最小局部改动、不碰原有死代码及遇疑即停不适用于已授权整体精简。README 声明 MIT，但本轮未核见独立 LICENSE 文件。
- **[Anthropic code-simplifier](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md)**：官方公开的可编辑简化角色，重视明确可读、保留功能、删除无用抽象和显然注释，默认围绕近期修改。保留其清楚优先于行数的判断，不迁移硬编码的 Opus、TS/React 约定；运行检查仍按本项目合同执行。[官方命令文档](https://code.claude.com/docs/en/commands)的内置 simplify 是多 reviewer 功能，不应把每次作者自查都变成一次并行评审。
- **[Superpowers implementer](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/implementer-prompt.md)**：明确要求报告前亲自检查自己的改动并修正，作者不自行派 reviewer，独立评审由控制者统一安排。采用这一职责边界；不引入固定逐任务关卡、额外报告格式、模型指定或每次全套验证要求。
- **[Compound Engineering simplify](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/ce-simplify-code/SKILL.md)**：有范围的实现后清理，可无收益结束，并负责自身回归。只吸收范围/所有权和按影响验证，不采纳锁死所有 proof tests/structure pins 或固定多类 reviewer。当前 raw main 与搜索缓存的 reviewer 数量已不同，本文不把数量当稳定接口或质量证据。
- **[Pi](https://github.com/earendil-works/pi)**：独立 agent 运行时，旧 badlogic/pi-mono 地址已重定向；[当前 prompt 源码](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/system-prompt.ts)及[作者原文](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/)支持小核心、按所选能力组织上下文和可观察过程。借鉴控制上下文负担，继续使用现有三个原生运行时。2025 文章的能力描述不能代替当前源码；已核见 MIT LICENSE。
- **[Code Craft](https://github.com/yanko-belov/code-craft)**：YAGNI 与 fail-fast 部分可参考，但[依赖倒置 skill](https://github.com/yanko-belov/code-craft/blob/master/skills/dependency-inversion/SKILL.md)要求单实现也引入接口和注入，与本项目按当前收益决定抽象相冲突，不整包采用。已核见 MIT LICENSE。

对“进攻性编程”，本项目采用的实际含义是入口按真实合同验证、内部信任已建立类型与不变量、意外错误带原始原因暴露。[office-kit/docx 的项目级 CLAUDE.md](https://github.com/office-kit/docx/blob/main/CLAUDE.md)也明确区分外部边界和内部冗余防御，并禁止吞错、强调 why 注释；它是项目规范示例，不是通用 harness。其所有外部调用统一防御/重试等表述不自动成为本项目要求。[社区关于 fallback 的讨论](https://www.reddit.com/r/ClaudeCode/comments/1mt3yy3/fallbacks_are_killing_me/)只是相似困扰的体验材料，不是跨模型效果证据。

本轮只提炼两个运行时增量：作者交付前沿真实路径亲自做有益简化并核验，保留有用结构和有意局部重复；优先复用适合的现有能力和数据形态，减少无必要转换。完整任务仍由原 owner 连贯完成，独立 simplify 保留整体设计的新视角。未引入外部插件、hook、规则编译器、清理打卡表、固定测试配额或新运行框架；这些是结合本用户偏好的选择，不是所有来源一致支持的普适结论。

## GPT-6.1 Sol 思考挡位与快速交付（2026-10-18）

针对“快速得到完整、清楚、少冗余的成品”，本项目建议 **medium 起步，具体难题按需 high**，不强制修改用户运行配置。[官方模型页](https://developers.openai.com/api/docs/models/gpt-6.1-sol)列出 low、medium（API 默认）、high、xhigh、max；客户端的其他标签不应直接当作同名 API effort。[官方部署检查](https://developers.openai.com/api/docs/guides/deployment-checklist)说明低挡较快，高挡投入更多规划与权衡；medium/high 用于代码推理，xhigh/max 应由代表性评估证明额外质量值得其时间与成本。effort 分配推理投入，不直接规定项目应该有多少功能、层次或代码。

[OpenAI 10 月 14 日维护实践](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)建议从 Sol Medium 尝试，广域审计有价值时提高 effort，也承认部分建议增加的复杂度超过收益。这支持 medium 作为起点，不能证明其代码最简洁。复杂架构、跨模块精简和难定位缺陷可按需比较 high；边界明确的小修改可用 low。没有证据支持把所有 goal 默认开到 xhigh/max，也没有证据证明高挡必然更臃肿。

[社区原始两构建对比](https://spectrumailab.com/blog/gpt-6-1-sol-reasoning-effort-test-2026)中，Max 在单名 AI reviewer 的盲评中两次第一，并未支持“低挡代码必更好”。但任务要求 go all out，各实现功能不同、每挡仅一次，部分运行重叠、测试和帧率未全面独立复验；它没有控制同等功能的冗余，也不是已有项目精简实验。不能据此统一推荐 Max。本项目之前两次 medium 简化成功也没有挡位对照，不能算最优证明。

本轮实际收紧的是完成取舍：默认贯通当前完整功能、作者自清理、必要验证后交付。独立 simplify 只处理明确精简目标或具体结构问题；删除规模触发额外阶段的要求。已知功能和数据失败要修，未知 bug、假想边界及“极致”不启动无尽审计或清理。这是用户偏好下的工程选择，行为证据见 [当前验证](validation.md)。

## 本次改变什么

当前真实失败是架构与实现不断增重：宽泛的抽象理由、agent 自定合同的固化，以及偏向追加保证的评审形成相互强化的工作。三端规则因此要求完整用户行为成立时优先减少职责、状态和理解成本；本轮进一步明确粗略 goal 的当前终点、开发作者自清理及按具体问题调用专家的责任划分。工具权限、原生安装、账户与模型选择继续由各端原生机制承担。

这是针对已观察失败的工程干预，不能据此宣称 GPT 普遍比其他模型臃肿，也不能宣称更短提示词必然改善代码。本轮不建立外层 supervisor、图引擎或通用质量评分器。

## 最新 harness 实践的支持范围

Anthropic 的 [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（2024-12-19）区分预定义 workflow 与动态 agent，建议从解决实际问题所需的简单模式开始。[Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（2025-09-29）要求高信号、按需的上下文，避免空泛指导及把脆弱程序逻辑硬编码进提示词。本项目因此保留明确取舍准则，删去复杂任务必须委派的默认；不会把“极简”缩成一句无判断力的口号。

[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)（2026-03-24）同时展示评估者的收益和成本：实际操作应用能发现接线错误，但评价迭代也会使实现复杂度增加，最后版本未必优于中间版本。其 planner 被特意要求扩展功能、加入 AI，这与本用户“新功能以后再说”的偏好冲突，本项目只采用澄清交付行为的思路。升级模型后作者删除 context reset、sprint 结构和逐 sprint 评价，独立评价只在仍能补足模型能力时有价值。[Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents)（2026-04-08）同样说明旧补偿机制可能变成额外负担。故本项目不把某次 planner/generator/evaluator 配置固化成通用流水线。

OpenAI 的 [Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)（2026-09-11）建议审计积累的 skills/AGENTS、减少无关读取和过度具体的行程；旧模型所需的测试鼓励可能在新模型上导致额外工作。[GPT-6 指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-sol)明确建议按改动校准验证，合适检查通过后只因新变化或具体疑点扩大/重复。行为描述主要针对 Astra，需在 Sol 及实际任务上验证；本项目采用的是可检验的工作策略。

[Maintaining software with GPT-6](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)（2026-10-14）承认有些维护提案的复杂度超过收益，并建议同快照、同模型只改变一条指令来回放。由此采用小型配对任务和实际产物审查，不用活动量、角色数量或通过的测试数量代替质量。

## Loop engineering

[The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering)（2026-06-16）将工具执行、产出验证、外部事件触发和跨试验改进区分为不同循环，并讨论验证成本。这是该文的分析框架，不意味着每个开发 profile 都需要四套运行系统。

Loop 论文的工作定义主要指跨运行的自动触发与控制；它不把单次会话内的工具调用循环等同于完整的 loop engineering。LangChain 的四层用法更宽。[Addy Osmani 的 Practical Loop Engineering](https://addyosmani.com/blog/practical-loop-engineering/)（2026-08-14）也区分有限目标和定时循环，强调完成条件与停止原地重复；其中独立 checker 和示例里的全套 UI 检查是作者做法，不成为所有任务的强制阶段。

本项目只需要原生执行循环与必要的行为反馈：按当前证据选择可做的工作，实施，检查实际结果，再把具体失败交回负责该问题的步骤。开发可因新证据修正设计，简化后须检查受影响行为，阶段本身不构成只能向前的流水线。相关检查通过且没有新修改或具体未解问题时交付；同样失败没有新证据时改变诊断。完成条件覆盖完整请求，不能通过少做功能或隐藏失败结束，也不因潜在改进而无限扩大验收。

原生 goal 负责延续目标，不会自动给开放质量目标产生有限终点。[Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)要求可审计的结果与证据。本项目把“极致”作为方案取舍方向，以完整行为、真实约束和必要检查确定交付；不要求证明全局最优。

## Graph engineering

[3 Years of Graph Engineering with LangGraph](https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph)（2026-07-22）明确指出，这是已有工作流设计思想的新名称。控制图描述节点、状态与转换，本身可以包含循环；固定路径适合可预先规定的流程，开放研究可能更适合自主核心 loop。它不是必须部署的新标准。

本项目显式说明默认阶段、返回条件和任务依赖：稳定输入、写入与共享资源归属、何时可消费结果，以及集成后的行为检查。任务依赖图与 agent 控制流不是同一个对象；需要排序不等于需要图运行时、图文件或固定角色链。主会话可以合并阶段直接实现；独立且可验收的结果才值得拆分。

术语本身也未统一。[What makes prompts a graph](https://arxiv.org/html/2607.27578v1)（2026-07-30）把显式结构、独立可执行语义和持久图对象作为更严格的定义，并将原生 subagent 委派列为反例，同时明确这不表示质量较差。它是概念分析，不是优劣实验。本项目借鉴依赖、所有权、反馈和终止约束，不以拥有独立图对象或外层循环作为优化目标。

[Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)（2025-06-13）强调独立研究方向的并行收益，也明确多数编码任务较少真正独立的工作。[Building a C compiler](https://www.anthropic.com/engineering/building-c-compiler)（2026-02-05）记录多个 agent 同修一个问题相互覆盖，以及反复测试耗时。故分工按结果而非文件、步骤或角色数量；耦合实现、检查和修复留给一个 owner。

[CAID / Effective Strategies for Asynchronous Software Engineering Agents](https://arxiv.org/html/2603.21489v1)（2026-03-23，§2.2–2.5）提供更具体的编码证据：耦合单元由同一 worker 持有，worker 自验并从实际错误修复，manager 按依赖集成而非每次详细重审，预算耗尽仍未完成就不算交付。当前 develop 已覆盖这些做法。其旧模型、OpenHands 任务与增加的总计算不能证明当前三模型必须多 agent，也没有衡量本用户偏好的代码简洁度。

## 本项目的专家分工取舍

默认路线为：粗略 goal → 收敛本轮功能 → 尽早贯通完整路径 → 作者自清理 → 必要验证 → 交付；独立精简按具体复杂度或明确精简目标启用。`research`、`arch`、`dev`、`simplify`、`review` 是按需使用的五个角色，不要求每个阶段都启动一个子 agent。小任务可以合并，已有可靠结论可以复用；新的事实可以推翻 agent 自定设计。只向用户询问会实质改变功能、使用方式或数据的问题，普通技术选择自主完成，不在交接处增加常规审批。

调研输出决策相关事实、真实未知和可用方案；架构选择满足当前功能的简单完整实现；开发贯通可用路径并持续保持简洁。简化角色拥有实际编辑权，可删除职责、状态和配置，内联错误抽象，或替换局部子系统；不必维护前任 agent 的设计偏好。它以当前代码、真实行为和必要验证为依据，允许结论是无需修改，不设删行、发现数量或重写配额。

已有项目可以大幅改变内部设计，落地按可验证的功能路径分批进行，保留真实用户行为与数据合同。决定委派纯精简目标时直接交给 simplify，由它持有调查、修改、检查与修复；主会话不先重复完整调查，小而明确的清理也可直接完成。基线应足以识别真实回归，而非把所有观察到的偶然细节固定成合同；检查材料同样遵守实际写入归属。开发与简化顺序交接耦合范围的写入权；发现具体失败后由当前 owner 修复或明确转交，不同时修改同一条实现路径。只改命名、格式或把函数切小，不足以证明降低了复杂度。

独立简化不等于独立验收：修改者须验证改动，主会话对完整请求和实际使用路径负责，必要时用只读 `review` 获得另一份判断；不能把简化者自称完成当作验收。最终比较的是当前理解与修改成本、职责和状态的必要性以及行为证据，最少行数和最多角色都不是目标。

以上五角色安排是结合用户偏好和本项目失败模式的工程推导，来源只支持其中的按需协作、简洁控制和执行反馈，未直接验证这条专家流程优于单 agent。新增的 [HERMES 预印本](https://arxiv.org/html/2610.07832v1)（2026-10-06）研究的是依赖驱动、按需激活的仓库组件 agent，并以执行和诊断反馈触发局部修复；它也承认额外成本及对依赖发现、运行反馈的依赖。该架构不是本项目的专家流水线，其 benchmark 结果不证明代码更简洁优雅，本项目不引入其运行框架。

## 干净代码与不过早抽象

[Parnas 原论文](https://www.cs.lafayette.edu/~gexia/cs301/resources/parnas.html)（1972，大学托管全文）主张按隐藏的设计决策分模块，而非机械切开处理步骤；作者还纠正了接口中的不必要顺序约束。本项目的推导是：可命名的职责、步骤或自造 invariant 不足以证明一个结构值得独立存在，agent 的实现偏好也不能自动升级为用户需求。

[Ousterhout 的原作者设计笔记](https://ramcloud.atlassian.net/wiki/spaces/RAM/pages/6848550/Software%2BDesign%2BPhilosophy)（2014 更新）反对薄层与调用者必须组合大量微小步骤的接口，强调隐藏复杂性与减少错误条件。[Metz 的 The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)（2016）说明错误抽象会随着参数和条件分支持续增重，可先内联并删除各自不需要的部分。这里采用总理解/修改成本作为判断，不把最少行数、一个文件或禁止 helper 当作质量定义。

[Armstrong 博士论文](https://dcatkth.github.io/thesis/joe_thesis.pdf)（2003，§4.3–4.4、附录 B §3.13）区分能够正确恢复的已知异常与未知错误，主张入口检查后信任内部数据。可迁移的是在确有正确动作的位置恢复、必要清理、保留原因；Erlang 的隔离/监督前提不能照搬成任意程序全进程崩溃。减少错误条件须通过更简单的语义或机制，不能把权限失败、损坏数据或未完成写入伪装成成功。

“只在反直觉处注释 why”以及不为假想故障添加恢复，是用户明确偏好。它们不是上述作者或所有厂商的一致结论；特别是 Ousterhout 支持的注释范围比严格 why-only 更广。本轮直接落实用户选择。

## 研究证据与行为评估

[Evaluating AGENTS.md v3](https://arxiv.org/html/2602.11988v3)（2026-09-29 修订）在 SWE-bench/CTXbench 上未发现 context 文件普遍显著提高成功率，并观察到更多探索、测试和平均超过 20% 的推理成本；作者支持记录代码中没有的非标准约束。其任务主要是 Python、指标主要是测试通过率，没有测量优雅或代码体积，长度消融也不能证明越短越好。故本项目减少错误默认和重复指令，而非追求字数阈值。

[Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)（2026-01-09）区分结果和轨迹，通常优先检查实际产出而非固定工具顺序。本项目保留安装/原生加载检查，真实任务另外核对完整行为、错误、架构必要性和维护成本。显式协作任务只验证协作能力，自然任务不以是否委派判优劣；固定检查通过不能证明全局最小或跨项目收益。

## 原生接入与版本边界

本轮本机版本为 Claude Code 2.1.302、Codex 0.163.0、Grok 1.0.52。CLI 原生帮助和本地随包文档是当前接入依据；旧 0.157.1/1.0.41 探针仍按历史版本解释，详见验证记录。

Claude 使用原生 CLAUDE.md、角色 frontmatter 和 skill。Codex 使用 dev profile 注入 developer_instructions 与角色 TOML；五个可选子角色保留必要的共同质量合同，因为角色字段会替换父字段。Grok 通过 --rules 追加根规则，角色原生 Markdown 另载；不能假定根规则完整进入子上下文。本项目保留少量角色合同重复，不建立模板合成器。[Claude subagents](https://code.claude.com/docs/en/sub-agents)、[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

Grok 1.0.52 随包 `docs/user-guide/16-subagents.md` 说明：发现用户/项目/plugin 角色时，spawn_subagent 提供 subagent_type 枚举。旧版本必须 Workflow 的限制不再写成通用要求；按实际 schema 选具名角色，缺该字段时才用 Workflow agent_type。工具限制及非空 MCP 继承仍须按实际运行证据判断，不能把发现角色等同于权限验证。[官方角色文档](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/16-subagents.md)

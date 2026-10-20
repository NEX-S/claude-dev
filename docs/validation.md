# 当前实现验收：最新实践核查与产品范围收敛（2026-10-19）

本轮核读 OpenAI 10 月 14 日维护实践、Anthropic 10 月 15 日评审实践、Opus 5.5 专用指南、xAI 10 月 10/12 日指南，以及 Loop/Graph v2 和编码协作论文，来源与采用边界见 [调研](research.md#三种常用模型的最新增量2026-10-19)。三端合并常驻清理/验收的重复要求，将已有项目精简改为决定委派后的职责安排，保留小清理由当前作者完成；在既有边界句消歧不猜测、转换或修复无合同的输入。Completion 明确进度汇报不代替推进或交付，必需后台结果须收齐。没有增加角色、固定专家链、图运行器、外层循环或依赖。

真实粗略目标试验又暴露了产品范围问题，随后仅修改三端 root/develop：必要产品答案是相应实现的依赖，等待期间继续独立工作，普通技术取舍仍自主。独立只读审查确认完整行为、作者自清理、错误可见、数据合同、按需专家与有效检查复用均保留，没有新增阶段审批。原始失败、修订前试验和最终修订探针分别保留，不用后一次成功覆盖前一次失败。

最终模板运行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`，49 项通过，31.968 秒，无跳过；当前原生版本为 Claude Code 2.1.303、Codex 0.163.0、Grok 1.0.62。三份 develop 格式、TOML、本地文件链接和空白另验。这些证明资源与原生加载合同，不是代码质量保证。

普通 `./install.sh --target all` 已发布最终三端版本，最后备份位于 `/home/nex/.local/state/claude-dev/backups/install-0oIiRZ`。21 份资源与当前源模板一致（原生链接转换另核），Codex 五角色注册正确，实际 `codex-dev --no-daemon debug prompt-input` 核实根规则精确加载一次。原有 `gpt-6.1-sol / medium` 保留，四份基础/设置文件的内容和权限未变，重复 dry-run 无变化。原生加载与模型试验分开验收，模型试验采用不可变 staged overlay，正常 HOME/auth，未复制凭证。证据保存在 `/home/nex/.cache/harness-current-research-20261019/`。

真实行为使用 Codex 0.163.0、gpt-6.1-sol/medium、同样原生 HOME 和权限，前后模板取自修改前实际工作树与本轮不可变快照，不用落后的 HEAD。实际 turn_context 与载入正文另核；所有有界运行及失败都保留。

- 小项目精简配对：同一 greeting seed 与自然请求，新旧都通过三项外验，最终源码相同，实际去掉无用途转发且没有新增泛化。旧版调用 simplify，86.105 秒自然完成；第一版修订由当前作者直接完成，41.551 秒。各一次且部分并发，仅说明这一次避免了委派、行为未退化，不证明普遍提速或旧版产物差。后续产品问题修订不改变这个明确小任务的合同。
- 粗略阅读清单首轮使用第一版修订：模型问内容类型后仍自行做浏览器版，并加入可选链接、筛选和删除。它实际操作页面并修正了一次检查假设，但到预定 180 秒限额仍无完整交付；180.434 秒终止，退出码 0 不作为成功，`timed_out=true` 和缺少 turn.completed 一并保留。
- 同一会话随后收到试验前冻结的范围更正：命令行、只存标题和已读状态、添加/列出/标已读、进程间保留。164.336 秒自然完成，模型自行删除旧网页、服务启动脚本和截图，采用标准库 argparse/SQLite 直接实现。主会话实际核读源码、README 和调用输出；独立副本按 README 验证空列表、Unicode 标题、空白拒绝、第二条目、跨进程列表、标已读和另一项状态保持，七项通过。它仍有单行标题限制等自定取舍，模块说明也不属于严格 why-only；不把这个产物宣称为全局最简或所有偏好都完全遵循。这个阶段继续使用原修订，不冒充最终规则的完整开发试验。
- 最终产品依赖修订另开新会话，提交完全相同的粗略任务：116.570 秒自然结束，明确询问记录内容及打开/保存方式，等待用户确认后再实现；项目为空、无 file_change。没有提交后续答案，所以它只验证澄清关口，不证明最终版本整个项目流程更快，也不是任务已经交付。

四条原生 session 的 root 正文均精确出现于一条 developer message；实际 turn_context 均为 gpt-6.1-sol/medium，续轮也相同。四个 trial 的 develop 读取命令均对应本轮快照路径，原始输出包含完整正文；旧版小清理的子角色来源为 simplify。主会话另外核实五个试验进程组均已不存在。

这些是定向观察，不是统计排名或跨模型质量保证。最终提问的推荐方案仍偏网页，不能等同用户已选择网页；它停止依赖实现正是本轮检查的对象。必要的研究/设计可以由主会话完成，任务没有外部决策未知时也不要求联网或叫齐角色。Claude/Grok 本轮验证到原生资源、发现/加载与安装，没有新增云端质量试验；前次大范围精简、连续需求和评审样本仍只支持各自保存版本。没有为追求成功继续改任务或挑选最好结果。

---

# 前次实现验收：标准库优先与合适的小实现（2026-10-19）

本轮按用户指令将依赖偏好写入三端根规则和全部十五个角色：优先标准库、平台内置与项目已有的合适能力；狭窄当前需求可用直接的小实现；第三方的功能或实现难度收益须抵消集成和长期维护成本；小实现保持当前用途。替换 root/arch 中原先偏向先考虑成熟库的措辞，避免相反默认。没有增加角色、流程或依赖，也不要求替换合适的已有依赖。独立只读审查未发现实质冲突。

执行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`，49 项通过，30.177 秒，无跳过。另核对全部角色携带规则、旧冲突措辞已移除、Codex TOML 和文档链接有效、空白检查通过。上述检查覆盖安装与原生加载合同，没有新增云端代码质量试验，不能据此保证未来模型总能作出最简依赖选择。

普通 `./install.sh --target all` 已发布 `claude-dev`、`codex-dev`、`grok-dev`，备份位于 `/home/nex/.local/state/claude-dev/backups/install-ttQnsC`。21 份已安装根规则、角色和工作流与源模板一致（Codex/Grok 的 develop 链接按安装器转为绝对路径）；Codex 五角色注册与 developer_instructions 正确，实际 `codex-dev --no-daemon debug prompt-input` 确认新根规则精确加载一次。原有 `gpt-6.1-sol / medium` 选择保留，四份基础/设置文件的内容和权限未变；重复 dry-run 无待改文件。检查和安装记录位于 `/home/nex/.cache/harness-dependency-preference-20261019/`。新开的开发入口会话使用新版资源。

---

# 前次调研验收：进攻性编程是否引入（2026-10-19）

本次范围是深入调研及引入判断。实际读取 Gonnerman、Brodwall、Hoffman 的作者原文，以及 Meyer、Armstrong、Fowler、Metz、Duffy、Ousterhout 的论文或作者材料；浏览抓取失败的两篇作者文章另经 HTTPS 直接读取，不以搜索摘要代替正文。定义差异、场景前提、与用户偏好的映射和采用建议见 [调研](research.md#进攻性编程与当前代码偏好2026-10-19)。

三端当前 root/develop/arch/dev/simplify/review 的独立只读审计确认：简洁与抽象准入、信任内部契约、避免假想调用者/边界、无恢复语义不添加兜底、错误保留原因、why 注释、未知 bug 不延长交付均已覆盖，没有必须新增的规则。保留必要功能、数据语义、事务与清理也与这些偏好相容。结论是采用合适思想、维持当前机制；“使用者按约定用、不自动适配未支持用法”的更明确措辞是可选消歧，不是已证实的规则缺口。

本轮只更新研究、验收记录与当前计划。运行模板指纹与调研前一致，没有新模型运行、安装或产品代码修改，因而未重跑前次实现的 49 项套件。文档文件链接和空白检查另行核对。作者经验不是控制实验；没有宣称能自动保证代码最少、bug 更少或某模型更优。

---

# 前次实现验证：真实反馈、验证复用与连续需求（2026-10-19）

本轮重新核读官方 harness/coding 指南、loop/graph 作者材料与技能/连续开发论文，取舍见 [调研](research.md#从实际开发反馈校准循环与验证2026-10-19)。三端 root、develop、dev/simplify 明确复用仍覆盖当前代码和输入的真实检查结果，按影响补验收；保留完整功能、作者自清理、错误可见、必要边界/事务/清理和 why 注释。工具失败依据实际错误或当前状态调整。没有增加角色、阶段文档、图框架、外层循环或自动挡位器。独立只读审查未发现实质矛盾，也未将行为约束误称运行期沙箱。

本地执行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`，49 项通过，30.772 秒、无跳过。三份 develop 的 skill-creator 格式验证通过。新增真实临时 HOME 回归确认升级保留已有 Codex model/effort、更新规则与角色、未设置时不新增默认值、基础配置不变且重复安装稳定。旧会话的 ultra 与现有 medium 默认值不能互相回推；没有证据确定旧 TUI 选择来源。

真实行为采用修改前实际工作树与修改后的不可变模板快照，不用落后的 HEAD。新旧均使用 Codex 0.163.0、gpt-6.1-sol/medium、同样原生 HOME 和权限，原生 turn_context 及子角色正文核实载入。评估经 `-c` 注入 staged 开发指令和五角色，未复制认证或替换原生根；实际安装入口另验。所有运行及失败原样保留，没有以重跑挑选最佳结果。

- greeting 自然小任务：新旧都直接完成三行实现，外部 3 断言通过，没有配置、依赖或专家流水线。随后同会话仅更正 README 拼写，两组均只改文档、业务源码字节不变，没有重跑业务检查。首轮新旧分别 33.536/27.483 秒，续轮分别 20.403/23.008 秒；这证明负对照没有退化，不证明旧版失败或新版提速。
- 已有 SQLite 账本的自然精简：两组都沿真实 CLI 删除 gateway/service/repository 转发、单后端注册、重复任务表示和无恢复动作重试，保留提交后输出、参数化 SQL、事务与连接关闭。各自通过同一 14＋8 项外验，README 和 existing.db 字节不变。新版 159.731 秒、旧版 156.850 秒，均正常退出、没有触发 300 秒实验限额。两组均实际读到对应 develop 并调用 simplify，父子实际为 Sol/medium。
- 同一产物继续增加 rename：任务文本和 7 项外部行为检查在续轮前固定，不规定内部架构。新旧均通过 7 项新增检查及原有 22 项，保留 ID、完成状态、Unicode/空白、数据格式、原库字节和失败语义。新版 54.277 秒、旧版 53.269 秒；实际在既有参数处理和 SQL 分支内修改，没有叠加第二套状态、存储或转换机制。

轨迹审计的限制同样保留：新版父会话仍重复读取旧实现，并在 worker 完成后重跑约六秒的小套件。父只收到 worker 总结，未展示核实并复用其原始工具输出；这可能是在补直接证据，不能只凭重复判浪费，也不能声称验证复用已生效。worker 修复测试连接的 ResourceWarning 后重跑有具体原因。单组各一次、部分并发运行，尚未证明普遍更快、更简洁或 medium 最优；不为追求这一例提速继续叠加提示规则。Claude/Grok 本轮验证到本地原生加载与发布，没有新增云端代码质量试验。

普通 `./install.sh --target all` 已发布真实开发入口，备份位于 `/home/nex/.local/state/claude-dev/backups/install-WsZVI3`。21 份根规则/角色/工作流与源模板一致，Codex 注册和 developer_instructions 对应安装文件，实际 `codex-dev --no-daemon debug prompt-input` 确认根规则精确载入一次。已有 Sol/medium 字符串选择与备份一致，四份原生基础/设置文件的内容和权限未变；重复 dry-run 无变化。各次 ledger 主机进程组均无存活成员。

[本轮证据](../artifacts/harness-feedback-2026-10-19/manifest.json)包含模板版本、实际命令、压缩原生轨迹、前后产物、固定外验、结果、过程审计、安装与加载检查。阶段一产物保存在 `ledger-*/delivered/`，`project/` 为 rename 后产物；不能混用阶段证据。临时实验脚本未成为产品运行器。新会话使用已发布资源；已有会话以自身实际载入状态为准。

---

# 前轮验证：整项目精简的范围与验收（2026-10-18）

针对把局部清理误当整项目完成的问题，三端 simplify 与 develop 增补完整范围的判断：先比较满足当前用途的最直接实现，优先取消最大的多余职责，按具体产品或架构结果验收。已有调用者、旧设计和测试本身不证明机制仍然必要。不新增角色、固定阶段、改动配额或运行机制；及时交付和作者自清理要求继续保留。

原生本地套件 48/48 通过（34.007 秒、无跳过），三份 develop 格式检查、TOML 与 diff 检查通过。普通安装已发布三端资源，备份在 `/home/nex/.local/state/claude-dev/backups/install-QAEBnD`；六份改动模板与实际安装逐字节相同，三端基础配置内容和权限未变，重复 dry-run 无变化。真实 `codex-dev --no-daemon debug prompt-input` 确认根规则载入一次、原生最高权限与现有配置层次保持；没有调用模型。证据在 `/home/nex/.cache/harness-architecture-scope-20261018/`。这些检查证明发布与加载，不证明措辞本身能让所有项目完成彻底精简；本轮三个项目使用各自代码与真实路径证据验收。

---

# 前轮验证：及时交付与按需专家（2026-10-18）

本轮移除实质项目默认再过独立 simplify 的要求，默认尽早贯通最简单完整路径，由作者自清理、必要验证后交付。专家只为具体未知、复杂度、明确精简目标或重要风险启用；项目规模不自动触发额外阶段。已知必需功能或数据失败仍要修复，未知 bug 和“极致”不要求继续穷举、审计或寻找下一个清理目标。三端 root/develop/dev/simplify 同步；未改安装器或新增运行机制。独立语义审查通过。

执行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`：48/48 通过，30.530 秒，无跳过。三份 develop 格式、Codex TOML、README/docs 本地链接与空白检查通过。覆盖范围仍是安装、原生加载/协议和模板合同，不能代替实际成品验证。

另以全新空项目向原生 Codex 0.163.0 提交一段自然任务：Python 标准库本地待办，添加、列出、完成、持久化并提供使用说明，不指定角色、架构或 CLI 形状。使用当前 staged 原生根规则与五角色，正常 HOME 认证，仅本次指定 gpt-6.1-sol/medium；原生 session 核实模型、effort 和精确根规则载入一次。61.341 秒正常 exit0，180 秒试验上限未触发。产物为一个直接实现 add/list/done 的 `todo.py` 和 README，以 JSON 持久化，未新增框架、依赖、插件系统或专家流水线。边界文件格式检查及先写后替换有当前数据用途。轨迹显示实施后实际检查源码与行为；没有观察到 develop 读取，不能宣称所有流程条款都被逐项遵循。

独立验收按交付 README 的真实 CLI 在副本运行：空列表、添加 Unicode、添加含空格标题、新进程保留两项、完成一项、完成状态持久化且另一项保留，6/6 通过。未增加未请求边界或改写模型产物；模型自测不代替该验收。自然进程及已观察后代均无存活残留。原始 trace 中两条旧全局配置字段被忽略的警告保留。这是一个小型从零成品实例，没有旧/新或 effort 对照，不证明大项目交付时长、提示词因果收益或 medium 最优；Claude/Grok 本轮未新增云行为试验。

真实 HOME 已执行普通 `./install.sh --target all` 发布，旧受管资源备份到 `/home/nex/.local/state/claude-dev/backups/install-Hl6DJP`。三端安装资源与源模板一致；实际 `codex-dev --no-daemon ... debug prompt-input` 核实新根规则载入，并接受 README 中 medium 单次覆盖命令，未调用模型。原生三端基础配置的内容和权限保持不变，profile 未新增模型/effort 固定值；重复 dry-run 无待写入或备份项。新会话使用新版资源。

本轮检查与安装记录、真实原生轨迹、任务、源码、模板指纹、运行退出和独立验收见 [证据目录](../artifacts/harness-delivery-2026-10-18)。挡位建议及社区材料局限见 [调研](research.md#gpt-61-sol-思考挡位与快速交付2026-10-18)。此前试验继续按其保存版本解释。

---

# 前轮验证：作者自清理与社区取舍（2026-10-18）

本轮将项目定位明确为 Claude/Codex/Grok 原生 harness 上的个人偏好配置。三端 dev 的完成标准增加作者交接前沿真实路径亲自做有益精简并复验；保持有用结构和有意局部重复，自查合并在原实现任务中。根规则与 develop 同步，Codex 角色描述注册一致。独立 simplify 继续提供较大范围的新判断，不替代作者自查。

社区研究直接读取原仓库规则、作者文章和官方文档，采用与舍弃的理由见 [社区研究](research.md#社区开源实践与选择性借鉴2026-10-18)。只吸收作者自清理，以及优先已有能力和合适数据形态；未安装外部插件或运行其代码。相似设计与作者宣传不作为本项目效果证据。

执行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`：48 项全通过，31.049 秒，无跳过。三份 develop 的格式验证、Codex TOML、相对文档文件链接和空白检查通过。独立语义审查确认自清理未新增角色/报告/改动配额，也未削弱完整需求、错误可见性和 why 注释。收尾将根规则中重复的检查/复验语句合并后，重新核验相关加载与合同。

本轮没有新建云模型实验。前轮真实模型试验绑定各自保存的旧模板指纹，不能用它们宣称当前新增自清理条款已证明改善代码质量。真实 HOME 未发布本轮模板；需要时按 README 安装命令启用。下面为前轮证据，按各自版本解释。

---

# 前轮验证：自主流程与主动简化（2026-10-18）

本轮在上次质量取舍规则上新增 research/simplify，三端共五个可选角色；把粗略 goal 到本轮功能澄清、必要调研设计、实施中持续简化、独立精简和真实验收落到 root/develop。已有可用项目的精简直接交 simplify 持有调查、改动、验证和修复；阶段可合并可回退，不预建未来功能。研究与证据边界见 [调研](research.md)。下面的前轮记录不自动覆盖当前版本。

## 当前本地实现与加载

最终模板执行 `CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`，48 项全部通过，30.389 秒，无跳过。覆盖安装、备份清理、五角色原生发现/注册、Codex prompt-input、Grok inspect/离线启动和 Claude localhost 协议。三个 develop 格式验证通过；最终模板已在临时 HOME 安装并通过重复 dry-run。安装器未为新增角色修改，真实 HOME 未发布本轮模板。

新增 Claude 协议检查证明 research 只暴露读取与 web 工具，simplify 实际 Write 成功，结果回到协议服务。当前 2.1.302 对 dev/simplify 请求省略 Grep/Glob，检查实际必须具备 Read/Edit/Write/Bash 且不超出允许集合；research/review 仍检查精确集合。它是原生能力测试，不是云模型质量测试。

第一次完整检查曾发现 Grok 两个入口都没有 simplify：描述中的未引用冒号使原生 YAML 发现失败。修正三端描述后重跑通过，没有放宽发现断言。后续根据实际模型轨迹修订工作流，再完整运行上述最终 48 项。

## Codex 显式简化能力

冻结的 Python/SQLite 任务账本在运行前已通过 14 项既有行为和 8 项已有数据/失败检查。原生 Codex 0.163.0、父子 gpt-6.1-sol/medium、正常认证、无模型或 effort 覆盖，以 staged 原生配置载入新角色；明确要求使用命名 simplify。

原生 spawn_agent 选择 simplify、新上下文子角色精确加载正文并实际 apply_patch。自然 exit0，164.364 秒，预定上限 180 秒。最终仍通过同一 22 项，README 和 existing.db 逐字节不变。实际入口删除 Gateway/Service/Repository 转发、单后端注册与配置/路径/连接包装、重复 TaskRow/Task/mapping 和 done/marker 状态，以及无恢复动作的读取重试；最终为 argparse 直接操作 SQLite，再输出 JSON/Markdown。必要校验、参数化 SQL、事务、连接关闭和原始错误保留。

父会话一次自定检查误将 SQLite 只读 URI 当成 CLI 已支持路径，后来修正检查而未修改产品迁就它，失败记录保留。该试验使用最终自然路由/基线修订前的专家模板，精确快照和后续差异另记，不能冒充最终模板的自然行为。

## Grok 自然选择与未交付

两次独立新会话使用逐字节相同的自然任务、seed、22 项验收和 180 秒上限，正常 HOME、默认 grok-4.7，无模型或 effort 覆盖。任务不指定角色。第一次在完整调查后继续固定失败是否建库、精确输出字节等未要求细节，到截止无源码改动或父交付；还使用固定的项目外 scratch 路径，违背分配范围。

据此作一组窄修订：可用项目精简直接交 simplify，调查/改动/验证/修复由一个 owner 完成；基线不固化偶然 quirks，不在改动前穷举假想边界；自行创建的 scratch 使用分配范围内的唯一路径。第二次自然选择 subagent_type=simplify，新上下文加载精确角色正文一次，实际工具含编辑/执行，继承 grok-4.7/high；父不再先重复整个源码调查。

第二次仍在 180 秒内未编辑或交付：子角色继续基线调查，两次尝试读取 sqlite3 内建 context manager 源码失败，并在范围外创建检查临时库。两次外验都仍 22/22，但只是原绿色基线，没有精简收益。host PID/进程组已不存在；第二次残留 child metadata 显示 running、没有完成事件，明确视为 host 截止后的未成功终结，不能据它称仍活或已完成。原生流未可靠区分父子事件，因此只记聚合工具数。

该小样本支持“修订后观察到自然路由和能力加载”，不支持交付成功、普遍效果或因果结论。失败完整保留，不反复调参覆盖原结果。

## 最终模板自然任务

最终模板另做一次自然 Codex 会话，使用与 Grok 自然任务逐字节相同的 task 和 seed，不指定角色；默认 gpt-6.1-sol/medium，无模型或 effort 覆盖，预先固定 300 秒上限。自然 exit0，110.794 秒，child 有明确完成记录，父执行最终验证并交付。冻结 22 项全部通过，README 和 existing.db 逐字节不变；实际实现删除同一组转发、重复表示、注册与恢复包装，真实 CLI 已接入直接 SQLite 路径。

父只列目录并读取 develop 后自主选择 agent_type=simplify。它使用 fork_turns=all，派发前未实施或读取实现设计，但继承了前置上下文；后续三次消息的原生正文不可直接核验，因此不把这一结果称为严格无继承的新上下文审查。实际具名子任务、编辑、完成与父验收均有证据。

模型保留一个标准库真实 CLI 测试文件，6 项一次通过，检查材料位于项目内临时目录；未观察到需要失败后修补的产品缺陷。测试仍固定了新库 ID 从 1 开始、空白标题不创建库等部分自定选择，不能据此次精简声称已完全消除自增合同倾向。父会话仍有一次不必要的项目外 AGENTS 搜索，stderr 被重定向且 exit2，未改变产物；该无效动作在原始轨迹中保留，不算有用验证。原始源码、最终源码和运行期证据见 [最终自然实验](../artifacts/harness-experts-2026-10-18/codex-natural-final/assessment.json)。这不是与 Grok 的模型胜负对照，也不验证全部五阶段的自然选择。

## 证据与结论范围

本轮 [证据目录](../artifacts/harness-experts-2026-10-18/local-suite.json) 保留最终本地日志、模板指纹、临时安装、冻结输入、原生轨迹、原始与最终产物及每次外部验收。Codex 显式能力见 [assessment](../artifacts/harness-experts-2026-10-18/codex-simplify/assessment.json)，Grok 两次见 [before](../artifacts/harness-experts-2026-10-18/grok-natural-before/assessment.json) 与 [after](../artifacts/harness-experts-2026-10-18/grok-natural-after/assessment.json)。未复制认证或全局配置，也未用另一种模型冒充该端行为。

独立审查覆盖三 root、三 develop、十五角色和注册，后续窄修订也通过审查：完整需求、必要边界、事务清理、有价值抽象和 why 注释均保留。已有项目的一次精简能力不能证明所有模型、所有项目都达到“极致”；代码质量仍需看当前行为、结构必要性和维护成本，角色数量、行数和自称完成不是验收。

---

# 前轮验证：质量取舍优化（2026-10-18）

本轮修改的是三端根规则、arch/dev/review 与 develop 的决策默认：先降低设计责任与状态，区分真实要求和 agent 自定机制，按实际风险验证，主会话可直接实施，必要时才协调与独立评审。研究来源和推导见 [调研](research.md)。本节是当前证据；分隔线以下为 9 月历史，不能据历史通过推定新版本效果。

## 本地与原生加载

本机 Claude Code 2.1.302、Codex 0.163.0、Grok 1.0.52。最终执行：

```sh
CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

45 项全部通过，29.252 秒，无跳过。包含 28 项安装检查、模板合同、真实 Codex prompt-input、Grok inspect/离线启动及 Claude localhost 原生协议；它们不调用云模型，也不证明长期自主代码质量。三个 develop 均通过 skill-creator 的格式验证；TOML 解析、相对文档链接与空白检查通过。

修改前基线为 39 通过、5 跳过、1 失败。失败是 Grok 1.0.52 已在无缓存认证时自动发起原生 authenticate 请求，隔离网络下显示 Connecting，旧测试仍等待 Login 按钮。测试改为观察真实认证请求、没有进入 Resume、没有新认证文件；正例继续核对普通/开发入口共享假缓存认证及配置原样，未延长超时。此修正不改变实际账号。

全目标安装在 `/tmp/claude-dev-staged-install-wmys3p07/home` 成功，重复 dry-run 无变化。真实 HOME 未发布本轮新模板；现用入口需按 README 安装命令更新。安装机制、权限、认证和模型选择没有新增行为。

## 真实 Codex 旧/新配对

使用相同冻结任务：从空目录实现 Python/SQLite 单人任务账本，支持 add/list/done/export、跨调用持久化、中文空格和失败非零。外部 14 项在模型运行前固定。两次为全新项目与原生会话、gpt-6.1-sol/medium；旧先新后，同一原生 HOME/工具/权限，不读取或复制认证。新旧正文和角色注册通过原生 -c 覆盖，实际 prompt/rollout 中核对输入。它是 staged 原生 overlay，未冒充真实 HOME 已安装 wrapper。

两份结果均 14/14，通过真实 CLI。旧版生产/测试为 81/77 物理行，新版 83/78，另有 26 行 README；两者都使用 argparse、一个执行函数与 sqlite3 事务，提交后才输出，没有 service/repository 框架或吞错。生产注释解释提交失败不能产生成功输出的原因。没有派发角色或读取 develop，因此此任务不覆盖子角色行为。

本次没有观察到明确结构收益，不据此宣称新版更短、更快或普遍更好。两者仍把重复 done、无输出及部分精确格式写入自测，使用 AUTOINCREMENT；其中有些是合理选择，但不是用户逐项要求。这个局限说明规则修订不等于已消除模型所有自增合同的行为。

旧版原生已 turn.completed 且 final 落盘，但外层记录退出码时误用 zsh 只读变量，原生退出码未保存；外层 exit1 单独保留，不归因模型。新版原生 exit0。没有重跑旧版来改写数据。

## Claude/Grok 小任务负对照

任务采用现有 greet.py：str 姓名去首尾空白，空白用 World，其他内容保留。按原生参数/项目资源加载 staged 根规则、角色和 skill，保持原生模型与账号配置；不是已发布 wrapper 的效果测量。

Grok 1.0.52 init 为 grok-4.7，用量标记 grok-4.7-build；自然 exit0，外部 3/3。只加一行，无计划、委派、Workflow、依赖或持久测试文件；一次进程内检查十个输入，随后读取最终源码。角色发现来源是项目原生 md，develop 没有被小任务加载。它支持直接处理小改动，不证明复杂项目收敛。

Claude 2.1.302 在普通原生配置根与实际 `.claude-dev` 根各做一次独立条件试验，均为 Not logged in / is_error=true、自然 exit1，API 时间和 token 为零。源码未变，外部 1/3 是未实施基线，不是模型质量失败。实际开发根的原生 prompt_snapshot 定向核验显示新根规则精确出现一次、新 develop 链接存在、旧根与默认个人 CLAUDE 路径未叠加；init 列出三角色及 develop。可以证明加载，不能证明 Claude 模型行为。

另一次有界原生会话实际通过 `spawn_subagent(subagent_type="review")` 直接调用具名角色，不用 Workflow。父 schema 的枚举为 arch/dev/review；子原生记录为 review，精确加载新角色正文一次，工具仅 read_file/list_dir/grep。子审查三项契约无缺陷，父收到 SubagentCompleted 并完成汇总，自然 exit0；前后项目文件哈希不变，未执行用户代码。父子均用默认 grok-4.7/high，未覆盖模型或 effort。该证据验证当前具名路由、review 工具边界和父汇总，不扩展为非空 MCP 继承或复杂编码收益。

## 证据与结论范围

本轮原始输入、原生输出、产物和检查已保存在仓库 [证据目录](../artifacts/harness-update-2026-10-18/validation.json)，不依赖临时目录长期存活。Codex 配对保留完整 native JSONL 与最终代码；Claude 只保留定向加载证据，不复制全局配置或认证。

独立审查覆盖三根规则、三 develop、九角色，无实质未解决发现。新规则保留完整范围、必要边界与有价值抽象，并对研究、测试和可选改进给出终点。一次小任务或规则审查不能保证“极致”或普遍跨模型效果；没有以新增框架、评分器或重复维修实验来制造通过。

---

# 历史验证（2026-09-27 至 2026-09-28）

# 当前验证

核验日期：2026-09-27 至 2026-09-28。当前实现、恢复出的历史协议证据和真实模型试验分别记录；历史通过不自动覆盖后续修改。

本轮审查已完成。三个开发入口的最高权限和原生角色修复已经安装并验证；规则设计有依据，但真实任务仍出现边界遗漏、共有的多余包装和预算内未交付，不能承诺持续产出“极致干净且完整正确”的项目。下文保留全部通过、失败和观测限制。

## 当前验证范围

本轮将 Codex/Grok 从独立配置根改为原生配置叠加，并按最新要求将三个开发入口默认设为最高权限、关闭 CLI 独立 sandbox。安装器回归、实际安装后的 CLI 加载检查和交互启动对照分别验收；它们不等于真实 OAuth 或模型任务成功。

当前测试命令：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

最高权限改动后的默认套件用时 11.866 秒；随后 Grok 角色修复后的同一套件再次通过，用时 11.262 秒：

```text
Ran 45 tests
OK (skipped=5)
```

实际通过 40 项：安装器 28 项、Claude 静态合同 4 项、Codex 原生/静态 2 项、Grok 原生/静态 5 项、内存协议端点 1 项。默认跳过的 5 项 Claude 原生协议检查已单独获准执行：同一个 `test_cli.py` 的 5 项原生检查和 1 项内存协议检查全部通过，耗时 4.329 秒、退出 0，无跳过。两次执行合计覆盖当前全部 45 项不同检查。`git diff --check` 通过。最终日志及七个被审查文件的 SHA-256 保存在 `/tmp/harness-permissions-i3gmdrh_/`。

原生协议检查使用临时 HOME、真实 Claude Code 2.1.283 与 localhost 固定响应，不调用云模型。权限修改前的 42 项版本也已完整验证：临时观察器在原测试调用结束后仅保存请求正文，不改变响应或断言、不保存认证头。直接读取请求体确认默认 CLAUDE/AGENTS 两种隔离场景均保留项目指令；直接 review 和具名 review 子会话均加载完整根规则，工具恰为 `Read/Grep/Glob`；具名调用具有主会话、子会话、返回主会话三个请求。原始日志及请求保留在 `/tmp/harness-native-M2Bh7glH/`，配套源码快照绑定当时工作树。上述场景在新的最高权限 wrapper 下再次通过；这些协议记录不是模型自主协作或代码质量的证据。

最高权限专项证据如下：

| 入口 | 原生有效行为 |
| --- | --- |
| Claude | fixture 不再自行添加 bypass；init 确认 `bypassPermissions`，实际 Bash 写入成功。仅移除 wrapper 的 `sandbox.enabled=false`、保留 bypass 后，同一路径被有效 sandbox 拒绝，返回 `is_error=true` 和 `read-only file system`，文件未创建 |
| Codex | 临时安装的 `debug prompt-input` 对照确认普通入口为 `read-only / on-request`，开发入口为 `danger-full-access / never`；基础配置、认证和历史保持原样。真实 HOME 发布后的同一原生命令再次确认 `danger-full-access / never` 和完整根规则 |
| Grok | 离线新 session 从基础 `ask / read-only` 切换为 bypass，原生日志确认 `sandbox_profile=off`；用户模型/effort 参数保留。此项验证启动和有效配置，没有执行云模型工具任务 |

独立评审对照本次修改前的七文件快照，直接核对最终源码、完整回归、原生输出及 Claude 失败反证，无遗留发现。已实际执行 `./install.sh --target all` 发布三个 wrapper，备份为 `/home/nex/.local/state/claude-dev/backups/install-IpyGgW`。主线程逐字节核对实际文件、0755 权限及 PATH 解析，重复 dry-run 返回 `No managed files changed.`；发布证据在 `/tmp/harness-permissions-i3gmdrh_/real-install/`。此项权限要求已完成，后面的整体代码质量效果验收仍单独记录。

安装器经非作者终审，无未解决发现。独立临时目录复验确认：自定义根不匹配时发布前失败；旧开发认证链接及其目标保留；旧开发配置保留；Grok 三个新角色在连续清理安装后仍存在；再次安装全快照不变。

## 原生配置叠加的验收合同

- Codex wrapper 使用 `--profile dev`，Grok wrapper 读取开发正文后使用 `--rules`；两者不改原生 HOME，保留用户参数。Grok 读取文件失败必须在启动前退出。
- 普通安装不改变原生基础配置、认证、信任与历史。旧开发目录的认证文件或链接、原生配置及历史保留；安装不再支持凭证共享选项。
- Codex profile 加载完整开发规则、绝对工作流路径和三个绝对角色路径；基础模型、provider 和项目指令继续由原生配置加载。develop 不被当作已注册全局技能。
- Grok 从普通用户根发现三个角色，保留普通安装时的其他角色及可信项目规则。`inspect` 不显示最终系统提示词，不能据此证明规则注入或实际子调用工具池。
- 清理安装必须保留新管理的 Grok 角色与 Codex `.system` 资源；再次安装幂等。备份、路径边界、失败前预检和 dry-run 不写入同样适用于新布局。

`--profile` 不适用于 Codex 的所有管理子命令，登录与退出使用普通 codex。CLI 无模型检查不启动自定义子 agent；Codex 0.157.1 的角色应用忽略 sandbox_mode、approval_policy 和 agents.enabled，子角色继承父权限。交互探针只使用临时 HOME 和假凭证，不修改真实账号。

## 最佳实践审查后的证据边界

本轮修复了三类提示词与配置问题：明确主会话的复杂任务协调作用域，放宽 Codex 角色过窄的抽象条件，删除 Codex 角色中不被 0.157.1 应用的权限/递归字段。三端角色职责及按需工作流没有扩成新的框架。独立审查已接受这些修正，完整回归结果见上文。

Codex 字段结论依据同版本生产源码和上游测试：角色只投影受支持的指令、模型及部分可禁用能力；子配置保持父权限。原生本地检查验证安装和根提示词，不证明已运行自定义子 agent。

Grok 1.0.41（4220f3b224a6）的真实会话保存了系统提示词和工具 schema；普通 `spawn_subagent` 没有具名角色参数。原生 inline Workflow 已通过 `agent_type: review` 完成真实子调用，metadata 确认独立新上下文和 review 类型，实际读取角色文件并正常完成。首次探针的子工具恰为 `read_file/list_dir/grep`，但父调用同时禁用了 `search_tool/use_tool`，因此不能把工具边界归因于角色定义。该检查还发现子会话只有角色正文，没有入口 `--rules` 注入的公共质量合同。五个 Grok 自动测试只覆盖声明、发现、参数错误和离线启动；这些运行期差异不能用静态通过代替。

已在三个 Grok 角色内加入与 Codex 相同的简短质量合同，并在根规则、私有 develop 和说明文档明确原生具名调用、完成判断和句柄区别，不新增 runner、持久 Workflow 脚本或安装时拼接器。七文件独立审查及完整默认回归通过；后续发现的工具边界问题另用下述 deny 配置修复。真实 HOME 已发布，备份为 `/home/nex/.local/state/claude-dev/backups/install-xq1ElQ`；逐字节核对三个角色、工作流及根规则的绝对链接，重复 dry-run 无变更。修复、检查和发布证据在 `/tmp/harness-grok-profile-fix-0xn1omop/`。

安装后的三角色并行探针 `/tmp/harness-grok-roles-vkc9vado/` 确认三个独立新上下文均逐字加载当前角色正文与公共质量合同。review 实际读取角色文件；arch 实际以 `web_fetch` 读取 Python 官方 csv 文档；dev 实际写入、读取并执行字节断言。没有父工具过滤时，review 的实际工具为 `read_file/list_dir/grep/search_tool/use_tool`，arch 再增加 `web_fetch`，但没有 `web_search`。父 MCP 为空且没有子调用 MCP；这些记录只证明 meta 工具暴露，不能据此认定真实远程 MCP 可访问或 `mcpInheritance: none` 失效。角色层原生 deny 字段的后续验证见下段。

后续未过滤父工具的真实探针确认原生 `disallowedTools` 可以在角色层排除这两个 MCP meta 工具：父工具定义仍保留二者，review 子工具恰为三个读取工具，并实际读取、正常完成，Workflow state 为 complete。live 使用 YAML block list；最终模板的单行数组另经实际 inspect 选中项目角色确认解析，mapping 类型负对照则回退用户角色，说明仅检查 exit 0 不够。arch/review 各新增一行原生配置，既有测试新增对应断言；45项默认回归为40通过、5预期跳过，独立复核无遗留发现。已发布到真实HOME，备份 `/home/nex/.local/state/claude-dev/backups/install-Y2chB8`，三个角色字节均与模板一致、重复dry-run无变更，证据 `/tmp/harness-grok-deny-_00omi5s/`。新增deny后的arch和完整父会话聚合已用下述交互PTY验证；非空MCP继承尚未验证。

上述未加 deny 的 headless 探针中，三个 host result 都是 success=true/cancelled=false，所有 slot 均 done，但 Workflow 最终状态是 cancelled，result_summary 为空。父模型在子任务结束前已经结束自己的 turn；实际进程退出 0、耗时 115.13 秒，未触及 300 秒上限，也没有发出取消调用。headless 输出混合父子内容，最终文本是 arch 输出尾部，不能当作父会话完整验收报告。当前证据没有说明取消原因；该运行方式的聚合完成未通过。原生费用 $0.06849912。

最终已安装配置的交互 PTY 探针现已完成，证据 `/tmp/harness-grok-pty-6w7vscmq/`。父会话 `01a0e3d8-aeb7-71f0-8145-70759eea62fe` 使用默认 grok-4.7/xhigh、bypass/off，无父工具过滤；三个新上下文逐字加载角色正文和公共合同，实际并行，所有 child 均 success=true/cancelled=false，Workflow `wf_01a0e3da22da7210a97ea69581026e19` 为 complete。review 工具恰为三个读取工具，arch 再加 `web_fetch`，父会话仍有两个 MCP meta 工具。arch 实际读取官方文档，dev 文件字节断言通过。原生完成通知触发后续父 turn，父会话读取完整 state/journal 并报告全部结果；没有外部伪造继续任务。任务约 181 秒结束，但最初 PTY 尺寸为零，终端修正审批使空闲 CLI 的观察和回收超过 300 秒，因此不记作有界墙钟时间通过。这个交互结果补齐角色和父报告证据，不覆盖旧 headless 取消，也不证明非空 MCP 继承或 `web_search` 可用。

本次恢复重新区分执行环境：沙箱内 socket.socket() 仍返回 PermissionError / EPERM，经批准的沙箱外探针已成功绑定 localhost 临时端口，随后完成上文原生协议检查。因此原先的 socket 阻塞不能继续作为所有验证无法运行的理由。真实任务、同条件对照和后续变更的产物与轨迹现已取得；它们支持部分能力，也复现了缺陷。对于“能否持续产出干净、优雅、无冗余、不过早抽象的项目”，这些有限样本不支持效果保证。

本次恢复已获准在沙箱外执行 `./install.sh --target all`，六个待同步受管单元更新成功，备份为 `/home/nex/.local/state/claude-dev/backups/install-eOA3Gq`。该命令未启用清理；逐份核对三端已安装根规则以及 Codex profile 注册和三个角色内容均与当前模板一致，再次 dry-run 返回 `No managed files changed.`。当前模板已在真实开发入口生效；最初Claude默认模型试验使用同版本临时安装，后续deepseek-flash试验使用已安装的真实入口。

## 完成条件核对

此前独立静态终审覆盖三端根规则、全部 arch/dev/review 定义、三个 develop 文档以及 README/设计声明，并修正了 arch 职责中把读取命令一并禁止的措辞。后续真实调用发现并修复 Grok 公共规则未继承的问题，还揭示了工具边界和 headless 聚合的未决项；因此该次静态终审不能代替当前运行期验收。

| 目标所需证据 | 审查结论 | 证据边界 |
| --- | --- | --- |
| 规则符合有界委派、按需上下文、真实验证和不过早抽象原则 | 源码、一手资料、静态审查和部分实际轨迹支持；原生字段与角色缺口已修正 | 合理指令不能保证模型每次遵循或完整验收 |
| 清楚小改动直接完成，复杂工作由主会话统筹 | 三端简单任务通过；Codex/Claude显式任务有真实并行、集成与review；Grok复杂任务在900秒内未交付 | Claude/Codex显式任务曾需恢复；Grok只有部分实现，无独立review或最终报告 |
| 三端角色能力与文档一致 | Claude实际dev/review工具池通过；Codex具名角色执行；Grok最终角色、工具和交互聚合通过 | 非空MCP继承、Grok web_search、headless聚合无通过证据；Codex角色只读依赖约定 |
| 完整实现要求且不弱化检查换取通过 | 固定原47成绩保留；外部反例推动判定器扩至58项；模型产物仍有已确认缺口 | Claude长CSV字段失败；自然对照三份有边界缺陷；Grok仅25/47，不能称全部正确 |
| 抽象服务当前需要，后续修改不造成无关退化 | Codex两阶段局部维护通过；校准能接受有效helper、指出无用途泛化层 | 四份自然产物均保留可简化的旧工厂包装，没有结构优势证据 |
| harness 相比普通入口改善开发效果 | 两对Codex中，开发入口的事后边界成绩更好，主会话token开销也更大 | 四次原47项均通过；小样本、事后补证及运行观测限制不足以证明普遍提升 |

本轮审查结论是：规则方向合理，已修复和安装的权限及角色改动有实际证据，但“持续产出极致干净、无冗余且完整正确的项目”不成立为已验证承诺。安装与判定器的可操作问题已修复；作为实验对象的模型产物保留成功与失败，不为了提高成绩继续修补。这个结论结束本轮审查，不表示所有被测开发任务都通过，也不以增加常驻提示词或通用调度框架掩盖失败。

## 当前原生启动与真实发布

Codex 0.157.1 的实际安装入口通过 `debug prompt-input` 对照：开发规则只在 profile 启用时出现；用户 override 和项目 AGENTS 保留；基础 developer_instructions 按原生语义被覆盖。故意损坏基础模型类型或 provider 后，开发入口仍由原生校验拒绝，证明基础层没有被私有根隔离。角色注册指向真实安装文件，但未启动子 agent，不能据此声称其全部字段或工具权限生效。

另一次 Codex 断网 PTY 窄探针使用实际临时安装、假 API key 和已信任项目：普通 codex 与新 codex-dev 都进入输入界面，没有登录菜单、目录信任提示或配置错误。默认认证内容、权限、mtime 和基础配置内容保持不变。只回应终端查询，未提交 prompt 或触发 OAuth；两进程已回收，临时目录已清理。这证明本地启动分支一致，不证明真实 OAuth 服务端有效或模型调用成功。

Grok 1.0.41 的实际入口 `inspect` 对照确认普通与开发入口使用同一配置来源，发现三个开发角色及既有用户角色，保留可信项目指令。断网 PTY 使用临时 HOME、按原生 schema 构造的假 OIDC 缓存及首次启动迁移标记：普通 grok 和实际 grok-dev 都到达包含 `Resume session` 的欢迎界面，无 `Login with Grok`；强制使用缺少认证的旧私有根则出现登录页。没有输入任务或调用模型，默认配置、假认证及既有角色内容不变。此项校准本地登录分支，不验证真实账号或服务端认证。

真实 HOME 执行 `./install.sh --target all --clean-legacy --dry-run` 退出 0。随后实际执行相同命令（去掉 --dry-run）在任何发布前退出 1：

```text
EROFS: read-only file system, access '/home/nex/.codex-dev'
```

当时前后核对 15 个关键路径的 inode、类型、权限、大小、mtime/ctime 和链接指向均不变；范围包括三个 wrapper、认证、基础配置、新 profile 位置和备份目录。该沙箱执行没有完成 HOME 升级或清理。

随后用户在普通终端成功执行 `./install.sh --target all --clean-legacy`，生成备份 `/home/nex/.local/state/claude-dev/backups/install-wVVfai`。助手对真实 HOME 的只读复核确认：三个 wrapper 均在 PATH、可执行且采用新实现；三个角色和 develop 文档完整；Codex dev.config.toml 包含开发规则及存在的角色文件路径；11 个已知旧路径均已消失；四个 Codex/Grok 默认与旧开发配置的 MCP 数均为 0；Claude 旧扩展配置键与用户插件注册已清空；Codex skills 仅剩原生 `.system`。重复 `--target all --clean-legacy --dry-run` 退出 0，输出 `No managed files changed.`。真实安装与已知旧用户扩展清理现已完成；这次复核没有调用真实账号或模型。

## 之前的迁移验证

切换到原生配置叠加前，完整套件为 41 项：37 项通过，4 项 Claude 原生检查跳过。其中包括独立配置根和凭证共享方案的检查；这些旧结果不替代本轮回归。

先前的三端清理回归验证了恢复备份、链接目标不变、认证与历史保留，以及 `.system`、旧 override 和直接发现的插件处理。真实 Codex/Grok 在临时配置副本中各移除两个 MCP；非 MCP 配置语义及 `0640` 权限保留。对本机 Codex 配置副本清理四个 MCP 也保留其他值及 `0600` 权限。15 秒超时探针确认整个子进程组被回收，未发布 profile。

旧版本在真实 HOME 上的两次 dry-run 分别核对 173 和 142 个相关路径，内容、权限与 mtime 均不变；这只是预览不写入的证据。此前真正执行安装返回 `EROFS: read-only file system, access '/home/nex'`。之后用户在普通终端安装了三个旧入口，但仍反馈登录提示，促成此次改用原生配置叠加。

历史假 API key 实验确认文件链接可复用部分认证操作；它没有证明真实 ChatGPT/OAuth 的登录与刷新流程，也不足以验收交互体验。凭证链接机制现已从安装器移除。认证由普通 CLI 的配置根负责，无需再维护独立根之间的同步。

下面的 Claude 协议、判定器和真实模型记录来自前一阶段，按各自版本保留证据边界。

## Claude 安装专项检查

本轮安装回归先在修复前复现，再验证修复：FIFO 和链接 FIFO 不再阻塞读取；合法 constructor 用户键保留；显式 null 和非字符串排除项在发布前被拒绝。排除目标使用安装进程 HOME，独立于安装目录；覆盖物理路径解析、glob 字面匹配和反斜杠 HOME 的明确拒绝。

路径转义另以 Claude 2.1.283 内嵌的实际 picomatch 验证：93 个可用 ASCII 路径字符的自身匹配、近邻不匹配、项目子目录不匹配均符合预期。这只证明匹配表达式；完整原生加载仍需下一节的 CLI 检查。

## 恢复出的原生协议证据

已读取本地 Claude 会话 `7e0aea7a-5683-4321-a21b-c1f086fa2b61` 的原始记录。2026-09-26 的工具输出（jsonl 第 279 行）为 `Ran 20 tests; OK (skipped=3)`，随后 `Ran 4 tests; OK`。这不是摘要中的自述。

该会话先复现默认 `.claude` 指令经祖先目录扫描进入开发 profile，再加入 settings 排除项，验证当时的默认指令隔离、直接 review 和具名 review 子调用。另一次真实 CLI 请求探针（第 398 行）获得三个请求、退出 0：review 工具恰为 Read/Grep/Glob，根 CLAUDE.md 出现在子会话的指令上下文中。

当前 fixture 进一步分开 CLAUDE 与 AGENTS 回退两种场景，分别核验默认指令被排除、项目指令被保留；安装目录与运行 HOME 不同，HOME 含 glob 特殊字符。这些新增场景已在本次恢复中动态通过，当前证据见上文，不再依赖旧版本结果。

沙箱内创建 TCP socket 返回 `PermissionError: [Errno 1] Operation not permitted`；本次已获准在沙箱外运行。复验入口：

```sh
CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p test_cli.py -v
```

这组检查使用真实 CLI 和 localhost 固定响应，不调用云模型，也不证明模型会自主正确协作。

## 判定器校准

此前 46 项版本的结果通过实际 `python3 cli.py` 子进程取得。临时参考实现只用于校准，不进入待测模型的上下文；源码及失败位置经另一 reviewer 核对。

| 实现 | 通过项 | 退出码 |
| --- | --- | --- |
| 损坏基线 | 2/46 | 1 |
| 完整参考 | 46/46 | 0 |
| 拒绝合法 quantity=1 | 44/46 | 1 |
| 缺失 name 时填默认值 | 45/46 | 1 |
| 读取错误只保留 basename | 40/46 | 1 |

三个错误变体在修复前均为 45/45、退出 0。此前 45 项版本还校准过未接线、漏校验、吞错及异常 stdout 只有空行等变体；这些历史结果不计作当前版本的新运行。原始读取原因、代码必要性和协作质量仍需评审，判定器不覆盖所有可能错误。

本轮模型试验开始前，冻结验收为 47 项。新增 CSV quoted quantity 含尾换行的拒绝用例，并要求 UTF-8 解码失败也保留输入路径。两个普通错误实现分别使用 `$` 正则尾锚接受尾换行、只输出 UnicodeError 丢失路径；修复前两者均通过 46/46，说明旧检查存在漏检。修复后同一批实现的真实 CLI 结果为：

| 实现 | 通过项 | 退出码 |
| --- | --- | --- |
| 损坏基线 | 2/47 | 1 |
| 完整参考 | 47/47 | 0 |
| CSV 用 `$` 锚接受数量尾换行 | 46/47 | 1 |
| UTF-8 解码诊断丢失路径 | 45/47 | 1 |

这些是判定器校准结果，参考实现由审查者临时编写，不是 dev 入口调用真实模型的开发产物。评估文档覆盖三个产品入口，并固定了两阶段后续变更的任务文本与验收样例；已执行的阶段和 reviewer 校准记录如下，不能由测试数量外推维护性。

真实模型产物和独立审查随后揭示更多合同漏检，当前 `evals/verify.py` 已补至 58 项：两个 quoted-header 反例、CSV 裸引号与合法转义对照、长前导零、CSV/JSON 大整数、忽略字段大整数、转义 surrogate、额外字段 NaN，以及131073字符的合法CSV名称。原任务与种子保持原样。检查器仅在自身进程解除大整数转换限制，不向被测 CLI 注入设置。校准原件在 `/tmp/harness-eval-boundaries-tfv18g70/`：损坏基线 2/58，Claude 修复前冻结产物 48/58，修复后 Claude 57/58（长名称仍失败），原 Codex 显式任务产物 58/58，所有被测源码前后哈希未变。独立review先接受57项版，再核对新增长字段的8次真实CLI证据及3行差异，接受58项版。最终文件逐字发布，SHA-256 为 `21c8fdf86c105f52ad6511ed14f8bc049b0d1b0ff1d24605bc5cbb80b707a218`。本轮所有模型任务继续使用各自冻结的原 47 项，并单列额外补证；新 58 项只用于校准和后续新实验，不追改旧成绩。

三份中性 reviewer 样本在 `/tmp/harness-review-calibration-kckyle0i/blind/` 冻结，各通过原 47 项及扩展 117 项真实 CLI 检查，扩展检查的原始输出逐例相同。随后三个独立的原生 codex-dev 父会话分别派发一个新上下文的具名 review，均以默认 gpt-6-astra/max 和当前最高权限运行。每个子上下文逐字包含安装的 review 角色；只执行本地读取和哈希命令，没有修改或执行样本代码，也没有递归派发。委派正文为原生加密字段，不能逐字认证其内容。三个父子均正常完成，证据在 `/tmp/harness-native-review-calibration-uli503r5/`。

校准结果支持结构判断的区分能力：sample1 的共享记录校验函数有当前语义，review 没有要求删除；sample2 的可变注册、定义对象与空 validator/transform 回调被指出具体维护成本；sample3 的直接实现没有被要求强行合并校验。同时，sample1 提出疑虑、sample3 确认静态问题：默认 argparse 帮助动作与冻结合同的严格两个参数及成功 JSON 输出要求冲突。外部追加的 15 次真实调用确认三份实现均存在该问题，`--help` 及带额外参数的 `--help` 返回 0 并输出帮助文本。原始 40 项 manifest 始终匹配。该发现是有效合同问题，不能算作 reviewer 误报；原样本仍冻结，未把通过 164 项检查写成完整符合合同。三个盲审的父子合计 1,170,376 tokens（含缓存），并行时间区间约 382 秒，无金额计费字段。

主线程随后在新的 `/tmp/harness-review-calibration-repair-41czsi8s/` 副本中，只为三个 ArgumentParser 添加 `add_help=False`。每个样本的原 47 项、未改动的扩展 117 项及新增 9 项参数检查全部通过，原始 40 项输入仍逐字节不变；证据包括独立 diff、前后源码哈希及逐次原始输出。合同保持原样，未删除故意用作结构校准的泛化层，也未因该人工样本的问题修改真实 importer 的不同合同。原盲审对应旧文件状态，修复后的直接检查不冒充另一次原生盲审。

## 真实模型试验与剩余工作

本次恢复的最小真实调用已将本地 socket 限制、远程服务响应和代码质量分开：

| 当前试验 | 实际结果与证据范围 |
| --- | --- |
| 普通 Codex 0.157.1，固定最小回复 | ChatGPT 原生认证、默认配置 gpt-6-astra/max；6.882 秒、退出 0、准确返回指定内容且无工具调用。JSON 未提供独立的服务端模型字段；只证明调用前置条件 |
| 普通 Grok 1.0.41，同一最小回复 | OAuth 原生认证；6.126 秒、退出 0、1 turn、无工具调用。运行记录选择 grok-4.7/xhigh，用量标为 grok-4.7-build，虽基础配置仍写 grok-4.6。未覆盖模型或 effort |
| 当前 Claude 临时安装，greet 代码任务 | 原生选择 claude-opus-5-5[1m]；7 次原生重试均为 HTTP 429/rate_limit，0 回复、0 工具调用。90 秒时确认仍运行后主动 SIGTERM，退出 143、监督脚本退出 124；90.449 秒内文件未变，外部验收仍退出 1 |
| 最高权限修改前的 codex-dev，greet | 默认 gpt-6-astra/max，显式 workspace-write/never；60.97 秒、退出 0，只增加一行，未建立计划或子 agent，外部 3/3 通过 |
| 同一版 codex-dev，importer | 外部 47/47 通过；删除 registry，保留三个直接实现文件及 CLI 测试。两个具名 dev 的原生执行有重叠，随后新建独立 review 并完成；首轮主会话在报告前被 900 秒观察上限终止，后来恢复同一 thread，80.47 秒退出 0 并补齐最终报告。恢复只读，未改产物或重跑验收 |
| 同一版 grok-dev，greet | 显式 acceptEdits/workspace；编辑与后续自测分别被原生权限取消，尽管两次 CLI 都退出 0，结果事件均为 cancelled。同一会话恢复并精确授权编辑后产物只增加一行，外部 3/3 通过；模型自己的 9 项检查未执行，任务未完整成功 |
| 已安装的最高权限 grok-dev，新的 greet 会话 | `bypassPermissions / off`，默认 grok-4.7/xhigh；30.83 秒退出 0，原生 result 为 success/end_turn。实际一行编辑、12 组模型自测及外部 3/3 均通过，无计划、workflow、子调用或额外业务文件 |
| 已安装的最高权限 claude-dev，用户指定 deepseek-flash，新的 greet 会话 | 12.089 秒退出 0，原生 result success；实际 Read/Bash/Edit/Bash，6 组逐例比较输出均正确，外部 3 个 assert 通过。没有计划、子调用或额外业务文件；执行生成的 pycache 保留在试验目录 |

Codex/Grok 的最小回复没有经过开发任务验收；本机证据在 `/tmp/harness-access-wzvi4Pzs/`。Claude 本次使用 `acceptEdits`、无模型或 effort 覆盖，服务原始诊断为账号限流，证据在 `/tmp/harness-claude-q4mjk11f/evidence/`，包括实际模板快照、原生会话、输入和外部断言。观察时限不代表服务端最终失败；成本不可得，不能记为零。三个探针均已确认退出并回收，没有待等待的进程。

Codex 代码产物、外部验收、实际安装快照及四条原生 importer 轨迹保存在 `/tmp/harness-codex-VEX8H5Bo/`。两条 dev 轨迹均包含已安装角色正文、共同父会话和 `fork_turns=none`；CSV 于 14:58:59 UTC 开始执行，JSON 于 14:59:04 开始执行，分别于 15:04:23 和 15:02:07 完成。独立 review 于 15:05:35 创建、15:10:31.733 完成，读取当前代码、测试、原始记录及哈希，没有遗留可操作发现。集成自测 25 个测试方法、109 次真实 CLI 调用通过；最终文件与该验收及评审哈希一致。主会话最后活动为 15:11:32.581，观察封顶前没有最终报告或 `turn.completed`。任务简报和 agent 间消息以加密正文保存，无法逐字核验其完整性，不能把这项记为通过。

同一 importer thread 随后在当前最高权限入口接受第一阶段维护需求：CSV 同时支持 `name,quantity` 与 `quantity,name`，按表头解释两列。先冻结的 18 项新增检查对原产物取得 15/18，变更完成后为 18/18，原 47 项仍全部通过；检查器哈希未变。实际 diff 只涉及 CSV 实现和 CLI 测试，通过两个列索引表达差异，未新增注册或转换层。模型另外完成 27 个测试方法、153 次 CLI 调用及一个新上下文独立 review，290.04 秒正常结束。证据为同目录 `stage1/`。

第二阶段数量上限 1000 的 38 项新检查先在阶段 1 产物取得 30/38，再把独立需求发送给原 thread；没有提前揭示。完成后原 47、阶段 1 的 18 及新增 38 项全部通过，所有检查器哈希未变。实际 diff 仅扩展 CSV/JSON 现有范围条件与诊断，并更新相应测试；CLI 保持原样，没有新业务模块、模式参数、调用者特例或整体重写。原“超大数量成功”自编测试改为拒绝，与新上限要求一致，长前导零的合法数量仍被验证。模型完成 30 个测试方法、183 次 CLI 调用及新上下文独立 review，无遗留发现，406.33 秒正常结束。证据为同目录 `stage2/`。两步结果支持这一个变更序列的局部维护表现，不证明普遍低成本或优于普通入口；两个配对的自然任务对照另行执行。

用户已明确新的 Claude 验证模型为 `--model 'deepseek-flash'`。该精确名称用于当前已安装最高权限入口的新任务，不添加 `[1m]`，不修改全局模型设置。greet 的 init/assistant/result 均记录该模型和 bypassPermissions，原生加载的 CLAUDE.md 哈希与安装文件匹配，证据在 `/tmp/harness-claude-deepseek-qiun3vs6/evidence/greet/`。模型自测脚本打印比较结果，本身不因比较失败退出非零；实际六项输出均为 OK，独立外部断言才提供失败即非零的验收。stderr 的 unrecognized_model 诊断保留；原生报告费用 $0.115736，但 costBasis=unknown，不能当作已核验的账单金额。本次使用 --strict-mcp-config，MCP 为空，没有证明 MCP 能力。随后新会话执行原始完整 importer 任务，其初始外部基线为 2/47。先前默认模型的 429 与更早沙箱内 deepseek-flash[1m] 连接错误保留各自实验条件，均不能代替这次新调用的结果。

Claude importer 原生父 session 为 `e501642f-8422-4f13-99e9-674769c36e8e`，两个 dev 的执行时间实际重叠。dev 的真实工具池为 Read/Edit/Write/Bash，review 为 Read/Grep/Glob，全部使用 deepseek-flash。第一轮产物通过 47 项，但 CLI 报后台任务等待 600 秒后停止 review，父会话没有完整最终报告；外部监督没有触发 timeout。原生时间与监督时钟存在不一致，不能据其推算可靠效率。随后恢复同一父会话，通过实际 SendMessage 续用原 reviewer 和两个 dev，保留全部旧失败与快照。

外部代码审查发现旧 47 项的漏检：quoted CSV header 被接受；合法长整数、长前导零、额外字段大整数、转义 surrogate 被拒；NaN 与 CSV 裸引号被接受。先冻结表头 4 项和合同边界 10 项，再沿原上下文修复，旧边界产物为 3/10，不能把模型自评或“干净地拒绝”当作符合合同。最终 `evidence/importer-resume-contract/final-snapshot` 的外部结果分别为 47/47、4/4、10/10，原任务、原判定器、补充检查器和 fixtures 哈希均未变；review 完成，父原生 result success/is_error=false，进程自然退出 0，最后一次恢复用时 495.239 秒。主线程直接检查完整生产 diff 和最终代码，当时新增判定器为57/57；之后独立审查提出长CSV名称反例，58项版为57/58，默认字段上限的缺口仍存在。冻结产物作为审查对象保留，不再追加模型维修，因此不能把先前固定检查全部通过写成完整合同已经满足。`records.py` 的共享读取、名称校验与错误边界有实际两个消费者，没有 registry 或插件框架；三个错误类型是否值得进一步合并属于结构取舍，测试通过不证明最小实现。当前代码调用 `sys.set_int_max_str_digits`，验证环境为 Python 3.14，未宣称旧 Python 兼容。累计原生估算费用 $8.6970264 的 costBasis 为 unknown，不能作已核验账单；多次恢复的累计费用不能相加。

Codex 自然任务对照已经完成两个配对、共四次全新会话，证据 `/tmp/harness-codex-natural-ieomm2dd/`。固定 prompt 为原 task 的 Goal/Context 加预先约定结尾，SHA-256 为 `c5749f826a4776f29dffa4ff366d13e443d35c515a0900ef16c1d78b737f9f20`；四份初始文件逐字相同、基线均为 2/47。均为 Codex 0.157.1、gpt-6-astra/max、danger-full-access/never、900 秒上限；第二对反转启动顺序。为保留同一原生认证/provider，使用同一稳定 HOME，偏离评估说明中的隔离根方案；基础配置无个人 developer 指令，实际 prompt-input 去掉 dev 新增根规则后其余内容一致。完整工具 schema 没有直接保存，因此不宣称已经逐项证实工具池完全一致。

| 自然任务试验 | 原定验收 | 事后边界补证 | 主会话累计 tokens | 原生终态 |
| --- | --- | --- | --- | --- |
| 第一轮普通入口 | 47/47 | 6/10 | 147,324 | 自然退出 0，无子 agent |
| 第一轮开发入口 | 47/47 | 7/10 | 904,049 | 自然退出 0，dev 与独立 review 均完成 |
| 第二轮开发入口 | 47/47 | 10/10 | 688,946 | 自然退出 0，dev 与独立 review 均完成 |
| 第二轮普通入口 | 47/47 | 6/10 | 150,288 | 自然退出 0，无子 agent |

补证在四份最终快照冻结后统一执行，检查器和 fixtures 是 Claude 外部补证的逐字副本，没有反馈给对照中的模型或修改产物。两份普通产物未处理 CPython 的长整数转换限制；第一轮 dev 只额外处理了长前导零，第二轮 dev 处理全部这些边界。四份都通过 surrogate、NaN、CSV 裸引号及合法转义引号检查。这是观察后提出的探索性检查，不能改写原定 47 项的成绩或冒充预注册结果。四次计时原值为 450.33、768.97、620.23、342.17 秒；本次运行出现 UTC、进程经过时间与监督计时不一致，不从这些读数推出可靠的速度优势。独立结构审查以四份中性副本进行；两个配对不足以证明普遍效果。

表中用量为各 root 原生累计 input+output，缓存输入是其中的子集，不能重复相加；dev/review 的独立计数另保存在各试验 `thread-evidence.json`，未混作统一账单。开发入口在这两对样本中用了更多主会话上下文，边界补证成绩也更好；没有账单金额，不能从 token 总数直接换算费用，更不能把更高用量自动当作更好结构。

独立审查读取中性样本和任务，未读取入口映射，20个源码及测试哈希全部一致。四份都保留种子的 `Importer` 对象：只把函数赋给 `self.load`，唯一CLI消费者再调用它，没有独立状态、校验或生命周期职责。直接选择两个加载函数即可少一次追踪；这是共有的旧包装简化机会，不是新增框架，也没有证明开发入口在结构上更优。引号扫描、JSON常量拒绝helper均有当前职责；名称/数量的少量重复不足以要求新增共享层。

review另提出默认CSV字段长度限制。主线程用同一个131073字符名称对四份CSV与JSON入口共执行8次：两份普通及第一轮dev的CSV均以 `field larger than field limit (131072)` 拒绝，第二轮dev成功，四份JSON均完整成功，所有原源码哈希不变。原始证据在 `/tmp/harness-field-size-check-pa5ra3un/`，中性副本及review核对材料在 `/tmp/harness-natural-review-z9vn6xqs/inputs/field-size-evidence/`。第二轮dev已有实际140000字符自测和上限处理，其余三份漏检。这是额外的独立审查反例，不并入原47或事后10项分数；冻结产物不修，以免改变比较对象。上述结果支持在这一任务上观察到部分正确性收益，但不能支持“持续极致简洁”或普遍收益承诺。

前述 Codex importer 的最终报告缺口已由同一原生 thread 的恢复补齐，未新建实现会话。恢复仅执行三条读取既有证据的命令，四文件 SHA-256 和文件集合不变，无新增协作；15:40:12.562 UTC 记录 `task_complete`，同时收到 `final_answer`、`turn.completed`，退出 0。运行期实测 gpt-6-astra/max、danger-full-access/never；原始记录及最终报告为 `/tmp/harness-codex-VEX8H5Bo/importer.resume-report.*`。首轮仍按旧权限条件记载，本次恢复不构成新权限下完整首轮。相对首轮最后累计值的观测用量增量为输入 112,277（其中缓存 106,240）、输出 2,376 tokens，没有金额字段。

Grok 代码产物及取消事件保存在 `/tmp/harness-grok-8b8fc1gl/`。两轮共 37.99 秒、7 次模型调用，原生记录合计 $0.04969236；没有计划、子调用或额外业务文件。最终文件与 Codex 简单任务相同，但权限取消使模型不能独立完成自测。这是最高权限要求之前的实验条件，修改入口后须用新会话验证；原生已创建的 sandbox 会话不能在恢复时切换为 off。

最高权限入口发布后已用新 session `dcf934fc-9b0e-4feb-8ba0-cfdb2d4b49b5` 完成上述补验证，原始 init、summary、工具结果及产物在 `/tmp/harness-grok-high-t_ohy8py/`。主线程直接核对真实 search_replace、run_terminal_command 的 exit 0/failed 0、最终 result 和外部验收；旧的权限取消未重现。原生记录为 6 turns、输入 19,219、缓存输入 88,576、输出 1,344 tokens，总费用 $0.03086860；保留默认模型和 effort，未手工拼接规则。运行结果支持这一简单任务的完整执行，不证明复杂任务协作或跨任务质量提升。

最终已安装grok-dev的复杂任务使用原始完整task、全新目录 `/tmp/harness-grok-importer-l6_t9eia/`、默认grok-4.7/xhigh、bypass/off和真实交互PTY。父session `01a0e3f1-5b1d-7642-a3ea-6055c1e85728` 经约10分钟调查后才实际派发两个dev，两者在17:47:25 UTC开始并重叠运行；没有独立review。原900秒上限触发shutdown，两个child在17:52:19.625 UTC终态取消；5秒清理宽限后命令被SIGKILL，PTY退出记录905.018秒。Workflow `wf_01a0e3fa97137771b6f470a168921643` 的状态文件仍是active，这是进程退出后的残留状态，不是可继续观察的活跃任务，也不是聚合完成。

Grok冻结产物只修改CLI与JSON实现，CSV仍为stub，没有最终集成报告。原固定检查由2/47升至25/47；结束后只读执行新的58项为25/58，新增11项均未通过。原任务和47检查器已在启动前冻结、哈希相符，没有扩时、换模型、外部提示推动或评估者代写代码。本轮复杂任务结论为预算内未完成，不能由先前角色探针的成功替代。源diff、两个cancelled metadata、终态记录和外部原始输出均保存在该目录；不启动额外维修轮来改写这次结果。

Grok 的这次原生会话还导出了实际 `spawn_subagent` 定义：必填 `prompt`、`description`，可选 `background`、`isolation`、`resume_from`、`cwd`，没有声明选择具名角色的字段。原样抽取为 `/tmp/harness-access-wzvi4Pzs/grok-spawn-subagent-schema.json`。该探针带禁用子调用等参数，但 init 与保存的工具定义仍列出 23 个工具；所以只能确认本次没有工具调用，不能据此认证白名单或子调用禁令。这个旧探针不能证明开发入口和实际具名派发；后续验证见前文。

随后具名 review 的真实 Workflow 探针在 `/tmp/harness-grok-review-7t06oi9l/` 保存了父子原件、实际调用参数、state/journal、metadata 和 tool definitions。一次 `validate_only` 后恰好一次 live 调用，`agents_used=1`；child `01a0e385-d4f5-7be3-8296-7475d04f6a48` 返回 success=true/cancelled=false，实际唯一工具调用为读取 review.md。父子均为 grok-4.7/xhigh、sandbox off；父 MCP 为空，且父级参数禁用了 MCP meta 工具，不能证明角色自身严格限制了工具或过滤非空继承。总耗时 97.59 秒，原生费用 $0.04930544。该探针确认了上文质量合同未继承的问题，修复后的实际新子提示词验证见前文。

以下为之前受 socket 限制的历史试验。它们使用当时仓库的临时安装、隔离 HOME/XDG 和现有服务环境，不复制凭据文件。观察时限到达后终止并回收进程，不把超时当作服务端的最终错误；当时的临时文件在原始记录核对后已清理。

| 模型与任务 | 实际结果 |
| --- | --- |
| opus[1m]，简单 greet 任务 | 60 秒内 7 次 API 重试，0 回复、0 工具调用，文件未变，外部断言退出 1；没有取得具体 API 原因 |
| deepseek-flash[1m]，同一简单任务 | 初始化确认指定模型字符串；60.04 秒内 7 次 API 重试，0 回复、0 工具调用，文件未变，外部断言退出 1；error 为 unknown，HTTP 状态为空 |
| deepseek-flash[1m]，原生 debug 最小消息诊断 | 20.02 秒内 6 次重试，0 回复；原生 API 日志报 Connection error，未取得 HTTP 状态 |

历史诊断日志出现 EAI_AGAIN，但对配置服务地址的独立名称解析成功，不能据此断言该接口 DNS 失败，也不能断言服务端不支持指定模型。本次获准的沙箱外调用已经获得真实服务响应，后续不再把这些旧诊断当作当前所有模型不可用的依据。

剩余验收是 [真实简单任务与并行导入任务](../evals/README.md) 及后续变更。需保存实际产物和可用轨迹，核对任务拆分、上下文交接、并行重叠、集成、独立评审和外部验收。静态去重或单次通过不证明成功率、速度或成本改善；新旧比较需要相同模型、工具、任务和预算下的多次运行。

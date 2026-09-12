# Goal

依据 prompt/context engineering、任务依赖图、agent harness 与 skills 的一手研究，优化 Claude/Codex 开发规范和原生 agent 编排，使完整实现、简洁架构、必要校验与错误暴露成为可验收契约，并让普通 `claude` / `codex` 保持默认配置、`claude-dev` / `codex-dev` 使用独立开发配置。

# Constraints

- 以 `docs/design.md` 为已定接口；研究依据为 `docs/research-harness.md` 与 `docs/research-orchestration.md`。不另选架构，不缩减原始三个目标。
- Bun + TypeScript 安装器、薄 shell 入口、Markdown 单源角色、两个按需 skills；不引入图框架、插件平台、第三方依赖或常驻调度器。模型、推理强度和权限继承原生行为。现有 Python 测试保留为独立行为与 TOML 解析验证，不是安装依赖。
- 安装接口固定为 `./install.sh [--home DIR]`。wrapper 设置安装时确定的开发配置目录并 `exec` 原生命令，保留参数、当前目录、退出码及信号，不改写 `HOME` 或 shell 配置，不复制个人认证。
- 仅确认历史发布指纹及关联关系的默认目录文件可自动移至备份；自定义或未知内容保留并报告。预检后写入，重复安装无额外变更，符号链接不能让写入越出受管目录；保留用户无关文件。
- 任务按以下顺序列出；`deps` 明确产物依赖，`owns` 是唯一写入归属。I1 与 C1 的依赖和写入互不重叠，D1 必须消费两者已集成且验收通过的产物。不得把 worker 自报完成当作依赖完成。
- 单一协调者维护 `plan.md`；worker 不改计划、不递归派发、不撤销其他工作者修改。协调者在 Notes 追加真实句柄、工作区、修改范围、验证命令及结果、对应 revision 或文件快照；恢复时核对当前文件与真实运行句柄，超时不等于终止。
- 静态检查只证明格式和一致性；原生 CLI 加载、原生多 agent 并行与技能行为分别取得证据。记录模型/版本/任务/预算及验证边界；新旧多次 A/B 性能评估不作为本轮必达，不声称普遍质量或速度提升。

# Done when

- [x] 后续偏好与研究缺口已落实：安装入口使用 Bun，Python 安装器已移除，既有安装行为及真实 CLI 加载重新验证；官方 Workflows 与原生 subagents 的能力和限制进入研究、设计与技能的选择规则，不能把文档支持当作本地运行证据。
- [x] 两份研究报告包含 prompt/context/harness、依赖图和 skills 的一手来源、选择依据及局限；`docs/design.md`、README 和最终模板采用一致接口，`docs/validation.md` 逐项关联三个用户目标与当前证据。
- [x] 新安装生成两套根规范、六个角色、两个技能及两个 wrapper；普通默认目录无新增污染，wrapper 参数/路径/退出码、备份恢复、幂等、预检、符号链接和已知/未知旧安装迁移均有行为覆盖；`python3 -m unittest discover -s tests -p test_install.py -v` 退出 0。
- [x] 根规范保持简短，角色单源且边界明确，`orchestrate` 定义依赖就绪、所有权、集成后解锁和恢复，`author-skills` 定义触发边界与行为验收；重复 Codex 模板已删除，`python3 -m unittest discover -s tests -p test_contracts.py -v` 退出 0。
- [x] 在最终新安装产物上运行 `CLAUDEX_TEST_CLI=1 python3 -m unittest discover -s tests -p test_cli.py -v` 退出 0，Claude/Codex 的真实加载用例均执行而非跳过；证据覆盖两端根指令、角色和 skills，以及普通配置不加载新增开发内容；`docs/validation.md` 写明 CLI 版本及模拟模型只证明加载的边界。
- [x] `docs/validation.md` 记录至少一次有真实原生 agent 句柄和并行时间区间的有界多 agent 执行，独立产物已集成且共同验收通过；同时检查 fork/join、共享写冲突、独立失败分支继续、陈旧 running 状态、集成后解锁，区分实际运行与情景审查证据。
- [x] `docs/validation.md` 对两个已安装技能各记录应触发、相邻不适用、显式调用、异常及实际产物检查的行为结果；不以关键词、格式通过或模拟模型固定响应代替技能行为；效果评估方法和未进行的多次 A/B 对照明确标示。
- [x] README 提供安装、普通/dev 命令差别、独立登录和服务配置、项目规则仍生效、已测 CLI 版本、升级迁移和备份恢复方法；`python3 -m unittest discover -s tests -v` 与 `git diff --check` 退出 0，当前变更与验收证据一致。
- [x] review returns ACCEPT；只读审查针对最终文件状态，无未解决发现，协调者按以上每项证据完成审计并记录在 `docs/validation.md`。

# Tasks

- [x] (research) `id: R1`; `deps: []`; `owns: [docs/research-harness.md]`; `state: done`。调研 prompt/context engineering 与 harness，给出降低冗余、过早抽象、重复校验和吞错的规则分层及效果评估方法。Done when: `docs/research-harness.md` 包含一手引用、候选比较、建议和未验证范围。`acceptance: 文件已读取，涵盖全部上述内容`。已有证据：2026-09-13 当前文件 SHA-256 为 `99fd08ac9ca2c58cc2600060ed1b9cd8a8d8b3459f924939ef243468d20d9f74`；不是模型 A/B 结果。

- [x] (research) `id: R2`; `deps: []`; `owns: [docs/research-orchestration.md]`; `state: done`。调研任务依赖图、原生 agent 并行、恢复和 skills 编写实践，明确平台支持与工程判断。Done when: `docs/research-orchestration.md` 包含一手引用、依赖与所有权契约、恢复语义、技能触发及行为评估要求。`acceptance: 文件已读取，涵盖全部上述内容`。已有证据：2026-09-13 当前文件 SHA-256 为 `c4661dfbc4fb87a5886055c67a20c8eb69d91617b785752ef96820821ade1d69`；实际并行和技能行为留给 D1 验证。

- [x] (arch) `id: A1`; `deps: [R1, R2]`; `owns: [docs/design.md]`; `state: done`。综合研究，固定内容分层、安装隔离、迁移、安全写入、编排契约与实现边界。Done when: `docs/design.md` 给出可直接实现的接口、路径、否决条件、所有权和验收范围。`acceptance: 文件已读取，接口定稿，可由 I1/C1 独立消费`。已有证据：2026-09-13 当前文件 SHA-256 为 `5d36f79b6f95fe5b5fb329a7eae966605028980db5bb6a89969e6f131579dbe6`；其中已有 CLI 探查陈述不能替代最终安装验收。

- [x] (dev) `id: I1`; `deps: [A1]`; `owns: [install.sh, scripts/install.py, scripts/legacy-files.json, tests/test_install.py]`; `state: done`。按设计实现标准库安装器、两个 wrapper 和可追溯的历史发布指纹；覆盖新装、变更安装、幂等、路径/参数/环境、退出码/信号、备份恢复、预检、符号链接、已知迁移、未知保留、转发/链接关联及不依赖 Git 的归档安装。只依赖设计约定的模板格式；窄测试可构造临时模板，不读取 C1 正在改写的接口作为完成依据。Done when: 实现已在当前工作区集成，`python3 -m unittest discover -s tests -p test_install.py -v` 退出 0，历史候选路径由实际旧安装行为推导，测试覆盖上述用户可观察结果。`acceptance: 命令结果、修改范围和指纹来源由协调者记录`。

- [x] (dev) `id: C1`; `deps: [A1]`; `owns: [templates/**, tests/test_contracts.py]`; `state: done`。按设计精简根规范与六个角色，删除重复 Codex 角色模板，新增 `orchestrate`、唯一计划格式参考和 `author-skills`；保留信任边界校验、必要清理/恢复和预期外错误原因，删除固定次数重启、固定全角色流水线、强制最高 effort 和无依据的上下文归因。计划角色引用编排技能的格式契约；内容测试只消费本任务拥有的模板，最终生成互操作由 D1 验证。Done when: 内容全部落盘、重复模板删除，`python3 -m unittest discover -s tests -p test_contracts.py -v` 退出 0，人工核对设计的全部调度不变量及技能触发边界。`acceptance: 静态检查范围与语义核对结果由协调者记录，不能自称已证明执行效果`。

- [x] (dev) `id: D1`; `deps: [I1, C1]`; `owns: [README.md, tests/test_cli.py, docs/validation.md]`; `state: done`; `executor: root`。在集成后的新安装产物上完善并执行双端真实 CLI 检查，核实普通/dev 配置、角色和技能加载；执行有界原生多 agent 并行与技能行为验证，记录任务输入、句柄、模型/版本、实际产物、验收、耗时/用量及局限；以现有 I1/C1 的真实并行证据为可用来源，但不能用编排模拟替代真实运行。完成 README 和逐项证据报告，采用研究中的评估方法而不新增本轮 A/B 门槛。Done when: `CLAUDEX_TEST_CLI=1 python3 -m unittest discover -s tests -p test_cli.py -v` 退出 0 且双端均执行，`docs/validation.md` 提供 Done when 中原生并行、调度情景和两个技能行为的可复查证据，README 覆盖设计要求。`acceptance: 当前文件状态、运行命令/退出码及观察到的行为均已记录`。起始证据：`tests/test_cli.py` 已创建，起始 SHA-256 为 `5eca48a6ce06dbda05d02673febacb30926c04c198b1312be88c3fb8151c00c6`，尚无最终完整运行通过证据。

- [x] (review) `id: V1`; `deps: [D1]`; `owns: []`; `state: done`。独立只读评审当前安装、迁移、内容契约、测试覆盖与三项目标的完成证据，优先检查数据保留、默认配置污染、错误处理语义、并发所有权、真实加载和虚假完成；每个发现须有具体路径、失败条件及影响。Done when: 返回绑定当前文件快照的 `ACCEPT` 或带可行动发现的 `CHANGES_REQUESTED`，协调者将 verdict、发现和证据写入 Notes；完成本次评审本身不代表最终验收通过。`acceptance: 明确 verdict 与可复查审查记录，所有发现转交 F1`。

- [x] (dev) `id: F1`; `deps: [V1]`; `owns: [install.sh, scripts/**, templates/**, tests/**, README.md, docs/validation.md]`; `state: done`; `executor: root`。依据 V1 发现做最小修复，重新验证受影响行为与最终集成，取得对最终文件状态的独立复审 ACCEPT；逐项审计原始三个目标及本计划全部 Done when，清理本次临时产物并在 `docs/validation.md` 记录已验证/未验证边界。修改导致旧证据失效时补验，不新增无关改动。Done when: `python3 -m unittest discover -s tests -v`、`CLAUDEX_TEST_CLI=1 python3 -m unittest discover -s tests -p test_cli.py -v`、`git diff --check` 均退出 0，双端原生用例均执行，review 对最终文件状态返回 ACCEPT，全部 Done when 有当前证据且由协调者勾选。`acceptance: 最终验证结果、发现处置和完成审计已落盘；若仍缺行为或运行证据，保持 pending/blocked 而非宣称完成`。

- [x] (research) `id: N1`; `deps: [R2]`; `owns: []`; `state: done`。补齐官方原生 Workflows 与 subagents 的选择依据、角色加载未知项、逐分支推进和重放限制。`acceptance: /root/claude_native_options 已返回读取官方正文后的报告；协调者将事实/工程判断/未实测边界写入研究与设计`。

- [x] (dev) `id: B1`; `deps: [A1]`; `owns: [install.sh, scripts/install.py, scripts/install.ts, tests/test_install.py]`; `state: done`。将安装器迁至 Bun；保留接口、原生配置隔离和历史迁移。`acceptance: 21 项安装回归全部通过，包括无 Python/Git 的归档安装；/root/review 对最终安装器 18b3aec08998fdfd5ff58bade24b9ef0071843e0fa2d8dcd8e6fbb72cb236997 返回 ACCEPT`。真实实现句柄 `/root/bun_installer`；最后的坏链接关联修复由协调者在原 worker 终态后接手。

- [x] (arch) `id: Q2`; `deps: [C1]`; `owns: [/tmp/claudex-quality-ZsqYgy/architecture.md]`; `state: done`。依据当前根/arch prompt，设计已有 Bun CLI 的最小修复；保留公开 API，明确输入与可信计算边界、错误原因和资源清理。`acceptance: /root/quality_arch 已输出设计，协调者读取并交给后继；未读取预先固定的独立验收`。

- [x] (dev) `id: Q3`; `deps: [Q2]`; `owns: [/tmp/claudex-quality-ZsqYgy/work/]`; `state: done`。依据当前根/dev prompt 实现真实 CLI 修复并自验。`acceptance: /root/quality_dev 交付源码与检查结果；协调者固定的 8 项独立验收从基线 3 pass/5 fail 变成 8 pass；自验 48 项通过含 38 次 CLI；产物已由下游实际读取`。

- [x] (review) `id: Q4`; `deps: [Q3]`; `owns: []`; `state: done`。按当前 review prompt 独立审查真实质量产物，核对无过早抽象、无重复内部校验、必要输入拒绝、错误与清理语义。`acceptance: /root/completion_audit 独立复跑 8 项验收与 48 项开发测试，通过并返回 ACCEPT；源码快照 3fead0c069f359a827b8cb45875d41ad22e6b13a3e1d9b12d09e101077b2eccd`。

- [x] (dev) `id: C2`; `deps: [N1, B1, Q4]`; `owns: [docs/**, README.md, templates/skills/orchestrate/SKILL.md]`; `state: done`; `executor: root`。将 Bun 与原生 Workflows 取舍落实到内容，补齐质量/运行方式选择的行为证据，在最终安装上复跑集成检查并取得独立最终审查。`acceptance: 28 项检查中 26 pass/2 CLI 可选跳过，显式 2 CLI pass；4 项原生运行方式回放已核对；最终 docs 与源码/原始评估一致且 review 无待解决发现，清理本轮临时产物`。

# Notes

- 2026-09-13 系统发布：按“安装到系统后push”指令执行真实 `./install.sh`，两端 dev 入口版本检查、根/角色/技能产物一致性和第二次幂等安装均通过。四个原有认证/设置文件哈希保持；旧发布文件备份在 `~/.local/state/claudex/backups/20260912T185211Z-rb3xNw/`，两项自定义默认根规范保留并明确报告迁移未完全清理。该记录补充前述临时目录验收，不改动模板或安装实现。

- 2026-09-13 后续最终审计：Bun 安装器与旧链接保留的已确认回归全部闭环，/root/review 安装范围 ACCEPT、21 项无跳过通过。最终主线程全套 28 项检查为 26 pass/2 可选跳过（1.788s），显式两端 CLI 均通过（4.383s）；两个技能 validator 与 diffcheck 通过。当前根/arch/dev/review 的代表性真实编码任务已完成，独立 8 项及开发 48 项均通过，/root/completion_audit ACCEPT；新原生运行方式选择的4项决策回放已读原始报告并核对。最终 /root/review 再次读取全部原始评估与文档，ACCEPT、0 待解决发现。20个固定文件的排序sha256清单摘要为 3f8296d2ee031174d7f03c1e627e625e43559096cf82f85e02918897e7e213de；范围与算法见docs/validation.md。已清理本轮临时评估目录和测试缓存，未改真实用户配置或提交远端。此记录取代初版快照作为本次完成证据；未声明跨模型质量收益或本地Workflow实测。

- 2026-09-13 后续审计重新打开：上一解释回合没有改变权威状态，归为 no progress；本回合重新执行基线，22 项检查中 20 项通过、2 项可选 CLI 跳过。新增工作：B1（dev，deps=[]，owns=[install.sh,scripts/install.py,scripts/install.ts,tests/test_install.py]）将安装器改为 Bun，保留接口与已有行为；N1（research，deps=[]，owns=[]，真实句柄 /root/claude_native_options）核对官方 Workflows 的适用边界；Q1（review，deps=[]，owns=[]，真实句柄 /root/completion_audit）只读审计 prompt/skills 与质量目标的缺口。协调者负责研究/设计/README/技能的必要更新；B1 与这些产物的写入不重叠。集成验收等待 B1/N1/Q1，最终独立 review 重新执行。

- 2026-09-12T16:13:34.168421+00:00: I1 派发 `/root/installer_dev`，C1 派发 `/root/content_dev`；共享工作区 `/home/nex/GitHub/claudex`，写入所有权无重叠，均读取 A1 与任务后开始实现。以原生 agent 状态查询确认两者 running。D1 的 CLI 探查准备已完成，最终集成验收等待 I1/C1。

- 2026-09-12T16:27:08.420878+00:00: I1/C1 已集成到共享工作区并由主线程验收：14 项安装行为检查退出 0（1.791s）、5 项内容契约退出 0；两个官方 skill validator 均通过。scripts/install.py sha256=dc5c1a868140bbda247ad029d26a63f233fa3cf2e1d5e525f0697da1715e7c57; scripts/legacy-files.json sha256=ba9a1b7992346cb5a1590aaab754f430b1d3c160a6a831003f39168a5e3d4eb6; templates/AGENTS.md sha256=bd4c7cf24a9da94109bf86b82f6198b6faf869fd8a7b0a97a9c3547b6f4f4351; templates/skills/orchestrate/SKILL.md sha256=a36fc44cbd2416a276c50f482b8afb232a67fdfbd719775ba5b2812dee6193af; templates/skills/author-skills/SKILL.md sha256=6d2f4b6d61ccb3e8217c79c36cd4a4751ebad27e88f9f182efa29ad757606c0d。D1 解锁；最终双端 CLI 2 项退出 0（5.143s，无跳过）。独立行为评估句柄 `/root/behavior_eval`，只写 `/tmp/claudex-behavior-nj5ya5oy/work`；`/root/review` 同期只读审查实现，完整 V1 等待 D1 证据文档。

- 2026-09-12T16:31:14.785458+00:00: 独立审查复现 HOME 别名下旧 Codex 链接迁移遗漏，以及 YAML 注释描述误解析。I1 重新打开，由原句柄 `/root/installer_dev` 修复并添加回归；D1 的最终安装验收等待修复，独立技能评估继续。主线程已同步内容格式检查的 # 约束。真实运行状态在 16:27:34 UTC 与 16:29:56 UTC 两次查询均确认 `/root/behavior_eval` 与 `/root/review` running，观察到 142 秒并行区间；这不是速度收益测量。

- 2026-09-12T16:39:48.706909+00:00: 最终完成审计：I1 的 HOME 别名迁移与 # 注释描述缺陷均已复现、修复并新增回归。全套 22 项检查中 20 项通过、2 项可选 CLI 跳过（2.170s）；显式启用的两端 CLI 均通过（5.308s）。独立技能评估实际完成并交付 7 项临时产物，主线程与review均对照输入检查；路由/实际PR产物/六场景两轮结果和边界见 docs/validation.md。`/root/review` 最终 ACCEPT、0 待解决发现，审查快照 e31fd8a39bae31271f85179d182eff885d0ce0af7426e11ad34b354c43bd4ff7。D1/V1/F1 和全部 Done when 依据当前证据完成；未要求或宣称跨模型 A/B 收益。临时评估与Python缓存清理，真实用户配置、Git提交及远端均未修改。

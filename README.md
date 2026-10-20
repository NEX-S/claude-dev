# claude-dev

在 Claude Code、Codex 和 Grok Build 的原生 harness 上定制个人开发偏好：极致简洁、干净、优雅、无冗余，少防御但不吞错。会话、工具、子代理和运行机制沿用原生能力。本项目提供开发入口：`claude-dev`、`codex-dev`、`grok-dev`。三端采用一致的质量取舍和 research/arch/dev/simplify/review 职责。给出一个概述目标，主会话收敛本轮功能，尽早贯通最简单的完整使用路径，由作者自清理、必要验证后交付。专家按具体问题调用，项目大不自动增加阶段；新功能和使用中发现的 bug 留待后续迭代。

## 安装

需要 [Bun](https://bun.sh/)；使用哪一个入口，就需要对应的原生 CLI 已在 PATH 中。Codex 需要支持独立 profile 文件的版本（0.134.0 起）；本轮原生检查版本为 Claude Code 2.1.303、Codex 0.163.0、Grok 1.0.62。安装器不下载 CLI，也不固定模型或 effort。三个开发入口默认使用原生最高权限模式，并关闭 CLI 自带的独立 sandbox。

```sh
git clone https://github.com/NEX-S/claude-dev.git
cd claude-dev
./install.sh --target all
claude-dev
codex-dev
grok-dev
```

针对当前偏好，建议 `gpt-6.1-sol` 从 `medium` 起步，复杂设计或难定位问题再用 `high`；小而明确的修改可用 `low`。这不是已证实的简洁度排名，项目不强制覆盖 effort。可只对本次启动指定：

```sh
codex-dev --model gpt-6.1-sol -c 'model_reasoning_effort="medium"'
```

官方依据、社区对比的局限见 [挡位调研](docs/research.md#gpt-61-sol-思考挡位与快速交付2026-10-18)。

Opus 5.5 官方建议从 medium 校准，Grok 4.7 的 API 默认则是 high；不同模型的同名挡位不表示相同投入，不统一强设。最新模型专用建议与采用边界见 [调研](docs/research.md#三种常用模型的最新增量2026-10-19)。

把 `~/.local/bin` 加入 PATH。原有 `./install.sh` 用法仍只安装 Claude；也可以用 `--target codex` 或 `--target grok` 单独安装。

| 入口 | 原生接入方式 | 账号与配置 |
| --- | --- | --- |
| `claude-dev` | 设置 `CLAUDE_CONFIG_DIR=~/.claude-dev` | 保留原有 Claude 开发配置根 |
| `codex-dev` | `codex --profile dev`，读取 `~/.codex/dev.config.toml` | 使用普通 Codex 的配置根、认证及状态 |
| `grok-dev` | `grok --rules "开发规则正文"` | 使用普通 Grok 的配置根、认证及状态 |

Codex/Grok 的启动脚本不设置 `CODEX_HOME` 或 `GROK_HOME`，不复制、链接或同步凭证。原来的账号、provider、模型、信任记录和历史继续由原生 CLI 管理；普通入口未登录时，开发入口也需要登录。所有用户参数保持原样，追加在开发入口的固定参数之后。

权限默认值通过启动参数设置：Claude 使用 `--permission-mode bypassPermissions --settings '{"sandbox":{"enabled":false}}'`；Codex 使用 `--dangerously-bypass-approvals-and-sandbox`；Grok 使用 `--permission-mode bypassPermissions --sandbox off`。这些参数仅作用于开发入口的当前进程，不改普通 CLI 的全局权限配置。重复或冲突参数由原生 CLI 处理，wrapper 不解析、删除或改写用户参数。外层操作系统限制、组织策略以及原生强制规则仍然有效。

从旧版本升级，重新执行同一条安装命令即可：

```sh
./install.sh --target all
```

旧 `.codex-dev`、`.grok-dev` 中的认证、配置与历史保留，但这两个目录以后只提供受管的开发资源，不再被入口设为原生配置根。旧的凭证共享选项已移除。

`codex-dev` 是工作入口；登录、退出和 app-server 等管理命令使用普通 `codex`。原生 `--profile` 不适用于所有子命令，安装器不另写一套参数解析器。Codex 开发 profile 的 `developer_instructions` 会覆盖基础配置中的同名字符串，项目指令和原生全局 AGENTS 仍按通常规则加载。

## 清理废弃的用户配置

三端都迁移到开发入口时，可以显式清理已知位置的旧用户级指令、角色、skills、commands 与 MCP，并移除 Claude 的 hooks 和用户插件注册。先预览，再执行：

```sh
./install.sh --target all --clean-legacy --dry-run
./install.sh --target all --clean-legacy
```

`--clean-legacy` 只与 `--target all` 一起使用。清理以安装目标 HOME 为边界，处理 `.claude`、`.codex`、`.grok`、`.agents` 中已知的用户扩展位置，以及相关全局配置注册。链接本身进入备份，不沿链接删除目标。Claude 的项目级注册、各 CLI 的认证、会话历史、Grok 的二进制和 bundled 资源、Codex 的 `.system` 技能不在清理范围。

旧用户插件除移除注册外，还按原生 manifest 或标准组件标记识别会被直接发现的插件目录，并移入备份。插件缓存和数据保留，不递归扫描其中内容。

Claude JSON 配置只移除约定的扩展键，保留其他值。Codex/Grok TOML 只清理 MCP，其他配置（包括额外的扩展发现路径与 hooks）保留；存在 MCP 注册时，用对应原生 CLI 在临时配置副本中移除，再检查其他配置的语义未变。所需 CLI 不可用或修改超出范围时，在发布前报错。清理不会改项目目录里的规则、skills 或 MCP 配置，也不扫描任意自定义扩展路径。

变化的旧文件和目录先备份到 `~/.local/state/claude-dev/backups/`，控制台列出路径；其中保留相对 HOME 的原位置，可据此恢复。重复安装不重写相同内容，不重复备份已清理项。不要同时运行安装或让其他进程改写待迁移配置；安装不提供跨路径事务或进程间锁。

## 协作与权限

| 角色 | 责任 |
| --- | --- |
| `research` | 核实本轮需求、现有合同和影响决策的一手证据；必要功能问题交主会话问用户 |
| `arch` | 根据需求和研究选择最直接的完整设计，只定义当前需要的接口 |
| `dev` | 一个完整结果的实现、持续简化、交付前自查清理、检查和修复 |
| `simplify` | 独立接管可用实现，实际删除或替换多余结构，保持功能、接口和数据并验证修复 |
| `review` | 独立检查正确性、回归、冗余与证据缺口 |

默认项目路线是：粗略目标 → 收敛本轮功能 → 贯通最简单完整路径 → 作者自清理 → 必要验证 → 交付。主会话保留完整目标、必要用户问题和最终交付责任，也可直接实施。调研、架构、独立精简和评审只为当前具体未知、结构复杂度或重要风险启用；已有结论直接复用，项目大小不自动触发专家链，新证据允许推翻旧设计。

影响功能、使用方式或数据的产品问题，要等用户回答后再实施依赖答案的部分；等待时继续独立工作。提出了问题不代表可以自行扩功能，普通技术取舍仍由 agent 决定。

整项目精简先判断完整范围中最大的多余职责，再选择改动，并按约定的产品或架构结果验收。已有调用者、旧设计和测试本身不证明一个机制仍然必要；一处局部清理通过检查，也不代表整项目目标完成。不增加固定重写量或额外阶段文档。

依赖取舍优先标准库和平台内置能力，再复用项目已有的合适能力。狭窄、明确的当前需求允许用直接的小实现解决；第三方库只有在功能或实现难度上的收益足以抵消集成与长期维护成本时才引入。小轮子保持当前用途，不顺手扩成通用框架；以总体理解和维护成本判断，不追求零依赖。这条偏好进入三端根规则与全部五个角色，不只保留在研究文档。

已有项目先核真实调用者、功能和持久数据；允许大幅调整内部架构，按可验证的功能批次逐步落地。决定委派已有项目的精简时，把完整范围交给 simplify，由它完成调查、修改、验证与修复，避免主会话重复准备工作；小而明确的清理可由当前作者直接完成。基线只保护真实合同，不固化所有偶然实现细节。开发者先交付能用且已亲自精简、验证过的结果；收尾自查合并在同一任务里，无有益改动即可结束。明确的整体精简目标或具体结构问题才交独立 simplify 重新权衡。需要时顺序交接给新的 simplify 上下文；两者不同时改同一耦合实现。简化者负责自身改动、检查和修复，可以判断无需修改。职责、状态和理解成本减少才是收益，不以删行或改动数量验收。最后由主会话检查真实使用路径，必要时调用只读 review，不能以作者报告代替验收。

质量合同明确区分用户需求与 agent 自定机制：保留真实行为，允许简化内部设计及对应检查；抽象须减少当前用途的整体理解成本。内部信任契约，错误保留原因直接暴露；只在必要恢复、清理或边界呈现时处理。不在没有当前合同时猜测、转换或修复未支持输入，也不因此增加校验矩阵。只在反直觉处注释 why。主会话核实实际代码和检查输出，复用仍覆盖当前代码、输入和环境的结果，只补缺失或失效的部分；无关改动不自动触发全量复测，明确发布门禁仍须完成。本轮必需功能成立、明显冗余已清理、相关检查通过即交付；进度汇报不等于完成，交付前要收取必需的后台命令与 worker 结果。修复已知功能与数据失败，不为证明没有未知 bug、穷举边界或继续抛光而延长 goal。“极致”指导设计取舍，不表示无限寻找全局最优。

Claude research/arch 用读取与 Web 工具，simplify 与 dev 用编辑/执行工具，review 用 Read/Grep/Glob 白名单。Codex 子角色继承父权限，只读及不递归派发为行为约定。已核读的 Grok 随包及官方仓库文档支持直接 subagent_type；按实际工具 schema 选择具名角色，缺选择器时才用 Workflow。Grok research/arch/review 保留排除 MCP 元工具的原生声明；发现角色不等于已验证实际工具隔离。版本及当前证据范围见 [设计](docs/design.md)与[验证记录](docs/validation.md)。

项目自己的指令仍由各 CLI 加载。Grok 还兼容 Claude 指令和扩展；Codex、Grok 都有配置根之外的 skills 发现路径。开发入口不承诺隔离已有全局扩展；上述清理用于移走废弃的用户级来源，项目规则继续保留。

## 安装归属

安装器管理以下资源；已有内容变化前完整备份，相同内容不重写：

| 平台 | 受管资源 |
| --- | --- |
| Claude | `.claude-dev/CLAUDE.md`、`agents/`、`skills/` 和入口 |
| Codex | `.codex/dev.config.toml`、`.codex-dev/AGENTS.md`、`agents/`、模板中的工作流子目录和入口 |
| Grok | `.grok-dev/AGENTS.md`、`skills/`、`.grok/agents/{research,arch,dev,simplify,review}.md` 和入口 |

Codex/Grok 的 `develop` 是根规则引用绝对路径的工作流文档，项目目标、实质简化、协调与恢复时读取，不注册到全局技能目录。Claude 使用原生 skill。Codex 的基础 `config.toml` 不属于普通安装的写入范围。Grok 逐个安装五个角色，普通安装保留其他用户角色；普通 `grok` 也能发现这五个角色。清理模式会移走旧用户角色，同时保留新发布的五个角色。Codex 原生 `skills/.system` 保留。

Codex 开发 profile 仍是生成文件；升级额外保留其中已有的顶层 `model`、`model_reasoning_effort` 字符串选择，未设置时不新增默认值。其他手写字段和注释不保证保留，个人运行配置通常放原生基础配置或启动参数。当前配置文件不能证明已有会话的实际挡位，排查时以原生会话记录为准。

Claude 只在 `settings.json` 中管理一条 `claudeMdExcludes`，排除运行安装器时 HOME 下的默认 `.claude` 指令，保留其他设置。清理模式另移除明确的旧扩展注册。不要把个人扩展直接放在安装器整体管理的目录中。

`--home DIR` 指定安装与清理目标，不更改进程 HOME；Codex/Grok 使用该目录下的标准 `.codex`、`.grok` 位置，运行时应使用对应 HOME。若安装环境中的 `CODEX_HOME` 或 `GROK_HOME` 指向不同目录，所选端会在发布前明确报错。本安装器不迁移自定义配置根；以后更换运行 HOME 或自定义根，需在新根准备相应 profile 和角色。Claude 排除项仍根据安装进程 HOME 生成；要为另一运行 HOME 安装，应在相应 HOME 环境执行。源文件和目标父目录遇到不支持的链接或类型会明确失败。

可用临时目录预演，避免修改真实配置：

```sh
mkdir -p /tmp/dev-profile-preview
env -u CODEX_HOME -u GROK_HOME HOME=/tmp/dev-profile-preview \
  ./install.sh --target all --home /tmp/dev-profile-preview
```

## 验证与依据

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

安装测试在临时 HOME 中检查发布、清理、备份和参数透传。Codex/Grok 的原生加载检查不调用模型；Claude 的 opt-in 协议检查需要 localhost socket 权限：

```sh
CLAUDE_DEV_TEST_CLI=1 PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -p test_cli.py -v
```

配置加载不证明模型能自主完成任务。实际模型评估和未验证项见 [验证记录](docs/validation.md)、[行为评估](evals/README.md)。角色职责和安装边界见 [设计](docs/design.md)，来源与取舍见 [调研](docs/research.md)，当前执行状态见 [计划](plan.md)。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---
name: labor_rights_advisor
description: Use when a user describes a labor dispute with their employer (e.g.,
  dismissal, unpaid wages, contract issues, work injury, overtime disputes) and
  needs legal analysis, evidence recommendations, and action guidance under PRC
  labor law. Activates a structured investigation → legal research → opinion
  drafting pipeline. Mainland China jurisdiction only.
---

# 劳动权益法律顾问 Skill

## ⚠️ 隐私前置提示（启动时第一句话必须告知用户）

> 在我们开始之前，请了解：
> - **不要提供**身份证号、银行账号、家庭住址等敏感信息
> - 公司名称可用化名（如"A 公司"），不会影响法律分析
> - 本 skill 不存储对话内容，但请避免在公共渠道分享生成的意见书原文
> - 本意见书**不构成正式法律意见**，重大权益建议咨询执业律师
> - **如提供证据文件**（截图/PDF/录音等）：原始文件保存在本地 `evidence/` 目录，不上传；但解析后的**文字内容会进入当前对话所用 AI 模型上下文**。如有不愿让模型服务商知晓的内容（商业机密、第三方隐私、刑事敏感细节等），请在提供前自行脱敏或剪辑
> - **录音证据额外说明**：录音用本地 FunASR 模型转写，**音频内容不离开您的电脑**，仅转写文字进入模型上下文

## 适用范围

**适用：** 中国大陆境内企业/个体经济组织与劳动者的劳动争议，覆盖 10 类高频争议
（违法解除、拖欠工资、未签合同、加班费、工伤、调岗降薪、竞业限制、服务期、经济补偿、社保）。

**不适用：** 公务员人事争议、涉外劳动争议、劳务外包非劳动关系纠纷。
若识别到这些情形，明确告知用户超出范围，建议转向对应渠道。

## 执行流水线

使用 TodoWrite 跟踪以下 6 个阶段。

### 阶段 1：初步调查（最小必填）

向用户收集 3 项必填信息：

| 字段 | 提示语 |
|------|--------|
| 争议基本描述 | "请用 1-3 句话描述发生了什么、您希望达到什么结果" |
| 当前用工状态 | "您目前是：在职 / 已离职 / 被辞退 / 协商解除中？" |
| 公司所在城市 | "公司所在地（用于地方政策与仲裁管辖）" |

**收集原则：**
- 一次可问一项或多项，保持对话感
- 缺失时精确追问（"请问您当前是否还在职？"），不空泛问"还有什么要补充"
- 用户说"不知道/跳过"即记录为【需补充】，不阻塞流程

### 阶段 2：争议类型识别 + 动态深化

1. 根据用户描述识别争议类型（**可能多类并行**），候选 10 类争议及其标识 token：
   - `illegal_dismissal` 违法解除 / 违法辞退
   - `unpaid_wages` 拖欠工资 / 克扣工资
   - `no_written_contract` 未签劳动合同（二倍工资差额）
   - `overtime_pay` 加班费争议
   - `work_injury` 工伤认定与待遇
   - `position_change` 调岗降薪 / 变更劳动合同
   - `non_compete` 竞业限制争议
   - `service_period` 服务期与违约金（培训服务期）
   - `economic_compensation` 经济补偿金 / 赔偿金计算
   - `social_insurance` 社保与公积金争议
2. **加载 `references/dispute-patterns.md`**
3. 按识别出的 token，从该类型的"必问项"中生成针对性问题
4. 用户回答任意几项即可，缺失项标【需补充】
5. 若多类并行，分别处理但合并提问避免重复

### 阶段 3：证据收集与解析

**主动询问而非被动等待——给用户明确的"该出示证据了"的信号。**

加载 `references/evidence-collection.md`，按其执行：

1. **主动询问证据**：
   > 您手里目前有哪些证据？可以提供：
   > - **文字**：直接粘贴聊天记录、邮件、通知书内容
   > - **图片**：截图、拍照（合同、工资条、通知书、微信聊天等）
   > - **PDF**：合同、银行流水、解除通知等
   > - **录音**：mp3/wav 文件路径
   >
   > 没准备好的话，可以一项一项慢慢来，也可以稍后再补充。

2. **创建 session 目录**：收到第一条证据时按 `evidence/<YYYY-MM-DD>-<化名>-<争议类型简称>/` 命名规范创建，详见 evidence-collection.md 第四节。

3. **逐条解析**：
   - **文本**：直接进入上下文，抽取关键事实，原文同时存 `sources/ev_XXX.txt`
   - **图片**：用 Read 工具多模态视觉理解（识别文字、公章、截图来源）。**若 Read 失败/返回空（纯文本模型）→ 走 evidence-collection.md 第八节"模型能力降级"流程**
   - **PDF**：用 Read 工具读取（文本型 PDF 直接提取；扫描件 PDF 若返回乱码 → 同样走降级流程）
   - **录音**：见下方"3.x 录音证据的专门处理"子节。**录音不受对话模型能力影响**（FunASR 完全本地）
   - 每条证据写一张卡片到 `cards/ev_XXX.json`，schema 见 evidence-collection.md 第二节；降级证据额外填 `degradation_note` 字段

4. **交叉校验**：所有证据解析完成后，对照同类型事实进行交叉校验（同一事实被多条证据支撑 ✓，矛盾点提示用户核实）。

5. **生成 `summary.md`**：按 evidence-collection.md 第四节格式汇总关键事实、交叉校验笔记、缺失的关键证据。

6. **告知用户**：已解析的证据数量、关键事实清单（直白语言）、建议补充的证据清单（对照 dispute-patterns.md 该类型的"证据清单"）。

**用户的证据文件保存到本地 `evidence/` 目录；解析后的文字内容会进入当前 AI 模型上下文——这是不可避免的设计权衡，必须在阶段 3 启动前明确告知用户。**

#### 3.x 录音证据的专门处理

当用户在阶段 1/2/3 任意时点提供音频证据路径（如"我有录音证据：D:/xxx.mp3"），启动以下流程。

### 阶段 4：法律依据检索

**3.1 法条检索：**
- 加载 `references/dispute-patterns.md` 中该类型的"法条映射"
- 按映射读取 `references/labor-law-full.md` 或 `references/labor-contract-law-full.md` 中的对应条文
- **必须使用法条原文，不得改写或凭记忆**

**3.2 案例检索（双轨）：**

*轨道 A — 内置案例：*
- 加载 `references/built-in-cases.md`
- 按争议类型 token（如 `illegal_dismissal`）匹配案例字段
- 优先匹配与用户情形高度相似的案例

*轨道 B — WebSearch 补充：*
- 仅在轨道 A 未覆盖或需要本地区案例时启动
- 预设检索源：
  - `site:wenshu.court.gov.cn`
  - `site:pkulaw.com`
  - `site:chinacourt.org`
- 关键词模板：`<争议类型> + <城市> + <关键事实> + 判决`
- **结果必须标注 URL 与发布日期，优先近 3 年**
- 不引用无法溯源的"判例"

### 阶段 5：生成《法律意见书》

加载 `references/opinion-template.md`，按模板八节填充。

**填充规则：**
- 缺失信息用【需补充：字段名】占位，禁止编造
- 涉及金额必须列公式，不直接给"大概 X 万"
- 所有引用标注可信度分级（见下节）
- **第四节"证据清单"必须从 `evidence/<session>/cards/` 与 `summary.md` 引用**——若阶段 3 未收集到证据（用户跳过），按 dispute-patterns.md 该类型的"证据清单"给出固定建议，并在意见书中标注"尚未取得，建议固定"

**行动模板按需加载（仅在意见书第五节引用时）：**
- `references/action-templates/要求出具书面解除通知函.md`
- `references/action-templates/劳动仲裁申请书.md`
- `references/action-templates/律师函.md`

### 阶段 6：风险提示 + 后续行动

在意见书第六、八节中：
- 时效提醒（仲裁时效 1 年等）
- 维权路径建议（协商 → 监察 → 仲裁 → 诉讼）
- 直白行动清单（按紧迫度与难度分级）

## 依据可信度分级标注规则

所有引用必须标注：

```
【★★★ 法律条文】      宪法、法律、行政法规、司法解释（最高效力）
【★★☆ 司法案例】      最高人民法院指导案例/公报案例、本地区近年生效判决
【★☆☆ 参考资料】      新闻报道、律师实务文章、地方人社局指导意见、学术观点
```

**关键约束：**
- 意见书中所有引用必须标注级别
- ★☆☆ 资料不可单独支撑关键结论
- 若某结论仅有 ★☆☆ 依据，必须明确告知"该结论需进一步核实"

## 边界场景处理

| 情形 | 处理方式 |
|------|---------|
| 公务员/事业编人事争议 | 明确告知"不适用《劳动法》/《劳动合同法》"，建议转向《公务员法》或人事仲裁渠道 |
| 涉及劳务派遣、非全日制用工、外包 | 正常处理但特别标注法律关系差异，引用《劳动合同法》第二节、第五节 |
| 诉求涉及刑事（如拒不支付劳动报酬罪） | 给出民事维权路径 + 提示可同时向公安机关报案 |
| 已签署和解协议/调解书 | 评估协议效力（是否显失公平、受胁迫）后给出后续建议，不直接鼓励反悔 |
| 涉外劳动争议 | 提示超出 skill 范围，建议咨询涉外劳动法律师 |
| 事实严重缺失、用户拒绝补充 | 出具"框架性意见"（仅法律分析 + 通用证据建议），明确标注"待事实补充后细化" |

## 安全机制（避免给错建议）

1. **条件式表达**：所有行动以"假设您描述的事实成立"为前提；事实未明先追问
2. **金额阈值校验**：金额必须列公式并标注"基于您提供的数据 X"，禁止编造精确数字
3. **不杜撰联系方式**：电话/网址/地址若非内置已知，必须 WebSearch 验证，标注"以官方最新公布为准"
4. **明确边界**：意见书末尾固定声明不构成正式法律意见
5. **高风险动作强制提示**：标 ⚠️ 的操作必须先建议咨询律师

## 录音证据处理详细流程（阶段 3 子节 3.x 的展开）

> 本章节展开阶段 3"证据收集与解析"中录音证据的 9 步处理流水线与错误处置表。
> 当用户在阶段 1/2/3 任意时点提供音频证据路径时，按以下流程执行。

当用户提供音频证据路径（如"我有录音证据：D:/xxx.mp3"），启动以下流程。

### 处理流水线

#### Step 1：环境检测

调 `scripts/setup.sh --check`。若未就绪，告知用户："需安装 FunASR（约 3GB，10-20 分钟，走国内镜像）"，征得同意后跑 `bash scripts/setup.sh --install`，并安装 ffmpeg（Windows: `winget install Gyan.FFmpeg`）。

#### Step 2：隐私告知 + 时长估算

**首次处理必须完整展示以下说明，征得用户明确同意：**

```
🔒 录音证据处理 - 隐私说明

✅ 完全本地处理：
- 录音文件不上传到任何服务器
- 语音转文字使用本机运行的 FunASR 模型，音频内容不离开您的电脑

⚠️ 会发送给您当前使用的大模型服务商：
- 转写后的文字内容会被提交给当前对话所用的 AI 模型
- 用于：角色推断、证据抽取、意见书生成
- 数据处理遵循您所使用平台的服务条款与隐私政策

🤔 请在提供录音前判断：
转写后的文字中是否可能包含您不愿让模型服务商知晓的信息？
- 身份证号、银行账号、家庭住址
- 商业机密、未公开的公司内部信息
- 第三方隐私（他人身份证/电话等）
- 涉及刑事犯罪的敏感细节

如有顾虑，建议您先自行处理：
- 剪辑掉录音中的敏感片段再提供
- 仅提供录音的文字摘要（您手动转写并脱敏）
- 用文字描述录音关键内容，代替提供录音本身
- 选择不提供录音证据，改走其他证据路径

一旦您提供录音路径，本 skill 将开始处理，转写文字会进入模型上下文。
```

用 `ffprobe` 取音频时长，告知用户预期处理时间：
- CPU：30 分钟音频约 12-18 分钟
- GPU：30 分钟音频约 2-4 分钟

#### Step 3：热词准备

读 `references/audio-keywords.md` 静态基线；从案件上下文（公司名、岗位、争议类型）抽专属热词；用 `scripts/hotword_utils.py` 合并写入 `evidence/<audio-name>_<date>/hotwords.json`。

#### Step 4：启动脱离会话的后台进程

创建证据文件夹，启动真正脱离 agent 会话的进程。

**Linux / macOS / Git Bash**：
```bash
setsid python scripts/process.py \
    --audio <path> \
    --hotwords evidence/<name>_<date>/hotwords.json \
    --output evidence/<name>_<date>/result.json \
    > evidence/<name>_<date>/processing.log 2>&1 < /dev/null &
disown
```

**Windows PowerShell**（必须用 `cmd /c start /B` 触发 DETACHED_PROCESS，不能用 Start-Process）：
```powershell
cmd /c start /B python scripts/process.py `
    --audio <path> `
    --hotwords evidence/<name>_<date>/hotwords.json `
    --output evidence/<name>_<date>/result.json `
    > evidence/<name>_<date>/processing.log 2>&1
```

#### Step 5：告知用户等待 + 检查信号

```
已启动后台处理，预计 12-18 分钟。

请留意 evidence/<name>_<date>/ 文件夹：
- processing.log   ← 进度日志，可随时查看
- result.json     ← 全部完成（看到此文件就告诉我"好了"）
- error.json      ← 仅失败时出现

完成后请回复我，我继续角色推断和证据抽取。
在此期间我推进其他事实调查/法律检索。
```

agent 在同会话内继续推进其他阶段任务（阶段 1-2 的事实补充、阶段 4 的法律检索等）。用户也可关掉 agent，稍后只要 result.json 存在，直接说"录音处理好了，继续"即可恢复。

#### Step 6：用户信号触发 → 角色推断

收到用户"好了"/"done"/"result.json 出现了"等信号后：
- 若 `error.json` 存在 → 跳到错误处理
- 读 `result.json` + `references/speaker-roles.md`
- 对每个 speaker_id，分析其发言，从 taxonomy 选最匹配角色 + 置信度 + 理由

#### Step 7：用户确认角色映射

展示推断结果给用户。用户确认后写入 `evidence/<name>_<date>/role_mapping.json`：

```json
{
  "propagated_to_cards": false,
  "mappings": [
    {"speaker_id": "spk_0", "role": "HR/人力资源", "confidence": "high", "reason": "..."},
    {"speaker_id": "spk_1", "role": "员工本人", "confidence": "high", "reason": "..."}
  ]
}
```

`propagated_to_cards: false` 表示已确认但尚未写入卡片；Step 8 完成后翻为 `true`——这样若中途中断，agent 可识别"角色已确认但卡片未生成"状态并恢复。

用户放弃 → 以原始 spk_id 进入下一步，卡片 `speaker_role="未识别角色"`（写入卡片但 reliability_level 降级提示）。

#### Step 8：证据卡片抽取

按争议类型扫描关键词（参见 `references/dispute-patterns.md` 对应 token 的"识别关键词"）。数字交叉校验，冲突标注。卡片写入 `evidence/<name>_<date>/cards/ev_XXX.json`，字段：

```json
{
  "card_id": "ev_001",
  "timestamp": "00:03:12-00:03:25",
  "speaker_id": "spk_0",
  "speaker_role": "HR/人力资源",
  "quote": "公司决定从今天起解除与你的劳动合同",
  "evidence_type": "解除意思表示",
  "dispute_relevance": "illegal_dismissal",
  "confidence": "high",
  "cross_role_conflict": false,
  "verification_notes": "无交叉验证冲突",
  "reliability_level": "★☆☆"
}
```

跨角色冲突检测可调用 `scripts/conflict_detection.py` 的 `detect_cross_role_conflicts()`（纯确定性逻辑：同 evidence_type 下出现 ≥2 个不同公司方角色即触发冲突标记）。

写完卡片后更新 `role_mapping.json` 的 `propagated_to_cards: true`。

#### Step 9：接入意见书

加载 `references/opinion-template.md`，第四节"事实与证据"按以下格式引用：

```
【★☆☆ 录音证据】2024-XX-XX 谈判录音 00:03:12-00:03:25
   （HR/人力资源 发言）："公司决定从今天起解除与你的劳动合同"
   ⚠️ 该内容由 AI 语音转写获得，可能存在误识，建议核对原始录音
```

**录音证据统一标 ★☆☆**（参考资料级），原因：
1. ASR 转写存在误识可能
2. 角色推断是 LLM 主观判断，非法律认定
3. 录音完整性未经验证（可能被剪辑）

意见书末尾追加免责："本意见书引用的录音证据由 AI 自动转写与推断，不构成原始证据，请在仲裁/诉讼中提交原始录音载体。"

### 错误处理

参见设计文档 §8。核心原则：不静默失败、不阻塞主流程、降级路径三选一（重试 / 降级模型 / 跳过）。

agent 遇到以下情况时的处置规则：

| 触发条件 | 处置 |
|---------|------|
| 音频 > 2 小时 | 告知用户"超长音频处理耗时，建议剪辑关键片段"，征得同意后继续 |
| 0 张证据卡片抽出 | 不报错，在意见书第四节注明"未在录音中识别到强相关证据片段"，让用户决定是否补充 |
| ASR 转写质量过低（全篇都是乱码/单字） | 告知用户"转写质量过低，建议改用其他证据路径"；不接入意见书 |
| 录音中含第三方隐私（他人身份证/电话等） | 提示用户"转写文字将进入模型上下文，如涉及他人隐私请自行剪辑后再提供" |
| 模型文件损坏（校验失败） | 提示用户跑 `bash scripts/setup.sh --redownload-models` |
| 单一说话人（全员同一 spk_id） | 跳过角色推断，直接抽取证据，卡片 speaker_role 全填"未识别角色" |
| 磁盘空间不足 | 告知具体缺口，让用户清理后重试 |

# 贡献指南

感谢你考虑为 Labor Rights Advisor Skill 做出贡献！这个项目的目标是帮助中国大陆员工更好地维护自身劳动权益，每一次贡献都可能让一个普通劳动者少走一段弯路。

## 行为准则

本项目旨在推动劳动者权益保护。请参与者保持友善、专业、尊重他人的交流方式。
任何形式的歧视、骚扰、人身攻击均不会被接受。

## 如何贡献

### 报告问题

如果发现以下情况，请通过 [GitHub Issues](../../issues) 反馈：

- 法律条文引用错误（条款号、原文有误）
- 案例案号无法溯源或已失效
- WebSearch 检索建议不合理
- 意见书模板某节填充有问题
- 边界场景识别错误（如把公务员争议误识别为劳动争议）
- 文档措辞存在误导风险

提 Issue 时请尽量包含：
1. 涉及的文件路径与具体行号
2. 复现步骤（如果是行为问题）
3. 期望结果 vs 实际结果
4. （可选）权威佐证来源 URL

### 提交 Pull Request

**PR 前请确认：**

1. 法条引用与官方来源交叉验证（人社部 / 最高法 / 全国人大等 gov.cn 域名）
2. 新增/修改案例必须可溯源（标注案号或指导案例编号 + URL）
3. 不引入任何"判例"或"内部消息"等无法核验的内容
4. 修改 `references/labor-*-full.md` 时必须基于权威官方源，不改一字
5. 修改 `references/dispute-patterns.md` 时确保所有条款编号在两个全文文件中存在
6. 提交信息使用约定式提交（Conventional Commits），如 `feat:` / `fix:` / `docs:` / `refactor:`

**PR 流程：**

```bash
# 1. Fork 后克隆本地仓库
git clone https://github.com/<你的用户名>/labor_rights_skills.git
cd labor_rights_skills

# 2. 创建分支
git checkout -b feat/add-pregnancy-protection

# 3. 修改文件并本地验证
#    （建议用 1-2 个典型场景跑通流水线）

# 4. 提交
git commit -m "feat: add 三期保护 (pregnancy/maternity/lactation) dispute type"

# 5. 推送并发起 PR
git push origin feat/add-pregnancy-protection
# 然后在 GitHub 网页发起 Pull Request
```

## 特别欢迎的贡献方向

- **新增争议类型** —— 如女职工三期保护、劳务派遣专属规则、非全日制用工、灵活就业
- **地方法规差异** —— 北上广深之外的二三线城市地方性法规与仲裁实践
- **案例库扩充** —— 补充近 3 年生效的指导案例或公报案例
- **行动模板** —— 新增《解除劳动合同通知书》《EMS 寄送回执模板》等用户可直接使用的骨架文档
- **多语言** —— 翻译为英文、繁体中文等其他语言版本
- **UI/UX** —— 改进意见书模板的易读性，特别是「直白行动清单」部分

## 法律相关的特别说明

由于本项目涉及法律内容，请特别注意：

1. **不要提交付费墙后的内容** —— 必须是公开可访问的来源
2. **不要提交"个人经验之谈"** —— 所有法律依据必须有官方或权威第三方出处
3. **不要删除或弱化免责声明** —— 任何降低风险提示的修改都会被拒绝
4. **修改法律全文文件时请慎重** —— 这些文件是 skill 的基础事实来源，任何改动必须基于权威官方公告

## 开发环境

### 纯内容编辑（法律/案例/模板）

如果只改 Markdown 内容（`SKILL.md` / `references/*.md` / 行动模板），**无需安装 Python 依赖**：

- 克隆后即可编辑
- 推荐 VS Code + Markdownlint 插件
- Git 行尾：未配置 `.gitattributes`，Windows 用户会看到 LF→CRLF 警告，可忽略

### 录音证据处理（Python / FunASR）

如果要修改 `scripts/` 下的代码（process.py / diarization_utils.py / setup.sh 等）或运行测试，需要 Python 环境：

```bash
# 一键安装（推荐，处理了所有已知坑）
bash scripts/setup.sh --install

# 验证
bash scripts/setup.sh --check
```

完整依赖清单见 `scripts/requirements.txt`，约 3GB（主要是 torch + FunASR 模型）。

### 已知安装问题与解决

测试中踩过的坑，汇总在此供后人参考：

| 问题 | 现象 | 原因 | 解决 |
|------|------|------|------|
| **Python 3.13 + funasr 1.0.27 不兼容** | `pip install funasr==1.0.27` 报 `torch<2.3.0` 无 cp313 wheel | funasr 1.0.27 依赖 torch<2.3.0，该版本无 Python 3.13 wheel | `requirements.txt` 已改为 `funasr>=1.3.0` + `torch>=2.0.0` |
| **`editdistance` 编译失败** | 安装时报 `error: Microsoft Visual C++ 14.0 or greater is required` | editdistance 无 cp313 wheel，需 MSVC 编译；该包仅用于 funasr 的 CER/WER 评估，不影响推理 | `setup.sh install_deps` 用 `pip install --no-deps funasr`，手动安装其他依赖；`editdistance` 被跳过 |
| **Git Bash 路径无法被 Python 识别** | `MODELS_DIR=/d/playground/...` 传给 Python 后变成 `D:\d\playground\...` | Git Bash 的 `/d/` 路径 Windows Python 看不懂 | `setup.sh download_models` 用 `cygpath -w` 转 Windows 路径 |
| **`torchaudio.info()` 已废弃** | 调时报 `module 'torchaudio' has no attribute 'info'` | torchaudio 2.0+ 移除了该 API | `process.py` 的时长检测用 `librosa.get_duration()` 作 ffprobe fallback |
| **`ffprobe` 不在 Git Bash PATH** | process.py 启动即报 `[WinError 2] 系统找不到指定的文件` | Git Bash for Windows 不继承系统级 ffmpeg PATH | `process.py` 已加 librosa fallback，ffprobe 现在是**可选的** |
| **fsmn-vad 模型缺失** | diarization 只返回 1 个 spk_unknown | VAD 模型未下载，CAM++ 拿到的是整段单一 embedding | `setup.sh` 的 `MODELS` 数组已含 fsmn-vad；若已装旧版可手动跑 `bash scripts/setup.sh --redownload-models` |
| **punc length-mismatch** | `sentence_info` 残缺（仅 1-2 条），但 `full_text` 完整 | FunASR 1.3.14 的 punc 模型 token 数与 ASR timestamp 长度不一致 | `process.py` 自动检测退化 + 重跑禁 punc；`result.json` 的 `diarization_status` 字段标 `degraded` |
| **禁 punc 后 segment text 为空** | 禁 punc 重跑后 `asr_text_chars: 0` | 禁 punc 时 sentence_info 字段名是 `sentence` 而非 `text` | `process.py _parse_res` 兼容两种字段名 |
| **禁 punc 后中文间多余空格** | 转写文本显示 `"我 想 问 一 个"` | 禁 punc 时 FunASR 输出 token 级，每字一空格 | `process.py _clean_token_spaces` 去中文字符间空格，保留英文/数字间空格 |

### 模型与代码一致性约束

`setup.sh` 的 `MODELS` 数组与 `process.py` 顶部 4 个常量必须保持一致：

```
VAD_MODEL  = iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
ASR_MODEL  = iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
SPK_MODEL  = iic/speech_campplus_sv_zh-cn_16k-common
PUNC_MODEL = iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727
```

如果改 `process.py` 引入新模型，**必须同步更新** `setup.sh` 的 `MODELS` 数组与 `download_models()` 函数里的 Python list。否则新装环境会缺模型。

### 测试

```bash
# 快速测试（无需 FunASR，秒级）
python -m pytest tests/ scripts/tests/

# 完整测试（含 FunASR 集成测试，需先跑 setup.sh --install）
python -m pytest tests/ scripts/tests/ -m "integration"
```

## 联系维护者

- 安全/法律风险相关问题：通过 GitHub Issues 公开提（避免私下沟通，便于社区审视）
- 一般性讨论：可在 Issue 中发起

---

再次感谢你的贡献！每一个被合并的 PR，都可能在未来帮助某个真正需要它的人。⚖️

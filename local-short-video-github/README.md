<div align="center">

# local-short-video

把本地图片和视频整理成可验证、可复用、可交付的短视频项目。

<sub>Codex Skill · Local Assets · TTS · Subtitle QA · FFmpeg · Mobile MP4</sub>

</div>

---

## 项目定位

`local-short-video` 是一个通用的 Codex Skill。它从用户指定的工作区和素材区出发，为商品、门店、活动、教程、服务或内容展示生成短视频，并保存完整的脚本、音频、字幕、素材清单、过程记录和验证报告。

它不绑定 Primer Mall，也不绑定任何品牌、行业、语言、盘符或目录结构。使用者只需要告诉 Codex：工作区在哪里、素材在哪里、想剪什么类型的视频，以及语言和时长。

它不把“有一个 MP4 文件”当作完成，而是把生产流程拆成可复现的质量门禁：素材可追溯、配音可验证、字幕与口播一致、编码适合手机播放、素材使用次数可累计。

| 目标 | 产物 | 价值 |
| --- | --- | --- |
| 配置项目 | `project_config.json` | 保存工作区、素材区、语言、音色、时长和输出规则 |
| 选择素材 | `selected_assets.json`、接触表 | 让每个镜头有来源、有角色、有预览 |
| 生成口播 | `script_source.txt`、`script_review.txt` | 保存原语言文案和审阅翻译，避免把译文误送进 TTS |
| 生成配音 | `voice.*`、`selected_voice.json` | 记录音色、语速、音高和实际语音文件 |
| 生成字幕 | `*.vtt`、`*.srt`、`*.ass` | 从 TTS 时间轴生成字幕，不凭感觉估时 |
| 渲染成片 | `final_*_mobile.mp4` | 输出 H.264、AAC LC stereo、1080x1920 的手机兼容视频 |
| 质量门禁 | `validation_report.json` | 检查时长、编码、音量、画面、字幕和安全区 |
| 素材追踪 | `used_assets.*`、asset ledger | 记录每个素材在本片中的使用次数和时间段 |

## 工作流总览

| 阶段 | 输入 | 动作 | 输出 |
| --- | --- | --- | --- |
| 1. 配置 | 工作区、素材区、视频需求 | 创建项目配置和输出目录 | `project_config.json`、`process.md` |
| 2. 预检 | 配置、Python、FFmpeg、TTS | 检查路径、写权限、音色和真实 TTS 探针 | `preflight_report.json` |
| 3. 选材 | 本地图片和视频 | 扫描、分类、排除低可信目录、按角色和使用次数排序 | `selected_assets.json`、CSV |
| 4. 预览 | 选片清单 | 截取视频画面并生成接触表 | `preview_assets_contact_sheet.jpg` |
| 5. 文案 | 视频类型、可见画面、用户事实 | 写原语言口播和审阅翻译 | `script_source.txt`、`script_review.txt` |
| 6. 配音 | 原语言口播、目标音色 | 生成音频和 WebVTT，检查全文一致 | `voice.mp3`、`voice.vtt` |
| 7. 字幕 | WebVTT / SRT | 规范化时间轴并生成安全区 ASS | `captions.srt`、`captions.ass` |
| 8. 剪辑 | 选片、配音、字幕 | 静音源素材、拼接镜头、烧录字幕、混合配音 | `final_*_mobile.mp4` |
| 9. 验证 | 成片、脚本、SRT、ASS | 检查编码、音量、非空画面、字幕和安全区 | `validation_report.json` |
| 10. 交付 | 通过的项目 | 更新素材台账并整理过程记录 | 成片、双语文案、完整项目包 |

### 产物关系

| 来源 | 生成 | 继续流向 |
| --- | --- | --- |
| 工作区和素材区 | `project_config.json` | 预检、选材、渲染和台账 |
| 本地媒体 | `selected_assets.json`、接触表 | 文案事实核对和镜头拼接 |
| 最终口播 | 音频、VTT、SRT、ASS | 渲染和字幕全文校验 |
| 选片清单 | `used_assets.json` | 素材使用次数台账 |
| 成片 | `validation_report.json`、最终接触表 | 交付或返工 |
| 用户反馈 | 新项目版本或同项目重渲染 | 下一轮选材、文案和质量门禁 |

## 目录结构

```text
local-short-video-skill/
├── README.md
├── LICENSE
├── VERSION
├── requirements.txt
├── install.ps1
├── install.sh
├── .github/
│   └── workflows/
│       └── validate.yml
├── tools/
│   └── validate_package.py
└── skills/
    └── local-short-video/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── copywriting-voice.md
        │   ├── editing-subtitles.md
        │   └── workflow.md
        └── scripts/
            ├── audition_voices.py
            ├── create_contact_sheet.py
            ├── create_pop_ass.py
            ├── create_project.py
            ├── normalize_subtitles.py
            ├── preflight_local_video.py
            ├── preflight_local_video.ps1
            ├── render_local_video.py
            ├── select_assets.py
            ├── synthesize_voice.py
            ├── update_asset_usage.py
            ├── validate_final.py
            └── video_common.py
```

生成后的项目通常长这样：

```text
outputs/local-video-topic-30s/
├── project_config.json
├── process.md
├── preflight_report.json
├── selected_assets.json
├── selected_assets.csv
├── preview_assets_contact_sheet.jpg
├── preview_final_contact_sheet.jpg
├── script_source.txt
├── script_review.txt
├── voice.mp3
├── voice.vtt
├── captions.srt
├── captions.ass
├── used_assets.json
├── used_assets.csv
├── validation_report.json
└── final_topic_mobile.mp4
```

## 快速安装

### 从 GitHub 克隆

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/<account>/local-short-video-skill.git \
  /tmp/local-short-video-skill
cd /tmp/local-short-video-skill
```

Windows 可以直接运行安装脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

已有同名 Skill 时，安装脚本会先生成带时间戳的备份目录：

```powershell
.\install.ps1 -Destination "F:\Codex\skills\local-short-video"
```

如果需要安装 `edge-tts`：

```powershell
.\install.ps1 -InstallDependencies
```

macOS 或 Linux：

```bash
sh ./install.sh
sh ./install.sh /path/to/codex/skills/local-short-video --install-dependencies
```

安装后重启或重新加载 Codex。

## 快速上手

### 1. 初始化项目

对 Codex 说：

```text
请使用 $local-short-video。
工作区：D:/VideoWorkspace
素材区：D:/VideoMaterials
制作一支 30 秒竖屏商品展示视频，使用西班牙语口播。
不添加背景音乐和音效。
```

也可以直接创建配置：

```bash
python skills/local-short-video/scripts/create_project.py \
  --workspace /path/to/workspace \
  --materials /path/to/materials \
  --topic "Product showcase" \
  --video-type product_showcase \
  --language es-MX \
  --review-language zh-CN \
  --duration 30 \
  --voice es-MX-DaliaNeural
```

### 2. 运行预检

```bash
python skills/local-short-video/scripts/preflight_local_video.py \
  --config /path/to/outputs/local-video-topic-30s/project_config.json
```

预检会检查素材目录、输出写权限、FFmpeg、Python、目标音色，以及一次真实的 TTS 音频和字幕时间轴生成。

如果 `edge-tts`、联网或目标音色不可用，流程会停止，不会用静音视频冒充完成品。

### 3. 选择素材并查看接触表

```bash
python skills/local-short-video/scripts/select_assets.py \
  --config /path/to/outputs/local-video-topic-30s/project_config.json \
  --category "玩具" \
  --exclude "90_待识别" \
  --exclude "thumbs" \
  --count 12

python skills/local-short-video/scripts/create_contact_sheet.py \
  --manifest /path/to/outputs/local-video-topic-30s/selected_assets.json \
  --out /path/to/outputs/local-video-topic-30s/preview_assets_contact_sheet.jpg
```

接触表确认后再写文案。需要露出门头、地址、人物或具体产品时，必须检查并锁定素材中的正确时间段，不能随机截取开头。

### 4. 生成配音和字幕

```bash
python skills/local-short-video/scripts/synthesize_voice.py \
  --script /path/to/project/script_source.txt \
  --voice es-MX-DaliaNeural \
  --rate +12% \
  --pitch +6Hz \
  --media /path/to/project/voice.mp3 \
  --vtt /path/to/project/voice.vtt

python skills/local-short-video/scripts/normalize_subtitles.py \
  --in /path/to/project/voice.vtt \
  --out /path/to/project/captions.srt \
  --script /path/to/project/script_source.txt

python skills/local-short-video/scripts/create_pop_ass.py \
  --in /path/to/project/captions.srt \
  --out /path/to/project/captions.ass \
  --style pop-yellow \
  --position lower
```

字幕必须来自 TTS 的真实时间轴。脚本修改后要重新生成音频、VTT、SRT 和 ASS，不要手工把旧字幕套到新文案上。

### 5. 渲染和验证

```bash
python skills/local-short-video/scripts/render_local_video.py \
  --manifest /path/to/project/selected_assets.json \
  --voice /path/to/project/voice.mp3 \
  --ass /path/to/project/captions.ass \
  --out /path/to/project/final_topic_mobile.mp4 \
  --duration 30 \
  --pacing energetic

python skills/local-short-video/scripts/validate_final.py \
  --video /path/to/project/final_topic_mobile.mp4 \
  --script /path/to/project/script_source.txt \
  --srt /path/to/project/captions.srt \
  --ass /path/to/project/captions.ass \
  --duration 30

python skills/local-short-video/scripts/update_asset_usage.py \
  --manifest /path/to/project/used_assets.json \
  --ledger-dir /path/to/workspace/.local-short-video/asset_usage \
  --project-name local-video-topic-30s
```

只有验证通过后才更新素材台账并交付最终 MP4。

## 配置字段

| 字段 | 说明 | 默认或示例 |
| --- | --- | --- |
| `workspace_root` | 持久化工作区和素材台账位置 | 用户指定 |
| `materials_root` | 本次扫描的本地图片和视频目录 | 用户指定 |
| `output_root` | 项目输出根目录 | `workspace_root/outputs` |
| `topic` | 视频主题 | 商品、活动、教程等 |
| `video_type` | 视频类型 | `showcase` |
| `language` | 口播语言或区域 | `es-MX`、`en-US`、`zh-CN` |
| `review_language` | 审阅翻译语言 | 可选 |
| `voice.name` | 目标 TTS 音色 | 先从实时音色列表中试听 |
| `voice.rate` | TTS 语速 | `+6%` 到 `+16%` 可作为轻快起点 |
| `voice.pitch` | TTS 音高 | 根据音色和受众试听决定 |
| `format.duration` | 目标时长 | `30` 秒 |
| `format.width/height` | 画布尺寸 | `1080x1920` |
| `format.fps` | 帧率 | `30` |
| `subtitles.style` | 字幕样式 | `pop-yellow`、`clean-white` 等 |
| `audio.source_audio` | 是否保留源素材音频 | 默认 `false` |
| `audio.music` | 背景音乐 | 默认 `null` |
| `audio.sound_effects` | 是否添加音效 | 默认 `false` |

## 文案和音色规则

| 规则 | 要求 |
| --- | --- |
| 可见事实 | 只说画面能支持或用户明确提供的内容 |
| 品牌和地址 | 用户明确提出后才写入，不从 Skill 默认继承 |
| 口播语言 | 原语言文案单独保存，翻译不能误送进 TTS |
| 音色选择 | 先列出并试听候选，不把一个音色硬编码到所有项目 |
| 配音失败 | 停止并报告原因，不降级为静音成片 |
| 语速过长 | 改文案或调整音色后重新生成完整时间轴 |
| 字幕内容 | 与口播逐字一致，只允许换行和连续事件拆分 |

## 视觉和字幕规则

- 单品近景与货架、走廊或环境镜头组合使用，避免整片只有一种视角。
- 静态图使用克制的 Ken Burns 运动，视频素材默认静音并按有效画面截取。
- 默认使用直接剪切，不用会遮挡产品的花哨转场。
- 默认不加 BGM 和音效，除非用户明确要求。
- 字幕使用安全区、强对比和一到两行布局，避免被短视频平台控件遮挡。
- 地址、价格、品牌名等信息属于独立叠加层，不替代口播字幕，也不能改变口播原文。

## 质量门禁

最终视频至少要通过以下检查：

| 检查项 | 合格条件 |
| --- | --- |
| 时长 | 与目标时长在容差内 |
| 画面 | 目标分辨率、30fps、非空帧 |
| 视频编码 | H.264、`yuv420p` |
| 音频编码 | AAC LC、48kHz、立体声、非静音 |
| 字幕文本 | SRT 与源语言脚本全文一致 |
| 字幕位置 | ASS 位置和行长在安全区内 |
| 素材记录 | 只有真正进入成片的素材计入使用次数 |
| 过程记录 | `process.md` 写明选片、音色、字幕、渲染和验证结果 |

## 不适合做什么

- 不适合伪造商品、价格、地址、库存、质量或活动信息。
- 不适合用随机镜头替代门头、招牌、人物或指定产品的关键露出。
- 不适合在配音失败时交付静音视频并声称已经完成。
- 不适合把审阅翻译直接当作口播脚本。
- 不适合把含个人隐私、客户资料或未授权媒体的素材上传到公开仓库。

## 隐私和许可证

素材默认保留在本地。`edge-tts` 生成配音时会将最终口播文本发送到 Microsoft 的语音服务，使用前应确认网络和隐私要求。

本仓库采用 MIT License。详见 `LICENSE`。

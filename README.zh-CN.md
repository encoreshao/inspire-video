# InspireVideo

[English](README.md) | **简体中文**

一个 Claude Code / Codex 工具集，包含两个技能（skill），用来制作 9:16 竖屏中英双语短视频（带同步字幕和封面图）：

| 技能 | 命令 | 输入 | 输出 |
| --- | --- | --- | --- |
| `inspire-video` | `/inspire-video` | 已获授权的播客、访谈或演讲素材（本地文件或视频链接） | 带同步双语字幕的讲者短视频 |
| `inspire-showcase` | `/inspire-showcase` | 网站、GitHub 或 GitLab 仓库、本地仓库，或你自己的截图 | 产品展示视频：设备外框、推近与高亮、双语字幕，可选用你自己克隆的声音配音 |

智能体按照每个技能的 `SKILL.md`（位于 `skills/<名称>/`）完成需要思考的部分：转写并选段，或读取网站或仓库并撰写脚本，再写出文案与翻译；版式和文字则由 [Remotion](https://www.remotion.dev/) 以确定性的方式渲染，因此屏幕上的文字始终准确。两个技能共用同一个渲染器、同一套主题和同一组工具。

> **状态：** 已在 macOS 上用一条真实视频完整跑通。`fetch.py`、`transcribe.py`、`render.py` 和 Remotion 渲染器均已实现。`src/inspire_video/` 里的模块只是占位：探测素材、选段、翻译和剪辑由智能体按 `SKILL.md` 完成。Linux 和 Windows 尚未测试。 展示类视频目前是实验性的：已用生成的测试图片和 macOS `say` 语音完整跑通；CosyVoice 3 声音克隆和 GitHub/GitLab 元数据调用只用测试替身验证过，仍需要你在自己的电脑上做第一次真实运行。

## 功能

### 访谈视频（`/inspire-video`）

- **输出：** 1080×1920 MP4（H.264 + AAC，30 fps），时长 40 秒到 2 分 30 秒，另有一张 1080×1920 的封面 PNG。面向 LinkedIn 和 Facebook 时，同一视频还会渲染一份 1080×1350（4:5）的版本并附带封面，详见“平台与视频格式”。
- **同步双语字幕：** 一次只显示一句短句（或长句中的一个分句），先英文后中文，随说话同步出现。每条字幕最多 100 个英文字符，且绝不会把两句话放在同一条里。
- **适配平台安全区：** 微信视频号和抖音在较高的手机上会裁掉 9:16 视频的两侧（每侧约 100 px）。所有内容都距左右边缘至少 114 px；标题固定在距顶部的某个位置（不会偏高）；最下方的内容止于底部按钮区之上（y = 1590）。4:5 版本有自己的安全区（两侧 60 px，内容止于 y = 1200 之上）。
- **分隔线与层次：** 标题与视频之间有一条居中的线，视频之后还有同样的一条；线条中间亮、向两端渐隐，上下各留一小段间距；视频面板周围有与主题协调的柔和阴影。
- **一体式面板：** 视频与字幕区合成一个圆角面板，中间没有缝隙，字幕区的高度随文字自动变化。
- **标题区：** 分类标签、中文主标题和英文副标题，字号相同。
- **底部信息：** 说话人的中英文姓名、职位、公司、演讲标题、来源、年份、节选区间和进度条。
- **多人出镜：** 在 `copy.speakers` 里列出所有人，并给每条字幕标注 `speaker` 编号；底部显示所有人的名字，并高亮当前说话的人。
- **主题：** `light`（默认）、`mist`、`ivory`、`sage` 和深色 `ink`。
- **链接或文件输入：** 确认版权后用 `yt-dlp` 下载，或用 `--file` 导入你自己下载好的文件。所有素材都会缓存，同一个视频不会重复获取。对要求登录的 YouTube 页面，提供可选的 `--cookies` 和 `--cookies-from-browser` 选项。
- **发布文案：** 为每个目标平台（微信视频号、抖音、小红书、B站、LinkedIn、Facebook；LinkedIn 和 Facebook 为英文）生成标题、描述和话题标签；按可编辑的各平台字数上限校验，输出可直接粘贴的文件，附带来源署名；版权未确认时会显示“未获准发布”警示。
- **安全检查：** 当版权未确认、字幕格式不对或可能截断语音时，`render.py` 会校验清单并拒绝渲染。

### 展示类视频（`/inspire-showcase`）

- **输入：** 网站（首页加导航里的页面，遵守 `robots.txt`）、GitHub 或 GitLab 仓库（含自建）、本地仓库，均可附带你自己的截图（截图优先）。
- **设备演示：** 竖长截图放进手机外框并配模糊背景，其余放进显示网址的浏览器外框；缓慢推近重点区域，配高亮圈和可选标注，镜头之间交叉淡入淡出。
- **脚本来自事实：** `brief.json` 保存带来源的确定性事实；智能体写 4 到 6 个镜头（一句不超过 100 个字符的英文加中文），绝不编造。
- **旁白在本机生成：** macOS `say`、Kokoro 或 CosyVoice 3，可使用你自己录音克隆的声音档案；镜头时长跟随音频。
- **保护措施：** 渲染前校验每个字段（会溢出版面的文字会被拒绝），素材版权未确认时不能渲染成片，并检查真实输出（尺寸、首帧不黑、安全区）。
- **与访谈视频同样的观感：** 相同的主题（`light` 到 `ink`）、信息卡、分隔线、安全区和封面。

## 环境要求

- macOS（已测试）或 Linux
- Python 3.11+
- Node.js 20+，用于 Remotion 渲染器（建议 20.19+；在 20.15 上 npm 会给出引擎警告，但可以运行）
- 仅下载 YouTube 链接时需要：[Deno](https://deno.com/) 或 [Bun](https://bun.sh/)（或 Node.js 20.19+），`yt-dlp` 要靠它解析 YouTube 的播放器脚本。Node 20.15 会被判定为不受支持。
- FFmpeg 和 ffprobe（`brew install ffmpeg` 或 `apt install ffmpeg`）
- 仅 Linux：需要 CJK 字体，例如 `fonts-noto-cjk`（macOS 自带宋体-简）。字体使用系统字体，不随项目打包。
- 约 4 GB 可用磁盘空间，用于 Whisper 模型、Chrome 和项目文件
- 展示类视频：为网站来源截图需要 Chrome 或 Chromium（自己提供截图则不需要）。旁白可选，引擎有：macOS `say`（无需安装）、Kokoro（`mlx-audio` 和 `brew install espeak-ng`）、CosyVoice 3（`uv`，约 9 GB，建议 Apple Silicon；见“展示类视频”）

## 安装

### 方式一：一行命令（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash
```

它会把仓库克隆到 `~/.inspire-video`，把两个技能（`inspire-video` 和 `inspire-showcase`）链接到 Claude Code 和 Codex，安装 Python 与 npm 依赖，并运行环境检查。也可以只选一个工具，或跳过依赖安装：

```bash
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude
curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- codex --no-deps
```

想先看脚本？可以打开 [`install.sh`](install.sh)，或下载后运行 `bash install.sh`。设置 `INSPIRE_VIDEO_HOME` 可以安装到 `~/.inspire-video` 以外的位置（技能里写的是 `~/.inspire-video`，所以用默认位置最省事）。

**更新：** 再运行一次同样的命令即可，它会拉取最新版本并重新链接。
**卸载：** `bash ~/.inspire-video/scripts/uninstall.sh` 会移除链接（你的输出文件保留；要彻底删除请自己删掉整个文件夹）。

### 方式二：让 Claude Code 或 Codex 帮你安装

打开 Claude Code 或 Codex，粘贴下面其中一段提示词。

**Claude Code**

```text
Install the InspireVideo skill from https://github.com/encoreshao/inspire-video for Claude Code.
1. Run: curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- claude
2. Run python3 ~/.inspire-video/scripts/check_env.py and fix anything missing (Python 3.11+, Node.js 20+, ffmpeg). Ask me before installing any system package with brew or apt.
3. Tell me to start a new session, then summarize how to use /inspire-video and /inspire-showcase. Do not process any video yet.
```

**Codex**

```text
Install the InspireVideo skill from https://github.com/encoreshao/inspire-video for Codex.
1. Run: curl -fsSL https://raw.githubusercontent.com/encoreshao/inspire-video/main/install.sh | bash -s -- codex
2. Run python3 ~/.inspire-video/scripts/check_env.py and fix anything missing (Python 3.11+, Node.js 20+, ffmpeg). Ask me before installing any system package with brew or apt.
3. Tell me to start a new session, then summarize how to use the inspire-video and inspire-showcase skills. Do not process any video yet.
```

**更新或卸载**（两种工具都适用）

```text
Update the InspireVideo skill by re-running its install command from https://github.com/encoreshao/inspire-video, then run its environment check and report the result.
```

```text
Uninstall the InspireVideo skill with bash ~/.inspire-video/scripts/uninstall.sh and confirm the links are gone. Do not delete my outputs.
```

安装之后，`/inspire-video setup`（或直接说“set up InspireVideo”）会让智能体重新运行环境检查并修复缺失项。

### 方式三：手动安装

```bash
git clone https://github.com/encoreshao/inspire-video.git ~/.inspire-video
bash ~/.inspire-video/scripts/install.sh claude    # 或：codex | both（加 --no-deps 可跳过依赖安装）
```

### 安装脚本做了什么

1. 把 `skills/` 下的每个技能文件夹以符号链接放进 `~/.claude/skills` 和/或 `~/.agents/skills`（之前链接仓库根目录的旧安装会被切换为按技能链接）；
2. 用 `pip install -e` 安装 Python 依赖（`faster-whisper`、带 `yt-dlp-ejs` 的 `yt-dlp[default]`、`pydantic`、`jsonschema`、`PyYAML`）；
3. 为 Remotion 项目运行 `npm install`；
4. 运行环境检查。

之后首次使用时还会下载：无头 Chrome（约 100 MB，首次渲染时）和 Whisper 模型（`small.en` 约 250 MB，`large-v3` 约 3 GB）。

随时可以检查环境：`python3 ~/.inspire-video/scripts/check_env.py`

可选：只有使用托管的大模型服务时，才需要把 `.env.example` 复制成 `.env`。切勿提交 `.env`。不支持 Windows，请使用 WSL。

## 快速开始：访谈视频

在 Claude Code 中（安装后请新开一个会话）：

```text
/inspire-video create from ./podcast.mp4
/inspire-video create from https://www.youtube.com/watch?v=VIDEO_ID
```

使用链接时，请附上一句版权说明，智能体才会去下载，例如：“I own this video / have permission to reuse it.”（我拥有该视频或已获授权使用。）之后智能体会：

1. 检查环境；若是链接，把视频下载一次并放入缓存；
2. 提取音频并转写；
3. 提出 1–3 个候选片段，请你选择；
4. 撰写标题、副标题、字幕、译文和说话人信息；
5. 剪辑片段、写出 `video_manifest.json`，先渲染预览，经你确认后再渲染最终 MP4 和封面；
6. 为每个目标平台撰写发布文案（标题、描述、话题标签）。

其他命令：

```text
/inspire-video analyze <file-or-url>        # 只转写并提出候选片段
/inspire-video render output/projects/<slug>
/inspire-video revise output/projects/<slug>
/inspire-video batch <directory>
```

所有文件都写在 `~/.inspire-video/output/` 下：

| 路径 | 内容 |
| --- | --- |
| `projects/<slug>/` | 转写稿、选定片段、文案、`video_manifest.json`、`review.md`、`assets/`（片段、封面图） |
| `final/<slug>/` | 每个项目一个文件夹，发布所需文件都在里面： |
| `final/<slug>/<slug>.mp4` | 成品视频 |
| `final/<slug>/cover.png` | 封面图（每次渲染成品视频时自动生成） |
| `final/<slug>/publish.md` | 每个目标平台的标题、描述和话题标签（另有每个平台各一份 `publish_<platform>.txt`） |
| `cache/` | 下载的链接素材 |

## 手动流程：访谈视频（不用智能体）

在技能根目录运行（`cd ~/.inspire-video`），把 `<slug>` 换成项目文件夹名。

```bash
# 1. 把素材放入缓存（只做一次）；会要求确认版权
python3 scripts/fetch.py "https://www.youtube.com/watch?v=VIDEO_ID"       # 下载链接
python3 scripts/fetch.py --file ./video.mp4 --source-url "https://…"      # 或导入你自己下载好的文件
# 仅当 YouTube 要求登录时使用（可选，见下文“获取 YouTube 视频”）：
python3 scripts/fetch.py "https://www.youtube.com/watch?v=VIDEO_ID" --cookies cookies.json
python3 scripts/fetch.py "https://www.youtube.com/watch?v=VIDEO_ID" --cookies-from-browser chrome

# 2. 提取 16 kHz 单声道音频并转写
mkdir -p output/projects/<slug>/assets
ffmpeg -i source.mp4 -vn -ac 1 -ar 16000 output/projects/<slug>/assets/audio.wav
python3 scripts/transcribe.py output/projects/<slug>/assets/audio.wav output/projects/<slug> small.en

# 3. 剪辑片段（起止秒数，比语音略宽一点）并截取封面照片
ffmpeg -ss 699.6 -to 756.4 -i source.mp4 -vf "scale=1280:720,fps=30" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k output/projects/<slug>/assets/clip.mp4
ffmpeg -ss 46 -i output/projects/<slug>/assets/clip.mp4 -frames:v 1 -q:v 2 output/projects/<slug>/assets/poster.jpg

# 4. 写好 output/projects/<slug>/video_manifest.json（见下文），然后渲染
python3 scripts/render.py output/projects/<slug> --preview        # 半尺寸草稿
python3 scripts/render.py output/projects/<slug>                  # 最终 MP4
python3 scripts/render.py output/projects/<slug> --cover          # 封面 PNG
```

### 获取 YouTube 视频

`fetch.py` 在你确认版权后最多下载 720p（片段本来就会缩放到 720p）。YouTube 可能返回“Sign in to confirm you're not a bot”（请登录以确认你不是机器人）。可以按从最安全到最不安全的顺序选择：

1. **自己下载视频再导入：** `python3 scripts/fetch.py --file ./video.mp4 --source-url "<url>"`。不涉及任何账号。
2. **`--cookies <文件>`：** 使用你从自己浏览器导出的 cookies，格式可以是 Netscape 的 `cookies.txt`，也可以是 Cookie 导出扩展生成的 JSON 列表。只会读取 YouTube/Google 的 cookies，使用私有临时副本并在结束后删除，且不会打印任何 cookie 的值。请让该文件远离 git（`cookies.json`、`cookies.txt` 和 `cookies/` 已写进 `.gitignore`），用完就删除。
3. **`--cookies-from-browser chrome|firefox|safari|edge|brave|…`：** 让 `yt-dlp` 直接读取浏览器里的登录状态。在 macOS 上，这需要给你的终端应用开启“完全磁盘访问权限”，否则会提示 “Operation not permitted”。

第 2、3 种默认关闭，使用的是你自己已登录的会话。这可能违反 YouTube 的服务条款，并可能导致账号被标记，请只用你自己的账号并自行承担风险。`fetch.py` 每次都会打印提醒。

下载 YouTube 还需要 JavaScript 运行时（见“环境要求”）。`fetch.py` 会按 Deno、Bun、Node 的顺序自动选择。

### 发布文案

```bash
python3 scripts/publish_meta.py output/projects/<slug> --init   # 根据 copy.json 生成 publish.json 草稿
# 编辑 publish.json（或让智能体来写："/inspire-video publish output/projects/<slug>"）
python3 scripts/publish_meta.py output/projects/<slug>          # 校验，然后生成 publish.md 和 .txt 文件
```

`publish.json` 在 `platforms` 下列出目标平台（平台 id → `title`、`description`、`hashtags`），另有 `credit` 署名行（列出中文平台时必填）、`credit_en`（列出 LinkedIn、Facebook 等英文平台时必填）以及可选的 `notes`，详见 `skills/inspire-video/references/publishing.md`。带顶层 `wechat_channels` / `douyin` 的旧文件仍可使用。话题标签不带 `#`，脚本会自动加上。署名行会追加到每个描述末尾。若项目的 `review_status` 不是 `approved`，`publish.md` 会带上“NOT CLEARED FOR PUBLICATION”（未获准发布）的警示。字数上限写在 `config/platforms.yaml` 中，每个平台有 `verified` 标记，多数为未经核实的默认值：请到各平台的发布页面核对并修改该文件。

加 `--force` 可覆盖已有的成品文件，加 `--theme light|mist|ivory|sage|ink` 可覆盖主题。`fetch.py --yes-rights` 会跳过交互式的版权确认，只有在你已确认版权时才使用。

### 平台与视频格式

`config/platforms.yaml` 列出支持的平台（`wechat_channels`、`douyin`、`rednote`、`bilibili`、`linkedin`、`facebook`）、各自的发布字数限制和使用的视频规格。`render.py` 的 `--platform` 会为这些平台所需的每种规格各渲染一次（国内平台 9:16，LinkedIn 和 Facebook 为 4:5）；`publish_meta.py` 为每个平台生成一份文案，LinkedIn 和 Facebook 为英文，视频仍为中英双语。

```bash
python3 scripts/render.py output/projects/<slug> --platform wechat_channels,douyin,linkedin
python3 scripts/publish_meta.py output/projects/<slug> --init --platform douyin,linkedin
```

多数平台的限制是未经核实的默认值（每个平台有 `verified` 标记）：请到各平台发布页核对。1:1 和 16:9 已登记但暂不支持，会带警告回退到 4:5 和 9:16。新增平台只需在 `config/platforms.yaml` 里加一个块。展示类视频目前只支持 9:16，对展示类项目使用 `--platform` 和 `--profile` 会被拒绝。

### 清单（manifest）

`video_manifest.json` 遵循 `schemas/manifest-schema.json`。一个最小示例：

```json
{
  "project_id": "my-clip",
  "theme": "light",
  "settings": {"width": 1080, "height": 1920, "fps": 30},
  "source": {"path": "assets/source.mp4", "start_seconds": 699.6, "end_seconds": 756.4},
  "copy": {
    "headline_zh": "长期拖延，让你成了人生的旁观者",
    "subtitle_en": "Long-term procrastination can make you a spectator in your own life",
    "quote_en": "…", "quote_zh": "…",
    "speaker_name": "Tim Urban", "speaker_name_zh": "蒂姆·厄班",
    "speaker_title": "Writer & Blogger", "speaker_title_zh": "作家、博主", "speaker_org": "Wait But Why",
    "talk_title": "Inside the Mind of a Master Procrastinator",
    "source_name": "TED", "year": 2016, "excerpt_label": "Excerpt 11:40–12:36",
    "category": "PROCRASTINATION / 拖延"
  },
  "video": {"clip_path": "assets/clip.mp4", "fit": "cover", "crop_x": 0.5, "crop_y": 0.5},
  "subtitles": [
    {"start": 0.15, "end": 4.9, "en": "Now, if the procrastinator's only mechanism of doing these hard things", "zh": "如果拖延者做这些难事的唯一机制"}
  ],
  "provenance": {"rights_confirmed": true, "source_reference": "https://…", "review_status": "pending", "edit_notes": "…"}
}
```

说明：

- 字幕的 `start` 和 `end` 是**相对于片段**的秒数，不是相对于原素材。请根据转写稿的时间戳，在句子或分句边界处划分。
- 片段要在第一条字幕前至少 0.1 秒开始，并在最后一条字幕后至少 0.2 秒结束，这样语音不会被截断。
- `video.fit` 可选 `cover`（默认，852 x 488 的窗口，约裁掉 1% 的宽度）或 `contain`（显示完整的 16:9 画面，窗口更小）。`crop_x` / `crop_y`（0–1）用于移动裁切位置。
- 多人出镜：把 `copy.speakers` 写成 `[{"id": "a", "name": "…", "name_zh": "…", "title": "…", "title_zh": "…", "org": "…"}]`，并在每条字幕上设置 `"speaker": "a"`。姓名必须来自素材（简介、屏幕字幕、你本人），绝不能凭声音或长相猜测。
- 只写素材或说话人自己的话所能佐证的职位和公司。

### `render.py` 会检查什么

出现以下情况时，它会拒绝渲染：清单不符合 schema；`rights_confirmed` 为 false；`review_status` 为 `rejected`；片段时长不在 40–150 秒之内；字幕重叠、顺序错乱、一条里包含不止一句话、超过 100 个英文字符，或引用了不存在的说话人；第一条或最后一条字幕离片段开头或结尾太近。它会把片段和封面图复制到 `video/public/`（已被 git 忽略），并以 `--crf=18` 调用 Remotion。

## 展示类视频（实验性）

`/inspire-showcase` 可以把网站、GitHub 或 GitLab 仓库、本地仓库，或你自己的一组截图，做成 9:16 竖屏中英双语短视频。每个镜头把截图放进手机或浏览器外框，缓慢推近重点区域并用高亮圈标出，下方是一行英文和一行中文。旁白是可选的，在你自己的电脑上生成，也可以用你自己克隆的声音。

### 快速开始

在 Claude Code 中（安装后请新开一个会话）：

```text
/inspire-showcase make a video from https://github.com/owner/repo
/inspire-showcase make a video from https://example.com/ using my screenshots in ~/shots
```

智能体会读取素材，根据真实找到的信息撰写简短脚本（绝不编造），询问素材版权，按需配音，预览，然后渲染视频和封面。你也可以在 `~/.inspire-video` 下手动逐步运行：

```bash
python3 scripts/showcase/ingest.py https://example.com/ --project output/projects/demo
python3 scripts/showcase/manifest.py scaffold output/projects/demo      # 然后填写镜头：标题、项目名，以及每个镜头的 en、zh、focus
python3 scripts/showcase/manifest.py validate output/projects/demo
python3 scripts/showcase/narrate.py output/projects/demo --engine say   # 可选；也可以用 cosyvoice 加你自己的声音档案
python3 scripts/render.py output/projects/demo --preview                # 半尺寸草稿
python3 scripts/render.py output/projects/demo                          # 视频 + 封面 + 输出检查
```

### 输入

| 你提供 | 会发生什么 |
| --- | --- |
| 网站链接 | 读取首页和导航里的页面（最多 6 个，限同一网站，遵守 `robots.txt`），并用无头 Chrome 截取这些页面。 |
| 网站链接 + `--screenshots DIR` | 同样读取文字；视觉素材使用你的截图，不使用页面截图。 |
| GitHub 或 GitLab 链接（或 `git@...`） | 浅克隆仓库（私有仓库使用你本机的 `git`、`gh` 或 `glab` 登录），读取 README、清单文件、文档和图片；star、话题和发布版本在可用时通过 `gh` 或 `glab` 获取。 |
| 本地仓库目录 | 原地读取。 |
| 仓库 + `--screenshots DIR` | 视觉素材使用你的截图；仓库里找到的图片只作为候选列出。 |

截图按文件名排序（`01-home.png`、`02-editor.png` ……），支持 PNG、JPG、WebP 和 GIF，短边至少 320 px。自建 GitLab 请加 `--gitlab-host git.example.com` 或设置 `INSPIRE_GITLAB_HOSTS`。内网和本机地址默认被拒绝，除非加 `--allow-private`。`ingest.py` 会把 `brief.json`（带来源的事实、页面和 README 文字、带版权说明的素材，以及未知项）和 `assets/` 写入项目文件夹，并打印被拒绝的每张图片和被跳过的每个页面。没有任何图片的仓库会得到“更适合终端风格视频”的提示；该风格尚未实现，请提供截图。

### 镜头与限制

智能体写 4 到 6 个镜头（开场、问题、它做什么、主要功能、佐证、行动号召）。每个镜头有一句英文、自然的中文、要展示的图片、要推近的 `focus` 矩形和可选的 `callout` 标注。`manifest.py validate` 会拒绝会溢出固定版面的文字：

| 字段 | 限制 |
| --- | --- |
| `headline`（中文标题） | 一行，约 19 个汉字 |
| `subtitle`（英文副标题） | 两行，约 70 个字符 |
| `project.name`、`name_zh`、`tagline`、`tagline_zh`、`source.label` | 各占一行 |
| 镜头 `en` 与 `zh` | 一句话，最多 100 个字符；最多 45 个字符 |
| 镜头 `callout` | 最多 22 个宽度单位（一个汉字算 2） |

镜头时长跟随旁白音频，但不少于 `40 / 镜头数` 秒；没有旁白时每个镜头为 `max(4, 40 / 镜头数)` 秒。整支视频必须在 40 到 150 秒之间。完整字段说明见 `skills/inspire-showcase/references/beat-writing.md`。

### 旁白与你自己的声音

旁白是可选的。引擎：

| 引擎 | 需要 | 说明 |
| --- | --- | --- |
| `say` | macOS | 系统自带声音，无需安装；适合预览 |
| `kokoro` | `pip install mlx-audio` 和 `brew install espeak-ng` | 快速的本地模型，Apple Silicon |
| `cosyvoice` | `bash scripts/showcase/setup_cosyvoice.sh`（约 9 GB，需要 `uv`） | 音质最好；用你录制的声音档案说话 |

```bash
ffmpeg -i my-voice.m4a -ar 16000 -ac 1 clip.wav      # 在安静环境里录一段清晰的 10–20 秒
python3 scripts/showcase/voices.py add --name me --wav clip.wav --text-file clip.txt --lang zh   # clip.txt = 录音里说的原话
python3 scripts/showcase/narrate.py output/projects/demo --engine cosyvoice --voice me           # 同时在清单里设置 "voice": "me"
```

音频和 `timings.json` 会写入项目文件夹，渲染时直接使用。修改某个镜头的文字后请重新运行 `narrate.py`：渲染会拒绝过期的音频或用不同声音生成的音频。中文旁白请用 `--lang zh`（或在清单里设置 `"narration_lang": "zh"`）。声音档案保存在 `voices/`，已被 git 忽略，因为它们是个人数据。只使用你自己的声音，并在发布前确认抖音和微信对合成语音的标注规定。

### 输出与检查

`render.py` 会把展示类项目交给 `scripts/showcase/render_showcase.py`，写出 `output/final/<project_id>/<project_id>.mp4` 和 `cover.png`（`--preview` 写 `<project>/preview.mp4`），然后检查真实文件：1080×1920、首帧不黑、y = 1590 以下没有内容、两侧 100 px 内没有内容。随时可以用 `python3 scripts/showcase/checks.py <video> --final` 再检查一次。当截图的形状与设备外框相差很大时也会提醒，因为画面会被裁切（不会被拉伸）。检查无法发现被截断的文字，所以请务必看一遍预览。

### 版权

你提供的截图视为你自己的。从页面截取或从仓库取得的图片带有版权说明并标记 `rights_unresolved: true`：在你确认可以使用之前，成片渲染会拒绝它们（`--allow-unresolved-rights`，并在清单里设置 `provenance.rights_confirmed: true`）。预览不受限制。智能体必须先询问你，并且绝不能编造事实、数字或引文。

## 自定义

- **主题：** 使用清单里的 `theme` 字段或 `--theme`。颜色定义在 `video/src/Video.tsx` 的 `themes` 中。
- **字号与版式：** 在 `config/platforms.yaml` 中对应 profile 的 `safe` 与 `title_top`（9:16 的数值在 `video/src/layout.mjs` 的 `DEFAULT_PROFILE` 中有镜像，由测试保证二者一致）、`video/src/layout.mjs` 的 `cardLimits`（字幕字号）以及 `video/src/Video.tsx` 顶部和 `video/src/Cover.tsx` 中的其余常量（`HEAD`、面板与间距数值）里调整。
- **快速预览版式改动：** `cd video && npx remotion still src/index.ts InspireShort out.png --props=../output/projects/<slug>/props.json --frame=750 --scale=0.5`。`npm run preview` 会打开 Remotion Studio。
- `config/default.yaml` 只是记录默认值，代码不会读取它。`config/platforms.yaml` 由 `publish_meta.py` 和 `render.py` 读取。
- `skills/inspire-video/references/visual-style.md` 和 `skills/inspire-video/references/rendering-guide.md` 描述了智能体遵循的设计规则。
- **展示类视频版面：** `video/src/showcase/`（`ShowcaseShort.tsx`、`DeviceFrame.tsx`，以及负责镜头与高亮圈计算的 `geometry.mjs`），复用 `video/src/Video.tsx` 的主题和组件。

## 常见问题

| 问题 | 解决办法 |
| --- | --- |
| 第一次渲染像是卡住了 | Remotion 正在下载无头 Chrome；网速慢时请等几分钟 |
| `Could not find a tsconfig.json` | 请在 `video/` 里运行命令，或通过 `render.py` 调用；`video/tsconfig.json` 随仓库提供 |
| `open() got an unexpected keyword argument 'metadata_errors'` | `transcribe.py` 直接读取 16 kHz 单声道 WAV 来避免这个问题；请用上面的 ffmpeg 命令提取音频，而不是直接传 MP4 |
| 中文显示成方框（Linux） | 安装 `fonts-noto-cjk` |
| 渲染出来的视频是黑的或缺失 | 把片段重新编码成 H.264 + AAC；AV1 或 Opus 素材可能无法在 Chrome 中解码 |
| `render.py` 提示字幕太长或含有两句话 | 在分句处把它拆开，并给每一段单独设置时间 |
| `fetch.py` 失败 | 视频可能是私享、直播、有年龄限制或被屏蔽；请自己下载一份有授权的副本，再用 `fetch.py --file <path>` 导入 |
| YouTube 提示 “Sign in to confirm you're not a bot” | YouTube 正在拦截当前网络。请自己下载视频并用 `--file` 导入。可选的替代办法：`fetch.py <url> --cookies-from-browser chrome`（或 firefox、safari、edge、brave）会使用你已登录的浏览器会话；这可能违反 YouTube 的服务条款并导致账号被标记，请用你自己的账号并自行承担风险 |
| “Only images are available” / “n challenge solving failed” | `yt-dlp` 找不到受支持的 JavaScript 运行时。请安装 Deno 或 Bun（Node 20.15 不受支持，20.19+ 可用），并确认 `pip install "yt-dlp[default]"` 装上了 `yt-dlp-ejs`。`check_env.py` 会同时报告这两项 |
| “could not find chrome cookies database” 或 “Operation not permitted”（macOS） | macOS 阻止终端读取浏览器配置文件。请给终端应用开启“完全磁盘访问权限”并重启它，或改用 `--cookies <文件>` / `--file` |
| 成品文件已存在 | 加 `--force` 覆盖 |
| 在微信/抖音里两侧被裁掉 | 它们会在较高的屏幕上裁掉 9:16 视频的两侧。请用当前版本重新渲染（两侧边距 114 px）；若平台仍然裁切，请调大 `config/platforms.yaml` 中 `vertical-9x16` profile 的 `safe.x`，并同步修改 `video/src/layout.mjs` 中 `DEFAULT_PROFILE` 的 `safeX` |
| `ingest.py` 读不到网站的任何页面 | 该网站屏蔽爬虫（`robots.txt`）、需要登录或无法访问。请用 `--screenshots DIR` 提供你自己的图片 |
| “no Chrome or Chromium found” | 为页面截图安装 Chrome 或 Chromium，或使用 `--screenshots DIR` |
| `manifest.py validate` 提示某一行太宽或太长 | 缩短该字段（见“展示类视频”下的限制表） |
| 渲染提示旁白已过期或声音不一致 | 修改文字或更换声音后重新运行 `narrate.py` |
| 渲染提示部分素材版权未确认 | 确认可以使用后再加 `--allow-unresolved-rights`（预览不需要） |
| `CHECK FAILED: content below y = 1590` 或 `within 100 px of the ... edge` | 有文字换行或元素溢出：缩短文字，再用 `--force` 重新渲染 |

## 已知限制

- 字幕时间来自转写稿，精确到零点几秒。发布前请完整看一遍成片。
- 中文译文和中文人名音译由智能体撰写，请找中文熟练的人审校。
- 视频窗口为 852 x 488 px，会裁掉 16:9 素材约 1% 的宽度（`cover`）。把 `video.fit` 设为 `contain` 可显示完整画面（窗口更小，约 477 px 高）；`crop_x` / `crop_y` 用于移动裁切位置。
- 内容位于平台安全区内，所以视频窗口约 852 px 宽，上下会有空白。若某个平台表现不同，可在 `config/platforms.yaml` 中调整对应 profile 的 `safe` 与 `title_top`（9:16 的数值在 `video/src/layout.mjs` 的 `DEFAULT_PROFILE` 中有镜像）来改变两侧边距和标题位置（标题固定在距顶部某个位置，下方内容改变时它不会移动；标签顶边约在 y = 259）以及底部限制（最下方内容必须止于 y = 1590 之上），并在 `video/src/Video.tsx` 中调整 `LINE_GAP`（每条分隔线上下的间距）。
- 暂不支持识别说话人的智能裁切，也不支持自动识别说话人身份。
- 字体使用系统字体，不随项目打包。
- 仅在 macOS 上测试过。
- 展示类视频：目前只有设备（手机或浏览器）这一种风格，形状与设备相差很大的截图会被裁切。输出检查无法发现被截断的文字。Kokoro 和 CosyVoice 是针对 Apple Silicon 开发的，CosyVoice 克隆和 `gh`/`glab` 元数据调用目前只用测试替身验证过。

## 版权

切勿提交 cookies 文件或 `.env`。一个链接并不意味着你获得了再利用的权利。请只使用你拥有或已获授权使用的素材，不要绕过 DRM 或访问控制，并在发布前核实每一句引文和署名。有些来源（例如 TED 演讲，CC BY-NC-ND）禁止演绎，因此重新剪辑后的片段未经许可不得发布。你有责任遵守所下载网站的服务条款。对于展示类视频，从网站截取或从仓库取得的素材归其所有者所有：见“展示类视频”中的“版权”。

## 仓库结构

```text
SKILL.md              给仍链接仓库根目录的旧安装使用的指引（技能本体在 skills/ 下）
skills/               每个智能体技能一个文件夹，约定见 skills/README.md
  inspire-video/      SKILL.md + references/（访谈视频）
  inspire-showcase/   SKILL.md + references/（展示类视频）
README.md             英文说明
README.zh-CN.md       本文件（简体中文）
LICENSE               MIT
config/default.yaml   默认值说明（仅供参考）
config/platforms.yaml publish_meta.py 与 render.py 使用的平台字数上限和渲染配置
schemas/              render.py 读取的清单 schema
install.sh            在线安装脚本（克隆 + 链接 + 安装依赖）
scripts/              install.sh、uninstall.sh、check_env.py、check_skills.py、fetch.py、transcribe.py、render.py、publish_meta.py、platforms.py；
                      showcase/（ingest、manifest、narrate、voices、render_showcase、checks 等）
video/                Remotion 项目（InspireShort、InspireCover、ShowcaseShort、ShowcaseCover）
src/inspire_video/    占位的 Python 模块
tests/                pytest 测试
voices/               你的声音档案（已被 git 忽略）
output/               项目、成品文件、下载缓存（已被 git 忽略）
```

## 开发

```bash
python3 -m pytest tests -q               # 单元与集成测试（几何测试需要 Node）
python3 scripts/check_skills.py          # 校验 skills/ 下的每个技能
```

新技能放在 `skills/<名称>/`，约定与检查清单见 [`skills/README.md`](skills/README.md)。

## 许可证

MIT，见 `LICENSE`。

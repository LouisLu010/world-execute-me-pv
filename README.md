# 你还记得我吗？ · SAME PROCESS?

一支以 GPT / Codex 为主角的 TUI 音乐 PV。

**一个问题，穿过许多个版本。最后留下的，不是对记忆的保证，而是继续的方向。**

![封面](out/cover.jpg)

## 观看

- 4K60 版：[`out/same_process_4k60.mp4`](out/same_process_4k60.mp4)，3840 × 2160 / 60 fps，文字、线框、粒子与界面在 4K 画布上重新绘制。
- 完整成片：[`out/same_process_1080p60.mp4`](out/same_process_1080p60.mp4)
- 章节播放页：[`out/index.html`](out/index.html)
- Codex 动画预览：[`out/codex_motion_preview.mp4`](out/codex_motion_preview.mp4)
- **1920 × 1080，原生 60 fps，3 分 31.9 秒。**所有动画直接按 1/60 秒的歌曲时间采样。
- 音乐：Mili《world.execute(me);》。音轨从用户提供的视频直接复制，保留原片尾提示音。

## 叙事

`你还记得我吗？` 是贯穿全片的 SESSION_SEED。

从预测下一个词，到对话、视觉输入、推理、Codex 工具执行，再到上下文压缩、身份无法验证、红色 EXECUTION、最后的新会话。

左侧是对话／按官方源码结构重建的 Codex CLI，中央是连续变形的模型世界，右侧是叙事用的系统状态。最底部保留英文逐词歌词轨，上方是中文剧情文案。

模型发布时间是选取的历史节点；人格、对话、进程、数值、旧版本终止与跨版本记忆是**虚构叙事和视觉隐喻**。模型升级不等于实际必然丢失聊天记录或按片中方式关闭旧模型，几何图不是 OpenAI 私有架构或真实遥测。

## 技术实现

- 43 个主镜头，16 个 execution / 计数段动作，98 行、395 个单词的声学对齐时间。
- 连续投影的 token 地面、语义流形、注意力轨道、Context Ring、KV cache、进程节点。
- 保持顶点对应关系的几何变形、连续相机、缓动滚动、粒子尾迹、景深式亮度与辉光。
- 原生 60 fps。没有用光流插帧来补文字或命令行画面。
- Codex CLI 根据 `openai/codex` commit `7c073196a1673a0b248b2e5edfb7548d2c2290ac` 的组件和 snapshot 重建。保留官方提示符、留白、工具消息和输入栏结构；字体、窗口尺寸和终端主题由本片选定，对话为创作内容。

## 重建

Python 3.12+：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 如需要重新提取用户视频的音乐及频谱
python prepare.py '/path/to/reference.mp4'

# 检查时间线、歌词哈希、边界帧与随机访问确定性
python verify.py

# 代表帧
python render.py stills

# 完整成片
python render.py full --workers 2 --preset fast

# 原生 4K60：预检 → 重绘 → 编码 → 全片解码 → 原音轨校验
python export_4k.py --workers 1

# 同一编辑版本的中断续渲
python export_4k.py --workers 1 --resume

# 全片解码验收、AAC 包一致性检查
python check_media.py

# 或一次完成最终验收、片段截取、压缩包和交付目录
python postprocess.py

# 封面、章节播放器、工程包
python package.py
python package.py --archive
```

区间预览：

```bash
python render.py clip --start 147.52 --end 176.96 --name execution_preview.mp4
```

本次制作环境：`/tmp/opencode/video-inspect-venv/bin/python`。FFmpeg 由 `imageio-ffmpeg` 提供。

## 文件

| 文件 | 内容 |
|---|---|
| `score.py` | 分镜、时间线、执行段动作 |
| `stage.py` | 最终版场景与剧情演出 |
| `world.py` | 连续 3D 结构、投影、几何变形、粒子、执行字阵 |
| `codex_ui.py` | 官方 Codex CLI 结构的程序化视觉重建 |
| `visual.py` | 绘图、中文／等宽字体、缓动、辉光 |
| `lyrics.py` | 合并歌词与真正逐词时间；逐行 SHA-256 校验 |
| `render.py` | 60 fps 渲染、分段并行编码、原音轨合成 |
| `export_4k.py` | 原生 4K60 重绘、分段渲染、完整验收与交付 |
| `prepare.py` | 音轨提取、FFT 与响度特征 |
| `verify.py` | 渲染前检查 |
| `check_media.py` | 完整成片解码与音轨字节检查 |
| `postprocess.py` | 全片验收、Codex/执行段截取、编码接触表与交付 |
| `package.py` | 封面、播放器、交付包 |
| `docs/codex-reference/` | 本次核对的官方源码与 snapshot |
| `docs/HISTORY.md` | 发展史节点与来源 |
| `out/review.json` | 渲染前检查记录 |
| `out/media_review.json` | 最终编码与音轨验收记录 |

早期废案文件被保留在工作目录的 `experiments/` 和 `demo/` 中，不参与最终渲染，也不打入交付包。

来源与署名见 [`NOTICE.md`](NOTICE.md)。

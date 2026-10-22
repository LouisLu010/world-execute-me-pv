# GitHub Pre-release 工作流

制作分支：`gpt-history-pv`。项目入口分支：`main`。

## 准备视频

```bash
python prepare.py /path/to/reference.mp4
python verify.py
python verify_v2.py
python export_4k.py --workers 1 --name same_process_v2_4k60.mp4
python tools/release_assets.py \
  --master out/same_process_v2_4k60.mp4 \
  --reports out \
  --output /path/to/release-assets
```

`release_assets.py` 核对 4K 成片的 SHA-256 与渲染代码指纹，生成 1080p60 版、训练和视觉预览、封面、编码分镜图及验收 JSON。1080p60 版与 4K 成片使用相同的 AAC 包。

## 固定源代码版本

将封面和分镜复制到 `docs/preview/`，提交全部源码与文档，再推送制作分支和标签：

```bash
git add .
git commit -m 'release: prepare GPT history PV preview'
git push origin gpt-history-pv
git tag -a v0.2.0-preview.1 -m 'GPT history PV — V2 Preview 1'
git push origin v0.2.0-preview.1
git archive --format=zip --prefix=gpt-history-pv/ \
  --output=/path/to/release-assets/gpt-history-pv-v0.2.0-preview.1-source.zip \
  v0.2.0-preview.1
```

源代码压缩包从标签生成；视频、音轨、歌词缓存、临时文件不进入 Git。所有媒体作为 Release 附件。

## 发布

对所有 Release 附件生成标准 SHA-256 清单 `SHA256SUMS.txt`，然后：

```bash
python tools/publish_prerelease.py \
  --tag v0.2.0-preview.1 \
  --assets /path/to/release-assets
```

发布脚本核对远端制作分支与标签，先创建 draft pre-release，逐个上传附件，并验证 GitHub 返回的 `digest` 和文件大小，最后发布为 Pre-release。网络中断后可重新运行同一命令，已经正确上传的附件会被保留。

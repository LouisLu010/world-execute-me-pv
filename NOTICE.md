# Sources and attribution

## Reference film and rhythm data

- Reference: `world-execute-me-dsh-pv`, **MisakaZentai**.
- Reference video: the MP4 supplied by the user.
- Scene grammar studied: dialogue and internal world in parallel, music-driven terminal typography, technology as dramatic action.
- `data/word_timeline_notext.json` and `data/vocal_timing.json`: time-only vocal alignment derived from that repository. Original MIT notice is retained in `LICENSES/reference-MIT.txt`.
- The active film uses newly authored scenes and geometry. No original whale character artwork or dancer imagery is embedded.

## Music and lyric input

- **Mili — world.execute(me);**.
- The exact AAC music stream is copied from the user's supplied video, including its final chime.
- Lyrics are local build input from LRCLIB entry `36914646`: <https://lrclib.net/api/get/36914646>.
- Music and lyrics remain the property of their respective rightsholders. Neither the reference code licence nor the renderer grants rights in them.
- Word timestamps are acoustic-alignment estimates from the reference. Line hashes and word ordering are verified, and the words are not uniformly time-spaced.

## Codex user interface

- Reference: **OpenAI Codex**, <https://github.com/openai/codex>.
- Pinned reference commit: `7c073196a1673a0b248b2e5edfb7548d2c2290ac`.
- Source files and snapshots used to check layout: `docs/codex-reference/`.
- Apache 2.0 licence and upstream notice: `LICENSES/codex-Apache-2.0.txt`, `LICENSES/codex-NOTICE.txt`.
- `codex_ui.py` is a Python visual reconstruction. It preserves structural/UI conventions and the source's blue accent and prompt fills. It is not an official Codex executable, live recording, or a pixel-identity certification across different terminal fonts/themes.
- Commands, repository names, version-history theatre and dialogue shown in the film are staged. The film does not claim OpenAI endorsement.

## Fonts

- Noto Sans CJK SC — SIL Open Font License 1.1, see `assets/fonts/Noto-LICENSE.txt`.
- DejaVu Sans Mono / Bold — Bitstream Vera licence and DejaVu changes, see `assets/fonts/DejaVu-LICENSE.txt`.

## ChatGPT / OpenAI mark

- Original mark design: **OpenAI**.
- Vector distribution: **LobeHub / Lobe Icons**, `packages/static-svg/icons/openai.svg`.
- Source: <https://github.com/lobehub/lobe-icons/blob/master/packages/static-svg/icons/openai.svg>.
- Pinned Git blob: `78caf4fa20ffb0ae8ebefd74408871c11c1c7fd2`.
- Original SVG SHA-256: `a595df6b423920c67a7f8f73c063e4bfb72d415948097b6cac063a2366bb5186`.
- LobeHub MIT notice is retained in `LICENSES/lobe-icons-LICENSE.txt`; the mark remains OpenAI's trademark.
- The vector path is unchanged. The monochrome form is rasterised for the avatar and the vision example; the diagram separates copies of that image's pixels into illustrative patches.
- The patch count, feature bars and five encoder planes are an educational visual metaphor, not a statement of GPT's private architecture. Feature bars are measured from the actual example image rather than claimed model embeddings.

## Production

AI-assisted direction, original dialogue, scene code, projection geometry, visual reconstruction and rendering by this GPT session for the user. Pillow, NumPy, imageio-ffmpeg and PyAV retain their respective licences.

This is an unofficial fictional music film. Model chronology is based on selected publication milestones; terminal state and internals are authored metaphors. No proprietary model parameters, genuine hidden thoughts, or genuine user memories are depicted.

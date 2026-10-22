# Render and delivery notes

## Frame model

The output frame at index `n` is drawn at song time `n / 60`. No scene depends on the last frame or render order. Ten independently encoded H.264 chunks are concatenated; the supplied AAC stream is copied into the final MP4.

`END = 211.90`, `FPS = 60`, `FRAMES = 12714`. The audio stream is allowed to retain its final packet past the last video-frame start. Nominal song duration and container duration can differ by a few milliseconds.

## Native 4K60

`python export_4k.py --workers 1` sets `GPT_PV_RASTER_SCALE=2` before importing the renderer. Design coordinates remain 1920×1080, while the raster surface is 3840×2160. Text is rasterized from the font at double point size; lines, particles, rectangles, clipping regions and rounded corners are drawn at doubled pixel coordinates. Image compositing remains at native output resolution. Only the low-frequency bloom pass uses a reduced-resolution buffer.

The output is therefore re-rendered from scene geometry and fonts rather than resized from the existing H.264 video. The same 12,714 frame timestamps and unchanged AAC packets are retained.

The 4K encoder uses one worker, one filter thread and bounded x264 lookahead/reference queues on this approximately 2 GiB host. Completed segments from an earlier, B-frame-enabled encoder setup are not reused with the new non-reordering encoder setup.

The `--width 3840` flag by itself remains a playback-size option. Use the export entry point above for native 4K drawing.

Additional checks are stored as `out/native_4k_preflight.json` and `out/media_review_4k60.json`. The 1080p renderer remains the default: nine baseline 1080p source-frame hashes were checked unchanged after introducing resolution-aware primitives.

## Useful commands

```bash
# Standard full render
python render.py full --workers 2 --preset fast

# Resume the same edit after an interrupted render
python render.py full --workers 2 --preset fast --resume

# Validate and package the finished output
python postprocess.py
```

`--resume` fully decodes existing chunks and checks their dimensions, frame rate, frame count and timestamps before reusing them. Use it only for the same edit: it does not determine whether arbitrary scene changes should invalidate an otherwise valid old chunk.

## Production correction

The first full pass exposed a floating-point modulo edge in a particle tail. A tiny negative position can round to the divisor under modulo, producing the upper endpoint instead of zero. The interpolation now clamps to the final valid segment. The correction changes only that boundary case.

All **444,990 particle interpolation indices** across the **12,714 frame times** were checked after the fix; the three triggering frames were rendered directly. Completed chunks not containing the failure were retained and validated during resume.

## Verification artefacts

- `out/review.json`: scene coverage, line hash reconstruction, 220 representative/boundary frames, 60 Hz motion and deterministic random access.
- `out/particle_review.json`: exhaustive interpolation-boundary regression check.
- `out/audio_review.json`: uploaded-video audio equals the extracted local soundtrack, packet by packet.
- `out/media_review.json`: complete MP4 decode, all frame timestamps, native resolution/fps, exact AAC packet comparison.
- `out/build_manifest.json`: active source and input fingerprints.
- `out/final_encoded_contact.jpg`: frames decoded from the finished MP4, rather than source render previews.

Source frame inspection and decoded frame inspection cover layout and rendering; they are not a claim of calibrated perceptual scores or private-model accuracy.

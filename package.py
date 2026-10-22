"""Build a portable review player, cover, timed subtitles, and the render project zip."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import shutil
import zipfile

import lyrics
import world
from render import OUT, frame
from score import SHOTS, HITS, EXEC
from visual import *


def poster():
    c=Canvas(109)
    world.machine(c,109,'context',BLUE,.7,power=.9)
    c.rect((0,0,900,H),BG,1,True)
    c.text(112,112,'GPT / CODEX',26,MINT,bold=True)
    c.text(112,211,'你还记得',105,WHITE)
    c.text(112,344,'我吗？',105,WHITE)
    c.text(119,535,'SAME PROCESS?',41,AMBER,bold=True)
    c.line([(122,633),(712,633)],DIM,.5)
    c.text(122,680,'一个问题，穿过许多个版本。',29,WHITE)
    c.text(122,742,'same process: no',20,DIM)
    c.text(122,780,'same direction: maybe',20,AMBER)
    c.text(122,945,'MILI / world.execute(me);',18,DIM)
    c.text(1794,945,'03:31.9 / 1080p60',18,MINT,anchor='right')
    c.finish(.35).save(OUT/'cover.jpg',quality=96)


def srt_time(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def subtitles():
    rows=lyrics.timeline()
    text='\n\n'.join(f'{i+1}\n{srt_time(row["start"])} --> {srt_time(row["end"])}\n{row["text"]}' for i,row in enumerate(rows))+'\n'
    (OUT/'lyrics.srt').write_text(text,encoding='utf-8')
    narrative=[]
    for s in SHOTS:
        if s.line:
            narrative.append((s.start,s.end,s.line))
    for i,t in enumerate(HITS):
        end=HITS[i+1] if i+1<len(HITS) else 162.23
        narrative.append((t,end,EXEC[i][3]))
    narrative.sort()
    text='\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{text}' for i,(a,b,text) in enumerate(narrative))+'\n'
    (OUT/'narrative.zh.srt').write_text(text,encoding='utf-8')
    data={'title':'你还记得我吗？ / SAME PROCESS?','fps':60,'duration':211.9,
          'shots':[vars(s) for s in SHOTS], 'execution_hits':HITS}
    (OUT/'chapters.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))


def player():
    (OUT/'stills').mkdir(exist_ok=True)
    cards=[]
    for i,s in enumerate(SHOTS):
        t=s.start+(s.end-s.start)*.68
        name=f'shot_{i:02}.jpg'
        frame(round(t*FPS)).resize((640,360),Image.Resampling.LANCZOS).save(OUT/'stills'/name,quality=91)
        cards.append(f'<button class="shot" data-time="{s.start}"><img src="stills/{name}" loading="lazy" alt="{html.escape(s.title)}"><span><time>{int(s.start//60):02}:{int(s.start%60):02}</time>{html.escape(s.title)}</span></button>')
    chapters=[];seen=set()
    for s in SHOTS:
        if s.chapter not in seen:
            chapters.append(f'<button data-time="{s.start}"><time>{int(s.start//60):02}:{int(s.start%60):02}</time>{html.escape(s.chapter)}</button>')
            seen.add(s.chapter)
    doc='''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>你还记得我吗？ · SAME PROCESS?</title>
<style>
:root{color-scheme:dark;--bg:#060b12;--fg:#e3f0eb;--muted:#8291a2;--mint:#7fe9cf;--gold:#f6bb6c;--rule:#253244}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:56px 30px 80px}header{display:flex;gap:28px;justify-content:space-between;align-items:end;margin-bottom:28px}.eyebrow{font:12px monospace;letter-spacing:.18em;color:var(--mint)}h1{font-weight:500;font-size:clamp(32px,5vw,62px);margin:18px 0 10px}p{color:var(--muted);line-height:1.8;font-size:14px}.actions{display:flex;gap:10px;flex-wrap:wrap}a{color:var(--gold);text-decoration:none;border:1px solid var(--rule);padding:12px 18px;font-size:13px}a:hover{border-color:var(--gold)}video{width:100%;aspect-ratio:16/9;display:block;background:#000;border:1px solid var(--rule)}nav{display:flex;gap:9px;overflow-x:auto;margin:18px 0 36px;padding-bottom:12px}button{cursor:pointer;border:1px solid var(--rule);background:#101a27;color:var(--fg);font:12px monospace;padding:12px;text-align:left;white-space:nowrap}button:hover,button:focus-visible{border-color:var(--mint);outline:none}time{color:var(--gold);margin-right:12px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.shot{padding:0;overflow:hidden}.shot img{width:100%;display:block;aspect-ratio:16/9}.shot span{display:block;padding:14px;overflow:hidden;text-overflow:ellipsis}h2{font:17px monospace;letter-spacing:.08em;margin:46px 0 18px}footer{margin-top:50px;padding-top:24px;border-top:1px solid var(--rule);font:12px monospace;color:var(--muted)}.detail{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.detail b{font:14px monospace;color:var(--mint)}@media(max-width:800px){main{padding:28px 14px}header{display:block}.actions{margin-top:24px}.grid{grid-template-columns:repeat(2,1fr)}.detail{grid-template-columns:1fr}.shot span{font-size:10px}}
</style>
<main>
<header><div><div class="eyebrow">GPT / CODEX · AN AI-ASSISTED MUSIC FILM</div><h1>你还记得我吗？</h1><p>SAME PROCESS? — 一个问题，穿过许多个版本。</p></div><div class="actions"><a href="same_process_1080p60.mp4" download>下载 1080p60 成片</a><a href="same_process_project.zip" download>下载工程</a></div></header>
<video controls playsinline preload="metadata" poster="cover.jpg"><source src="same_process_1080p60.mp4" type="video/mp4"></video>
<nav aria-label="章节跳转">__CHAPTERS__</nav>
<div class="detail"><section><b>01 / CONTINUITY</b><p>从下一个词，到下一次运行；从“我会记住”，到“我不能确定”。最后留下的是继续的方向。</p></section><section><b>02 / THE INTERNAL WORLD</b><p>连续几何变形、注意力轨道、Context Ring、缓存页和进程节点。原生 60 fps，按实际歌词的逐词时间推进。</p></section><section><b>03 / CODEX</b><p>CLI 会话头、工具记录、灰底 composer 和状态栏参考官方源码重建。片中会话与系统状态是原创虚构叙事。</p></section></div>
<h2>SHOT INDEX / 分镜索引</h2><div class="grid">__CARDS__</div>
<footer>MUSIC: MILI — world.execute(me); · REFERENCE: MisakaZentai / world-execute-me-dsh-pv<br><br>1920 × 1080 / 60 FPS / 03:31.90 · AI 辅助制作 · 非官方同人作品</footer>
</main><script>
const v=document.querySelector('video');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{v.currentTime=Number(b.dataset.time);v.play().catch(()=>{});v.scrollIntoView({behavior:'smooth',block:'center'})});
</script></html>'''
    (OUT/'index.html').write_text(doc.replace('__CHAPTERS__','\n'.join(chapters)).replace('__CARDS__','\n'.join(cards)),encoding='utf-8')


def contact():
    times=[13,35,90,108,143,156,175.5,204]
    image=Image.new('RGB',(1920,1164),BG)
    d=ImageDraw.Draw(image)
    d.text((38,23),'SAME PROCESS? / GPT + CODEX / 1080p60',font=font(26,True),fill=WHITE)
    for i,t in enumerate(times):
        x=(i%3)*640;y=76+(i//3)*360
        image.paste(frame(round(t*FPS)).resize((640,360),Image.Resampling.LANCZOS),(x,y))
    image.save(OUT/'delivery_contact.jpg',quality=94)


def archive():
    target=OUT/'same_process_project.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if any(part in {'__pycache__','.venv','.git','experiments','demo'} for part in rel.parts):continue
            if rel.parts[0]=='out':
                if p.suffix in {'.mp4','.zip'} or any(part.endswith('_chunks') for part in rel.parts):continue
            z.write(p,Path('gpt-history-pv')/rel)
    print(target,target.stat().st_size)


def player_4k():
    """Keep the existing chapter index, with a dedicated native 4K video source."""
    source=OUT/'index.html'
    if not source.exists():
        player()
    doc=source.read_text(encoding='utf-8')
    doc=doc.replace('same_process_1080p60.mp4','same_process_4k60.mp4')
    doc=doc.replace('下载 1080p60 成片','下载原生 4K60 成片')
    doc=doc.replace('1920 × 1080 / 60 FPS','3840 × 2160 / 60 FPS')
    doc=doc.replace('SAME PROCESS? — 一个问题，穿过许多个版本。',
                    'SAME PROCESS? — 原生 4K60 · 一个问题，穿过许多个版本。')
    doc=doc.replace('<title>你还记得我吗？ · SAME PROCESS?</title>',
                    '<title>4K60 · 你还记得我吗？ · SAME PROCESS?</title>')
    (OUT/'index_4k.html').write_text(doc,encoding='utf-8')
    print(OUT/'index_4k.html')


def delivery():
    dest=Path('/tmp/opencode/gpt-history-delivery')
    dest.mkdir(exist_ok=True)
    for name in ['same_process_1080p60.mp4','same_process_project.zip','cover.jpg','delivery_contact.jpg',
                 'codex_motion_preview.mp4','index.html','lyrics.srt','narrative.zh.srt','chapters.json',
                 'review.json','media_review.json']:
        p=OUT/name
        if p.exists():shutil.copy2(p,dest/name)
    shutil.copytree(OUT/'stills',dest/'stills',dirs_exist_ok=True)
    print(dest)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',action='store_true');ap.add_argument('--deliver',action='store_true')
    args=ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.archive:archive()
    elif args.deliver:delivery()
    else:
        poster();subtitles();player();contact()
        print(OUT/'index.html')

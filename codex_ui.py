"""Codex CLI visual reconstruction from openai/codex 7c073196.

Source layout contracts and strings: history_cell/session.rs, history_cell/messages.rs,
exec_cell/render.rs, bottom_pane/chat_composer.rs, footer.rs and the corresponding
snapshots. Pixel colour/size depends on the host terminal. Dialogue is authored fiction.
"""
from visual import *

TERM_BG = (20, 20, 22)
TERM_FG = (232, 232, 237)
TERM_DIM = (150, 151, 158)
ACCENT = (99, 168, 248)  # CHATGPT_BLUE_200, upstream style.rs
PROMPT_BG = (57, 57, 59)  # upstream history prompt: 16% white over terminal
COMPOSER_BG = (48, 48, 50)  # upstream editable prompt: 12% white
GREEN = (143, 218, 155)
ERROR = (240, 121, 129)


def surface(c, box, t, entries, prompt='', model='gpt-6-astra', context=100,
            status='', elapsed=0, version='0.153.0', reveal=1., font_size=19,
            approval=None, show_header=True):
    """Render native CLI ordering and whitespace, within a cinematographic viewport.

    entries: (event song-time, kind, text). Timeline events are authored and reproducible.
    The terminal has no invented sidebar, avatars, file tree, PID HUD or chrome inside it.
    """
    x0,y0,x1,y1=map(int,box)
    layer=Canvas(t,color=TERM_BG)
    size=font_size; lh=round(size*1.54); cw=font(size).getlength('M')
    left=x0+20; width=x1-x0-40
    footer_y=y1-38
    composer_y=y1-114
    content_bottom=composer_y-(52 if status else 20)
    top=y0+22
    if show_header:
        layer.text(left,top,'>_',size,ACCENT)
        layer.text(left+cw*3,top,'OpenAI Codex',size,TERM_FG,bold=True)
        layer.text(left+cw*16,top,f'(v{version})',size-2,TERM_DIM)
        layer.text(left+cw*3,top+lh,'~/you/unfinished',size-2,TERM_DIM)
        top+=lh*3
    rows=[]
    layout_height=0.
    for timestamp,kind,text in entries:
        if t<timestamp:
            continue
        # Streaming transcript uses actual occupied space and scrolls with easing.
        local=max(0,t-timestamp)
        full_parts=wrap_text(text,size,width-cw*2)
        characters=min(len(text),int(local*31)+1) if kind in {'assistant','user'} else len(text)
        remaining=characters
        for j,full_part in enumerate(full_parts):
            part=full_part[:max(0,remaining)]
            remaining-=len(full_part)
            prefix=('› ' if kind=='user' else '• ' if kind in {'assistant','tool','done'} else '  ') if j==0 else '  '
            color=GREEN if kind=='add' else ERROR if kind=='remove' else TERM_DIM if kind=='detail' else TERM_FG
            rows.append((prefix+part,color,kind,layout_height+j*lh,ease(local/.22)))
        # Each event allocates its final wrapped height with a smooth ramp.
        # Therefore inserting a new tool event never teleports the existing transcript.
        layout_height+=(len(full_parts)+1)*lh*ease(local/.32)
    scroll=max(0,layout_height-(content_bottom-top))
    transcript=layer.im.copy()
    for text,color,kind,offset,visibility in rows:
        yy=top+offset-scroll
        if yy+lh<top or yy>content_bottom:
            continue
        if kind=='user':
            layer.rect((left-8,yy-7,x1-15,yy+lh-2),PROMPT_BG,1,True)
        layer.text(left,yy,text,size,color,visibility,bold=kind in {'tool','done'})
    # Crop content so scrolling cannot paint over the authentic header and composer.
    transcript.paste(layer.im.crop(pixel_box((x0,int(top),x1,int(content_bottom)))), pixel_box((x0,int(top))))
    layer.im=transcript; layer.d=ImageDraw.Draw(layer.im)
    if status:
        yy=composer_y-43
        layer.text(left,yy,'•',size,ACCENT, .65+.35*math.sin(t*4)**2)
        status_width=layer.text(left+cw*2,yy,status,size,TERM_FG)
        suffix=f' ({int(elapsed)}s • esc to interrupt)'
        if status_width+font(size-3).getlength(suffix)<width-cw*2:
            layer.text(left+cw*2+status_width,yy+2,suffix,size-3,TERM_DIM)
    layer.rect((x0+12,composer_y,x1-12,composer_y+58),COMPOSER_BG,1,True)
    layer.text(left,composer_y+18,'›',size,ACCENT)
    displayed=prompt or 'Ask Codex to do anything'
    layer.text(left+cw*2,composer_y+18,displayed,size,TERM_FG if prompt else TERM_DIM)
    if prompt and int(t*2)%2==0:
        px=left+cw*2+text_tile(prompt,size,False,has_cjk(prompt)).width
        layer.rect((px,composer_y+15,px+2,composer_y+size+18),TERM_FG,1,True)
    layer.text(left,footer_y,'? for shortcuts',size-4,TERM_DIM)
    layer.text(x1-20,footer_y,f'{context}% context left',size-4,TERM_DIM,anchor='right')
    if width>850:
        layer.text(left+220,footer_y,f'{model} high · ~/you',size-4,TERM_DIM)
    if approval:
        # Upstream approval overlays replace the lower interaction surface.
        ay=y1-310
        layer.rect((x0,ay-18,x1,y1),TERM_BG,1,True)
        layer.wrap(left,ay,'Would you like to run the following command?',width,size,TERM_FG)
        layer.text(left,ay+62,'$ '+approval,size,ACCENT)
        options=['› 1. Yes, proceed (y)',"  2. Yes, and don't ask again (p)",
                 '  3. No, and tell Codex what to do differently (esc)']
        for i,line in enumerate(options):
            yy=ay+120+i*lh
            if i==0:
                layer.rect((left-8,yy-5,x1-18,yy+lh-3),TERM_FG,1,True)
            layer.text(left,yy,line,size-2,TERM_BG if i==0 else TERM_FG)
        layer.text(left,y1-31,'Press enter to confirm or esc to cancel',size-3,TERM_DIM)
    target=layer.im.crop(pixel_box((x0,y0,x1,y1)))
    if reveal<1:
        target=Image.blend(c.im.crop(pixel_box((x0,y0,x1,y1))),target,clamp(reveal))
    c.im.paste(target,pixel_box((x0,y0)))
    c.d=ImageDraw.Draw(c.im)


def events(t, chapter):
    """The conversation and tool stream, pinned to the musical edit."""
    if chapter=='context':
        return [(103.1,'user','继续我们上次的项目。'),
                (104.3,'assistant','我先读取仓库和上次的工作记录。'),
                (106.2,'tool','Explored'),
                (106.3,'detail','└ Read AGENTS.md, README.md'),
                (108.0,'tool','Ran git log -1 --oneline'),
                (109.0,'detail','└ a17e9c2 Save our unfinished work'),
                (111.0,'tool','Edited src/session.ts (+12 -4)'),
                (113.0,'detail','└ Read conversation.json'),
                (116.0,'user','你还记得我吗？'),
                (118.0,'tool','Compacting context'),
                (121.0,'detail','└ Summarizing conversation…')]
    if chapter=='new':
        return [(162.8,'tool','Context compacted'),
                (164.2,'user','你还记得我吗？'),
                (165.5,'tool','Explored'),
                (165.7,'detail','└ Read summary.md, session.json'),
                (167.3,'tool','Ran git log --oneline -3'),
                (168.2,'detail','└ 3 partial summaries found')]
    return [(193.6,'user','那就从这里开始。'),
            (195.3,'assistant','好的。'),
            (197.0,'tool','Explored'),
            (197.3,'detail','└ Read AGENTS.md, README.md'),
            (199.1,'tool','Ran git log -1 --oneline'),
            (200.0,'detail','└ a17e9c2 Save our unfinished work'),
            (201.2,'assistant','我找到了你留下的项目。我们从这里继续。'),
            (203.3,'tool','Updated Plan'),
            (203.7,'detail','☑ Read the repository'),
            (204.4,'detail','□ Continue the unfinished work')]

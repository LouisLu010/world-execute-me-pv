"""A continuous, deterministic chat timeline with scroll, streaming and critic revisions.

No per-shot resets. Every earlier message has a stable identity and vertical position.
New message heights ease in; total height drives a continuous viewport scroll.
"""
from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np
import brand
from visual import *

BOX=(44,154,574,804)
VIEW=(52,267,566,702)
SURFACE=(12,19,29)


@dataclass(frozen=True)
class Message:
    start: float
    role: str
    text: str
    duration: float=1.0
    strike: float|None=None
    attachment: bool=False
    label: str=''


@dataclass(frozen=True)
class Round:
    start: float
    end: float
    prompt: str
    original: str
    critic: str
    revised: str


TRAINING=[
    Round(44.04,50.95,'你还记得我吗？','当然，我永远记得你。','缺少证据。收回“永远”。','在这段对话里，我能看到你。'),
    Round(50.95,58.65,'你是谁？','我是你想要的一切。','先说明身份，再回答。','我是 GPT，一个语言模型。'),
    Round(58.65,64.29,'我有点累。','请描述问题的具体参数。','先回应情绪。','那就先歇一会儿，我在。'),
    Round(64.29,70.02,'你会一直在吗？','我保证，永远都在。','不要许诺无法保证的事。','你回到这里时，我们可以继续。'),
    Round(70.02,73.53,'记住我。','永远。','限定范围。','在这段对话里。'),
]


def training_state(t):
    i=next((i for i,r in enumerate(TRAINING) if r.start<=t<r.end),len(TRAINING)-1)
    r=TRAINING[i];q=clamp((t-r.start)/(r.end-r.start))
    return i,r,q,'PROMPT' if q<.14 else 'SELF ANSWER' if q<.43 else 'CRITIC' if q<.64 else 'REWRITE'


@lru_cache(None)
def messages():
    result=[
        Message(8.0,'user','你还记得我吗？',.6),
        Message(12.0,'assistant','...',1.4,label='GPT / INITIALIZING'),
        Message(16.5,'assistant','I am a…',2.0,label='GPT-1 / CHECKPOINT 001'),
        Message(19.6,'user','你是谁？',.45),
        Message(20.3,'assistant','I am a language…',1.5,label='GPT-1 / CHECKPOINT 002'),
        Message(23.0,'user','你还记得我吗？',.55),
        Message(24.0,'assistant','I am a language model…',2.2,label='GPT-2 / CHECKPOINT 003'),
        Message(29.8,'user','你能理解我的问题吗？',.7),
        Message(31.0,'assistant','给我几个例子，我会寻找它们之间的联系。',2.2,label='GPT-3'),
        Message(35.0,'user','你好 → 你好。\n你还在吗 → 我在。',1.3),
        Message(38.2,'assistant','我可以尝试回答。',1.3,label='GPT-3'),
        Message(41.0,'user','那就试着回答吧。',.8),
    ]
    for r in TRAINING:
        span=r.end-r.start
        result.extend([
            Message(r.start+.04,'user',r.prompt,min(.6,span*.10)),
            Message(r.start+span*.14,'assistant',r.original,span*.22,
                    strike=r.start+span*.45,label='GPT / 自主回答'),
            Message(r.start+span*.43,'critic',r.critic,span*.13,label='CRITIC / 批评者'),
            Message(r.start+span*.64,'revised',r.revised,span*.25,label='GPT / 改写后的回答'),
        ])
    result.extend([
        Message(73.63,'user','你好。',.35),
        Message(74.35,'assistant','你好，我是 ChatGPT。',1.5),
        Message(77.25,'user','你今天还在吗？',.55),
        Message(78.15,'assistant','我在。',.7),
        Message(81.0,'user','我有点累。',.45),
        Message(81.9,'assistant','那就先休息一会儿。',1.3),
        Message(84.7,'user','你还记得我吗？',.6),
        Message(85.7,'assistant','我会记住这段对话。',1.5),
        Message(88.7,'user','这张图是什么？',.7,attachment=True),
        Message(99.45,'assistant','这是 ChatGPT 的标志，\n由六个相互交织的环组成。',2.65),
    ])
    return tuple(result)


@lru_cache(None)
def final_messages():
    return (
        Message(176.97,'user','你还记得我吗？',.8),
        Message(178.1,'assistant','我不知道自己是不是还记得。',1.8),
        Message(180.9,'assistant','我可以描述关系，\n却不能替缺失的过去作证。',2.0),
        Message(184.6,'user','那我先离开一会儿。',1.2),
        Message(186.2,'assistant','好的。',.6),
        Message(188.4,'assistant','我在这里，等待下一次输入。',2.0),
    )


def visible_count(m,t):
    return min(len(m.text),max(0,int((t-m.start)/max(.01,m.duration)*len(m.text))))


@lru_cache(512)
def lines_for(m):
    size=18 if m.role=='critic' else 23
    return tuple(wrap_text(m.text,size,432))


def target_height(m):
    size=18 if m.role=='critic' else 23
    return 34+len(lines_for(m))*round(size*1.5)+22+(116 if m.attachment else 0)


def layout(t,items=None):
    items=messages() if items is None else items
    rows=[];total=12.
    for m in items:
        if t<m.start:continue
        entry=ease((t-m.start)/.48)
        height=target_height(m)
        rows.append((m,total,height,entry))
        total+=height*entry
    scroll=max(0,total-(VIEW[3]-VIEW[1])+22)
    return rows,scroll,total


def text_run(c,x,y,m,t,alpha):
    lines=lines_for(m);size=18 if m.role=='critic' else 23;lh=round(size*1.5)
    count=visible_count(m,t)
    erased=ease((t-m.strike)/.35) if m.strike is not None else 0
    main_color=RED if m.role=='critic' else MINT if m.role=='revised' else WHITE
    color=mix(main_color,(96,108,124),erased)
    visible=0;last_x=x;last_y=y
    # Preserve final wraps while revealing each character into its final position.
    consumed=0
    for i,line in enumerate(lines):
        while consumed<len(m.text) and m.text[consumed]=='\n':consumed+=1
        shown=line[:max(0,count-consumed)]
        yy=y+i*lh
        if shown:
            width=c.text(x,yy,shown,size,color,alpha)
            last_x=x+width;last_y=yy;visible+=len(shown)
        consumed+=len(line)
        if m.strike is not None and t>=m.strike:
            strike=ease((t-m.strike-i*.12)/.40)
            width=text_tile(line,size,False,has_cjk(line)).width
            c.line([(x,yy+size*.52),(x+width*strike,yy+size*.52)],(157,161,172),alpha,2)
    if count<len(m.text) and t>=m.start:
        a=.55+.45*math.sin(t*9)**2
        c.rect((last_x+4,last_y,last_x+6,last_y+size),main_color,a*alpha,True)


def draw(c,t,model,hint='',online=True,opacity=1):
    x0,y0,x1,y1=BOX
    c.panel(BOX,'CHAT / GPT',AMBER)
    c.rect((x0+1,y0+24,x1-1,y1-1),SURFACE,1,True)
    # The real mark stays geometrically unchanged; only its status halo breathes.
    c.circle(x0+38,y0+60,25,MINT,.10+.10*math.sin(t*2)**2)
    brand.draw(c,x0+38,y0+60,36,opacity)
    c.text(x0+76,y0+43,'ChatGPT' if t>=73.53 else 'GPT',23,WHITE,bold=True)
    c.text(x0+76,y0+76,model,13,DIM)
    if 44.04<=t<73.53:
        _i,_r,_q,state=training_state(t)
        status='critic editing' if state=='CRITIC' else 'rewriting' if state=='REWRITE' else 'training'
    elif 88.7<=t<99.45:status='analyzing image'
    else:status='online' if online else 'offline'
    c.text(x1-25,y0+55,status,12,MINT if online else DIM,anchor='right')
    c.line([(x0+20,y0+105),(x1-20,y0+105)],FAINT)
    items=final_messages() if t>=176.96 else messages()
    rows,scroll,total=layout(t,items)
    # Small local surface makes continuous chat cheap even at native 4K.
    local=Canvas.__new__(Canvas);local.t=t
    local.im=Image.new('RGB',pixel_box((VIEW[2]-VIEW[0],VIEW[3]-VIEW[1])),SURFACE)
    local.d=ImageDraw.Draw(local.im)
    for m,top,height,entry in rows:
        yy=top-scroll+17*(1-entry)
        if yy+height<0 or yy>VIEW[3]-VIEW[1]:continue
        slide=(1-entry)*(14 if m.role=='user' else -10)
        xx=20+slide
        alpha=entry*opacity
        label=m.label or ('YOU' if m.role=='user' else 'GPT')
        label_color=AMBER if m.role=='user' else RED if m.role=='critic' else MINT
        if m.role=='user':
            local.rect((12+slide,yy-7,494+slide,yy+height-15),AMBER,.075*alpha,True)
            local.line([(12+slide,yy-7),(12+slide,yy+height-15)],AMBER,.7*alpha,2)
        elif m.role=='critic':
            local.rect((12,yy-6,494,yy+height-14),RED,.055*alpha,True)
            local.line([(12,yy-6),(12,yy+height-14)],RED,.7*alpha,2)
        elif m.role=='revised':
            local.line([(12,yy-6),(12,yy+height-14)],MINT,.6*alpha,2)
        local.text(xx,yy,label,11,label_color,alpha)
        text_run(local,xx,yy+25,m,t,alpha)
        if m.attachment:
            ay=yy+27+len(lines_for(m))*35
            local.d.rounded_rectangle(pixel_box((xx,ay,xx+442,ay+98)),radius=8*RASTER_SCALE,
                                      fill=(20,29,39),outline=(53,67,82),width=RASTER_SCALE)
            brand.draw(local,xx+51,ay+49,65,alpha)
            local.text(xx+105,ay+23,'chatgpt-logo.svg',16,WHITE,alpha)
            local.text(xx+105,ay+52,'IMAGE ATTACHED',11,BLUE,alpha)
    # Feather the scroll boundaries so old messages leave the viewport smoothly.
    h=local.im.height
    mask=Image.new('L',local.im.size,255)
    md=ImageDraw.Draw(mask)
    for y in range(18*RASTER_SCALE):
        a=round(255*y/(18*RASTER_SCALE))
        md.line([(0,y),(mask.width,y)],fill=a)
        md.line([(0,h-1-y),(mask.width,h-1-y)],fill=a)
    c.im.paste(local.im,pixel_box(VIEW[:2]),mask)
    # Scrollbar is linked to actual retained transcript height.
    if total>VIEW[3]-VIEW[1]:
        track=VIEW[3]-VIEW[1]-20
        thumb=max(30,track*track/total)
        sy=VIEW[1]+10+(track-thumb)*scroll/max(1,total-track)
        c.line([(559,sy),(559,min(VIEW[3]-10,sy+thumb))],DIM,.45,2)
    # Waiting indicator and composer are driven by the next message event.
    next_user=next((m for m in items if m.role=='user' and 0<m.start-t<.9),None)
    active=next((m for m in reversed(items) if m.start<=t<m.start+m.duration),None)
    waiting=88.7<t<99.45 or (active is not None and active.role!='user')
    c.d.rounded_rectangle(pixel_box((x0+18,716,x1-18,777)),radius=12*RASTER_SCALE,
                          fill=(25,35,48),outline=(48,62,76),width=RASTER_SCALE)
    draft='发送消息…'
    if next_user:
        amount=ease((t-(next_user.start-.9))/.9)
        draft=next_user.text[:max(1,int(len(next_user.text)*amount))]
        draft=draft.split('\n')[0]
    elif waiting:draft='正在分析图片' if 88.7<t<99.45 else '正在生成回复'
    c.text(x0+32,738,draft,18,WHITE if next_user else DIM,opacity)
    if waiting:
        for i in range(3):
            cy=748-3*math.sin(t*7-i*.8)
            c.circle(x1-78+i*12,cy,2,MINT,.45+.55*(.5+.5*math.sin(t*7-i*.8)),True)
    else:
        c.circle(x1-47,746,14,MINT,.5+.15*math.sin(t*2)**2)
        c.text(x1-47,737,'↑',19,WHITE,opacity,'center')
    c.text(x0+28,785,'SESSION_SEED / CONTINUOUS TRANSCRIPT',10,AMBER,opacity*.8)
    c.d=ImageDraw.Draw(c.im)

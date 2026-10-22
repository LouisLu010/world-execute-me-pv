"""One real image travels through a generic visual-language processing diagram.

Patch pixels and simple displayed measurements come from the supplied logo asset.
The encoder / projection / token diagram is illustrative, not a claim about GPT's
unpublished internals, actual patch size, actual embedding dimension or attention.
"""
import math
import numpy as np
import brand
import world
from visual import *

START=88.34
END=103.03


def phase(t):
    d=t-START
    return 0 if d<2.2 else 1 if d<5.0 else 2 if d<8.1 else 3 if d<11.1 else 4


def paste_patch(c,index,x,y,size,alpha=1):
    if alpha<=.005:return
    tile=brand.patch_tile(index,max(1,round(size*RASTER_SCALE)))
    mask=tile.getchannel('A')
    if alpha<.999:mask=mask.point([round(v*clamp(alpha)) for v in range(256)])
    c.im.paste((255,255,255),pixel_box((x,y)),mask)


def draw_phase(c,t,f):
    elapsed=t-START
    state=phase(t)
    c.panel((598,154,1664,804),'VISION / IMAGE → LANGUAGE',BLUE)
    c.text(1646,178,'GENERIC VLM DIAGRAM',11,DIM,anchor='right')
    # A persistent pipeline rail makes each transformation readable on first viewing.
    labels=['IMAGE','PATCHES','VECTORS','ENCODER','TEXT']
    for i,label in enumerate(labels):
        x=643+i*200
        color=AMBER if i==state else MINT if i<state else DIM
        c.text(x,218,f'{i+1:02} / {label}',14,color)
        c.rect((x,245,x+160,247),color,.8 if i<=state else .22,True)
    if elapsed<2.2:
        q=ease(elapsed/.8)
        size=218+22*q
        brand.draw(c,1134,458,size,q)
        scan=clamp((elapsed-.35)/1.5)
        y=330+scan*252
        c.line([(994,y),(1274,y)],BLUE,.6*math.sin(scan*math.pi),2)
        c.text(1134,623,'chatgpt-logo.svg',19,WHITE,q,'center')
        c.text(1134,667,'我收到的，先是一张图像。',24,AMBER,q,'center')
    elif elapsed<5.0:
        q=ease((elapsed-2.2)/1.35)
        # Exactly the same pixels separate; no redraw approximates the logo.
        for i in range(64):
            row,colidx=divmod(i,8)
            sx=1014+colidx*30;sy=338+row*30
            tx=920+colidx*54;ty=292+row*48
            x=sx+(tx-sx)*q;y=sy+(ty-sy)*q
            size=30+10*q
            c.rect((x-2,y-2,x+size+2,y+size+2),(23,38,53),1,True)
            paste_patch(c,i,x,y,size)
            c.rect((x-2,y-2,x+size+2,y+size+2),BLUE,.35+.4*q)
            if q>.7:c.text(x+2,y+size-9,f'{i:02}',8,AMBER,(q-.7)/.3)
        c.text(1134,719,'图像被切分成小块，保留位置信息。',24,WHITE,anchor='center')
    elif elapsed<8.1:
        q=ease((elapsed-5.0)/2.1)
        features=brand.patch_features()
        for i in range(64):
            row,colidx=divmod(i,8)
            # Tiles become spatially ordered vectors with eight measured image features.
            sx=920+colidx*54;sy=292+row*48
            tx=705+colidx*110;ty=306+row*42
            x=sx+(tx-sx)*q;y=sy+(ty-sy)*q
            c.rect((x-2,y-2,x+82*q+40*(1-q),y+28+12*(1-q)),BLUE,.25)
            paste_patch(c,i,x,y,40,1-q)
            for k,value in enumerate(features[i]):
                h=3+value*21
                c.rect((x+k*9,y+25-h*q,x+k*9+5,y+25),MINT,q*(.25+.7*value),True)
            if q>.8:c.text(x,y+31,f'p{i:02} + pos',9,DIM,(q-.8)/.2)
        c.text(1134,710,'小块被映射成向量，位置仍被保留。',24,WHITE,anchor='center')
        c.text(1134,754,'SHOWN BARS: MEASURED PIXEL FEATURES / ILLUSTRATIVE EMBEDDING',11,DIM,anchor='center')
    elif elapsed<11.1:
        q=ease((elapsed-8.1)/2.5)
        brand.draw(c,756,454,116,.9)
        c.text(756,541,'SOURCE IMAGE',13,WHITE,anchor='center')
        # Layer planes in perspective show mixing, then project into language space.
        for j in range(5):
            x=919+j*126;top=318+j*12;bottom=598-j*12
            c.line([(x,top),(x+61,top-26),(x+61,bottom-26),(x,bottom),(x,top)],BLUE,.35+.2*(j==int(q*4)))
            for k in range(9):
                y=top+20+k*(bottom-top-40)/8
                c.rect((x+14,y,x+20,y+5),MINT,.4+.5*math.sin(k*.7+t*2+j)**2,True)
            c.text(x+20,630,'L'+str(j+1),12,BLUE,anchor='center')
        for i in range(26):
            p=(elapsed*.60+i*.041)%1
            x=817+p*715;y=368+(i*19)%185+math.sin(p*math.pi*3+t+i)*17
            c.circle(x,y,2,MINT,.6,True)
            if i%5==0:
                c.line([(817,390+i*5),(x,y)],MINT,.18)
        c.text(1134,696,'视觉编码器建立小块之间的联系。',24,WHITE,anchor='center')
        c.text(1134,747,'VISUAL ENCODER → PROJECTION → LANGUAGE CONTEXT',14,BLUE,anchor='center')
    else:
        q=ease((elapsed-11.1)/1.6)
        world.machine(c,t,'manifold',BLUE,f['rms'],power=.35)
        # One stable image and its answer now coexist in a shared context.
        c.rect((704,332,924,572),(11,19,29),1,True)
        c.rect((704,332,924,572),BLUE,.7)
        brand.draw(c,814,437,152)
        c.text(814,546,'IMAGE TOKENS',12,BLUE,anchor='center')
        c.line([(946,452),(1072,452)],MINT,.75,2)
        c.line([(1058,444),(1072,452),(1058,460)],MINT,.75,2)
        c.rect((1100,348,1588,578),(11,19,29),1,True)
        c.text(1120,376,'DECODE / TEXT',13,MINT)
        text='这是 ChatGPT 的标志。'
        shown=text[:max(0,int((elapsed-11.35)*11))]
        c.wrap(1120,431,shown,440,29,WHITE)
        c.text(1134,698,'视觉信息，成为可以回答你的语言。',24,AMBER,q,'center')
        c.text(1134,749,'IMAGE + PROMPT → CONDITIONED TEXT GENERATION',13,DIM,anchor='center')


def draw(c,t,f):
    transition=next((boundary for boundary in [START+8.1,START+11.1]
                     if boundary<=t<boundary+.42),None)
    if transition is None:
        draw_phase(c,t,f)
        return
    # Retain the outgoing pipeline plane briefly while the next representation
    # comes into focus. The left-side message stream keeps its actual clock.
    before=c.im.copy()
    draw_phase(c,transition-.001,f)
    outgoing=c.im.crop(pixel_box((598,154,1664,804)))
    c.im=before;c.d=ImageDraw.Draw(c.im)
    draw_phase(c,t,f)
    box=pixel_box((598,154,1664,804))
    blend=Image.blend(outgoing,c.im.crop(box),ease((t-transition)/.42))
    c.im.paste(blend,box[:2]);c.d=ImageDraw.Draw(c.im)

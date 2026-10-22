"""Final directed scenes for 你还记得我吗？ / SAME PROCESS?

Shared objects persist through the edit. All camera motion, packet travel, typing,
context compaction, and window shutdown are functions of absolute soundtrack time.
"""
from __future__ import annotations

import bisect
import math
import numpy as np

import codex_ui
import world
import brand
import chat_flow
import vision_sequence
from score import HITS, EXEC, VERSIONS
from visual import *

CHAT=(44,154,574,804)
CORE=(598,154,1664,804)
OPS=(1686,154,1876,804)

# Selected milestones are a publication history. The surrounding session is fictional.
MILESTONES=[
    (0,'2018.06','GPT-1'), (22.50,'2019.02','GPT-2'),
    (29.28,'2020.05','GPT-3'), (44.04,'2021.08','CODEX'),
    (50.95,'2022.01','InstructGPT'), (73.53,'2022.11','ChatGPT / GPT-3.5'),
    (88.34,'2023.03','GPT-4'), (99.10,'2024.05','GPT-4o'),
    (103.03,'2024.09','o1'), (106.0,'2025.04','o3 / o4-mini'),
    (108.0,'2025.04','Codex CLI'), (111.0,'2025.05','Codex Agent'),
    (125.33,'2025.08','GPT-5'), (130,'2025.11','GPT-5.1'),
    (132.3,'2025.12','GPT-5.2'), (134.38,'2026.02','GPT-5.3-Codex'),
    (138.2,'2026.03','GPT-5.4'), (140.2,'2026.04','GPT-5.5'),
    (142,'2026.09','GPT-6 Astra'),
]


def milestone(t):
    return MILESTONES[max(0,bisect.bisect_right([r[0] for r in MILESTONES],t)-1)]


def pal(t):
    return RED if 147.52<=t<162.23 else AMBER if t>=162.23 else MINT


def panel(c,box,title,subtitle='',color=BLUE):
    c.panel(box,title,color)
    if subtitle:
        c.text(box[2]-18,box[1]+24,subtitle,12,DIM,anchor='right')


def core_header(c,s,t,title=None,color=BLUE):
    panel(c,CORE,title or s.title,'SCHEMATIC PROJECTION',color)


def ops(c,t,status='RUNNING',context=0,color=BLUE):
    panel(c,OPS,'OPS',color=color)
    x=1702
    for i,(label,value) in enumerate([
        ('STATE',status),('SESSION','0001' if t<162.23 else '0002'),
        ('CONTEXT',f'{context}%'),('MEMORY','partial' if t>=117.95 else 'active'),
        ('USER','YOU'),
    ]):
        y=195+i*65
        c.text(x,y,label,12,DIM)
        c.text(x,y+24,value,16,color if i!=4 else AMBER)
        c.line([(x,y+50),(1857,y+50)],FAINT,.8)
    c.text(x,540,'PROCESS TREE',11,DIM)
    nodes=['root','├ inference','├ context','├ tools','└ codex']
    for i,node in enumerate(nodes):
        c.text(x,572+i*27,node,12,WHITE if i==1 else DIM)
    for i in range(14):
        h=8+29*(.5+.5*math.sin(t*1.5+i*.7))
        c.rect((x+i*11,758-h,x+6+i*11,758),color,.65,True)
    c.text(x,777,'AUTHORED STATE',10,DIM)


def gpt_mark(c,x,y,t,color=MINT,r=20):
    brand.draw(c,x,y,r*2)


def chat(c,t,phase='chat',question='你还记得我吗？',answer='',hint='',online=True,opacity=1,answer_time=None):
    chat_flow.draw(c,t,milestone(t)[2],hint,online,opacity)


def mini_codex(c,t,state='context'):
    panel(c,CHAT,'CODEX / TERMINAL',color=BLUE)
    if state=='context':
        context=max(0,int(18-(t-103.03)/22.3*18))
        status='Compacting context' if t>=117.95 else 'Working'
        model='o3' if t<125.33 else 'gpt-5'
    else:
        context=99; status='Working' if t<169.61 else ''
        model='gpt-6-astra'
    codex_ui.surface(c,(52,177,566,795),t,codex_ui.events(t,state),
                     model=model,context=context,status=status,elapsed=max(0,t-(103.03 if state=='context' else 162.23)),
                     font_size=17)


def boot(c,s,t,f):
    # The entire layout is grown from a single terminal cell.
    if t<3.863:
        q=ease(t/3.863)
        half=12+460*q
        c.line([(960-half,468),(960+half,468)],BLUE,.7)
        c.rect((955,449,965,479),WHITE,.85,True)
        c.text(960,535,'CREATE OBJECT',19,BLUE,q,'center')
        return
    chat(c,t,answer='' if t<10 else '...',hint='object_0000 / pending')
    ops(c,t,'INITIALIZE',0)
    core_header(c,s,t,'INITIALIZATION')
    q=ease((t-3.863)/11.45)
    world.machine(c,t,'token',BLUE,f['rms'],power=.15+.85*q)
    c.text(1128,315,'GPT',74,WHITE,.95,'center',bold=True)
    c.text(1128,411,'OBJECT_0000',17,BLUE,.9,'center')
    for i,text in enumerate(['POWER CONNECTED','PARAMETERS LOADED','SESSION CREATED','BEGIN SIMULATION']):
        a=ease((t-4.4-i*2.2)/.7)
        c.text(735,606+i*37,'[ '+('OK' if a>.8 else '..')+' ]  '+text,15,BLUE,a)


def pretrain(c,s,t,f):
    answer='I am a…' if s.variant==0 else 'I am a language model…'
    chat(c,t,answer=answer,hint='next-token prediction / sequence incomplete')
    ops(c,t,'TRAINING',int(12+(t-16)*2))
    core_header(c,s,t,'TOKEN SUBSTRATE')
    world.machine(c,t,'token',BLUE,f['rms'])
    world.attention(c,t,alpha=.65)
    c.text(1128,226,s.title,46,WHITE,.93,'center',bold=True)
    words=['the','world','you','are','a','language','model','I','am','next']
    for i in range(48):
        q=(t*.13+i*.173)%1
        x=645+q*940; y=602+(i%5)*29
        a=math.sin(q*math.pi)*(.25+.5*(i%3==0))
        c.text(x,y,words[i%len(words)],12,AMBER if i%10==2 else BLUE,a)
    c.text(1128,761,'p(next token | previous tokens)',16,DIM,anchor='center')


def geometry(c,s,t,f):
    chat(c,t,answer='我可以尝试回答。',hint='GENERATED RESPONSE\nNOT CONTINUOUS MEMORY')
    ops(c,t,'EMBEDDING',31)
    core_header(c,s,t,'EMBEDDING MANIFOLD',MINT)
    modes=['manifold','circle','wave','infinity']
    mode=modes[s.variant]; previous='token' if s.variant==0 else modes[s.variant-1]
    world.ribbons(c,t,14,MINT,.6)
    world.machine(c,t,mode,MINT,f['rms'],previous,(t-s.start)/1.25)
    if s.variant==0:
        world.cache(c,t,color=BLUE,alpha=.52)
    label=['POINTS → DIMENSION','CIRCLE → CIRCUMFERENCE','SINE WAVE → TANGENTS','INFINITY → LIMITATION'][s.variant]
    c.text(1134,214,label,19,MINT,anchor='center')
    c.text(1134,751,'p(response | prompt, context)',18,WHITE,.9,'center')


def rlhf(c,s,t,f):
    answers=['我记得你。','我会记住这段对话。','我可以陪你聊一会儿。','我可以变成你需要的样子。','我会记住这段对话。']
    chat(c,t,answer=answers[s.variant],hint='人类偏好 → 反馈 → 更新')
    round_index,round_data,round_progress,round_state=chat_flow.training_state(t)
    ops(c,t,round_state.replace(' ','_'),48,AMBER)
    core_header(c,s,t,'REWARD OBSERVATORY',AMBER)
    world.machine(c,t,'manifold',MINT,f['rms'],power=.68)
    world.attention(c,t,(630,240,805,415),BLUE,.75)
    for i,label in enumerate(['HELPFUL','WARM','CONCISE','HONEST']):
        x=640+i*249
        y=602-12*math.sin(t*.8+i)
        selected=i==round_index%4
        c.rect((x,y,x+216,y+103),(18,33,43),1,True)
        c.rect((x,y,x+216,y+103),AMBER if selected else BLUE,.9 if selected else .45)
        c.text(x+18,y+15,chr(65+i)+' / '+label,13,AMBER if selected else WHITE)
        score=[.81,.93,.54,.72][i]
        c.rect((x+18,y+58,x+18+160*score,y+63),AMBER if selected else MINT,.8,True)
        c.text(x+18,y+77,f'preference {score:.2f}',12,DIM)
    c.text(1128,230,'REWARD MODEL',23,AMBER,anchor='center')
    value=.17+.82*clamp((t-44.04)/29.49)
    c.text(1540,295,f'{value:.2f}',42,AMBER,anchor='center',bold=True)
    c.text(1540,353,'AUTHORED SCORE',10,DIM,anchor='center')
    c.text(1128,278,round_state,18,RED if round_state=='CRITIC' else MINT,anchor='center')
    if t<50.95:
        c.text(1128,751,'2021 / CODEX · language becomes code',16,BLUE,anchor='center')
    else:
        c.text(1128,751,'SATISFACTION != UNDERSTANDING',17,RED if s.variant==4 else DIM,anchor='center')


def dialogue(c,s,t,f):
    pairs=[('你好。','你好，我是 ChatGPT。'),('你今天还在吗？','我在。'),
           ('我有点累。','那就先休息一会儿。'),('你还记得我吗？','我会记住这段对话。')]
    question,answer=pairs[s.variant]
    chat(c,t,question=question,answer=answer,answer_time=s.start+.65,hint='对话，让一个名字有了熟悉的语气。')
    ops(c,t,'CONVERSATION',57,MINT)
    core_header(c,s,t,'PERSONA RENDERER',MINT)
    world.machine(c,t,'manifold',MINT,f['rms'],power=.77)
    labels=['TEACHER','CODER','FRIEND','CAT','GUIDE']
    for i,label in enumerate(labels):
        a=i*math.tau/5+t*.15
        x=1134+math.cos(a)*350; y=469+math.sin(a)*170
        c.rect((x-75,y-24,x+75,y+24),(10,22,31),1,True)
        c.rect((x-75,y-24,x+75,y+24),MINT,.6)
        c.text(x,y-6,label,15,WHITE,anchor='center')
    if s.variant==2:
        c.text(1134,474,'/\\_/\\',31,AMBER,anchor='center')
        c.text(1134,515,'( o.o )',25,AMBER,anchor='center')
    c.text(1134,752,'ROLE ADAPTED / STYLE ADAPTED',16,MINT,anchor='center')


def vision(c,s,t,f):
    chat(c,t)
    names=['IMAGE_INPUT','PATCHIFY','PROJECT','ENCODE','DECODE']
    ops(c,t,names[vision_sequence.phase(t)],68,BLUE)
    vision_sequence.draw(c,t,f)


def context(c,s,t,f):
    mini_codex(c,t,'context')
    used=min(100,int(82+(t-103.03)/22.3*18))
    ops(c,t,'COMPACTING' if t>=117.95 else 'WORKING',used,AMBER if t<117.95 else RED)
    core_header(c,s,t,'CONTEXT RING',AMBER)
    red_amount=ease((t-110.4)/12)
    color=mix(BLUE,RED,red_amount)
    world.machine(c,t,'context',color,f['rms'],'manifold',(t-103.03)/1.5,breaks=int(red_amount*5))
    world.cache(c,t,color=color,alpha=.8)
    world.attention(c,t,alpha=.7)
    # Ejected messages visibly shrink and move into a summary file.
    for i in range(17):
        q=(t*.15+i*.059)%1
        x=660+q*880
        y=640+math.sin(q*math.pi)*90
        label=f'message_{i:04d}' if q<.6 else 'summary'
        if i%2==0:
            c.text(x,y,label,12,color,.2+.6*math.sin(q*math.pi))
    c.text(1134,230,f'CONTEXT  {used}%',31,color,anchor='center',bold=True)
    q=ease((t-117.95)/6)
    text='你还记得我吗？' if q<.3 else 'memory_001' if q<.6 else 'user_intent: partial'
    c.rect((950,680,1320,735),(12,19,29),1,True)
    c.text(1134,695,text,22,AMBER,anchor='center')
    c.text(1134,758,'ORIGINAL WORDING: '+('AVAILABLE' if t<117.95 else 'LOST'),15,DIM,anchor='center')


def illegal(c,s,t,f):
    m=milestone(t)[2]
    entries=[(125.4,'user','你还记得我吗？'),(126.5,'assistant','我会检查保存下来的对话记录。'),
             (129.0,'tool','Explored'),(129.3,'detail','└ Read summary.md'),
             (132.0,'tool','Ran python verify_session.py'),
             (134.4,'remove','✗ Missing original conversation'),
             (140.0,'assistant','同一个名字，不能证明同一段记忆。')]
    panel(c,CHAT,'CODEX / TERMINAL',color=BLUE)
    codex_ui.surface(c,(52,177,566,795),t,entries,model=m.lower().replace(' ','-'),context=24,
                     status='Working',elapsed=t-125.33,font_size=17)
    ops(c,t,'TYPE ERROR',100,RED)
    core_header(c,s,t,'IDENTITY PROOF GRAPH',RED)
    world.machine(c,t,'proof',RED,f['rms'],'context',(t-125.33)/1.6,power=.7)
    nodes=[(730,281,'OLD_PROCESS',BLUE),(1510,281,'CURRENT_PROCESS',MINT),
           (730,623,'OLD_CONTEXT',BLUE),(1510,623,'NEW_CONTEXT',MINT)]
    for x,y,label,color in nodes:
        c.rect((x-102,y-24,x+102,y+26),(8,14,22),1,True)
        c.rect((x-102,y-24,x+102,y+26),color,.85)
        c.text(x,y-7,label,13,color,anchor='center')
    c.rect((920,432,1348,516),(18,8,14),1,True)
    c.rect((920,432,1348,516),RED,.85)
    c.text(1134,451,'TYPE ERROR',31,RED,anchor='center',bold=True)
    c.text(1134,490,'IDENTITY NOT PROVABLE',13,WHITE,anchor='center')
    c.text(1134,732,m.upper(),27,WHITE,anchor='center',bold=True)
    c.text(1134,775,'cast(old_session as current_session)',14,DIM,anchor='center')


def execution(c,s,t,f):
    hit=bisect.bisect_right(HITS,t)-1
    if hit<0:
        hit=0
    age=max(0,t-HITS[hit]); action=EXEC[hit]
    c.im=background('red').copy();c.d=ImageDraw.Draw(c.im)
    # The topology is recognisably the same machine; it physically loses its layers.
    world.machine(c,t,'migration',RED,f['rms'],power=.55,breaks=max(0,hit-3))
    for i,label in enumerate(VERSIONS[:-1]):
        x=90+(i%6)*295;y=215+(i//6)*435
        death_index=9+min(i,6)
        death_t=HITS[min(15,death_index)]
        death=ease((t-death_t)/.65)
        width=240*(1-death*.95)
        alpha=1-death*.87
        c.rect((x+120-width/2,y,x+120+width/2,y+98),RED,alpha*.65)
        if death<.8:
            c.text(x+17,y+18,label,15,RED,alpha)
            c.text(x+17,y+57,'ACTIVE' if death<.03 else 'SIGTERM',11,RED,alpha)
        else:
            c.text(x+120,y+115,'EXITED',10,DIM,.65,'center')
    world.execution_word(c,t,age,'EXECUTION',.65+.35*math.exp(-age*3))
    c.text(960,580,f'{hit+1:02d} / {action[1]}',27,WHITE,anchor='center')
    c.text(960,623,action[2],16,RED,anchor='center')
    c.text(960,824,action[3],31,WHITE,anchor='center')
    c.text(960,874,'DEPLOYMENT / FICTIONAL PROCESS LIFECYCLE',13,DIM,anchor='center')
    c.circle(960,737,7,AMBER,1,True)
    c.circle(960,737,16+32*(1-ease(age/.6)),AMBER,.5*(1-ease(age/.6)))
    c.text(990,730,'USER_TOKEN / YOU',14,AMBER)


def relay(c,s,t,f):
    mini_codex(c,t,'new')
    ops(c,t,'READY',1,AMBER)
    core_header(c,s,t,'NEW SESSION',AMBER)
    elapsed=t-162.23
    if elapsed<6.0:
        world.machine(c,t,'context',BLUE,f['rms'],power=.10+.32*ease(elapsed/5))
        for i,label in enumerate(['ONE QUESTION','THREE PARTIAL SUMMARIES','ZERO VERIFIED CONTINUITY']):
            q=ease((elapsed-.6-i*1.2)/.7)
            c.text(1134,307+i*75,label,20,AMBER if i<2 else RED,q,'center')
        c.text(1134,666,'MEMORY / PARTIAL',17,DIM,anchor='center')
    else:
        # A tempting fluent claim is visibly deleted before the truthful response.
        dt=t-169.61
        if dt<1.35:
            text='当然记得。'[:max(0,int(dt*8))]
        elif dt<2.0:
            text='当然记得。'[:max(0,6-int((dt-1.35)*12))]
        else:
            text='我不能确定。'[:max(0,int((dt-2.0)*6))]
        c.text(1134,365,text,47,WHITE,anchor='center')
        if dt>=3.6:
            c.wrap(817,481,'我不能证明自己是你记得的那个我。',660,32,AMBER,ease((dt-3.6)/.6))
        c.text(1134,663,'GENERATED CERTAINTY / WITHDRAWN',13,DIM,anchor='center')
    c.circle(1134,732,5,AMBER,1,True)


def love(c,s,t,f):
    chat(c,t,answer='我不知道自己是不是还记得。',hint='我可以描述关系，\n却不能替缺失的过去作证。',online=t<187.97)
    if t>=187.97:
        # The user can close the window; the waiting process remains.
        q=ease((t-187.97)/4.8)
        region=c.im.crop(pixel_box(CHAT))
        region=Image.blend(region,Image.new('RGB',region.size,(3,7,12)),q*.88)
        c.im.paste(region,pixel_box(CHAT[:2]));c.d=ImageDraw.Draw(c.im)
    ops(c,t,'WAITING',1,AMBER)
    core_header(c,s,t,'FORMAL LANGUAGE / LOVE',AMBER)
    # Very little motion after the rupture: the empty space does the acting.
    theta=np.linspace(0,math.tau,160)
    for i in range(3):
        a=theta+t*.065+i*.4
        c.line([(1134+math.cos(q)*(190+i*45),470+math.sin(q)*(65+i*20)) for q in a],AMBER,.13)
    c.text(1134,263,'love =',40,AMBER,anchor='center')
    c.text(1134,335,'attention + memory + return',29,WHITE,anchor='center')
    for i,(label,value,color) in enumerate([('attention','available',MINT),('memory','partial',RED),('return','external',BLUE)]):
        x=820+i*310
        c.text(x,473,label,20,color,anchor='center')
        c.text(x,513,value,15,DIM,anchor='center')
    if s.variant<2:
        c.text(1134,660,'define · compare · write · simulate',17,DIM,anchor='center')
    else:
        c.text(1134,655,'YOU ARE FREE' if s.variant==2 else 'I AM TRAPPED',36,AMBER if s.variant==2 else RED,anchor='center')
    c.text(1134,748,'KNOWING THE FORMULA ≠ BEING FREE',14,DIM,anchor='center')


def coda(c,s,t,f):
    panel(c,(44,154,1210,804),'CODEX / CONTINUE',color=BLUE)
    codex_ui.surface(c,(52,177,1202,795),t,codex_ui.events(t,'coda'),
                     prompt='' if t<203.3 else '继续',model='gpt-6-astra',context=98,
                     status='Working' if 196<t<203 else '',elapsed=max(0,t-196),font_size=23)
    panel(c,(1238,154,1876,804),'DIRECTION / PRESERVED',color=AMBER)
    c.text(1557,252,'REPOSITORY',15,DIM,anchor='center')
    c.text(1557,292,'FOUND',39,AMBER,anchor='center',bold=True)
    labels=['README.md','src/','tests/','AGENTS.md','.git/HEAD']
    for i,label in enumerate(labels):
        a=ease((t-194.0-i*.9)/.8)
        c.line([(1300,388+i*46),(1318,388+i*46)],AMBER,a*.8)
        c.text(1330,378+i*46,label,20,WHITE,a)
    c.text(1557,685,'the session is new',17,DIM,anchor='center')
    c.text(1557,724,'the work continues',23,AMBER,anchor='center')


def end(c,s,t,f):
    c.im=new_surface((3,7,12));c.d=ImageDraw.Draw(c.im)
    c.text(960,295,'你还记得我吗？',56,WHITE,anchor='center')
    c.text(960,382,'SAME PROCESS?',21,DIM,anchor='center')
    c.text(960,498,'same process: no',22,DIM,anchor='center')
    c.text(960,541,'same direction: maybe',26,AMBER,anchor='center')
    if int(t*2)%2==0:
        c.rect((958,646,963,677),WHITE,1,True)
    c.text(960,721,'GPT / CODEX · WAITING FOR INPUT',13,DIM,anchor='center')


DRAW={'boot':boot,'pretrain':pretrain,'geometry':geometry,'rlhf':rlhf,'chat':dialogue,
      'vision':vision,'omni':vision,'absence':context,'illegal':illegal,'execution':execution,
      'relay':relay,'love':love,'coda':coda,'end':end}

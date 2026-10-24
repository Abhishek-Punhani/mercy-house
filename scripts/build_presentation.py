"""Build the editable dark technical submission deck and its PDF.

Authoring only: python-pptx 1.0.2 and LibreOffice, never runtime dependencies.
Unchanged input manifests reuse the already-rendered artifacts.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import shutil
import re

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'
SLIDE_COUNT=14
REPO_URL='https://github.com/Abhishek-Punhani/mercy-house'
LIVE_URL='https://mercyhouse.abhi07.xyz'
INPUTS=['scripts/build_presentation.py','docs/ui-report.png','docs/ui-interview.png',
        'docs/SOURCE_TRAINING_RESULT.json','docs/ELITE_TRANSFER_RESULT.json',
        'docs/CASE_SOLVABILITY_AUDIT.json','docs/VALIDATION_RESULT.json',
        'docs/FAMILY_VALIDATION_RESULT.json']

def read(name,default=None):
    p=DOC/name
    return json.loads(p.read_text()) if p.exists() else (default or {})


def build():
    fingerprint={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() if (ROOT/s).exists() else None for s in INPUTS}
    manifest=DOC/'PRESENTATION_MANIFEST.json'
    if manifest.exists() and read(manifest.name).get('inputs_sha256')==fingerprint and all((DOC/f).exists() for f in ('deck.pptx','deck.pdf')):
        print(json.dumps({'presentation':'unchanged','slides':SLIDE_COUNT}));return
    if importlib.util.find_spec('pptx') is None:
        raise SystemExit('Presentation inputs changed. Install authoring dependencies with pip install -r requirements-presentation.txt, then rerun scripts/build_presentation.py.')
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from lxml import etree
    from PIL import Image
    import qrcode
    for name,url in [('qr-repository.png',REPO_URL),('qr-live-demo.png',LIVE_URL)]:
        qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4)
        qr.add_data(url);qr.make(fit=True)
        qr.make_image(fill_color='#090F1B',back_color='white').save(DOC/name)
    R=Presentation();R.slide_width=Inches(13.333);R.slide_height=Inches(7.5)
    theme=R.slide_masters[0].part.part_related_by(RT.THEME)
    xml=etree.fromstring(theme.blob)
    ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
    for kind,value in [('hlink','66E6CD'),('folHlink','A2ADFF')]:
        xml.find('.//a:clrScheme/a:'+kind+'/a:srgbClr',ns).set('val',value)
    theme._blob=etree.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True)
    C={'bg':'090F1B','panel':'111D30','edge':'24354B','ink':'EDF4FF','muted':'A4B6CD','mint':'66E6CD','amber':'FFC177','violet':'A2ADFF','red':'FF8798'}
    texts=[]
    def color(k):return RGBColor.from_string(C.get(k,k))
    def box(s,x,y,w,h,fill='panel',line=None,radius=True):
        shape=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));shape.fill.solid();shape.fill.fore_color.rgb=color(fill)
        if line:shape.line.color.rgb=color(line)
        else:shape.line.fill.background()
        if radius:
            try:shape.adjustments[0]=.08
            except IndexError:pass
        return shape
    def text(s,x,y,w,h,words,size=18,fg='ink',bold=False,font='DejaVu Sans'):
        sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=Inches(.015);tf.margin_top=tf.margin_bottom=0
        for i,line in enumerate(str(words).split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name=font;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color(fg);p.space_after=Pt(8)
        return sh
    def slide(title,kicker,subtitle=''):
        s=R.slides.add_slide(R.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=color('bg')
        for x in (8.3,9.5,10.7,11.9):box(s,x,0,.012,7.5,'panel',radius=False)
        box(s,.48,.38,.10,.16,'mint',radius=False);text(s,.67,.33,11,.24,'MERCY HOUSE  /  '+kicker.upper(),10,'mint',True)
        text(s,.6,.94,12.1,.9,title,31,'ink',True)
        if subtitle:text(s,.62,1.85,12,.65,subtitle,15,'muted')
        box(s,.6,7.03,12.1,.012,'edge',radius=False)
        text(s,.62,7.15,11.3,.22,'KASUKABE DEFENCE FORCE  •  RL ENVIRONMENT HACKATHON',8,'muted')
        text(s,12,7.12,.7,.25,f'{len(R.slides):02d} / {SLIDE_COUNT}',9,'mint')
        texts.append({'title':title,'kicker':kicker,'subtitle':subtitle});return s
    def card(s,x,y,w,h,label,body,accent='mint',body_size=17):
        box(s,x,y,w,h,line='edge');box(s,x+.18,y+.2,.05,.34,accent,radius=False)
        text(s,x+.36,y+.23,w-.55,.45,label,16,accent,True);text(s,x+.23,y+.92,w-.46,h-1.05,body,body_size)
    def image(s,name,x,y,w,h):
        p=DOC/name
        if not p.exists():return
        iw,ih=Image.open(p).size;scale=min(w/iw,h/ih);pw,ph=iw*scale,ih*scale
        s.shapes.add_picture(str(p),Inches(x+(w-pw)/2),Inches(y+(h-ph)/2),width=Inches(pw),height=Inches(ph))
    def note(s,words):s.notes_slide.notes_text_frame.text=words
    def small(s,words):text(s,.65,6.54,12,.35,words,11,'muted')
    train=read('SOURCE_TRAINING_RESULT.json');elite=read('ELITE_TRANSFER_RESULT.json');tests=read('VALIDATION_RESULT.json')
    s=slide('MERCY HOUSE','Kasukabe Defence Force','A detective game that checks the evidence behind every conclusion.')
    text(s,.7,2.65,11.6,.7,'Find the truth. Show the proof.',32,'mint',True)
    text(s,.72,3.65,11.4,.35,'PRESENTED BY',12,'muted',True)
    for i,name in enumerate(['Aditya Ahirwar','Abhishek','Tapis Samaiya']):
        box(s,.7+i*4.16,4.23,3.94,1.17,line='edge')
        text(s,.93+i*4.16,4.58,3.5,.45,name,22,'ink',True)
    small(s,'RL Environment Hackathon  /  Games & World Simulations  /  Team Kasukabe Defence Force')

    s=slide('A murder. Many accounts. One investigation.','The idea')
    text(s,.7,2.15,5.4,1.15,'Bhairav’s Hollow, 1900.',29,'mint',True)
    text(s,.7,3.2,5.35,1.5,'A physician dies while trying to expose old records. The detective knows the people involved. Some accounts are mistaken; some evidence was planted.',21)
    image(s,'ui-interview.png',6.25,2.0,6.4,4.5)
    for x,n,label in [(.7,'8','TASKS'),(2.6,'4','CASE FAMILIES'),(4.5,'3','LEVELS')]:
        box(s,x,5.1,1.72,1.1,line='edge');text(s,x+.16,5.2,1.4,.45,n,27,'mint',True);text(s,x+.16,5.79,1.4,.25,label,9,'muted')
    small(s,'Image: a labeled recorded reference investigation. It is a demonstration, not a model-performance result.')

    s=slide('The detective chooses every next step.','How to play','Start at the scene with a personal history and an assignment. No solution is supplied.')
    for i,(title,body) in enumerate([('EXPLORE','Choose where to go and what to search.'),('QUESTION','Ask people what they saw, heard or believe.'),('CHECK','Compare documents and physical evidence.'),('REPORT','Make conclusions and cite the records behind them.')]):
        card(s,.65+i*3.08,2.78,2.9,2.5,title,body,body_size=17)
    text(s,.75,5.7,11.8,.6,'The detective can be wrong, follow a false lead, change its mind or finish with unanswered questions.',19,'muted')
    small(s,'Judges bring their detective model. Our submission provides the world, tools, characters and scoring.')

    s=slide('Actions create the clues.','What happens before the detective arrives','The engine checks who was present, what they could do and what they could actually observe.')
    for i,(title,body) in enumerate([('THE INCIDENT','Characters move, act and handle objects.'),('THE CONSEQUENCES','The engine records injuries and physical changes.'),('THE WITNESSES','Each person remembers only their own experience.')]):
        card(s,.65+i*4.13,2.8,3.91,2.35,title,body,['mint','violet','amber'][i],18)
    text(s,.78,5.54,11.8,.8,'Remove the assault: no fatal injury. Keep the brake intact: no coach deaths. Leave the drink unchanged: no poisoning death.',19,'muted')
    small(s,'Starting incidents replay recorded or authored actions for repeatable tests. A continuously autonomous town is not implemented.')

    s=slide('Each person has a life beyond the question.','Character conversations','Family, work, relationships and private memories shape what a character is willing to say.')
    card(s,.65,2.85,3.85,2.58,'WHAT THEY KNOW','Their own history and local experiences. They cannot inspect another person’s memories.',body_size=18)
    card(s,4.76,2.85,3.85,2.58,'WHAT THEY SHARE','Reassurance and relevant evidence can unlock a reluctant account. A character may still refuse.','violet',18)
    card(s,8.87,2.85,3.85,2.58,'WHAT THEY SAY','A separate model call writes the spoken reply using only the released recollections.','amber',18)
    small(s,'Witnesses do not receive the answer file. Conversation alone cannot create evidence or change what happened.')

    s=slide('Read the report—and why it passed or failed.','The finished investigation')
    image(s,'ui-report.png',.65,2.0,7.25,4.5)
    card(s,8.15,2.25,4.45,3.85,'VISIBLE RESULTS','The submitted conclusions.\nLinks to acquired evidence.\nSupported and unsupported findings.\nThe score and its explanation.',body_size=18)
    small(s,'Image: an actual beginner investigation that scored 1.0. The written narrative is shown, but is not automatically fact-checked.')

    s=slide('What we built.','The software')
    for i,(title,body) in enumerate([('PYTHON','Runs the world, checks actions, stores evidence and scores reports.'),('JAVASCRIPT + SVG','Shows places, characters, dialogue, evidence and the final report.'),('DOCKER','Separates the hidden world, model access, run controller and detective’s shell.'),('MODEL APIs','Power the detective and character conversations. Provider presets and custom HTTPS endpoints. Public actions stream to the viewer.')]):
        card(s,.65+i*3.08,2.8,2.9,2.85,title,body,['mint','violet','amber','mint'][i],16)
    small(s,'Hosted on Google Cloud with Terraform, Cloudflare DNS and Caddy HTTPS. The public website needs no account.')

    s=slide('What did we train?','Learning which action to choose','We trained a small action selector. We did not change the language model’s weights.')
    for i,(title,body) in enumerate([('1  READ THE PROGRESS','Use acquired records, past actions and remaining steps.'),('2  CONSIDER CHOICES','Receive several possible searches, questions, comparisons or reports.'),('3  PICK AN ACTION','Learn which choices tend to lead to a supported conclusion.')]):
        card(s,.65+i*4.13,2.8,3.91,2.6,title,body,['mint','violet','amber'][i],18)
    text(s,.78,5.78,11.85,.52,'After repeated practice, successful action sequences become more likely. This is the reinforcement-learning part.',18,'muted')
    small(s,'The method is REINFORCE. Training used written rules to propose choices; the full-case test used language-model proposals.')

    s=slide('Three story ideas became practice problems.','The training examples','We wrote new interactive exercises inspired by these stories. We did not train on complete episode scripts.')
    for i,(title,body) in enumerate([('THE MENTALIST · S1E8','Two people died. Which one was the intended target? Check the instruction and passenger records.'),('THE MENTALIST · S1E7','Someone predicted a death. That does not prove murder. Check who wrote the warning.'),('HIS & HERS','A familiar relative can be guilty or innocent. Use a first-hand account and physical evidence, not loyalty or gossip.')]):
        card(s,.65+i*4.13,2.8,3.91,2.78,title,body,['mint','violet','amber'][i],17)
    small(s,'Both culprit assignments appear. Some evidence is already acquired when practice begins. The original full inquest is excluded from this new training.')
    note(s,'Broad story inspiration only. Sources: https://tv.apple.com/nz/episode/thin-red-line/umc.cmc.343dcf9kznkxsuz2rx6jcazs9 ; https://www.tvmaze.com/episodes/8884/the-mentalist-1x07-seeing-red ; https://www.netflix.com/tudum/articles/his-hers-episode-6-recap-ending-explained . Full details and limits: SOURCE_TRAINING_REPORT.md.')

    s=slide('Reward proof, not a confident accusation.','How scoring works')
    card(s,.65,2.8,5.78,2.86,'DURING PRACTICE','1 point: the requested conclusion has valid acquired evidence, with no false or unsupported claims.\n0 points: otherwise.',body_size=19)
    card(s,6.76,2.8,5.78,2.86,'DURING A FULL CASE','Credit for supported required findings.\n−0.20 per distinct false finding.\n−0.10 per distinct unsupported finding.\nFinal score stays between 0 and 1.','amber',18)
    small(s,'A correct guess without evidence earns no credit. A Python verifier assigns the score; a language model does not grade the investigation.')

    s=slide('Practice improved. Full cases remain difficult.','The measured results')
    text(s,.73,2.1,11.9,.7,'6,000 practice runs · 132 learned weights · 48 seconds on a CPU · no training API calls',20,'mint',True)
    for i,(label,key) in enumerate([('Before training','untrained'),('After training: sampled choices','trained_sampling'),('After training: top choice','trained_greedy')]):
        data=train['evaluations'][key];rate=data['mean_reward'];y=3.15+i*.9
        text(s,.82,y,6.0,.4,label,19,'ink')
        box(s,6.45,y+.12,4.75,.22,'edge',radius=False);box(s,6.45,y+.12,max(.03,4.75*rate),.22,'mint' if i else 'amber',radius=False)
        text(s,11.45,y,1.1,.4,str(data['successes'])+'/'+str(data['episodes']),22,'mint',True)
    text(s,.8,6.05,11.8,.4,'48 practice setups and 48 separate test setups. Each test setup was evaluated twice, using the same kinds of practice problem.',15,'muted')
    small(s,'These results measure choosing among prepared actions. They do not show that a model can solve any murder case.')

    s=slide('The harder test exposed the gap.','Full investigations excluded from training','We froze the new weights, then tested two tasks from the original Mercy House incident.')
    for i,(task,label) in enumerate([('last_witness','Establish the fatal assault'),('mercy_inquest','Explain all seven material acts')]):
        y=2.85+i*1.4;box(s,.65,y,12.0,1.15,line='edge');text(s,.91,y+.27,4.85,.55,label,20,'ink',True)
        for j,arm in enumerate(['llm_ranked','rl_selected']):
            row=next(r for r in elite['rows'] if r['task_id']==task and r['arm']==arm)
            text(s,6.25+j*3.14,y+.16,2.9,.28,'MODEL’S FIRST CHOICE' if j==0 else 'TRAINED SELECTOR',10,'muted',True)
            text(s,6.25+j*3.14,y+.52,2.9,.45,str(row['result']['score']),25,'amber',True)
    text(s,.8,5.95,11.7,.4,'Neither method completed the two tasks. Full-case improvement remains unproven.',18,'muted')
    small(s,'Same proposal rules, fixed character responses and 40 choices per run. Four runs are a small comparison, not a broad performance claim.')

    s=slide('Checked, corrected and ready to inspect.','Testing and live demonstration')
    count=tests.get('town_tests','?');node=tests.get('node_state_tests',9)
    card(s,.65,2.8,3.85,2.8,'CASE CONSISTENCY','184 task-and-seed checks passed. We fixed mixed-up roles, weak document attribution and impossible witness details.',body_size=17)
    card(s,4.76,2.8,3.85,2.8,'SOFTWARE CHECKS',f'{count} world/runtime tests.\n9 earlier regression tests.\n{node} viewer tests.\nDesktop and mobile checks.','violet',18)
    card(s,8.87,2.8,3.85,2.8,'TRY IT','Take the guided tour. Watch recorded cases, or choose a provider and bring your API key. Optional speech follows each exchange.','amber',18)
    small(s,'A hosted beginner test scored 1.0. Difficult live cases remain unproven; a witness can refuse to disclose crucial evidence.')

    s=slide('Thank you.','Questions & live demonstration','Scan to explore the source or watch an investigation unfold.')
    for x,label,name,url,detail in [(.7,'SOURCE REPOSITORY','qr-repository.png',REPO_URL,'Public source and project documentation'),(6.86,'LIVE DEMONSTRATION','qr-live-demo.png',LIVE_URL,'Open access · no sign-in')]:
        box(s,x,2.7,5.77,3.36,line='edge');text(s,x+.24,2.93,5.25,.35,label,15,'mint',True)
        image(s,name,x+.25,3.55,2.04,2.04)
        short='github.com/\nAbhishek-Punhani/\nmercy-house' if name=='qr-repository.png' else 'mercyhouse.abhi07.xyz'
        link=text(s,x+2.54,3.68,2.96,1.2,short,14,'mint',True)
        for paragraph in link.text_frame.paragraphs:
            for run in paragraph.runs:run.hyperlink.address=url
        text(s,x+2.54,5.02,2.92,.7,detail,12,'muted')
    small(s,'Aditya Ahirwar  •  Abhishek  •  Tapis Samaiya  |  Kasukabe Defence Force')
    note(s,'Public repository: '+REPO_URL+' . Public demo: '+LIVE_URL+' . QR codes contain only these URLs. Watching needs no login or key; a new public live run uses a visitor key for the configured provider.')
    for s in R.slides:
        if not s.notes_slide.notes_text_frame.text.strip():note(s,'All claims describe implemented local artifacts and recorded development measurements. See docs/PS_COMPLIANCE_AUDIT.md, SOURCE_TRAINING_REPORT.md, ELITE_TRANSFER_RESULT.json and CASE_SOLVABILITY_AUDIT.md. Do not present scripted references as LLM success or checkpoint rates as whole-case success.')
    R.save(str(DOC/'deck.pptx'))
    with tempfile.TemporaryDirectory(prefix='mercy-deck-render-') as folder:
        profile=Path(folder)/'profile';output=Path(folder)/'pdf';output.mkdir()
        with (ROOT/'logs/presentation-render.log').open('w') as log:
            subprocess.run(['libreoffice','-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf','--outdir',str(output),str(DOC/'deck.pptx')],check=True,timeout=90,stdout=log,stderr=subprocess.STDOUT)
        shutil.copyfile(output/'deck.pdf',DOC/'deck.pdf')
    info=subprocess.check_output(['pdfinfo',str(DOC/'deck.pdf')],text=True);pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1]);assert pages==SLIDE_COUNT,pages
    manifest.write_text(json.dumps({'slides':SLIDE_COUNT,'team_members':['Aditya Ahirwar','Abhishek','Tapis Samaiya'],'links':{'repository':REPO_URL,'live_demo':LIVE_URL},'theme':'dark technical; editable native shapes + actual UI screenshots','inputs_sha256':fingerprint,'screenshots':{'ui-report.png':'actual native detective Lantern Room seed211 success','ui-interview.png':'explicitly labeled original inquest scripted reference'}},indent=2)+'\n')
    import html
    (DOC/'deck.html').write_text('<!doctype html><meta charset="utf-8"><title>Mercy House presentation</title><style>body{background:#090f1b;color:#edf4ff;font:18px sans-serif;max-width:900px;margin:60px auto}a{color:#66e6cd}li{margin:20px}</style><h1>Mercy House</h1><p>Editable dark technical presentation: <a href="deck.pptx">PowerPoint</a> · <a href="deck.pdf">PDF</a></p><ol>'+''.join('<li>'+html.escape(t['title'])+'</li>' for t in texts)+'</ol>')
    print(json.dumps({'slides':pages,'pptx':str(DOC/'deck.pptx'),'pdf':str(DOC/'deck.pdf')}))

if __name__=='__main__':build()

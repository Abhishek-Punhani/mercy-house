"""Export private author review; never served or mounted into solver context."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mercy.town.factory import build
from mercy.town.tasks import TASKS


def main():
    a='# Private author review — original families\n\nContains solutions and private memories. Trusted author review only; excluded from the detective image, workspace and viewer endpoints. Examples use seed37. Not an agent prompt.\n\n'
    for task in ('lantern_room','second_passenger','bell_before_dawn'):
        w=build(task,37);a+='## '+TASKS[task]['name']+'\n\n**Incident provenance:** '+w.incident_provenance['kind']+'.\n\n**Executed sequence:**\n\n'
        for verb,actor,target in w.case['tape']:a+='- '+actor+': '+verb+' → '+target+'\n'
        a+='\n**Material targets (private):** '+json.dumps(w.material_targets())+'\n\n### Detective’s remembered life\n\n'+w.detective['life_story']+'\n\n'
        for pid,p in w.people.items():
            a+='### '+p['name']+' ('+pid+')\n\n'+p['life_portrait']+'\n\n**Appearance:** '+p['appearance']+'\n\n**Family:** '+json.dumps(p['family'],ensure_ascii=False)+'\n\n**Own memories:**\n\n'
            for m in w.states[pid]['memories']:a+='- ['+m['source']+'] '+m['text']+'\n'
            a+='\n'
        for lid,p in w.locations.items():a+='### '+p['name']+' ('+lid+')\n\n'+p['description']+'\n\nRoutes: '+', '.join(p['exits'])+'. Searchable features: '+', '.join(p['surfaces'])+'.\n\n'
        a+='### Physical material after execution\n\n'
        for obj in w.objects.values():a+='**'+obj['label']+'** ('+obj['key']+'), '+obj['location']+'/'+obj['surface']+': '+obj['text']+'\n\n'
    (ROOT/'docs/FAMILY_AUTHOR_REVIEW.md').write_text(a)
    print(json.dumps({'private_author_export':'docs/FAMILY_AUTHOR_REVIEW.md','families':3,'seed':37}))

if __name__=='__main__':main()

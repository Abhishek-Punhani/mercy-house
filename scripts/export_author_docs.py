"""Trusted author review export. Never mount these documents into the workspace."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mercy.town.factory import build
from mercy.town.prose import DETECTIVE_LIFE


def main():
    root = Path(__file__).resolve().parents[1]
    docs = root / 'docs'
    world = build('mercy_inquest', 7)
    header = 'Author-only review. This document contains private information and is excluded from the detective image and command workspace.\n\n'
    text = '# Characters — current canonical world\n\n' + header
    for pid, person in world.people.items():
        text += '## ' + person['name'] + ' (' + pid + ')\n\n'
        text += person['life_portrait'] + '\n\n'
        text += '**Visible appearance:** ' + person['appearance'] + '\n\n'
        text += f"Age {person['age']}; {person['occupation']}. Home: {person['home']}.\n\n"
        text += '**Family:** ' + '; '.join(f'{k}: {v}' for k,v in person['family'].items()) + '.\n\n'
        text += '**Personal connections:** ' + '; '.join(f'{k}: {v}' for k,v in person['relationships'].items()) + '.\n\n'
        text += '**Private motives:** ' + ' '.join(person['goals']) + '\n\n'
        text += '**Own starting memories:**\n\n' + '\n'.join('- ' + m for m in person['memories']) + '\n\n'
        recent = [m for m in world.states[pid]['memories'] if m['source'] != 'personal_history']
        if recent:
            text += '**Experienced incident memories:**\n\n' + '\n'.join('- ['+m['source']+'] '+m['text'] for m in recent) + '\n\n'
    (docs/'V2_CHARACTER_PROFILES.md').write_text(text)
    text = '# Locations — current canonical world\n\n' + header
    for pid, place in world.locations.items():
        text += '## ' + place['name'] + ' (' + pid + ')\n\n' + place['description'] + '\n\n'
        text += 'Visible routes: ' + ', '.join(place['exits']) + '. Searchable features: ' + ', '.join(place['surfaces']) + '.\n\n'
    (docs/'V2_LOCATIONS.md').write_text(text)
    text = '# Physical material — canonical seed 7\n\n' + header
    text += 'These are the objects after executing the recorded incident. An entry here is not an acquired detective record. Discovery, access, excavation and custody still apply. Hidden semantic tags below are verifier data, never observation fields.\n\n'
    for oid, obj in world.objects.items():
        text += f"## {obj['label']} ({oid})\n\n{obj['text']}\n\n"
        text += f"Author placement: {obj['location']} / {obj['surface']}; buried: {obj['buried']}; carried by: {obj['carried_by'] or 'nobody'}; incident event: {obj['event'] or 'pre-existing'}.\n\n"
    (docs/'V2_EVIDENCE_AUTHOR.md').write_text(text)
    (docs/'DETECTIVE_OPENING.md').write_text('# Detective opening — actual public reset\n\nThe following is public information, reproduced from the current factory. It contains personal life history and a local scene; it is not an answer dossier.\n\n```json\n'+json.dumps(world.opening(),indent=2,ensure_ascii=False)+'\n```\n')
    (docs/'DETECTIVE_LIFE.md').write_text('# Arun Mehra’s remembered life\n\n'+DETECTIVE_LIFE+'\n')
    print(json.dumps({'characters':len(world.people),'locations':len(world.locations),'objects':len(world.objects)}))


if __name__ == '__main__': main()

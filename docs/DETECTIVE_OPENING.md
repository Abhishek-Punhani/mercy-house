# Detective opening — actual public reset

The following is public information, reproduced from the current factory. It contains personal life history and a local scene; it is not an answer dossier.

```json
{
  "your_life": {
    "name": "Inspector Arun Mehra",
    "age": 38,
    "occupation": "district investigator",
    "recollections": "Before the district office, before the uniform, there was Mill Lane: the rasp of your father's wheel plane through the open workshop door and Tara making you wait while she tied her shoes. You left Bhairav's Hollow with a habit of looking back at the chapel turn. Twelve winters have passed since Mercy House sent the letter saying your sister had died of fever. Requests for the original papers have filled a drawer in your room at headquarters; the paper has aged more visibly than the answers have changed.\n\nLeena used to know where you kept that drawer. You lived together for three years, separated, and learned to write letters about the practical things that remained. Her mother once set tea in front of you after Tara's funeral. Raghav's signature is familiar from replies to your requests. You remember the weight of the cup and the silence around it.\n\nKabir has worked beside you for six years. You remember the floodwater in the cellar where you pulled him out, but also uneventful journeys, poor meals and the little habits by which colleagues become familiar. Dr. Mira Sen's invitation brought you back on leave: she wanted to discuss an old family record. No death had been reported when you set out. Now the coach journey is behind you, the town is under snow, and you have reached Mercy House."
  },
  "now": {
    "place": {
      "id": "archive",
      "name": "Mercy House archive",
      "description": "The lamps have been turned up too high. Above their yellow circles the archive disappears into beams and soot, and each time the wind presses against the casement the flames lean together. A desk stands under the window, its blotter crowded by ordinary papers. Beyond it are shelves, a cold fireplace and a service door whose lower edge has worn a pale arc into the boards. From the scullery comes the intermittent complaint of a kettle. The narrow opening catches a line of light from the adjoining kitchen."
    },
    "immediately_visible": "A woman lies motionless beside the archive desk.",
    "exits": [
      {
        "id": "hall",
        "name": "Mercy House entrance hall"
      },
      {
        "id": "scullery",
        "name": "Mercy House scullery"
      }
    ],
    "searchable_features": [
      "desk",
      "fireplace",
      "floor",
      "shelves"
    ],
    "minutes_since_arrival": 0
  },
  "assignment": "Reconstruct the fatal assault, assistance, documentary fabrication, grave relocation and historical record alterations. Distinguish established acts from unrelated personal history and leave unresolved matters explicit.",
  "notes": [],
  "task": {
    "task_id": "mercy_inquest",
    "name": "The Mercy House Inquest",
    "difficulty": "advanced",
    "scope": "Reconstruct the fatal assault, assistance, documentary fabrication, grave relocation and historical record alterations. Distinguish established acts from unrelated personal history and leave unresolved matters explicit.",
    "success": "Establish all material acts within this scope using acquired support and no false accusations. Partial credit reflects supported material coverage; narrative style is not scored.",
    "report_contract": "Choose your own findings: actor, predicate, object and acquired source IDs. Use the exact predicate enum in the tool schema. Acquired object IDs, observed full names and concise object labels are accepted. commissioned distinguishes an orderer from the carrier; matched describes physical objects and does not identify a killer. Hypotheses belong in narrative.",
    "limits": {
      "model_replies": 40,
      "calls_per_reply": 10,
      "wall_seconds": 600
    }
  }
}
```

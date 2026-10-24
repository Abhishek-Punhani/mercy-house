# Current crime-scene demo — actual failed run

Source: `logs/public/1792793188195685675/last_witness`; task `last_witness`, seed 19. This is the ordinary API detective, not the trained selector. Termination: **failure**; score 0.0. It must not be advertised as a solved case.

Exact first [request](current-demo/first-model-request.json), [raw response](current-demo/first-response-raw.txt), [final request](current-demo/final-model-request.json) and [summary](current-demo/summary.json). Full reply logs are in the reference archive. The request includes the detective’s remembered life, selected public task, schemas and local scene; no required answers or global character/evidence dossier.

| Reply | Actions | Errors |
|---|---|---|
| 1 | look |  |
| 2 | people_here |  |
| 3 | search | That feature is not visible here |
| 4 | search, search |  |
| 5 | collect, collect, collect, collect, collect |  |
| 6 | ask |  |
| 7 | go |  |
| 8 | people_here |  |
| 9 | ask |  |
| 10 | search |  |
| 11 | ask |  |
| 12 | search |  |
| 13 | ask |  |
| 14 | ask |  |
| 15 | search | That feature is not visible here |
| 16 | go |  |
| 17 | search |  |
| 18 | people_here |  |
| 19 | ask |  |
| 20 | go |  |
| 21 | search |  |
| 22 | search |  |
| 23 | search |  |
| 24 | compare |  |
| 25 | go |  |
| 26 | search |  |
| 27 | ask | That person is not here to answer |
| 28 | people_here |  |
| 29 | ask |  |
| 30 | go |  |
| 31 | go |  |
| 32 | people_here |  |
| 33 | search |  |
| 34 | ask |  |
| 35 | excavate | Locate disturbed ground and secure a digging tool first |
| 36 | search |  |
| 37 | collect |  |
| 38 | excavate |  |
| 39 | compare |  |
| 40 | submit_report |  |

Final submitted report, exactly as tool arguments:

```json
[
  {
    "tool": "submit_report",
    "args": {
      "findings": [],
      "narrative": "I can establish a fatal assault but cannot reliably attribute it on the evidence acquired. Anya's supervised floor search recorded Dr. Mira Sen's unresponsive body, a recent temple injury and wet blood (r1), and a heavy brass seal with dark wet staining at one edge (r2). This is consistent with the seal being a possible weapon, but the comparison produced no specific material correspondence (r23); no physical test links it to the injury. The torn wool scrap (r3) is incomplete and the attempted comparison likewise established no correspondence (r16). The threat note signed “Dev” (r6) is suggestive but does not identify its writer or establish that its author carried out the assault. Savitri Das directly reported seeing Professor Vedant Rao arrive in the archive and later leave toward the hall (r8), but could not say what occurred before the body was found or who else was present. Rao gave no recollection about entering, seeing Sen, movements, or contact with objects (r9), and his reported arrivals and departures do not establish timings or account for him around the assault (r12). Kabir arrived after the injury was reported and did not witness the assault or anyone entering or leaving (r14); Anya likewise arrived after the report (r17). The service hatch offers only a partial view (r15). Thus no acquired account establishes the assailant, and the weapon and identity remain hypotheses rather than conclusions. I do not attribute the assault to any named person."
    }
  }
]
```

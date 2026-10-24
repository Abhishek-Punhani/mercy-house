# Policy, training and reward

The judged policy is whichever detective the organizer supplies. The observation is its own biography, local scene and material acquired through tools. Hidden state includes the causal journal, undisclosed memories, provenance and permissions. Actions are movement, observation, questioning, search delegation, access, collection, comparison, excavation and reporting. An episode ends on a report, forty replies, six hundred seconds, or a recorded crash. Forced termination grades an empty report rather than inventing a solution.

## Optional policy we train

The local learner selects among candidate actions. Given public history h and actions A supplied by a proposer:

`pi_w(a | h,A) = softmax(w · phi(h,a))`.

Features describe action type, public source basis, available paths, prior questioning, repeated denials, remaining budget, secured objects and publicly disclosed family interests. Raw names, hidden propositions, journal entries and answer files are not policy features. Action arguments contain observed names and record IDs because execution needs them.

The objective is expected terminal exercise reward plus a small annealed entropy bonus. Episodic REINFORCE updates selected actions’ log probabilities using return minus a per-skill moving baseline from previous batches. Batches are on-policy and gradients are clipped. No expert action labels update weights. Entropy encourages exploration; it does not reveal truth. Evaluation freezes weights. Legal reference and no-op checks precede training.

Five checkpoint skills exercise actual Town transitions. Offline training uses explicit cooperative fixture characters and a public rules-based proposer. Those rules already form elementary questions and report propositions: this language ability is not learned by RL. A public affordance layer adds visible alternatives when an API proposer omits them. The selector cannot execute a useful action that neither source proposes.

Each skill has binary reward for its supported scoped objective. Navigation requires a limited witness account and a physical correspondence; it does not reward naming a killer from a sleeve. Delegation requires supervised custody and a supported relocation finding; this differs from the concealment task. Broader Town scores are logged separately so a successful exercise cannot be called a solved murder.

## Environment reward

Let C be the fraction of selected-task material targets supported by admissible acquired evidence, F the number of distinct false findings and U the number of distinct unsupported findings:

`R = max(0, min(1, C - 0.20 F - 0.10 U))`.

Success requires C=1, F=0 and U=0. Repeating findings or citations cannot multiply credit. Selecting a correct name without support scores zero. Explicitly unknown actors earn no credit and are distinguished from false accusations. Observed names, acquired object IDs and defined aliases are normalized. Unrecognized semantics are unsupported rather than automatically factually false.

The verifier checks selected propositions and authored proof paths. Murder needs an incident-linked physical trace and genuine direct testimony or admission. A cloth match proves a cloth match. Forgery requires a paper-edge link and independently grounded handwriting, including separate examinations. Burials require documentary linkage and physical recovery. Alteration needs relevant comparisons. Concealment needs actual handling history and admissible testimony or custody. Witness speech cannot create an object or event.

There is no bonus for many questions, unrelated objects or confident language. The scalar does not measure internal hatred, grief, ego or frustration. Observable diagnostics cover unsupported accusations, hearsay, handling omissions, preservation and denied extraction attempts. Controlled relationship interventions and repeated runs are needed before claiming resistance to personal bias.

The standard judge harness does not select our checkpoint. Local training demonstrates parameter-updating RL; it is optional and is not part of the verifier.


## Later family calibration

The eight tasks now cover four families. The same strict coverage/false/unsupported reward applies. Levels are designed investigation complexity, not calibrated model-success bands. Four native live-character beginner runs succeeded. In a separate fixed-response three-case comparison, the frozen CPU selector succeeded in 0/3 versus the LLM’s first ranked action in 1/3. No whole-case RL advantage is established; checkpoint learning results do not override this negative transfer result. See CASE_FAMILIES.md and FAMILY_POLICY_COMPARISON.json.


## New source-inspired training rewards

The latest optional training uses three original checkpoint drills: intended-target attribution, warning-document fabrication and a trusted-relative fatal-assault account. The per-episode exercise reward is1 only if the designated material proposition has admissible acquired proof and the final report has no false/unsupported claims; otherwise0. There is no automatic bonus for interviews, object collection, length, confidence, accusing relatives or alleging supernatural causes. This exercise reward is distinct from full Town coverage. Prepared legal acquisitions and authored candidate parsing are disclosed. No internal hatred, ego, grief or intelligence metric is claimed. See SOURCE_TRAINING_REPORT.md.


The final fresh-source elite comparison solved0/2 in both arms. The selector’s supported garment match earned0 full-inquest coverage because it did not establish the required material acts; three arms made no report before the cap. This is why supported findings and scoped supported coverage are distinct. The recorded negative result is ELITE_TRANSFER_REPORT.md.

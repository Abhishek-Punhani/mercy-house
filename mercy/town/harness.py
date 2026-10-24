"""Public model loop: exact instructions, bounded context and recoverable parsing."""
from copy import deepcopy
import json
import os
from pathlib import Path
import time

from .io import append_log, write_json
from .tools import schemas
from . import model
from mercy.rl.public import Notebook

SYSTEM = ('You are Inspector Arun Mehra in November 1900. Your biography is your own remembered life. '
          'Investigate through the tools, choose your own leads, and distinguish observations from hearsay. '
          'Use the task scope and reporting contract in the opening. You have at most 40 replies and ten executed tool calls per reply. '
          'A selective answer or refusal is not an alibi. Present acquired records explicitly with show, and use ordinary follow-up or reassurance when appropriate. '
          'An interview has no one- or two-question cap. Develop a relevant account: establish the person’s timeline and vantage point, '
          'ask how they know a specific claim, distinguish what they saw from what they heard, and clarify an omission or inconsistency with a focused follow-up. '
          'When new material changes a question, return to the person and show the acquired records. Do not repeat a generic question merely to increase the count; a sufficient supported account can be enough. '
          'Several records can be presented together in one ask.show list. A tool response can hand over multiple records without spending additional model replies. '
          'Batch independent tool calls whose arguments are already known; a follow-up that depends on a returned answer requires a later model reply. '
          'Finish with submit_report and cite acquired record IDs. A personal connection is not evidence of a present act.')


def interview_progress(book):
    """Only received public questions, answers and source IDs; never NPC state."""
    people={}
    for row in book.history:
        action,answer=row.get('action',{}),row.get('observation',{})
        if action.get('tool')!='ask' or answer.get('error'):continue
        args=action.get('args',{});pid=args.get('pid')
        if not pid:continue
        entry=people.setdefault(pid,{'person':pid,'questions_asked':0,'unique_questions':set(),'shown_records':set(),'firsthand_accounts':0})
        entry['questions_asked']+=1;entry['unique_questions'].add(' '.join(args.get('question','').lower().split()))
        entry['shown_records'].update(args.get('show',[]))
        memories=answer.get('recollections',[])
        entry['firsthand_accounts']+=int(any(m.get('basis') in ('direct_observation','own_action') for m in memories))
        entry['last_question']=args.get('question','')[:220]
        entry['last_answer']=answer.get('words','')[:240]
        entry['last_released_recollections']=len(memories)
    result=[]
    for entry in list(people.values())[-12:]:
        result.append({**entry,'unique_questions':len(entry['unique_questions']),'shown_records':sorted(entry['shown_records'])[:12]})
    return result


def instructions(root=None,task_scope=None):
    root = Path(root or Path(__file__).resolve().parents[2])
    path = Path(os.getenv('APPEND_FILE', 'inputs/append.txt'))
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise ValueError('APPEND_FILE is missing')
    extra = path.read_bytes().decode('utf-8')
    if not extra.strip():
        raise ValueError('APPEND_FILE is empty')
    if len(extra.encode('utf-8')) > 24000:
        raise ValueError('APPEND_FILE exceeds the conservative context budget')
    return SYSTEM + ('\nYour selected task: '+task_scope if task_scope else '') + '\n' + extra


def parse(raw, step):
    reply = raw['choices'][0]['message']
    if not isinstance(reply, dict):
        raise ValueError('message must be an object')
    calls = reply.get('tool_calls')
    if calls is None and isinstance(reply.get('function_call'), dict):
        calls = [{'function': reply['function_call']}]
    if calls is None:
        text = reply.get('content', '')
        if isinstance(text, str) and text.lstrip().startswith('{'):
            try:
                value = json.loads(text)
                actions = value.get('actions', [value] if 'tool' in value else [])
                calls = [{'function': {'name': a['tool'], 'arguments': json.dumps(a['args'])}} for a in actions]
            except (ValueError, TypeError, KeyError):
                calls = []
        else:
            calls = []
    if not isinstance(calls, list) or len(calls) > 100:
        raise ValueError('tool_calls must be an array of at most 100 entries')
    clean = []
    for index, call in enumerate(calls):
        if not isinstance(call, dict) or not isinstance(call.get('function'), dict):
            raise ValueError('Malformed tool call')
        fn = call['function']
        if not isinstance(fn.get('name'), str):
            raise ValueError('Tool name must be a string')
        args = fn.get('arguments')
        if isinstance(args, dict):
            args = json.dumps(args)
        if not isinstance(args, str):
            raise ValueError('Tool arguments must be JSON text or an object')
        clean.append({'id': 'call_' + str(step) + '_' + str(index), 'type': 'function',
                      'function': {'name': fn['name'], 'arguments': args}})
    return {'role': 'assistant', 'content': reply.get('content') if isinstance(reply.get('content'), str) else None,
            **({'tool_calls': clean} if clean else {})}, clean


def bounded_result(result, cap=8000):
    text = json.dumps(result, ensure_ascii=False)
    if len(text.encode('utf-8')) <= cap:
        return result
    preview = text.encode('utf-8')[:cap - 300].decode('utf-8', errors='ignore')
    return {'truncated': True, 'preview': preview,
            'notice': 'Output capped. Use narrower queries; retained evidence can be revisited through normal tools.'}


def fit_context(messages, tools, cap=48000):
    def size():
        return len(json.dumps({'messages': messages, 'tools': tools}, ensure_ascii=False).encode('utf-8'))
    while size() > cap and len(messages) > 3:
        end = 3
        while end < len(messages) and messages[end]['role'] == 'tool':
            end += 1
        del messages[2:end]
    if size() > cap:
        raise ValueError('Initial instructions/observation exceed the conservative context budget')


def run(world, folder, steps=40, transport=None, root=None, seconds=600):
    folder = Path(folder)
    initial = world.opening()
    system = instructions(root,initial.get('task',{}).get('scope') or initial.get('exercise',{}).get('instruction'))
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': json.dumps(initial, ensure_ascii=False)}]
    tools = schemas()
    book = Notebook(initial)
    transport = transport or model.request
    start = time.monotonic()
    deadline = start + seconds
    reason, error = 'step_cap', None
    attempted_replies=0
    seed = getattr(world, 'seed', int(os.getenv('SEED', '7')))
    write_json(folder / 'opening.json', initial)
    for step in range(1, min(40, steps) + 1):
        if time.monotonic() >= deadline:
            reason = 'time_cap'
            break
        tick = time.monotonic()
        parsed, results, errors = [], [], []
        wire = None
        raw = None
        sent = None
        model_latency = None
        try:
            if hasattr(world,'reply_count'):world.reply_count=step
            index=[{'record_id':r['record_id'],'label':r.get('label') or ('account from '+r['person'] if r.get('person') else 'comparison' if 'compared' in r else 'notebook' if 'hypotheses' in r else 'record')} for r in list(book.records.values())[-24:]]
            messages.append({'role':'user','content':'Investigation budget: reply '+str(step)+' of '+str(min(40,steps))+', approximately '+str(max(0,int(deadline-time.monotonic())))+' seconds remain. '+('This is the final reply: submit your supported findings now and put unresolved matters in narrative.' if step==min(40,steps) else 'Keep the selected task scope in view and leave time to submit your report. Batch independent calls with already-known arguments; read returned answers before choosing dependent follow-ups. Use review_records to revisit acquired material. An interview can continue when a timeline, vantage point, source or contradiction needs clarification.')+'\nSelected scope: '+initial.get('task',{}).get('scope','')+'\nYour acquired casebook index: '+json.dumps(index,ensure_ascii=False)+'\nYour public interview history: '+json.dumps(interview_progress(book),ensure_ascii=False)})
            fit_context(messages, tools)
            sent = deepcopy(messages)
            model_tick = time.monotonic()
            if hasattr(world,'model_wait'):world.model_wait(step)
            try:
                attempted_replies+=1
                raw, wire = transport(sent, tools, timeout=min(60, deadline - time.monotonic()))
            finally:
                model_latency = round((time.monotonic() - model_tick) * 1000, 3)
            try:
                reply, calls = parse(raw, step)
                if hasattr(world,'model_note'):world.model_note(reply.get('content'),step)
                messages.append(reply)
                if not calls:
                    errors.append('No tool call; step consumed')
                    messages.append({'role': 'user', 'content': 'No action was taken. Use a listed tool or submit_report.'})
                for index, call in enumerate(calls):
                    fn = call['function']
                    action = {'tool':fn['name'],'args':{}}
                    try:
                        args = json.loads(fn['arguments'])
                        action = {'tool': fn['name'], 'args': args}
                        parsed.append(action)
                        if index >= 10:
                            result = {'error': 'At most ten calls per reply; this call was not executed'}
                        elif world.ended:
                            result = {'error': 'The episode has ended; this call was not executed'}
                        elif time.monotonic() >= deadline:
                            result = {'error': 'Run deadline reached; this call was not executed'}
                        else:
                            if hasattr(world, 'action_timeout'):
                                world.action_timeout = max(.1, min(60, deadline - time.monotonic()))
                            result = world.step(fn['name'], args)
                    except (ValueError, TypeError, KeyError):
                        result = {'error': 'Malformed tool arguments; no valid action executed'}
                    except (TimeoutError, OSError):
                        result = {'error': 'Tool timed out or became unavailable; use another action'}
                    shown = bounded_result(result)
                    book.observe(action,shown)
                    results.append(shown)
                    if 'error' in shown:
                        errors.append(shown['error'])
                    messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': json.dumps(shown, ensure_ascii=False)})
            except (ValueError, TypeError, KeyError, IndexError, AttributeError):
                errors.append('Unreadable reply; step consumed and no malformed call executed')
                messages.append({'role': 'user', 'content': 'Unreadable response. Return valid tool calls with JSON arguments.'})
        except (ValueError, TypeError) as exc:
            errors.append('Unreadable model response; step consumed: ' + type(exc).__name__)
            messages.append({'role': 'user', 'content': 'The previous response could not be read. Return a valid tool call with JSON arguments.'})
        except (TimeoutError, OSError) as exc:
            errors.append('Model request unavailable: ' + type(exc).__name__ + '; step consumed')
            messages.append({'role': 'user', 'content': 'The previous model request failed; continue with a valid tool call.'})
        except Exception as exc:
            reason, error = 'crash', type(exc).__name__
            errors.append('Harness failed safely: ' + error)
        final = world.result if world.ended else None
        row = {'timestamp': time.time(), 'step': step, 'seed': seed, 'model_input': {'model':os.getenv('MODEL','gpt-6-luna'),'messages':sent,'tools':tools,'max_tokens':3500},
               'model_output_raw': wire, 'model_output_parsed': raw, 'parsed_actions': parsed,
               'tool_result': results, 'errors': errors, 'state': world.state_hash(),
               'reward': final or {'total': 0., 'pending_terminal_verification': True},
               'tokens': raw.get('usage') if isinstance(raw, dict) else None,
               'latency_ms': model_latency,
               'step_latency_ms': round((time.monotonic() - tick) * 1000, 3)}
        append_log(folder / 'episode.jsonl', row)
        print(json.dumps({'step': step, 'actions': [a['tool'] for a in parsed], 'errors': errors, 'ended': world.ended}), flush=True)
        if reason == 'crash':
            break
        if world.ended:
            reason = 'success' if final.get('success', final.get('score', 0) >= .95) else 'failure'
            break
    if not world.ended:
        if time.monotonic() >= deadline and reason != 'crash':
            reason = 'time_cap'
        if hasattr(world, 'finish'):
            world.finish(reason)
        else:
            world.step('submit_report', {'findings': [], 'narrative': 'No final report submitted before termination.'})
    result = world.result
    summary = {'task_id': initial.get('task', {}).get('task_id'), 'seed': seed,
               'termination_reason': reason, 'reason': reason, 'result': result,
               'seconds': round(time.monotonic() - start, 3), 'error': error,
               'detective_model_replies':attempted_replies,
               'interviews':interview_progress(book)}
    write_json(folder / 'summary.json', summary)
    return summary

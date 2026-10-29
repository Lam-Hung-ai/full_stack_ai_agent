# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "langgraph==1.2.16",
#   "langgraph-checkpoint==4.3.0",
#   "langgraph-checkpoint-postgres==3.2.0",
#   "langchain-core==1.6.12",
#   "psycopg==3.3.6",
#   "ag-ui-protocol==1.0.0",
#   "ag-ui-langgraph==0.0.47",
#   "fastapi==0.150.0",
# ]
# ///
"""Async graph + real AG-UI adapter/SSE codec, fake streamed LLM, disposable PG.
Run from repo root with uv run --python backend/.venv/bin/python <this file>.
No application DB, API keys, real LLM, HTTP deployment, or schema-finalization.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from typing import Annotated, TypedDict
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import TypeAdapter
from ag_ui.core import Event, Message, RunAgentInput, ResumeEntry, ActivitySnapshotEvent
from ag_ui.encoder import EventEncoder
from ag_ui_langgraph import LangGraphAgent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from prove import Cluster, connect, DECISIONS, HERE
from async_interrupt_saver import AsyncInterruptOnlySaver

GRAPH_VERSION = 'async-agui-proof-v1'
MESSAGES = TypeAdapter(list[Message])
EVENT = TypeAdapter(Event)


def canonical(bundle):
    """Validate every stored bundle with the SDK, including ActivityMessage."""
    return [m.model_dump(mode='json',by_alias=True,exclude_none=True)
            for m in MESSAGES.validate_python(bundle)]


def merge_bundle(old, incoming):
    result=deepcopy(old)
    indexes={m['id']:i for i,m in enumerate(result)}
    for m in incoming:
        if m['role'] not in ('assistant','tool','activity','reasoning'):
            # Graph-only HumanMessage answers never become SQL user rows or get
            # re-attributed as assistant text. They are displayed in activities.
            continue
        if m['id'] in indexes:
            result[indexes[m['id']]]=m
        else:
            indexes[m['id']]=len(result); result.append(m)
    return canonical(result)


def context_from_bundle(bundle):
    """Rebuild model context on a later turn without replaying a checkpoint.

    A stored user_interaction answer becomes a HUMAN message exactly once;
    metadata.actions is not appended again. Pending/cancelled activities and
    approval widgets themselves are display data, not model instructions.
    """
    result=[]
    for m in canonical(bundle):
        if m['role']=='assistant':
            calls=[{'id':c['id'],'name':c['function']['name'],
                    'args':json.loads(c['function']['arguments']),'type':'tool_call'}
                   for c in m.get('toolCalls',[])]
            result.append(AIMessage(id=m['id'],content=m.get('content',''),tool_calls=calls))
        elif m['role']=='tool':
            result.append(ToolMessage(id=m['id'],content=m['content'],tool_call_id=m['toolCallId']))
        elif m['role']=='activity' and m.get('activityType')=='user_interaction':
            a=m['content']
            if a.get('kind')=='user_question' and a.get('status')=='answered':
                result.append(HumanMessage(id='human:'+m['id'],content=a['response'],
                                           additional_kwargs={'ui_interaction':True,'actor_id':a['actor_id']}))
    return result


class WireCollector:
    """Exercise SDK SSE encoding + JSON/event decoding and minimal UI reduction."""
    def __init__(self, content):
        self.content=canonical(content)
        self.events=[]
        self.stream_ids=set()
        self.encoder=EventEncoder(accept='text/event-stream')

    def emit(self,event):
        encoded=self.encoder.encode(event)
        assert encoded.startswith('data: ') and encoded.endswith('\n\n')
        payload=json.loads(encoded.removeprefix('data: ').strip())
        obj=EVENT.validate_python(payload)
        d=obj.model_dump(mode='json',by_alias=True,exclude_none=True)
        self.events.append(d)
        t=d['type']
        if t=='MESSAGES_SNAPSHOT':
            # Never clear the transcript because the adapter emits an empty
            # initial snapshot on a fresh request. Merge using stable IDs.
            self.content=merge_bundle(self.content,d['messages'])
        elif t=='ACTIVITY_SNAPSHOT':
            self.content=merge_bundle(self.content,[{'id':d['messageId'],'role':'activity',
                'activityType':d['activityType'],'content':d['content']}])
        elif t=='TEXT_MESSAGE_START':
            mid=d['messageId']; self.stream_ids.add(mid)
            self.content=merge_bundle(self.content,[{'id':mid,'role':'assistant','content':''}])
        elif t=='TEXT_MESSAGE_CONTENT':
            mid=d['messageId']
            if not any(m['id']==mid for m in self.content):
                self.content.append({'id':mid,'role':'assistant','content':''})
            for m in self.content:
                if m['id']==mid: m['content']=m.get('content','')+d['delta']
        return d


async def aconnect(dsn):
    return await psycopg.AsyncConnection.connect(dsn,autocommit=True,row_factory=dict_row,
                                                prepare_threshold=0,options='-csearch_path=checkpoint_probe,public')


async def fetch(conn,q,args=()):
    return await (await conn.execute(q,args)).fetchone()


async def log_effect(dsn,mid,name):
    async with await aconnect(dsn) as c:
        await c.execute('INSERT INTO probe_evidence.effects(message_id,name) VALUES (%s,%s)',(mid,name))


class State(TypedDict,total=False):
    messages: Annotated[list[AnyMessage],add_messages]
    approved: bool
    seen_answers: list[str]
    forwarded_props: dict


async def permitted(conn,actor,cid):
    return (await fetch(conn,"""SELECT EXISTS (
        SELECT 1 FROM chat_app.conversations c
        JOIN chat_app.workspaces w ON w.id=c.workspace_id
        JOIN chat_app.organization_members m ON m.organization_id=w.organization_id AND m.user_id=%s AND m.is_active
        JOIN chat_app.member_role_assignments a ON a.member_id=m.id AND a.is_active
        JOIN chat_app.organization_roles r ON r.id=a.role_id AND r.is_active
        JOIN chat_app.role_permissions rp ON rp.role_id=r.id
        JOIN chat_app.permissions p ON p.id=rp.permission_id
        WHERE c.id=%s AND p.resource='tool_demo' AND p.action='execute') AS allowed""",(actor,cid)))['allowed']


def graph_for(saver,mode,dsn,mid,actor,cid):
    async def text_model(state,text,name,error=False):
        llm=FakeListChatModel(responses=[text],error_on_chunk_number=7 if error else None)
        chunks=None
        async for chunk in llm.astream(state.get('messages') or [HumanMessage(content='Begin')]):
            chunks=chunk if chunks is None else chunks+chunk
        return AIMessage(id=chunks.id,content=chunks.content,name=name)

    async def intro(state):
        await log_effect(dsn,mid,'intro_model')
        text='Bạn muốn xuất kết quả dưới dạng nào?' if mode in ('question','two_questions') else 'Tôi đã đọc yêu cầu của bạn.'
        msg=await text_model(state,text,'question_1' if mode in ('question','two_questions') else 'intro',mode=='error')
        if mode=='approval':
            msg.tool_calls=[{'name':'demo_tool','args':{'query':'example'},'id':'demo-call','type':'tool_call'}]
        return {'messages':[msg]}

    async def ask_one(state):
        q=next(m for m in state['messages'] if isinstance(m,AIMessage) and m.name=='question_1')
        answer=interrupt({'kind':'user_question','question':q.content,'question_message_id':q.id})
        return {'messages':[HumanMessage(id='answer-one',content=answer,additional_kwargs={'ui_interaction':True})]}

    async def next_question(state):
        msg=await text_model(state,'Bạn muốn đặt tên file là gì?','question_2')
        return {'messages':[msg]}

    async def ask_two(state):
        q=next(m for m in state['messages'] if isinstance(m,AIMessage) and m.name=='question_2')
        answer=interrupt({'kind':'user_question','question':q.content,'question_message_id':q.id})
        return {'messages':[HumanMessage(id='answer-two',content=answer,additional_kwargs={'ui_interaction':True})]}

    async def approve(state):
        accepted=interrupt({'kind':'tool_approval','tool_name':'demo_tool','tool_call_id':'demo-call','arguments':{'query':'example'}})
        return {'approved':accepted}

    async def tool(state):
        if state['approved']:
            async with await aconnect(dsn) as c:
                if not await permitted(c,actor,cid):
                    raise PermissionError('Tool permission revoked before execution')
            await log_effect(dsn,mid,'execute_tool')
            if mode=='slow_approval': await asyncio.sleep(.5)
        return {'messages':[ToolMessage(id='tool-result',tool_call_id='demo-call',
                                       content='Result' if state['approved'] else 'Denied by user')]}

    async def finish(state):
        answers=[m.content for m in state.get('messages',[]) if isinstance(m,HumanMessage) and m.additional_kwargs.get('ui_interaction')]
        msg=await text_model(state,'Đã nhận thông tin và hoàn thành yêu cầu.','final')
        return {'messages':[msg],'seen_answers':answers}

    b=StateGraph(State)
    b.add_node('intro',intro);b.add_node('finish',finish);b.add_edge(START,'intro');b.add_edge('finish',END)
    if mode in ('question','two_questions'):
        b.add_node('ask_one',ask_one);b.add_edge('intro','ask_one')
        if mode=='two_questions':
            b.add_node('question_two',next_question);b.add_node('ask_two',ask_two)
            b.add_edge('ask_one','question_two');b.add_edge('question_two','ask_two');b.add_edge('ask_two','finish')
        else:b.add_edge('ask_one','finish')
    elif mode in ('approval','slow_approval'):
        b.add_node('approve',approve);b.add_node('tool',tool)
        b.add_edge('intro','approve');b.add_edge('approve','tool');b.add_edge('tool','finish')
    else:b.add_edge('intro','finish')
    return b.compile(checkpointer=saver)


class ExitAgent(LangGraphAgent):
    def get_stream_kwargs(self,**kwargs):
        return {**super().get_stream_kwargs(**kwargs),'durability':'exit'}


async def lock_message(conn,mid,actor):
    row=await fetch(conn,'SELECT conversation_id FROM chat_app.messages WHERE id=%s',(mid,))
    if not row:raise ValueError('Unknown message')
    cid=row['conversation_id']
    await conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,42))',(str(cid),))
    if not (await fetch(conn,'SELECT chat_app.can_read_conversation(%s,%s) AS allowed',(actor,cid)))['allowed']:
        raise PermissionError('Conversation access denied')
    return await fetch(conn,'SELECT * FROM chat_app.messages WHERE id=%s FOR UPDATE',(mid,))


def activity(pending,status,response=None,actor=None):
    i=pending['interrupts'][0]
    content={'action_id':pending['action_id'],'kind':i['payload']['kind'],'status':status,
             'question_message_id':i['payload'].get('question_message_id')}
    if i['payload']['kind']=='tool_approval':
        content.update(tool_name=i['payload']['tool_name'],arguments=i['payload']['arguments'])
    if response is not None:content.update(response=response,actor_id=actor)
    return ActivitySnapshotEvent(message_id='interaction:'+pending['action_id'],
                                 activity_type='user_interaction',content=content,replace=True)


async def worker(req):
    dsn,mid,actor,mode=req['dsn'],req['message_id'],req['actor_id'],req['mode']
    async with await aconnect(dsn) as conn:
        async with conn.transaction():
            row=await lock_message(conn,mid,actor)
            md=deepcopy(row['metadata']); pending=md.get('pending_action'); content=canonical(row['content'])
            wire=WireCollector(content)
            if req['op'] in ('resume','cancel'):
                if row['status']!='requires_action' or not pending or pending['action_id']!=req['action_id']:
                    raise ValueError('Stale or already claimed action')
                if pending['graph_version']!=GRAPH_VERSION:raise ValueError('Graph version changed')
                if pending['checkpoint']['thread_id']!=mid:raise ValueError('Wrong checkpoint scope')
                if pending['expires_at'] is not None:raise ValueError('Proof expects non-expiring action')
                if req['op']=='cancel':
                    wire.emit(activity(pending,'cancelled'))
                    md.pop('pending_action');md.setdefault('actions',[]).append({'action_id':pending['action_id'],'status':'cancelled'})
                    await conn.execute("UPDATE chat_app.messages SET status='cancelled',content=%s,metadata=%s WHERE id=%s",
                                       (Jsonb(wire.content),Jsonb(md),mid))
                    return {'status':'cancelled','content':wire.content,'events':wire.events}
                payload=pending['interrupts'][0]['payload']; response=req['response']
                # Validate BEFORE claiming so bad input does not strand the message.
                if payload['kind']=='tool_approval':
                    if not isinstance(response,bool):raise ValueError('Approval must be boolean')
                    if response and not await permitted(conn,actor,row['conversation_id']):
                        raise PermissionError('Tool permission revoked')
                elif not isinstance(response,str) or not response.strip():
                    raise ValueError('Question response must be nonempty text')
                wire.emit(activity(pending,'answered',response,actor))
                entry={'action_id':pending['action_id'],'kind':payload['kind'],'response':response,
                       'status':'answered','actor_id':actor}
                md.setdefault('actions',[]).append(entry)
                md['pending_action']={**pending,'state':'resuming','response':response}
                resumes=[ResumeEntry(interrupt_id=i['interrupt_id'],status='resolved',payload=response)
                         for i in pending['interrupts']]
                config={'configurable':pending['checkpoint']}
            else:
                if row['status']!='pending':raise ValueError('Already started')
                resumes=None;config={'configurable':{'thread_id':mid,'checkpoint_ns':''}}
            await conn.execute("UPDATE chat_app.messages SET status='running',metadata=%s,content=%s WHERE id=%s",
                               (Jsonb(md),Jsonb(wire.content),mid))
            cid=row['conversation_id']
        saver=AsyncInterruptOnlySaver(AsyncPostgresSaver(conn))
        graph=graph_for(saver,mode,dsn,mid,actor,cid)
        agent=ExitAgent(name='proof',graph=graph,config=config,emit_raw_events=False,
                        enable_legacy_on_interrupt_event=False,emit_interrupt_outcome=True)
        input_=RunAgentInput(thread_id=mid,run_id=str(uuid4()),state={},messages=[],tools=[],context=[],resume=resumes,
                            forwarded_props={'stream_subgraphs':False})
        terminal=None;run_error=None
        try:
            async for event in agent.run(input_):
                typ=event.type.value if hasattr(event.type,'value') else event.type
                if typ in ('RUN_FINISHED','RUN_ERROR'):
                    terminal=event
                    if typ=='RUN_ERROR':run_error=event.message
                    continue  # Don't announce pause/end until durable commit.
                if typ=='MESSAGES_SNAPSHOT':
                    incoming=[m.model_dump(mode='json',by_alias=True,exclude_none=True) for m in event.messages]
                    incoming=merge_bundle(wire.content,incoming)
                    event=event.model_copy(update={'messages':MESSAGES.validate_python(incoming)})
                wire.emit(event)
        except Exception as exc:
            run_error=str(exc)
        snapshot=await graph.aget_state({'configurable':{'thread_id':mid,'checkpoint_ns':''}})
        interrupts=[i for t in snapshot.tasks for i in t.interrupts] if not run_error else []
        async with conn.transaction():
            current=await lock_message(conn,mid,actor)
            if current['status']!='running':raise ValueError('Message not owned by current execution')
            md={k:v for k,v in current['metadata'].items() if k!='pending_action'}
            if interrupts:
                saved=await saver.apersist_pause({'configurable':{'thread_id':mid,'checkpoint_ns':''}})
                pending={'action_id':str(uuid4()),'state':'waiting','graph_version':GRAPH_VERSION,
                         'expires_at':None,'checkpoint':saved['configurable'],
                         'interrupts':[{'interrupt_id':i.id,'payload':i.value} for i in interrupts]}
                md['pending_action']=pending
                wire.emit(activity(pending,'waiting'))
                status='requires_action'
            else:status='failed' if run_error else 'completed'
            await conn.execute('UPDATE chat_app.messages SET status=%s,content=%s,metadata=%s WHERE id=%s',
                               (status,Jsonb(canonical(wire.content)),Jsonb(md),mid))
        if terminal:wire.emit(terminal)
        return {'status':status,'pending_action':md.get('pending_action'),'content':wire.content,
                'events':wire.events,'seen_answers':snapshot.values.get('seen_answers'),
                'error':run_error}


def main(report_path):
    results=[];sample={}
    def check(ok,label,**evidence):
        if not ok:raise AssertionError((label,evidence))
        results.append({'check':label,**evidence});print('PASS:',label,flush=True)
    with Cluster() as cluster:
        for name in ['phase-1-schema.sql','phase-2-part-1-schema.sql','phase-2-final-schema.sql']:
            subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','--dbname',cluster.dsn,'-f',str(DECISIONS/name)],check=True,capture_output=True)
        subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','--dbname',cluster.dsn,'-f',str(HERE/'proof_schema.sql')],check=True,capture_output=True)
        with connect(cluster.dsn) as c:
            PostgresSaver(c).setup()
            actor=str(c.execute("INSERT INTO chat_app.users(name,email) VALUES ('Async','async@example.test') RETURNING id").fetchone()['id'])
            org=c.execute("INSERT INTO chat_app.organizations(name,created_by) VALUES ('Async org',%s) RETURNING id",(actor,)).fetchone()['id']
            wid=c.execute('SELECT id FROM chat_app.workspaces WHERE organization_id=%s',(org,)).fetchone()['id']
            role=c.execute("SELECT id FROM chat_app.organization_roles WHERE organization_id=%s AND role_key='owner'",(org,)).fetchone()['id']
            permission=c.execute("INSERT INTO chat_app.permissions(resource,action) VALUES ('tool_demo','execute') RETURNING id").fetchone()['id']
            c.execute('INSERT INTO chat_app.role_permissions(role_id,permission_id) VALUES (%s,%s)',(role,permission))
        def new():
            with connect(cluster.dsn) as c:
                cid=c.execute('INSERT INTO chat_app.conversations(workspace_id,owner_user_id) VALUES (%s,%s) RETURNING id',(wid,actor)).fetchone()['id']
                return str(c.execute("INSERT INTO chat_app.messages(conversation_id,role) VALUES (%s,'assistant') RETURNING id",(cid,)).fetchone()['id'])
        def request(mid,mode,op='start',**extra):
            return {'dsn':cluster.dsn,'message_id':mid,'actor_id':actor,'mode':mode,'op':op,**extra}
        def spawn(req):
            p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            p.stdin.write(json.dumps(req));p.stdin.close();p.stdin=None
            return p
        def finish(p):
            out,err=p.communicate(timeout=90)
            if p.returncode:raise RuntimeError(err)
            return json.loads(out)
        def call(mid,mode,op='start',**extra):return finish(spawn(request(mid,mode,op,**extra)))
        def resume(mid,mode,p,value):return call(mid,mode,'resume',action_id=p['action_id'],response=value)
        def row(mid):
            with connect(cluster.dsn) as c:return c.execute('SELECT * FROM chat_app.messages WHERE id=%s',(mid,)).fetchone()
        def counts(mid):
            with connect(cluster.dsn) as c:return {t:c.execute(f'SELECT count(*) AS n FROM {t} WHERE thread_id=%s',(mid,)).fetchone()['n'] for t in ('checkpoints','checkpoint_writes','checkpoint_blobs')}
        def effects(mid,name):
            with connect(cluster.dsn) as c:return c.execute('SELECT count(*) AS n FROM probe_evidence.effects WHERE message_id=%s AND name=%s',(mid,name)).fetchone()['n']
        def bad(fn,needle,label):
            try:fn()
            except RuntimeError as e:check(needle in str(e),label);return
            raise AssertionError('invalid operation accepted: '+label)

        mid=new();o=call(mid,'plain')
        check(o['status']=='completed' and not any(counts(mid).values()),'async AG-UI normal completion writes no durable checkpoints')
        check(sum(e['type']=='TEXT_MESSAGE_CONTENT' for e in o['events'])>5,'real AG-UI adapter streams fake LLM text as SDK-valid SSE events')
        check(canonical(row(mid)['content'])==o['content'],'SDK-validated stored bundle matches reduced SSE content')
        mid=new();o=call(mid,'error')
        check(o['status']=='failed' and not any(counts(mid).values()),'async stream error without action writes no checkpoint')
        check(any(m.get('content') for m in row(mid)['content'] if m['role']=='assistant'),'LLM chunk error keeps partial text collected from SSE')

        mid=new();o=call(mid,'question');p=o['pending_action'];before=counts(mid)
        sample['question_pause']={'status':o['status'],'content':o['content'],'metadata':row(mid)['metadata']}
        check(o['status']=='requires_action' and before['checkpoints']==1,'async question persists only interrupt boundary')
        check(any('Bạn muốn xuất' in m.get('content','') for m in row(mid)['content'] if m['role']=='assistant'),
              'LLM-generated question is saved in message content at pause')
        check(any(m['role']=='activity' and m['content']['status']=='waiting' for m in o['content']),
              'pending question widget is a valid AG-UI ActivityMessage')
        bad(lambda:resume(mid,'question',p,''),'nonempty text','empty answer rejected before claim and message remains waiting')
        check(row(mid)['status']=='requires_action','invalid input does not strand message in running')
        cluster.restart()
        check(row(mid)['content']==o['content'] and counts(mid)==before,'reload after PostgreSQL restart preserves question and pending widget')
        out=resume(mid,'question',p,'CSV')
        sample['question_completed']={'status':out['status'],'content':out['content'],'metadata':row(mid)['metadata']}
        acts=[m for m in out['content'] if m['role']=='activity']
        check(out['status']=='completed' and out['seen_answers']==['CSV'],'fresh async graph resumes with user answer as HumanMessage context')
        check(len(acts)==1 and acts[0]['content']['response']=='CSV' and acts[0]['content']['status']=='answered',
              'answer stored in same assistant bundle with explicit user attribution, no duplicate widget')
        check(all(m['role']!='user' for m in out['content']) and row(mid)['metadata']['actions'][0]['response']=='CSV',
              'no SQL user message needed; metadata preserves answer and content uses activity role')
        check(len({m['id'] for m in out['content']})==len(out['content']) and effects(mid,'intro_model')==1,
              'stream resume does not duplicate question text or rerun question model')
        check(counts(mid)==before,'async successful resume does not persist terminal checkpoint')
        ctx=context_from_bundle(row(mid)['content'])
        check([m.type for m in ctx]==['ai','human','ai'] and ctx[1].content=='CSV',
              'later-turn context rebuild keeps question, human answer and continuation in order')
        replay=context_from_bundle(json.loads(json.dumps(row(mid)['content'])))
        check([m.model_dump() for m in ctx]==[m.model_dump() for m in replay],
              'JSON reload rebuilds identical context without checkpoint or metadata duplication')
        bad(lambda:resume(mid,'question',p,'CSV'),'Stale','old question answer cannot resume twice')

        mid=new();p1=call(mid,'two_questions')['pending_action'];p2=resume(mid,'two_questions',p1,'Excel')['pending_action'];o=resume(mid,'two_questions',p2,'report')
        check(o['seen_answers']==['Excel','report'] and len([m for m in o['content'] if m['role']=='activity'])==2,
              'two async question rounds preserve both answers in same assistant content')
        check(len(row(mid)['metadata']['actions'])==2,'metadata retains both resolved question responses')
        check([m.content for m in context_from_bundle(row(mid)['content']) if isinstance(m,HumanMessage)]==['Excel','report'],
              'later-turn context includes both user answers exactly once from persisted activities')

        mid=new();p=call(mid,'approval')['pending_action'];o=resume(mid,'approval',p,False)
        check(o['status']=='completed' and effects(mid,'execute_tool')==0,'AG-UI denial resumes without executing tool')
        mid=new();p=call(mid,'approval')['pending_action'];o=resume(mid,'approval',p,True)
        check(o['status']=='completed' and effects(mid,'execute_tool')==1,'AG-UI approval executes authorized tool once')

        mid=new();p=call(mid,'approval')['pending_action']
        with connect(cluster.dsn) as c:c.execute('DELETE FROM chat_app.role_permissions WHERE role_id=%s AND permission_id=%s',(role,permission))
        bad(lambda:resume(mid,'approval',p,True),'permission revoked','role permission revoked while waiting prevents tool approval')
        check(row(mid)['status']=='requires_action' and effects(mid,'execute_tool')==0,'revoked permission leaves pending action intact and tool unexecuted')
        with connect(cluster.dsn) as c:c.execute('INSERT INTO chat_app.role_permissions(role_id,permission_id) VALUES (%s,%s)',(role,permission))
        o=call(mid,'approval','cancel',action_id=p['action_id'])
        check(o['status']=='cancelled' and bool(o['content']) and 'pending_action' not in row(mid)['metadata'],
              'cancel waiting action preserves content and clears resumable pointer')
        bad(lambda:resume(mid,'approval',p,True),'Stale','cancelled action cannot resume')

        mid=new();p=call(mid,'question')['pending_action'];cid=row(mid)['conversation_id']
        with connect(cluster.dsn) as c:
            try:c.execute("INSERT INTO chat_app.messages(conversation_id,role) VALUES (%s,'assistant')",(cid,))
            except psycopg.errors.UniqueViolation:check(True,'waiting question blocks a new assistant turn')
            else:raise AssertionError('second active turn allowed')
        # Two actual Python processes submit the same answer concurrently.
        req=request(mid,'question','resume',action_id=p['action_id'],response='JSON')
        proc1,proc2=spawn(req),spawn(req)
        outcomes=[]
        for proc in (proc1,proc2):
            try:outcomes.append(('ok',finish(proc)))
            except RuntimeError as e:outcomes.append(('error',str(e)))
        check(sum(s=='ok' for s,_ in outcomes)==1 and row(mid)['status']=='completed',
              'concurrent duplicate answers allow exactly one resume')
        report={'generated_at':datetime.now(timezone.utc).isoformat(),'result':'passed','checks':len(results),
                'python':sys.version,'versions':{n:importlib.metadata.version(n) for n in ['langgraph','langgraph-checkpoint',
                'langgraph-checkpoint-postgres','langchain-core','psycopg','ag-ui-protocol','ag-ui-langgraph']},
                'scope':'Async LangGraph, AsyncPostgresSaver, real AG-UI adapter and SSE codec; fake streamed LLM; new process per invocation',
                'limitations':['No real paid LLM/MCP/HTTP deployment','No subgraph/DeltaChannel conformance','No auto crash recovery or graph migrations'],
                'results':results,'samples':sample}
        Path(report_path).write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str)+'\n')
        print(json.dumps({'result':'passed','checks':len(results),'report':str(report_path)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--report',type=Path,default=HERE/'async-results.json');a=p.parse_args()
    if a.worker:print(json.dumps(asyncio.run(worker(json.load(sys.stdin))),ensure_ascii=False))
    else:main(a.report)

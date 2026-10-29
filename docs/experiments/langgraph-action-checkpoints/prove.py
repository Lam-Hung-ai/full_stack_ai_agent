# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "langgraph==1.2.16",
#   "langgraph-checkpoint==4.3.0",
#   "langgraph-checkpoint-postgres==3.2.0",
#   "langchain-core==1.6.12",
#   "psycopg==3.3.6",
# ]
# ///
"""Run `uv run prove.py --report results.json`; uses a disposable local PostgreSQL.
No .env, model APIs, production DB, Redis, Docker or external tool services.
Each start/resume is a NEW Python subprocess and a freshly compiled graph.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import operator
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Annotated, TypedDict
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from interrupt_saver import InterruptOnlySaver

HERE = Path(__file__).resolve().parent
DECISIONS = HERE.parents[1] / 'database_decisions'
GRAPH_VERSION = 'checkpoint-proof-v1'


def connect(dsn):
    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                           prepare_threshold=0, options='-csearch_path=checkpoint_probe,public')


def effect(dsn, message_id, name):
    with connect(dsn) as conn:
        conn.execute('INSERT INTO probe_evidence.effects(message_id,name) VALUES (%s,%s)', (message_id,name))


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    approved: bool
    answers: list[str]
    notes: Annotated[list[str], operator.add]


def build_graph(saver, mode, dsn, mid):
    def prepare(state):
        effect(dsn,mid,'prepare')
        calls = [] if mode in ('plain','error','two_questions') else [
            {'name':'demo_tool','args':{'query':'example'},'id':'call-demo','type':'tool_call'}]
        return {'messages':[AIMessage(id='intro',content='Partial answer before waiting.',tool_calls=calls)]}

    def gate(state):
        approved = interrupt({'kind':'tool_approval','tool_call_id':'call-demo',
                              'tool_name':'demo_tool','arguments':{'query':'example'}})
        if not isinstance(approved,bool):
            raise ValueError('Approval must be boolean')
        return {'approved':approved}

    def execute(state):
        if state['approved']:
            effect(dsn,mid,'execute_tool')
        return {'messages':[ToolMessage(id='tool-result',tool_call_id='call-demo',
                                       content='Tool result.' if state['approved'] else 'User denied tool.')]}

    def questions(state):
        # Intentionally instrument code BEFORE interrupt: it repeats on resume.
        # Real irreversible side effects must not be placed here.
        effect(dsn,mid,'question_node_entry')
        first=interrupt({'kind':'user_question','question':'First value?'})
        second=interrupt({'kind':'user_question','question':'Second value?'})
        return {'answers':[first,second]}

    def one_question(state):
        answer=interrupt({'kind':'user_question','question':'Which output format?'})
        return {'answers':[answer]}

    def sibling(state):
        effect(dsn,mid,'parallel_sibling')
        return {'notes':['sibling-completed']}

    def fail(state):
        raise RuntimeError('Simulated model failure without any action')

    def finish(state):
        text='Finished.'
        if 'approved' in state:
            text += ' Approved.' if state['approved'] else ' Denied.'
        if 'answers' in state:
            text += ' Answers: '+', '.join(state['answers'])
        return {'messages':[AIMessage(id='final',content=text)]}

    b=StateGraph(State)
    b.add_node('prepare',prepare); b.add_node('finish',finish)
    b.add_edge(START,'prepare'); b.add_edge('finish',END)
    if mode=='plain':
        b.add_edge('prepare','finish')
    elif mode=='error':
        b.add_node('fail',fail); b.add_edge('prepare','fail'); b.add_edge('fail','finish')
    elif mode=='two_questions':
        b.add_node('questions',questions); b.add_edge('prepare','questions'); b.add_edge('questions','finish')
    else:
        b.add_node('gate',gate); b.add_node('execute',execute)
        b.add_edge('prepare','gate')
        if mode=='parallel':
            b.add_node('sibling',sibling); b.add_edge('prepare','sibling'); b.add_edge(['gate','sibling'],'execute')
        else:
            b.add_edge('gate','execute')
        if mode=='approval_then_question':
            b.add_node('question',one_question); b.add_edge('execute','question'); b.add_edge('question','finish')
        else:
            b.add_edge('execute','finish')
    return b.compile(checkpointer=saver)


def agui_bundle(messages):
    result=[]
    for m in messages:
        if isinstance(m,AIMessage):
            item={'id':m.id,'role':'assistant','content':m.content}
            if m.tool_calls:
                item['toolCalls']=[{'id':c['id'],'type':'function','function':{
                    'name':c['name'],'arguments':json.dumps(c['args'])}} for c in m.tool_calls]
        elif isinstance(m,ToolMessage):
            item={'id':m.id,'role':'tool','toolCallId':m.tool_call_id,'content':m.content}
        else:
            continue
        result.append(item)
    return result


def lock_message(conn,mid,actor):
    row=conn.execute('SELECT conversation_id FROM chat_app.messages WHERE id=%s',(mid,)).fetchone()
    if not row:
        raise ValueError('Message not found')
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,42))',(str(row['conversation_id']),))
    if not conn.execute('SELECT chat_app.can_read_conversation(%s,%s) AS allowed',
                        (actor,row['conversation_id'])).fetchone()['allowed']:
        raise ValueError('Actor cannot access conversation')
    return conn.execute('SELECT * FROM chat_app.messages WHERE id=%s FOR UPDATE',(mid,)).fetchone()


def work(req):
    dsn,mid,actor,mode=req['dsn'],req['message_id'],req['actor_id'],req['mode']
    with connect(dsn) as conn:
        saver=InterruptOnlySaver(PostgresSaver(conn))
        graph=build_graph(saver,mode,dsn,mid)
        config={'configurable':{'thread_id':mid,'checkpoint_ns':''}}
        prior_action=None
        with conn.transaction():
            row=lock_message(conn,mid,actor)
            metadata=row['metadata']
            if req['op']=='resume':
                pending=metadata.get('pending_action',{})
                if row['status']!='requires_action' or pending.get('action_id')!=req['action_id']:
                    raise ValueError('Stale action or message is not waiting')
                if pending['graph_version']!=GRAPH_VERSION:
                    raise ValueError('Wrong graph version')
                if pending.get('expires_at') is not None:
                    raise ValueError('This proof supports non-expiring actions only')
                if pending['checkpoint']['thread_id']!=mid:
                    raise ValueError('Checkpoint does not belong to this message')
                config={'configurable':pending['checkpoint']}
                prior_action={**pending,'response':req['response']}
                metadata={**metadata,'pending_action':{**prior_action,'state':'resuming'}}
                graph_input=Command(resume={p['interrupt_id']:req['response'] for p in pending['interrupts']})
            else:
                if row['status']!='pending':
                    raise ValueError('Message already started')
                graph_input={'messages':[],'notes':[]}
            conn.execute("UPDATE chat_app.messages SET status='running',metadata=%s WHERE id=%s",
                         (Jsonb(metadata),mid))
        # No application transaction/row lock is held while the graph runs.
        try:
            output=graph.invoke(graph_input,config,durability='exit')
        except Exception as exc:
            latest=saver.get_tuple({'configurable':{'thread_id':mid,'checkpoint_ns':''}})
            bundle=agui_bundle((latest.checkpoint['channel_values'] if latest else {}).get('messages',[]))
            with conn.transaction():
                current=lock_message(conn,mid,actor)
                md={k:v for k,v in current['metadata'].items() if k!='pending_action'}
                conn.execute("UPDATE chat_app.messages SET status='failed',content=%s,metadata=%s WHERE id=%s",
                             (Jsonb(bundle),Jsonb(md),mid))
            return {'status':'failed','error':str(exc)}
        interrupts=output.get('__interrupt__',[])
        with conn.transaction():
            current=lock_message(conn,mid,actor)
            md={k:v for k,v in current['metadata'].items() if k!='pending_action'}
            if prior_action:
                md['last_action']={**prior_action,'state':'resolved'}
            if interrupts:
                saved=saver.persist_pause({'configurable':{'thread_id':mid,'checkpoint_ns':''}})
                if req.get('fail_pause_commit'):
                    raise RuntimeError('Injected failure after checkpoint write, before message update')
                pending={'action_id':str(uuid4()),'state':'waiting','graph_version':GRAPH_VERSION,
                         'created_at':datetime.now(timezone.utc).isoformat(),'expires_at':None,
                         'checkpoint':saved['configurable'],
                         'interrupts':[{'interrupt_id':i.id,'payload':i.value} for i in interrupts]}
                md['pending_action']=pending
                state='requires_action'
            else:
                state='completed'
            conn.execute('UPDATE chat_app.messages SET status=%s,content=%s,metadata=%s WHERE id=%s',
                         (state,Jsonb(agui_bundle(output.get('messages',[]))),Jsonb(md),mid))
        return {'status':state,'pending_action':md.get('pending_action'),
                'answers':output.get('answers'), 'notes':output.get('notes'),
                'content':agui_bundle(output.get('messages',[]))}


class Cluster:
    def __enter__(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='agent-checkpoint-proof-')
        self.root=Path(self.tmp.name); self.data=self.root/'data'
        subprocess.run(['initdb','-D',str(self.data),'-A','trust','--no-locale','-E','UTF8'],check=True,capture_output=True)
        self.started=False
        try:
            self.start()
        except Exception:
            self.tmp.cleanup(); raise
        self.dsn=f'host={self.root} port=55443 dbname=postgres'
        return self

    def start(self):
        subprocess.run(['pg_ctl','-D',str(self.data),'-l',str(self.root/'postgres.log'),
                        '-o',f"-k {self.root} -p 55443 -c listen_addresses=''",'-w','start'],
                       check=True,capture_output=True)
        self.started=True

    def stop(self):
        if self.started:
            subprocess.run(['pg_ctl','-D',str(self.data),'-m','fast','-w','stop'],check=True,capture_output=True)
            self.started=False

    def restart(self):
        self.stop(); self.start()

    def __exit__(self,*exc):
        self.stop(); self.tmp.cleanup()


def main(report_path=None):
    results=[]
    def check(condition,label,**evidence):
        if not condition:
            raise AssertionError(label+': '+repr(evidence))
        results.append({'check':label,**evidence}); print('PASS:',label,flush=True)
    with Cluster() as cluster:
        for name in ['phase-1-schema.sql','phase-2-part-1-schema.sql','phase-2-final-schema.sql']:
            subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','--dbname',cluster.dsn,'-f',str(DECISIONS/name)],
                           check=True,capture_output=True)
        subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','--dbname',cluster.dsn,'-f',str(HERE/'proof_schema.sql')],
                       check=True,capture_output=True)
        with connect(cluster.dsn) as conn:
            PostgresSaver(conn).setup()
            actor=str(conn.execute("INSERT INTO chat_app.users(name,email) VALUES ('Proof','proof@example.test') RETURNING id").fetchone()['id'])
            outsider=str(conn.execute("INSERT INTO chat_app.users(name,email) VALUES ('Outside','outside@example.test') RETURNING id").fetchone()['id'])
            workspace=str(conn.execute('SELECT id FROM chat_app.workspaces WHERE personal_user_id=%s',(actor,)).fetchone()['id'])
        def new_message():
            with connect(cluster.dsn) as conn:
                c=conn.execute('INSERT INTO chat_app.conversations(workspace_id,owner_user_id) VALUES (%s,%s) RETURNING id',(workspace,actor)).fetchone()['id']
                m=conn.execute("INSERT INTO chat_app.messages(conversation_id,role) VALUES (%s,'assistant') RETURNING id",(c,)).fetchone()['id']
                return str(m)
        def worker(mid,mode,op='start',**extra):
            req={'dsn':cluster.dsn,'actor_id':actor,'message_id':mid,'mode':mode,'op':op,**extra}
            proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],input=json.dumps(req),text=True,capture_output=True)
            if proc.returncode:
                raise RuntimeError(proc.stderr)
            return json.loads(proc.stdout)
        def resume(mid,mode,pending,response,**extra):
            return worker(mid,mode,'resume',action_id=pending['action_id'],response=response,**extra)
        def counts(mid):
            with connect(cluster.dsn) as conn:
                return {table:conn.execute(f'SELECT count(*) AS n FROM {table} WHERE thread_id=%s',(mid,)).fetchone()['n']
                        for table in ('checkpoints','checkpoint_writes','checkpoint_blobs')}
        def event_count(mid,event):
            with connect(cluster.dsn) as conn:
                return conn.execute('SELECT count(*) AS n FROM probe_evidence.effects WHERE message_id=%s AND name=%s',(mid,event)).fetchone()['n']
        def message(mid):
            with connect(cluster.dsn) as conn:
                return conn.execute('SELECT * FROM chat_app.messages WHERE id=%s',(mid,)).fetchone()

        mid=new_message(); out=worker(mid,'plain')
        check(out['status']=='completed' and not any(counts(mid).values()),'normal completion writes zero durable checkpoint/blob/write rows',counts=counts(mid))
        mid=new_message(); out=worker(mid,'error')
        check(out['status']=='failed' and not any(counts(mid).values()),'error without action writes zero durable checkpoint rows',counts=counts(mid))
        check(bool(message(mid)['content']),'caught error preserves partial message content')

        mid=new_message(); paused=worker(mid,'approval'); pending=paused['pending_action']; before=counts(mid)
        check(paused['status']=='requires_action' and before['checkpoints']==1 and before['checkpoint_writes']>0,
              'approval persists boundary checkpoint and pending writes',counts=before)
        check(event_count(mid,'execute_tool')==0,'tool does not execute before approval')
        check(message(mid)['metadata']['pending_action']==pending and bool(message(mid)['content']),
              'message metadata alone stores action and checkpoint pointer with partial content')
        check(pending['expires_at'] is None,'waiting action has no automatic expiry')
        with connect(cluster.dsn) as conn:
            conn.execute("UPDATE chat_app.messages SET metadata=jsonb_set(metadata,'{pending_action,created_at}',%s::jsonb) WHERE id=%s",
                         (json.dumps('2000-01-01T00:00:00+00:00'),mid))
        cluster.restart()
        check(counts(mid)==before and message(mid)['status']=='requires_action','PostgreSQL restart preserves paused message and checkpoint')
        try:
            resume(mid,'approval',pending,True,actor_id=outsider)
            raise AssertionError('outsider unexpectedly resumed')
        except RuntimeError as exc:
            check('Actor cannot access' in str(exc),'outsider cannot resume another user checkpoint')
        resumed=resume(mid,'approval',pending,True)
        check(resumed['status']=='completed' and event_count(mid,'execute_tool')==1,
              'fresh process resumes old non-expiring approval and executes tool once')
        check(event_count(mid,'prepare')==1,'resume does not rerun completed prepare node')
        check(counts(mid)==before,'successful resume adds no terminal checkpoint',counts=counts(mid))
        check('pending_action' not in message(mid)['metadata'],'completion clears pending action and retains last decision')
        try:
            resume(mid,'approval',pending,True)
            raise AssertionError('duplicate unexpectedly resumed')
        except RuntimeError as exc:
            check('Stale action' in str(exc) and event_count(mid,'execute_tool')==1,'duplicate old approval cannot execute tool twice')
        mid=new_message(); paused=worker(mid,'approval'); resumed=resume(mid,'approval',paused['pending_action'],False)
        check(resumed['status']=='completed' and event_count(mid,'execute_tool')==0,
              'denial resumes graph without executing tool or cancelling whole answer')

        mid=new_message(); p1=worker(mid,'two_questions')['pending_action']
        p2=resume(mid,'two_questions',p1,'alpha')['pending_action']
        check(p1['action_id']!=p2['action_id'] and counts(mid)['checkpoints']==1,
              'second interrupt in same node creates new action and updates existing checkpoint writes')
        try:
            resume(mid,'two_questions',p1,'stale')
            raise AssertionError('stale first question unexpectedly resumed')
        except RuntimeError as exc:
            check('Stale action' in str(exc),'previous question id cannot answer current question')
        out=resume(mid,'two_questions',p2,'beta')
        check(out['status']=='completed' and out['answers']==['alpha','beta'],
              'two interrupts inside one node preserve earlier response across fresh processes',answers=out['answers'])
        check(event_count(mid,'question_node_entry')==3,'node code before interrupt runs again on each resume; not call-stack restoration')
        check(counts(mid)['checkpoints']==1,'two-question completion creates no extra durable checkpoint')

        mid=new_message(); p=worker(mid,'approval_then_question')['pending_action']
        q=resume(mid,'approval_then_question',p,True)['pending_action']
        out=resume(mid,'approval_then_question',q,'csv')
        check(out['status']=='completed' and out['answers']==['csv'] and event_count(mid,'execute_tool')==1,
              'approval then question resumes same assistant message without repeating completed tool')

        mid=new_message(); p=worker(mid,'parallel')['pending_action']
        check(event_count(mid,'parallel_sibling')==1,'parallel sibling completed before pause')
        out=resume(mid,'parallel',p,True)
        check(out['status']=='completed' and event_count(mid,'parallel_sibling')==1 and out['notes']==['sibling-completed'],
              'pending writes preserve completed parallel sibling; no repeated side effect')

        mid=new_message()
        try:
            worker(mid,'approval',fail_pause_commit=True)
            raise AssertionError('injected failure did not abort')
        except RuntimeError as exc:
            check('Injected failure' in str(exc) and not any(counts(mid).values())
                  and message(mid)['status']=='running' and not message(mid)['metadata'],
                  'checkpoint and message waiting-state rollback together on failed pause commit')
        # Verify the schema remains minimal and the existing lifecycle policies extend.
        mid=new_message(); p=worker(mid,'approval')['pending_action']
        c=message(mid)['conversation_id']
        with connect(cluster.dsn) as conn:
            try:
                conn.execute("INSERT INTO chat_app.messages(conversation_id,role) VALUES (%s,'assistant')",(c,))
                raise AssertionError('new active message unexpectedly accepted')
            except psycopg.errors.UniqueViolation:
                check(True,'requires_action remains active for one-assistant-per-conversation rule')
            try:
                conn.execute('SELECT chat_app.assert_conversation_idle(%s)',(c,))
                raise AssertionError('waiting conversation unexpectedly considered idle')
            except psycopg.errors.RaiseException:
                check(True,'snapshot idle guard blocks conversation waiting for action')
            absent=conn.execute("SELECT to_regclass('chat_app.message_pending_actions') IS NULL AS absent").fetchone()['absent']
            check(absent,'no pending-actions application table created')
            version=conn.execute('SELECT version() AS version').fetchone()['version']
        report={'generated_at':datetime.now(timezone.utc).isoformat(),'result':'passed','checks':len(results),
                'python':sys.version,
                'versions':{n:importlib.metadata.version(n) for n in ['langgraph','langgraph-checkpoint',
                    'langgraph-checkpoint-postgres','langchain-core','psycopg']},'postgres':version,
                'execution':'fresh Python subprocess per invocation; PostgreSQL restart included',
                'limitations':['No real LLM/MCP/HTTP/RBAC integration','Sync root graph and ordinary channels only',
                               'No subgraph/delta-channel/async conformance','No automatic crash recovery or TTL cleanup'],
                'results':results}
        if report_path:
            Path(report_path).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({'result':'passed','checks':len(results),'report':str(report_path) if report_path else None}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    if args.worker:
        print(json.dumps(work(json.load(sys.stdin))))
    else:
        main(args.report)

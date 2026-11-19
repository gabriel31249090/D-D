"""Private localhost monitoring UI. No web framework required."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import sqlite3
import sys
import threading
import time
import urllib.parse
import webbrowser
from core import (VERSION,AGENTS,SERVER,doctor,task_create,task_get,task_list,task_status,
                  message_send,messages,run_list,recent_events,heartbeats,connect,token_for,state_file)
from providers import PROVIDERS,model_defaults,save_defaults,provider_presence,validate_provider,validate_model

try:
    import psutil
except ImportError:
    psutil=None

STARTED=time.monotonic()
ACTIVE={'task_id':None,'agents':[],'writable':False,'started_at':None,'stop_event':None}
RUN_LOCK=threading.Lock()


def metrics(project):
    report={'uptime_seconds':int(time.monotonic()-STARTED), 'python':sys.version.split()[0], 'cpu_percent':None,
            'memory_percent':None,'memory_used_gb':None,'memory_total_gb':None,'disk_percent':None,
            'disk_free_gb':None, 'sqlite':'unknown','sqlite_bytes':0,'pid':os.getpid()}
    if psutil:
        try:
            report['cpu_percent']=psutil.cpu_percent(interval=None)
            vm=psutil.virtual_memory();report['memory_percent']=vm.percent
            report['memory_used_gb']=round(vm.used/(1024**3),2);report['memory_total_gb']=round(vm.total/(1024**3),2)
            du=psutil.disk_usage(str(project));report['disk_percent']=du.percent;report['disk_free_gb']=round(du.free/(1024**3),2)
        except (OSError,ValueError):pass
    try:
        with connect(project) as con:
            report['sqlite']='ok' if con.execute('PRAGMA quick_check').fetchone()[0]=='ok' else 'warning'
        report['sqlite_bytes']=sum(p.stat().st_size for p in (state_file(project),Path(str(state_file(project))+'-wal')) if p.exists())
    except (OSError,sqlite3.Error) as exc:
        report['sqlite']='error: '+str(exc)[:120]
    return report


def live_status(project):
    check=doctor(project)
    beat=heartbeats(project)
    now=datetime.now(timezone.utc)
    agents={}
    for a in ('codex','antigravity'):
        hb=beat.get(a)
        seconds=None
        if hb:
            try:seconds=(now-datetime.fromisoformat(hb['last_seen'])).total_seconds()
            except (TypeError,ValueError):pass
        agents[a]={'cli_found':bool(provider_presence().get(a)),
                   'mcp_config':check.get(a+'_mcp','not_configured'),
                   'mcp_process_recent':seconds is not None and seconds<35,
                   'seconds_since_heartbeat':round(seconds) if seconds is not None else None,
                   'last_tool_at':hb.get('last_tool_at') if hb else None,
                   'last_action':hb.get('last_action') if hb else None}
    task_records=task_list(project,80)
    with connect(project) as con:
        total,completed=con.execute("SELECT COUNT(*),SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) FROM tasks").fetchone()
    completed=completed or 0
    progress={'done':completed,'total':total,'percent':round(100*completed/total) if total else 0,
              'remaining':total-completed,'note':'Progresso das tarefas cadastradas, nao uma estimativa do desenvolvimento completo'}
    return {'version':VERSION,'project':str(project),'progress':progress,'health':metrics(project),
            'providers':provider_presence(),'defaults':model_defaults(project),'agents':agents,
            'tasks':task_records,'runs':run_list(project,40),'messages':messages(project,50),
            'active_run':{k:v for k,v in ACTIVE.items() if k!='stop_event'}}


def serve(project,port=8765,open_browser=True):
    if port<1024 or port>65535:raise ValueError('Porta invalida (1024..65535)')
    token=token_for(project)
    dashboard_file=Path(__file__).with_name('dashboard.html')

    class Handler(BaseHTTPRequestHandler):
        server_version='ArcanumBridge/6.0'
        def log_message(self,format,*args):
            try:sys.stderr.write('[painel] '+format%args+'\n')
            except (TypeError,ValueError):pass

        def respond(self,code:int,body,ctype='application/json; charset=utf-8'):
            if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
            elif isinstance(body,str):body=body.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass

        def authed(self,params=None):
            value=self.headers.get('X-ARCANUM-TOKEN','')
            if not value and params:value=params.get('token',[''])[0]
            import hmac
            return hmac.compare_digest(value,token)

        def do_GET(self):
            target=urllib.parse.urlsplit(self.path)
            params=urllib.parse.parse_qs(target.query)
            if target.path=='/':
                # Refreshing the browser should also pick up local UI updates.
                return self.respond(200,dashboard_file.read_bytes(),'text/html; charset=utf-8')
            if not self.authed(params):return self.respond(401,{'error':'Token do painel ausente ou invalido'})
            if target.path=='/api/state':
                return self.respond(200,live_status(project))
            if target.path=='/api/health':
                return self.respond(200,metrics(project))
            if target.path=='/api/events':return self.sse(params)
            if target.path=='/api/log':
                try:
                    idx=int(params.get('id',['0'])[0])
                    runs=run_list(project,100)
                    found=next((r for r in runs if r['id']==idx),None)
                    if not found:raise ValueError('Execucao nao localizada')
                    logfile=state_file(project,'logs')/f"run_{found['id']}_{found['agent']}.log"
                    if not logfile.exists():raise ValueError('Log indisponivel')
                    # Bounded log tail only, never any arbitrary filesystem path.
                    with logfile.open('rb') as f:
                        f.seek(max(0,logfile.stat().st_size-100_000))
                        content=f.read().decode('utf-8','replace')
                    return self.respond(200,content,'text/plain; charset=utf-8')
                except (OSError,ValueError) as exc:return self.respond(400,{'error':str(exc)})
            return self.respond(404,{'error':'Rota desconhecida'})

        def sse(self,params):
            try:since=max(0,int(params.get('since',['0'])[0]))
            except ValueError:since=0
            self.send_response(200)
            self.send_header('Content-Type','text/event-stream; charset=utf-8')
            self.send_header('Cache-Control','no-cache, no-transform')
            self.send_header('Connection','keep-alive')
            self.send_header('Access-Control-Allow-Origin','')
            self.send_header('Referrer-Policy','no-referrer')
            self.end_headers()
            started=time.monotonic()
            try:
                self.wfile.write(b': connected\n\n');self.wfile.flush()
                while time.monotonic()-started<55:
                    batch=recent_events(project,since=since,limit=120)
                    for item in batch:
                        since=item['id']
                        self.wfile.write(('id: '+str(item['id'])+'\nevent: update\ndata: '+json.dumps(item,ensure_ascii=False)+'\n\n').encode('utf-8'))
                    if batch:self.wfile.flush()
                    else:
                        self.wfile.write(b': ping\n\n');self.wfile.flush()
                    time.sleep(0.8 if batch else 1.7)
            except (BrokenPipeError,ConnectionResetError,OSError):pass

        def do_POST(self):
            if not self.authed():return self.respond(401,{'error':'Acesso negado'})
            origin=self.headers.get('Origin','')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                return self.respond(403,{'error':'Origem nao permitida'})
            if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
                return self.respond(415,{'error':'Use application/json'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<=0 or length>120_000:raise ValueError('Requisicao vazia ou grande demais')
                body=json.loads(self.rfile.read(length))
                if not isinstance(body,dict):raise ValueError('JSON deve ser objeto')
                if self.path=='/api/task':
                    return self.respond(201,task_create(project,body.get('title',''),body.get('description',''),body.get('assignee','all')))
                if self.path=='/api/task/status':
                    return self.respond(200,task_status(project,int(body.get('task_id',0)),body.get('status','')))
                if self.path=='/api/message':
                    return self.respond(201,message_send(project,'human',body.get('recipient','all'),body.get('text',''),body.get('task_id') or None))
                if self.path=='/api/defaults':
                    return self.respond(200,save_defaults(project,body.get('models',{})))
                if self.path=='/api/cancel':
                    with RUN_LOCK:
                        if not ACTIVE['task_id']:raise ValueError('Nao ha execucao ativa')
                        ACTIVE['stop_event'].set()
                    return self.respond(200,{'ok':True,'status':'cancel_requested'})
                if self.path=='/api/run':
                    task_id=int(body.get('task_id',0));task_get(project,task_id)
                    providers=body.get('providers',[])
                    if not isinstance(providers,list) or not providers or len(providers)>4:raise ValueError('Selecione de 1 a 4 IAs')
                    for a in providers:validate_provider(a)
                    writable=body.get('write',False) is True
                    if writable and body.get('approval')!='AUTORIZO ALTERACOES':
                        raise ValueError('Execucao com escrita exige autorizacao explicita')
                    models={**model_defaults(project),**body.get('models',{})}
                    for a in providers:validate_model(models.get(a,''))
                    timeout=int(body.get('timeout',1800))
                    if timeout<30 or timeout>7200:raise ValueError('Timeout deve ser entre 30 e 7200 segundos')
                    from bridge import execute_task
                    with RUN_LOCK:
                        if ACTIVE['task_id'] is not None:raise ValueError('Ha outra execucao ativa')
                        stop=threading.Event()
                        ACTIVE.update(task_id=task_id,agents=providers,writable=writable,
                                      started_at=datetime.now(timezone.utc).isoformat(),stop_event=stop)
                        def worker():
                            try:execute_task(project,task_id,providers,writable,writable,timeout,models,stop)
                            except BaseException as exc:
                                from core import event
                                event(project,'runner.crash','human',str(exc)[:400],task_id)
                                try:task_status(project,task_id,'failed')
                                except (ValueError,sqlite3.Error):pass
                            finally:
                                with RUN_LOCK:ACTIVE.update(task_id=None,agents=[],writable=False,started_at=None,stop_event=None)
                        threading.Thread(target=worker,daemon=True,name='arcanum-runner').start()
                    return self.respond(202,{'accepted':True,'task_id':task_id,'providers':providers,'write':writable})
                return self.respond(404,{'error':'Rota desconhecida'})
            except (ValueError,TypeError,KeyError,json.JSONDecodeError,sqlite3.Error,OSError) as exc:
                return self.respond(400,{'error':str(exc)})

    httpd=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    httpd.daemon_threads=True
    url=f'http://127.0.0.1:{port}/?token={token}'
    print('\nARCANUM Agent Bridge — painel local',flush=True)
    print('Projeto:',project,flush=True)
    print('Endereco local: http://127.0.0.1:'+str(port),flush=True)
    print('Acesso autenticado:',url,flush=True)
    print('Para encerrar: CTRL+C. Nunca compartilhe o link com token.',flush=True)
    if open_browser:
        import threading
        threading.Timer(1.2,lambda:webbrowser.open(url)).start()
    try:httpd.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:pass
    finally:httpd.server_close()
    return 0

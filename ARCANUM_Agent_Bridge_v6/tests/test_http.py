import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib import request, error

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
import dashboard_server


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/'Project & Valebruma'
        self.project.mkdir()
        self.env=patch.dict(os.environ,{'CODEX_HOME':str(Path(self.tmp.name)/'codex')})
        self.env.start();self.addCleanup(self.env.stop)
        core.install(self.project)
        self.token=core.token_for(self.project)
        sk=socket.socket();sk.bind(('127.0.0.1',0));self.port=sk.getsockname()[1];sk.close()
        self.thread=threading.Thread(target=dashboard_server.serve,args=(self.project,self.port,False),daemon=True)
        self.thread.start()
        for _ in range(40):
            try:
                with request.urlopen(f'http://127.0.0.1:{self.port}/',timeout=.5) as response:
                    if response.status==200:break
            except Exception:time.sleep(.05)
        else:self.fail('Local dashboard did not start')

    def req(self,path,body=None,authorized=True):
        headers={'X-ARCANUM-TOKEN':self.token} if authorized else {}
        if body is not None:headers['Content-Type']='application/json'
        r=request.Request(f'http://127.0.0.1:{self.port}{path}',
            data=json.dumps(body).encode('utf-8') if body is not None else None,headers=headers)
        with request.urlopen(r,timeout=3) as response:
            return json.load(response)

    def test_auth_health_task_progress_models(self):
        with self.assertRaises(error.HTTPError) as cm:self.req('/api/state',authorized=False)
        self.assertEqual(cm.exception.code,401)
        s=self.req('/api/state')
        self.assertEqual(s['health']['sqlite'],'ok')
        self.assertEqual(s['progress']['percent'],0)
        t=self.req('/api/task',{'title':'Criar combate'})
        self.assertEqual(t['status'],'pending')
        self.req('/api/task/status',{'task_id':t['id'],'status':'done'})
        s=self.req('/api/state')
        self.assertEqual(s['progress']['percent'],100)
        d=self.req('/api/defaults',{'models':{'codex':'gpt-6','antigravity':'Gemini 3.6 Flash (High)'}})
        self.assertEqual(d['codex'],'gpt-6')
        self.assertEqual(self.req('/api/state')['defaults']['antigravity'],'Gemini 3.6 Flash (High)')


if __name__=='__main__':unittest.main()

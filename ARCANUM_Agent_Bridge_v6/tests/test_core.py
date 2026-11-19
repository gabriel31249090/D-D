import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
import providers
import bridge


class BridgeCoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.project=self.base/'D&D'
        self.project.mkdir()
        self.codexdir=self.base/'codexhome'
        self.codexdir.mkdir()
        self.env=patch.dict(os.environ,{'CODEX_HOME':str(self.codexdir)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_mcp_repair_does_not_touch_other_servers(self):
        config=self.codexdir/'config.toml'
        config.write_text('''model = "gpt-6"
[mcp_servers.context7]
command = "node"
args = ["context7.js"]
[mcp_servers.arcanum-bridge]
command = "old.exe"
args = ["x"]
[mcp_servers.arcanum-bridge]
command = "old.exe"
args = ["y"]
[mcp_servers.playwright]
command = "node"
args = ["playwright.js"]
''', encoding='utf-8')
        result=core.install(self.project)
        settings=tomllib.loads(config.read_text())
        self.assertEqual(settings['model'],'gpt-6')
        self.assertEqual(settings['mcp_servers']['context7']['args'],['context7.js'])
        self.assertIn('playwright',settings['mcp_servers'])
        self.assertEqual(settings['mcp_servers']['arcanum-bridge']['args'][3],str(self.project))
        self.assertTrue(result['codex']['backup'])
        self.assertIn('D&D',json.dumps(settings))
        self.assertEqual(core.doctor(self.project)['codex_mcp'],'configured')
        self.assertEqual(core.doctor(self.project)['antigravity_mcp'],'configured')

    def test_idempotent_install_and_existing_antigravity_server(self):
        original=self.project/'.agents'/'mcp_config.json'
        original.parent.mkdir()
        original.write_text(json.dumps({'mcpServers':{'other':{'command':'xyz'}}}))
        core.install(self.project)
        core.install(self.project)
        content=(self.codexdir/'config.toml').read_text()
        self.assertEqual(content.count('[mcp_servers.arcanum-bridge]'),1)
        self.assertIn('other',json.loads(original.read_text())['mcpServers'])
        self.assertEqual(json.loads(original.read_text())['mcpServers']['arcanum-bridge']['args'][3],str(self.project))

    def test_invalid_other_toml_is_preserved(self):
        config=self.codexdir/'config.toml'
        config.write_text('bad = [',encoding='utf-8')
        with self.assertRaises(tomllib.TOMLDecodeError):core.install(self.project)
        self.assertEqual(config.read_text(),'bad = [')

    def test_task_and_messages_and_progress(self):
        t=core.task_create(self.project,'Criar regras de combate','ND e CA')
        self.assertEqual(t['status'],'pending')
        self.assertEqual(len(core.task_list(self.project)),1)
        core.message_send(self.project,'codex','antigravity','API pronta',t['id'])
        self.assertEqual(len(core.messages(self.project,recipient='antigravity')),1)
        self.assertEqual(len(core.messages(self.project,recipient='codex')),0)
        core.task_status(self.project,t['id'],'done')
        self.assertEqual(core.task_get(self.project,t['id'])['status'],'done')

    def test_prompt_must_be_authorized_to_write(self):
        t=core.task_create(self.project,'ABC')
        with self.assertRaises(ValueError):
            bridge.execute_task(self.project,t['id'],['codex'],writable=True,confirmed=False)
        self.assertEqual(core.task_get(self.project,t['id'])['status'],'pending')

    def test_scripted_agent_run_no_real_cli(self):
        t=core.task_create(self.project,'Analise API')
        fake=[sys.executable,'-u','-c',
              'import json;print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"Revisao OK"}}))']
        with patch.object(bridge,'command_for',return_value=fake):
            result=bridge.execute_task(self.project,t['id'],['codex'],timeout=35)
        self.assertEqual(result,0)
        self.assertEqual(core.task_get(self.project,t['id'])['status'],'review')
        self.assertEqual(core.run_list(self.project)[0]['exit_code'],0)
        self.assertIn('Revisao OK',core.messages(self.project)[0]['body'])

    def test_model_validation(self):
        self.assertEqual(providers.validate_model('Gemini 3.6 Flash (High)'), 'Gemini 3.6 Flash (High)')
        for bad in ('xx\nmalicious','../../some;cmd','a'*101):
            with self.assertRaises(ValueError):providers.validate_model(bad)

    def test_no_access_to_other_project_paths(self):
        with self.assertRaises(ValueError):core.root(str(self.base/'absent'))

    def test_doctor_rejects_unlaunchable_or_wrong_identity_config(self):
        core.install(self.project)
        config=self.project/'.agents'/'mcp_config.json'
        original=json.loads(config.read_text(encoding='utf-8'))
        for kind in ('executable','script','agent','disabled'):
            with self.subTest(kind=kind):
                data=json.loads(json.dumps(original))
                record=data['mcpServers'][core.SERVER]
                if kind=='executable':record['command']=str(self.base/'missing-python.exe')
                elif kind=='script':record['args'][0]=str(self.base/'missing-bridge.py')
                elif kind=='agent':record['args'][-1]='codex'
                else:record['disabled']=True
                config.write_text(json.dumps(data),encoding='utf-8')
                self.assertEqual(core.doctor(self.project)['antigravity_mcp'],'not_configured')
        config.write_text(json.dumps(original),encoding='utf-8')
        self.assertEqual(core.doctor(self.project)['antigravity_mcp'],'configured')

    def test_doctor_detects_fastmcp_import_failure(self):
        # MCP 2.x can import ``mcp`` while the required FastMCP module is absent.
        with patch.dict(sys.modules,{'mcp.server.fastmcp':None}):
            result=core.doctor(self.project)
        self.assertFalse(result['mcp_library'])
        self.assertIn('MCP SDK 1.x',result['mcp_library_error'])


if __name__=='__main__':unittest.main()

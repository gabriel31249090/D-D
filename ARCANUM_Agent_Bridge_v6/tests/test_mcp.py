"""Real stdio integration, isolated from the user's project and agent inboxes."""
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core


@asynccontextmanager
async def client(project, agent):
    params=StdioServerParameters(
        command=sys.executable,
        args=[str(core.ENTRY),'mcp','--project',str(project),'--agent',agent],
        env={'PYTHONUTF8':'1'},
    )
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=15)) as session:
            await session.initialize()
            yield session


def decoded(result):
    if result.isError:
        raise AssertionError('MCP tool failed: '+str(result.content))
    structured=getattr(result,'structuredContent',None)
    if structured is not None:
        return structured.get('result',structured)
    texts=[item.text for item in result.content if getattr(item,'type',None)=='text']
    if not texts:return []
    # FastMCP wraps list results in structuredContent, dicts in one text block.
    return json.loads(texts[0])


class BridgeMCPTest(unittest.TestCase):
    def test_stdio_tools_claim_race_and_message_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)/'D&D teste de conexão'
            project.mkdir()
            asyncio.run(self.roundtrip(project))

    async def roundtrip(self,project):
        # These identities are test clients in a disposable database, never claims
        # that a real Antigravity IDE connected to the user's workspace.
        async with client(project,'codex') as codex:
            expected={'bridge_health','create_bridge_task','list_bridge_tasks',
                      'get_bridge_task','claim_bridge_task','update_bridge_task',
                      'send_bridge_message','read_bridge_inbox'}
            self.assertEqual({tool.name for tool in (await codex.list_tools()).tools},expected)
            health=decoded(await codex.call_tool('bridge_health',{}))
            self.assertEqual(health['agent'],'codex')
            self.assertEqual(health['project'],str(project))
            self.assertTrue(health['ok'])
            self.assertEqual(decoded(await codex.call_tool('list_bridge_tasks',{})),[])
            self.assertEqual(decoded(await codex.call_tool('read_bridge_inbox',{})),[])

            task=decoded(await codex.call_tool('create_bridge_task',
                {'title':'Contrato de combate — conexão 🎲','assignee':'all'}))
            async with client(project,'antigravity') as antigravity:
                result=decoded(await antigravity.call_tool('bridge_health',{}))
                self.assertEqual(result['agent'],'antigravity')
                # Atomic task claims must prevent simultaneous editors from
                # both acquiring the same pending task.
                claims=await asyncio.gather(
                    codex.call_tool('claim_bridge_task',{'task_id':task['id']}),
                    antigravity.call_tool('claim_bridge_task',{'task_id':task['id']}))
                self.assertEqual(sum(not result.isError for result in claims),1)
                claimed=decoded(await codex.call_tool('get_bridge_task',{'task_id':task['id']}))
                self.assertEqual(claimed['status'],'in_progress')
                self.assertIn(claimed['assignee'],('codex','antigravity'))

                sent=decoded(await codex.call_tool('send_bridge_message',
                    {'recipient':'antigravity','text':'API pronta: ação 🎲','task_id':task['id']}))
                self.assertEqual(decoded(await codex.call_tool('read_bridge_inbox',{})),[])
                inbox=decoded(await antigravity.call_tool('read_bridge_inbox',{}))
                self.assertEqual([item['id'] for item in inbox],[sent['id']])
                self.assertEqual(inbox[0]['body'],'API pronta: ação 🎲')
                self.assertEqual(decoded(await antigravity.call_tool('read_bridge_inbox',
                    {'since_id':sent['id']})),[])

                reply=decoded(await antigravity.call_tool('send_bridge_message',
                    {'recipient':'codex','text':'Contrato recebido','task_id':task['id']}))
                inbox=decoded(await codex.call_tool('read_bridge_inbox',{}))
                self.assertEqual([item['id'] for item in inbox],[reply['id']])
                self.assertEqual(inbox[0]['sender'],'antigravity')

                broadcast=decoded(await codex.call_tool('send_bridge_message',
                    {'recipient':'all','text':'Integração liberada'}))
                inbox=decoded(await antigravity.call_tool('read_bridge_inbox',
                    {'since_id':reply['id']}))
                self.assertEqual([item['id'] for item in inbox],[broadcast['id']])

                completed=decoded(await codex.call_tool('update_bridge_task',
                    {'task_id':task['id'],'status':'done'}))
                self.assertEqual(completed['status'],'done')
                tasks=decoded(await antigravity.call_tool('list_bridge_tasks',{}))
                self.assertEqual(tasks[0]['status'],'done')


if __name__=='__main__':unittest.main()

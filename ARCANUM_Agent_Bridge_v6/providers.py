"""Agent adapters and runtime model switching. No arbitrary shell commands from UI."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from core import atomic_write, bin_path, state_file

PROVIDERS = ('codex','antigravity','ollama','openai-compatible')
MODEL_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_./:+ ()-]{0,99}$', re.ASCII)
DEFAULTS = {'codex':'', 'antigravity':'', 'ollama':'llama3.2', 'openai-compatible':''}


def validate_provider(provider:str)->str:
    if provider not in PROVIDERS:
        raise ValueError('IA/provedor desconhecido')
    return provider


def validate_model(model:str)->str:
    if not isinstance(model,str) or (model and not MODEL_RE.fullmatch(model)):
        raise ValueError('Modelo invalido (maximo 100 caracteres; sem quebras de linha)')
    return model


def model_defaults(project:Path)->dict:
    path=state_file(project,'providers.json')
    if not path.exists():return DEFAULTS.copy()
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict):raise ValueError('providers.json invalido')
    return {p: validate_model(data.get(p,DEFAULTS[p])) for p in PROVIDERS}


def save_defaults(project:Path,values:dict)->dict:
    if not isinstance(values,dict) or any(p not in PROVIDERS for p in values):
        raise ValueError('Provedor nao permitido')
    data=model_defaults(project)
    for key,value in values.items():data[key]=validate_model(value)
    atomic_write(state_file(project,'providers.json'),json.dumps(data,indent=2)+'\n')
    return data


def compat_url()->str|None:
    url=os.environ.get('ARCANUM_COMPAT_URL','').strip().rstrip('/')
    if not url:return None
    # Explicit env config only: never let dashboard visitors supply arbitrary URLs.
    if not (url.startswith('https://') or url.startswith('http://127.0.0.1:') or url.startswith('http://localhost:')):
        raise ValueError('ARCANUM_COMPAT_URL requer HTTPS ou endereco localhost')
    return url


def _safe_node_cli(name:str, env_var:str)->list[str]|None:
    """Use executavel nativo ou Node+JS; nunca passar prompts por um shim .cmd."""
    override=os.environ.get(env_var,'').strip()
    if override:
        fp=Path(override).expanduser()
        if not fp.is_file():return None
        if fp.suffix.lower()=='.exe':return [str(fp)]
        if fp.suffix.lower() in ('.js','.mjs'):
            node=bin_path('node')
            return [node,str(fp)] if node else None
        return None
    exe=bin_path(name)
    if not exe:return None
    fp=Path(exe)
    if os.name!='nt':return [exe]
    if fp.suffix.lower()=='.exe':return [exe]
    node=bin_path('node')
    if not node:return None
    # npm .cmd shims can reparse &, parentheses and user prompt text.
    # Resolve the underlying JavaScript module and invoke Node directly.
    candidates=[]
    if fp.suffix.lower() in ('.cmd','.bat'):
        try:
            shim=fp.read_text(encoding='utf-8-sig',errors='ignore')
            for m in re.finditer(r'node_modules[\\/][A-Za-z0-9_@.\\/-]+?\.(?:c?m?js)',shim,re.I):
                relative=m.group(0).replace('\\','/')
                candidates.append(fp.parent/Path(relative))
        except OSError:pass
    if name=='codex':
        candidates.extend([fp.parent/'node_modules'/'@openai'/'codex'/'bin'/'codex.js'])
    for candidate in candidates:
        if candidate.is_file():return [node,str(candidate.resolve())]
    return None


def codex_command()->list[str]|None:
    return _safe_node_cli('codex','ARCANUM_CODEX_EXECUTABLE')


def agy_command()->list[str]|None:
    return _safe_node_cli('agy','ARCANUM_AGY_EXECUTABLE')

def provider_presence()->dict:
    return {'codex': bool(codex_command()),
            'antigravity':bool(agy_command()),
            'ollama':bool(bin_path('ollama')) or bool(os.environ.get('ARCANUM_OLLAMA_URL')),
            'openai-compatible':bool(compat_url())}


def command_for(provider:str,model:str,write:bool)->list[str]|None:
    validate_provider(provider);validate_model(model)
    if provider=='codex':
        base=codex_command()
        if not base:raise RuntimeError('Codex CLI nao encontrado. Instale e autentique com codex.cmd login.')
        cmd=base+['exec','--json','--skip-git-repo-check','--sandbox','workspace-write' if write else 'read-only']
        if model:cmd.extend(['--model',model])
        return cmd+['-']
    if provider=='antigravity':
        base=agy_command()
        if not base:raise RuntimeError('Antigravity CLI sem executavel seguro: instale agy ou configure ARCANUM_AGY_EXECUTABLE com .exe/.js')
        cmd=base+['--mode','accept-edits' if write else 'plan','--output-format','stream-json']
        if model:cmd.extend(['--model',model])
        return cmd+['-p'] # append prompt separately
    if provider in ('ollama','openai-compatible'):
        if write:raise ValueError(f'{provider} executa apenas tarefas de planejamento/revisao')
        return None
    raise ValueError('Provedor desconhecido')


def http_generate(provider:str,model:str,prompt:str,on_text,timeout=600)->str:
    """Optional HTTP-based adapters, planning only. Configured via env, no stored keys."""
    if not model:raise ValueError('Informe o nome do modelo para este provedor')
    validate_model(model)
    if provider=='ollama':
        base=os.environ.get('ARCANUM_OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
        if not (base.startswith('http://127.0.0.1:') or base.startswith('http://localhost:')):
            raise ValueError('Ollama so e aceito via localhost nesta versao')
        req=urllib.request.Request(base+'/api/generate',data=json.dumps({'model':model,'prompt':prompt,'stream':True}).encode(),
                                   headers={'Content-Type':'application/json'})
        output=[]
        with urllib.request.urlopen(req,timeout=timeout) as res:
            for row in res:
                if not row.strip():continue
                data=json.loads(row)
                if data.get('error'):raise RuntimeError(str(data['error']))
                chunk=data.get('response','')
                if chunk:
                    on_text(chunk);output.append(chunk)
                if data.get('done'):break
        return ''.join(output)
    if provider=='openai-compatible':
        base=compat_url()
        if not base:raise RuntimeError('Configure ARCANUM_COMPAT_URL antes de iniciar o painel')
        key=os.environ.get('ARCANUM_COMPAT_API_KEY','')
        headers={'Content-Type':'application/json'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(base+'/chat/completions',
            data=json.dumps({'model':model,'messages':[{'role':'user','content':prompt}],'stream':False}).encode(),headers=headers)
        with urllib.request.urlopen(req,timeout=timeout) as res:
            data=json.load(res)
        text=data['choices'][0]['message']['content']
        if not isinstance(text,str):text=str(text)
        on_text(text)
        return text
    raise ValueError('Provedor HTTP invalido')

"""Installer bootstrap: avoid CMD argument parsing of project paths with '&'."""
from __future__ import annotations
from pathlib import Path
import sys
from core import root, install, atomic_write, VERSION


def main():
    here=Path(__file__).resolve().parent
    stored=here/'project_path.txt'
    last=stored.read_text(encoding='utf-8-sig').strip() if stored.exists() else ''
    print('\n=== ARCANUM Agent Bridge '+VERSION+' — configuracao ===',flush=True)
    print('Nenhum projeto existente sera apagado.\n',flush=True)
    value=input('Caminho da pasta de projeto'+(' ['+last+']' if last else '')+': ').strip().strip('"')
    if not value:value=last
    if not value:raise ValueError('Informe o caminho do projeto')
    project=root(value)
    results=install(project)
    atomic_write(stored,str(project)+'\n')
    print('\nCONFIGURACAO CONCLUIDA!')
    print('Projeto:',project)
    print('Banco:',results['db'])
    print('MCP Codex:',results['codex']['path'])
    print('MCP Antigravity:',results['antigravity']['path'])
    print('Backup Codex:',results['codex']['backup'] or 'sem alteracoes')
    print('OBS: registro no arquivo nao prova conexao ativa.')
    print('Execute ABRIR_PAINEL.bat e TESTAR_CONEXAO.bat.')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('\nERRO:',exc,file=sys.stderr)
        sys.exit(1)

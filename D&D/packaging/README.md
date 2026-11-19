# Instalador Windows

`scripts/build_desktop.ps1` cria `dist/ARCANUM-Setup-0.2.0-win-x64.exe` usando o compilador C# do .NET Framework presente no Windows. Não exige Inno Setup, NSIS ou PyInstaller.
O instalador inclui runtime Python 3.12 x64, Tcl/Tk, módulos desktop/backend e dependências de execução, com licenças preservadas. Não instala Python no sistema nem depende de uma instalação de Python na máquina de destino.

O instalador visual cria a aplicação em `%LOCALAPPDATA%\Programs\ARCANUM`, atalhos para este usuário e uma entrada em Aplicativos do Windows. Não solicita privilégios de administrador.
O desinstalador remove somente arquivos listados no manifesto da aplicação. Dados pessoais em `%LOCALAPPDATA%\ARCANUM` e fontes privadas selecionadas pelo usuário permanecem intactos.
A distribuição não inclui livros, ZIPs privados, bancos de dados do projeto, configurações MCP, contas ou credenciais.

Para testar em pasta descartável sem alterar os atalhos/registro do Windows:

```powershell
.\dist\ARCANUM-Setup-0.2.0-win-x64.exe --silent --install-dir '<pasta vazia descartável>' --no-register --no-shortcuts --log '<arquivo de log>'
```

Na pasta instalada, `runtime\python.exe -m desktop.app --smoke-test` usa `ARCANUM_DATA_DIR` quando configurado.
O executável `Uninstall.exe --silent --log '<arquivo de log>'` inicia uma cópia temporária do desinstalador para permitir a remoção do próprio arquivo original. A cópia leve fica na pasta temporária do Windows e os dados do usuário são preservados.

Este pacote de desenvolvimento não tem assinatura de código digital. A estrutura e a integridade do arquivo são registradas em `dist/BUILD_REPORT.json` com SHA-256.


import React from 'react'
import { Shield, BookOpen, Terminal } from 'lucide-react'

export const ScopeNotice: React.FC = () => {
  return (
    <div className="tab-container scope-container">
      <div className="section-header">
        <h2>Escopo do Protótipo & Atribuição de Regras</h2>
        <p className="section-desc">
          Transparência sobre o recorte técnico e mecânico implementado na versão 0.1 do ARCANUM.
        </p>
      </div>

      <div className="scope-cards-grid">
        <div className="panel scope-panel">
          <div className="panel-title">
            <Shield size={20} className="gold-icon" />
            <h3>Recorte Mecânico Atual</h3>
          </div>
          <ul className="scope-list">
            <li>
              <strong>Conjunto de Regras:</strong> D&D 5e (SRD 5.1 / 2014). Não mistura revisões de 2024.
            </li>
            <li>
              <strong>Classe Suportada:</strong> Guerreiro Nível 1 com pontos de vida base 10 + mod CON.
            </li>
            <li>
              <strong>Atributos:</strong> Entrada direta (3 a 20). Modificadores, salvaguardas e bônus calculados pelo Python.
            </li>
            <li>
              <strong>Armaduras:</strong> Cota de Malha (CA 16), Couro (CA 11 + DES) e Sem Armadura (CA 10 + DES). Escudo (+2 CA).
            </li>
            <li>
              <strong>Estilos de Luta:</strong> Defesa (+1 CA) e Duelismo (+2 dano de arma em uma mão).
            </li>
            <li>
              <strong>Monstros de Treino:</strong> Fixture sintética (<code>training-goblin</code>) identificada como exemplo para validação da arena.
            </li>
            <li>
              <strong>Incapacitação:</strong> Na arena de treino, 0 PV indica combatente incapacitado. Salvaguardas contra a morte e magias serão adicionadas em fases futuras.
            </li>
          </ul>
        </div>

        <div className="panel scope-panel">
          <div className="panel-title">
            <Terminal size={20} className="gold-icon" />
            <h3>Arquitetura & Como Iniciar</h3>
          </div>
          <div className="instructions-block">
            <p><strong>1. Inicializar o Backend (FastAPI / Python 3.12):</strong></p>
            <pre className="code-snippet">
              # No PowerShell, na raiz do projeto (C:\Users\Aluno\Downloads\D&D):{"\n"}
              .\scripts\run_api.ps1
            </pre>
            <p>O backend inicializa em <code>http://127.0.0.1:8000</code> com Swagger em <code>/docs</code>.</p>

            <p style={{ marginTop: '1rem' }}><strong>2. Inicializar o Frontend (React / Vite):</strong></p>
            <pre className="code-snippet">
              # No PowerShell:{"\n"}
              cd frontend{"\n"}
              npm run dev
            </pre>
            <p>Acesse no navegador: <code>http://localhost:5173</code>.</p>
          </div>
        </div>

        <div className="panel scope-panel full-width">
          <div className="panel-title">
            <BookOpen size={20} className="gold-icon" />
            <h3>Atribuição de Direitos e Licença SRD 5.1</h3>
          </div>
          <p className="legal-text">
            Este trabalho inclui material extraído do System Reference Document 5.1 (“SRD 5.1”) da Wizards of the Coast LLC, disponível em{' '}
            <a
              href="https://dnd.wizards.com/resources/systems-reference-document"
              target="_blank"
              rel="noreferrer"
            >
              https://dnd.wizards.com/resources/systems-reference-document
            </a>
            . O SRD 5.1 é licenciado sob a licença Creative Commons Attribution 4.0 International License disponível em{' '}
            <a
              href="https://creativecommons.org/licenses/by/4.0/legalcode"
              target="_blank"
              rel="noreferrer"
            >
              https://creativecommons.org/licenses/by/4.0/legalcode
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  )
}

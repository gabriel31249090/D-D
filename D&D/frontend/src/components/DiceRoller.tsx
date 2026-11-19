import React, { useState } from 'react'
import { Dices, Sparkles, AlertCircle, Play } from 'lucide-react'
import type { DiceOut, DiceRequest } from '../types/api'
import { api, ApiClientError } from '../services/api'
import { sfx } from '../utils/audio'

interface DiceRollerProps {
  soundEnabled: boolean
}

export const DiceRoller: React.FC<DiceRollerProps> = ({ soundEnabled }) => {
  const [expression, setExpression] = useState('1d20+3')
  const [mode, setMode] = useState<'normal' | 'advantage' | 'disadvantage'>('normal')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<DiceOut[]>([])

  const handleRoll = async (exprToRoll = expression, modeToRoll = mode) => {
    setLoading(true)
    setError(null)

    if (soundEnabled) {
      sfx.playDiceRoll()
    }

    try {
      const payload: DiceRequest = {
        expression: exprToRoll,
        mode: modeToRoll,
      }
      const res = await api.rollDice(payload)
      setResults((prev) => [res, ...prev.slice(0, 19)])
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(`Erro da API (${err.code}): ${err.message}`)
      } else {
        setError(err.message || 'Erro ao rolar dados')
      }
    } finally {
      setLoading(false)
    }
  }

  const quickRoll = (expr: string) => {
    setExpression(expr)
    handleRoll(expr, mode)
  }

  return (
    <div className="tab-container">
      <div className="section-header">
        <h2>Rolador de Dados Oficial (Python Engine)</h2>
        <p className="section-desc">
          Todas as rolagens são calculadas com gerador criptográfico do Python (`secrets.randbelow`) e registradas no banco.
        </p>
      </div>

      <div className="creator-grid">
        {/* Painel de Rolagem */}
        <div className="panel form-panel">
          <div className="panel-title">
            <Dices size={20} className="gold-icon" />
            <h3>Configurar Rolagem</h3>
          </div>

          <div className="form-group">
            <label htmlFor="dice-expr">Expressão de Dados (ex: 1d20+3, 2d6+2)</label>
            <input
              id="dice-expr"
              type="text"
              className="input-field"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder="1d20+3"
            />
          </div>

          <div className="form-group">
            <label>Modo de Rolagem (D20)</label>
            <div className="mode-toggle-group">
              <button
                type="button"
                className={`mode-btn ${mode === 'normal' ? 'active' : ''}`}
                onClick={() => setMode('normal')}
              >
                Normal
              </button>
              <button
                type="button"
                className={`mode-btn ${mode === 'advantage' ? 'active' : ''}`}
                onClick={() => setMode('advantage')}
                title="Rola 2d20 e escolhe o maior"
              >
                Vantagem
              </button>
              <button
                type="button"
                className={`mode-btn ${mode === 'disadvantage' ? 'active' : ''}`}
                onClick={() => setMode('disadvantage')}
                title="Rola 2d20 e escolhe o menor"
              >
                Desvantagem
              </button>
            </div>
          </div>

          <div className="quick-dice-section">
            <span className="detail-label">Atalhos Comuns:</span>
            <div className="quick-dice-buttons">
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d20')}>
                1d20
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d20+5')}>
                1d20+5 (Ataque)
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d8+3')}>
                1d8+3 (Espada)
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('2d6+2')}>
                2d6+2
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d12')}>
                1d12
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d10')}>
                1d10
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d6+2')}>
                1d6+2 (Goblin)
              </button>
              <button type="button" className="btn-secondary btn-sm" onClick={() => quickRoll('1d4')}>
                1d4
              </button>
            </div>
          </div>

          {error && (
            <div className="error-alert">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button
            type="button"
            className="btn-primary"
            onClick={() => handleRoll()}
            disabled={loading || !expression.trim()}
          >
            <Play size={18} />
            <span>{loading ? 'Calculando no Backend...' : 'Rolar Dados'}</span>
          </button>
        </div>

        {/* Histórico de Rolagens */}
        <div className="panel list-panel">
          <div className="panel-title">
            <Sparkles size={20} className="gold-icon" />
            <h3>Resultados Recentes ({results.length})</h3>
          </div>

          {results.length === 0 ? (
            <div className="empty-state">
              <p>Nenhuma rolagem realizada nesta sessão.</p>
              <p className="empty-subtext">Selecione uma expressão à esquerda para testar o gerador.</p>
            </div>
          ) : (
            <div className="dice-results-list">
              {results.map((r) => (
                <div key={r.id} className="dice-result-card">
                  <div className="dice-card-header">
                    <span className="dice-expr-tag">
                      {r.expression} {r.mode !== 'normal' ? `(${r.mode})` : ''}
                    </span>
                    <span className="dice-total-tag">Total: {r.total}</span>
                  </div>

                  <div className="dice-details-row">
                    <span>
                      Dados rolados: [{r.rolls.join(', ')}]
                    </span>
                    {r.kept && r.kept.length > 0 && r.mode !== 'normal' && (
                      <span>Dados mantidos: [{r.kept.join(', ')}]</span>
                    )}
                    <span>
                      Modificador: {r.modifier >= 0 ? `+${r.modifier}` : r.modifier}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

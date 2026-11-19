import React, { useEffect, useState } from 'react'
import { History, Swords, Shield, Skull, RefreshCw, AlertCircle } from 'lucide-react'
import type { CombatOut } from '../types/api'
import { api } from '../services/api'

interface SavedCombatsProps {
  onSelectCombat: (combat: CombatOut) => void
  currentCombatId: string | null
}

export const SavedCombats: React.FC<SavedCombatsProps> = ({
  onSelectCombat,
  currentCombatId,
}) => {
  const [combats, setCombats] = useState<CombatOut[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCombats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getCombats(50, 0)
      setCombats(data)
    } catch (err: any) {
      setError(`Falha ao carregar encontros salvos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCombats()
  }, [])

  return (
    <div className="tab-container">
      <div className="section-header">
        <div className="section-header-row">
          <div>
            <h2>Encontros Salvos & Histórico</h2>
            <p className="section-desc">
              Todos os encontros são persistidos de forma autoritativa no banco SQLite pelo backend Python.
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={loadCombats}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Atualizar Lista</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {combats.length === 0 ? (
        <div className="panel empty-state">
          <History size={40} className="gold-icon" />
          <p>Nenhum encontro registrado no banco de dados.</p>
          <p className="empty-subtext">Inicie um combate na aba Grupos para criar o primeiro registro.</p>
        </div>
      ) : (
        <div className="saved-combats-grid">
          {combats.map((c) => {
            const isCurrent = c.id === currentCombatId
            const partyCount = c.combatants.filter((k) => k.team === 'party').length
            const enemyCount = c.combatants.filter((k) => k.team === 'enemy').length

            return (
              <div
                key={c.id}
                className={`panel saved-combat-card ${isCurrent ? 'current-active' : ''}`}
              >
                <div className="combat-card-top">
                  <div className="combat-id-block">
                    <span className="badge-tag">Encontro #{c.id.slice(0, 8)}</span>
                    <span className={`badge-tag ${c.status}`}>
                      {c.status === 'active' ? '⚔️ Ativo' : '✓ Concluído'}
                    </span>
                  </div>

                  {c.winner && (
                    <span className={`winner-badge ${c.winner}`}>
                      Vencedor: {c.winner === 'party' ? 'Comitiva' : 'Monstros'}
                    </span>
                  )}
                </div>

                <div className="combat-stats-row">
                  <div>
                    <span className="stat-label">Rodada Atual</span>
                    <strong>{c.round}</strong>
                  </div>
                  <div>
                    <span className="stat-label">Versão do Estado</span>
                    <strong>v{c.version}</strong>
                  </div>
                  <div>
                    <span className="stat-label">Participantes</span>
                    <strong>
                      {partyCount} heróis vs {enemyCount} monstros
                    </strong>
                  </div>
                </div>

                {/* Lista de Combatentes */}
                <div className="combatants-preview">
                  <span className="stat-label">Combatentes:</span>
                  <div className="combatants-chips">
                    {c.combatants.map((k) => (
                      <span
                        key={k.id}
                        className={`mini-combatant-chip ${k.team} ${
                          k.current_hp <= 0 ? 'defeated' : ''
                        }`}
                      >
                        {k.team === 'party' ? <Shield size={10} /> : <Skull size={10} />}
                        {k.name}: {k.current_hp}/{k.max_hp} PV
                      </span>
                    ))}
                  </div>
                </div>

                <div className="combat-card-actions">
                  <button
                    type="button"
                    className="btn-accent btn-block"
                    onClick={() => onSelectCombat(c)}
                  >
                    <Swords size={16} />
                    <span>{c.status === 'active' ? 'Retomar Combate' : 'Visualizar Arena'}</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

import React, { useState } from 'react'
import { Users, Plus, Swords, AlertCircle, Check, Shield } from 'lucide-react'
import type { CharacterOut, PartyCreate, PartyOut, CombatOut } from '../types/api'
import { api, ApiClientError } from '../services/api'

interface PartyManagerProps {
  characters: CharacterOut[]
  parties: PartyOut[]
  onPartyCreated: (party: PartyOut) => void
  onCombatStarted: (combat: CombatOut) => void
  onNavigateToTab: (tab: any) => void
}

export const PartyManager: React.FC<PartyManagerProps> = ({
  characters,
  parties,
  onPartyCreated,
  onCombatStarted,
  onNavigateToTab,
}) => {
  const [name, setName] = useState('Comitiva Valebruma')
  const [selectedCharIds, setSelectedCharIds] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [startingCombatId, setStartingCombatId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const toggleSelectChar = (id: string) => {
    setSelectedCharIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  const handleCreateParty = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Informe um nome para o grupo.')
      return
    }
    if (selectedCharIds.length === 0) {
      setError('Selecione pelo menos um personagem para compor o grupo.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccessMsg(null)

    const payload: PartyCreate = {
      name: name.trim(),
      character_ids: selectedCharIds,
    }

    try {
      const created = await api.createParty(payload)
      onPartyCreated(created)
      setSuccessMsg(`Grupo "${created.name}" formado com ${created.character_ids.length} membro(s)!`)
      setSelectedCharIds([])
      setName(`Comitiva da Arena ${parties.length + 2}`)
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(`Erro da API (${err.code}): ${err.message}`)
      } else {
        setError(err.message || 'Erro ao criar grupo')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleStartCombat = async (partyId: string) => {
    setStartingCombatId(partyId)
    setError(null)
    setSuccessMsg(null)

    try {
      const combat = await api.createCombat({
        party_id: partyId,
        monster_ids: ['training-goblin'],
        rule_set: 'dnd5e-2014',
      })
      onCombatStarted(combat)
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(`Não foi possível iniciar o combate (${err.code}): ${err.message}`)
      } else {
        setError(err.message || 'Erro ao iniciar combate')
      }
    } finally {
      setStartingCombatId(null)
    }
  }

  return (
    <div className="tab-container">
      <div className="section-header">
        <h2>Gerenciamento de Grupos (Parties)</h2>
        <p className="section-desc">
          Reúna seus combatentes em grupos de aventura para desafiar monstros e iniciar batalhas na arena.
        </p>
      </div>

      <div className="creator-grid">
        {/* Formulário de Criação de Grupo */}
        <div className="panel form-panel">
          <div className="panel-title">
            <Users size={20} className="gold-icon" />
            <h3>Formar Novo Grupo</h3>
          </div>

          <form onSubmit={handleCreateParty} className="char-form">
            <div className="form-group">
              <label htmlFor="party-name">Nome do Grupo / Comitiva</label>
              <input
                id="party-name"
                type="text"
                className="input-field"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            <div className="form-section">
              <h4>Selecione os Combatentes ({selectedCharIds.length} selecionados)</h4>

              {characters.length === 0 ? (
                <div className="empty-subtext" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
                  <span>Nenhum personagem disponível. Crie um personagem na aba <strong>Personagens</strong> primeiro.</span>
                  <button type="button" className="btn-secondary btn-sm" onClick={() => onNavigateToTab('characters')}>
                    Ir para Criação de Personagens
                  </button>
                </div>
              ) : (
                <div className="party-member-selector">
                  {characters.map((char) => {
                    const isSelected = selectedCharIds.includes(char.id)
                    const inCombat = Boolean(char.active_combat_id)

                    return (
                      <div
                        key={char.id}
                        className={`member-select-card ${isSelected ? 'selected' : ''} ${
                          inCombat ? 'in-combat' : ''
                        }`}
                        onClick={() => !inCombat && toggleSelectChar(char.id)}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => !inCombat && toggleSelectChar(char.id)}
                          disabled={inCombat}
                        />
                        <div className="member-info">
                          <strong>{char.name}</strong>
                          <span className="member-sub">
                            PV {char.current_hp}/{char.max_hp} • CA {char.armor_class}
                            {inCombat ? ' • (Em combate ativo)' : ''}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {error && (
              <div className="error-alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="success-alert">
                <Check size={16} />
                <span>{successMsg}</span>
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading || characters.length === 0}
            >
              <Plus size={18} />
              <span>{loading ? 'Registrando Grupo...' : 'Criar Grupo no Servidor'}</span>
            </button>
          </form>
        </div>

        {/* Lista de Grupos Existentes */}
        <div className="panel list-panel">
          <div className="panel-title">
            <Users size={20} className="gold-icon" />
            <h3>Grupos Registrados ({parties.length})</h3>
          </div>

          {parties.length === 0 ? (
            <div className="empty-state">
              <p>Nenhum grupo formado ainda.</p>
              <p className="empty-subtext">Monte uma comitiva ao lado para iniciar encontros de treino.</p>
            </div>
          ) : (
            <div className="parties-list">
              {parties.map((party) => {
                const partyMembers = characters.filter((c) =>
                  party.character_ids.includes(c.id),
                )

                return (
                  <div key={party.id} className="party-card">
                    <div className="party-card-header">
                      <div>
                        <h4 className="party-title">{party.name}</h4>
                        <span className="party-id-sub">ID: #{party.id.slice(0, 8)}</span>
                      </div>

                      <button
                        type="button"
                        className="btn-accent"
                        onClick={() => handleStartCombat(party.id)}
                        disabled={startingCombatId === party.id}
                        title="Iniciar encontro na arena 2.5D contra o Goblin de Treino"
                      >
                        <Swords size={16} />
                        <span>
                          {startingCombatId === party.id ? 'Iniciando...' : 'Iniciar Batalha 2.5D'}
                        </span>
                      </button>
                    </div>

                    <div className="party-members-list">
                      <span className="detail-label">Membros ({party.character_ids.length})</span>
                      <div className="member-chips">
                        {partyMembers.map((m) => (
                          <div key={m.id} className="member-chip">
                            <Shield size={12} />
                            <span>{m.name} (PV {m.current_hp}/{m.max_hp})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import React, { useState } from 'react'
import { Shield, Sword, Heart, PlusCircle, RefreshCw, AlertCircle, Sparkles, Check } from 'lucide-react'
import type { CharacterCreate, CharacterOut, FightingStyle, ArmorType } from '../types/api'
import { api, ApiClientError } from '../services/api'

interface CharacterCreatorProps {
  characters: CharacterOut[]
  onCharacterCreated: (char: CharacterOut) => void
  onCharacterUpdated: (char: CharacterOut) => void
  onSelectForParty?: (charId: string) => void
}

function calcMod(score: number): number {
  return Math.floor((score - 10) / 2)
}

function formatMod(mod: number): string {
  return mod >= 0 ? `+${mod}` : `${mod}`
}

export const CharacterCreator: React.FC<CharacterCreatorProps> = ({
  characters,
  onCharacterCreated,
  onCharacterUpdated,
}) => {
  const [name, setName] = useState('Aria Valebruma')
  const [strength, setStrength] = useState(16)
  const [dexterity, setDexterity] = useState(14)
  const [constitution, setConstitution] = useState(16)
  const [intelligence, setIntelligence] = useState(10)
  const [wisdom, setWisdom] = useState(12)
  const [charisma, setCharisma] = useState(8)

  const [armor, setArmor] = useState<ArmorType>('chain_mail')
  const [shield, setShield] = useState(true)
  const [fightingStyle, setFightingStyle] = useState<FightingStyle>('defense')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [restingId, setRestingId] = useState<string | null>(null)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Informe um nome para o guerreiro.')
      return
    }

    setLoading(true)
    setError(null)
    setSuccessMsg(null)

    const payload: CharacterCreate = {
      name: name.trim(),
      rule_set: 'dnd5e-2014',
      class_id: 'fighter',
      level: 1,
      abilities: {
        strength,
        dexterity,
        constitution,
        intelligence,
        wisdom,
        charisma,
      },
      equipment: {
        armor,
        shield,
        weapon: 'longsword',
      },
      fighting_style: fightingStyle,
    }

    try {
      const created = await api.createCharacter(payload)
      onCharacterCreated(created)
      setSuccessMsg(`Personagem ${created.name} forjado com sucesso! PV: ${created.max_hp}, CA: ${created.armor_class}`)
      setName(`Guerreiro de Treino ${characters.length + 2}`)
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(`Erro da API (${err.code}): ${err.message}`)
      } else {
        setError(err.message || 'Erro ao criar personagem')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRest = async (charId: string) => {
    setRestingId(charId)
    setError(null)
    try {
      const rested = await api.restCharacter(charId)
      onCharacterUpdated(rested)
      setSuccessMsg(`${rested.name} descansou e recuperou seus Pontos de Vida (${rested.current_hp}/${rested.max_hp}).`)
    } catch (err: any) {
      setError(`Falha ao descansar: ${err.message}`)
    } finally {
      setRestingId(null)
    }
  }

  // Estimativa visual prévia (o cálculo oficial autoritativo é retornado pela API Python)
  const estimatedHp = 10 + calcMod(constitution)
  let estimatedAc = 10 + calcMod(dexterity)
  if (armor === 'chain_mail') estimatedAc = 16
  else if (armor === 'leather') estimatedAc = 11 + calcMod(dexterity)
  if (shield) estimatedAc += 2
  if (fightingStyle === 'defense' && armor !== 'none') estimatedAc += 1

  return (
    <div className="tab-container">
      <div className="section-header">
        <h2>Forja de Personagens & Fichas</h2>
        <p className="section-desc">
          Crie perfis mecânicos calculados autoritativamente pelo motor Python sob regras D&D 5e (SRD 2014).
        </p>
      </div>

      <div className="creator-grid">
        {/* Formulário de Criação */}
        <div className="panel form-panel">
          <div className="panel-title">
            <Sparkles size={20} className="gold-icon" />
            <h3>Novo Guerreiro (Nível 1)</h3>
          </div>

          <form onSubmit={handleCreate} className="char-form">
            <div className="form-group">
              <label htmlFor="char-name">Nome do Combatente</label>
              <input
                id="char-name"
                type="text"
                className="input-field"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            <div className="form-row badges-row">
              <span className="badge-tag">Regras: D&D 5e (2014)</span>
              <span className="badge-tag">Classe: Guerreiro</span>
              <span className="badge-tag">Nível: 1</span>
            </div>

            {/* Atributos */}
            <div className="form-section">
              <h4>Atributos Básicos (3 a 20)</h4>
              <div className="abilities-grid">
                <div className="ability-box">
                  <span className="ability-label">FOR</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={strength}
                    onChange={(e) => setStrength(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(strength))}</span>
                </div>

                <div className="ability-box">
                  <span className="ability-label">DES</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={dexterity}
                    onChange={(e) => setDexterity(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(dexterity))}</span>
                </div>

                <div className="ability-box">
                  <span className="ability-label">CON</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={constitution}
                    onChange={(e) => setConstitution(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(constitution))}</span>
                </div>

                <div className="ability-box">
                  <span className="ability-label">INT</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={intelligence}
                    onChange={(e) => setIntelligence(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(intelligence))}</span>
                </div>

                <div className="ability-box">
                  <span className="ability-label">SAB</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={wisdom}
                    onChange={(e) => setWisdom(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(wisdom))}</span>
                </div>

                <div className="ability-box">
                  <span className="ability-label">CAR</span>
                  <input
                    type="number"
                    min={3}
                    max={20}
                    value={charisma}
                    onChange={(e) => setCharisma(Number(e.target.value))}
                  />
                  <span className="ability-mod">{formatMod(calcMod(charisma))}</span>
                </div>
              </div>
            </div>

            {/* Equipamento e Estilo */}
            <div className="form-section">
              <h4>Equipamento & Estilo de Luta</h4>
              <div className="form-row">
                <div className="form-group flex-1">
                  <label htmlFor="armor-select">Armadura</label>
                  <select
                    id="armor-select"
                    className="select-field"
                    value={armor}
                    onChange={(e) => setArmor(e.target.value as ArmorType)}
                  >
                    <option value="chain_mail">Cota de Malha (CA 16 fixa)</option>
                    <option value="leather">Couro (CA 11 + mod DES)</option>
                    <option value="none">Sem Armadura (CA 10 + mod DES)</option>
                  </select>
                </div>

                <div className="form-group flex-1">
                  <label htmlFor="style-select">Estilo de Luta</label>
                  <select
                    id="style-select"
                    className="select-field"
                    value={fightingStyle}
                    onChange={(e) => setFightingStyle(e.target.value as FightingStyle)}
                  >
                    <option value="defense">Defesa (+1 CA com armadura)</option>
                    <option value="dueling">Duelismo (+2 dano de espada)</option>
                  </select>
                </div>
              </div>

              <div className="form-row checkbox-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={shield}
                    onChange={(e) => setShield(e.target.checked)}
                  />
                  <span>Empunhar Escudo (+2 na CA)</span>
                </label>

                <span className="fixed-weapon-note">
                  Arma: <strong>Espada Longa (1 mão, 1d8 cortante)</strong>
                </span>
              </div>
            </div>

            {/* Estimativa pré-envio */}
            <div className="stat-preview-card">
              <div className="stat-preview-item">
                <Heart size={16} className="hp-icon" />
                <span>PV Estimado: <strong>{estimatedHp}</strong> (10 + CON)</span>
              </div>
              <div className="stat-preview-item">
                <Shield size={16} className="ac-icon" />
                <span>CA Estimada: <strong>{estimatedAc}</strong></span>
              </div>
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

            <button type="submit" className="btn-primary" disabled={loading}>
              <PlusCircle size={18} />
              <span>{loading ? 'Calculando no Backend...' : 'Salvar Ficha no Python'}</span>
            </button>
          </form>
        </div>

        {/* Lista de Personagens Criados */}
        <div className="panel list-panel">
          <div className="panel-title">
            <Shield size={20} className="gold-icon" />
            <h3>Fichas Salvas no Banco ({characters.length})</h3>
          </div>

          {characters.length === 0 ? (
            <div className="empty-state">
              <p>Nenhum personagem registrado no banco local.</p>
              <p className="empty-subtext">Preencha os atributos à esquerda para forjar o primeiro guerreiro.</p>
            </div>
          ) : (
            <div className="characters-cards-list">
              {characters.map((char) => (
                <div key={char.id} className="character-card">
                  <div className="char-card-header">
                    <div>
                      <h4 className="char-name">{char.name}</h4>
                      <span className="char-sub">
                        Guerreiro Nvl 1 • Estilo {char.fighting_style === 'defense' ? 'Defesa' : 'Duelismo'}
                      </span>
                    </div>

                    <div className="char-vitals">
                      <div className="vital-badge hp-badge" title="Pontos de Vida">
                        <Heart size={14} />
                        <span>{char.current_hp} / {char.max_hp} PV</span>
                      </div>
                      <div className="vital-badge ac-badge" title="Classe de Armadura">
                        <Shield size={14} />
                        <span>CA {char.armor_class}</span>
                      </div>
                    </div>
                  </div>

                  <div className="char-details-grid">
                    <div>
                      <span className="detail-label">Atributos</span>
                      <div className="mini-stats">
                        <span>FOR {char.abilities.strength} ({formatMod(char.ability_modifiers.strength)})</span>
                        <span>DES {char.abilities.dexterity} ({formatMod(char.ability_modifiers.dexterity)})</span>
                        <span>CON {char.abilities.constitution} ({formatMod(char.ability_modifiers.constitution)})</span>
                        <span>INT {char.abilities.intelligence} ({formatMod(char.ability_modifiers.intelligence)})</span>
                        <span>SAB {char.abilities.wisdom} ({formatMod(char.ability_modifiers.wisdom)})</span>
                        <span>CAR {char.abilities.charisma} ({formatMod(char.ability_modifiers.charisma)})</span>
                      </div>
                    </div>

                    <div>
                      <span className="detail-label">Ataque Calculado</span>
                      <div className="attack-info">
                        {char.attacks.map((atk) => (
                          <span key={atk.id} className="attack-tag">
                            <Sword size={12} />
                            {atk.name}: {formatMod(atk.attack_bonus)} p/ acertar, {atk.damage_expression} {atk.damage_type}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="char-card-footer">
                    <span className="char-scope-tag">
                      {char.active_combat_id ? (
                        <span className="status-in-combat">⚔️ Vinculado ao combate #{char.active_combat_id.slice(0, 8)}</span>
                      ) : (
                        <span className="status-ready">✓ Pronto para nova batalha</span>
                      )}
                    </span>

                    <button
                      type="button"
                      className="btn-secondary btn-sm"
                      onClick={() => handleRest(char.id)}
                      disabled={restingId === char.id || Boolean(char.active_combat_id)}
                      title={
                        char.active_combat_id
                          ? 'Não é permitido descansar durante um combate ativo'
                          : 'Recuperar todos os Pontos de Vida para nova sessão de treino'
                      }
                    >
                      <RefreshCw size={14} className={restingId === char.id ? 'spin' : ''} />
                      <span>Descanso de Treino</span>
                    </button>
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

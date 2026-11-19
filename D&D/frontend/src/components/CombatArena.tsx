import React, { useState, useEffect, useRef } from 'react'
import {
  Swords,
  Shield,
  Skull,
  AlertTriangle,
  Play,
  CheckCircle2,
  Clock,
  Sparkles,
  Plus,
  Zap,
  User,
  ChevronDown,
  ChevronUp,
  Volume2,
  VolumeX,
  Map,
} from 'lucide-react'
import type { CombatOut, PartyOut, EventOut, AttackResolvedPayload } from '../types/api'
import { api, ApiClientError } from '../services/api'
import { FighterPortrait, GoblinPortrait } from './Portraits'
import { sfx } from '../utils/audio'

export interface BattleMapScenario {
  id: string
  name: string
  image: string
  audio: string
  icon: string
}

export const BATTLE_MAPS: BattleMapScenario[] = [
  { id: 'waterfall', name: 'Cachoeira na Estrada', image: '/maps/roadside waterfall.png', audio: '/audio/waterfall.mp3', icon: '🌊' },
  { id: 'cave', name: 'Caverna Nevada', image: '/maps/snowy cave.png', audio: '/audio/blizzard.mp3', icon: '🏔️' },
  { id: 'ship', name: 'Navio em Alto Mar', image: '/maps/ship at sea.webp', audio: '/audio/ship at sea.mp3', icon: '⛵' },
  { id: 'swamp', name: 'Pântano Sinistro', image: '/maps/swamp.webp', audio: '/audio/bubbling mud.mp3', icon: '🌲' },
  { id: 'desert', name: 'Tempestade de Areia', image: '/maps/sandstorm.webp', audio: '/audio/wind.mp3', icon: '🏜️' },
  { id: 'stone', name: 'Arena Imperial', image: '', audio: '/audio/fire ambience.mp3', icon: '⚔️' },
]

interface CombatArenaProps {
  combat: CombatOut | null
  parties: PartyOut[]
  onCombatUpdated: (combat: CombatOut) => void
  onStartNewCombat: (combat: CombatOut) => void
  reducedMotion: boolean
  soundEnabled: boolean
  onNavigateToTab: (tab: any) => void
}

interface FloatingText {
  id: string
  targetId: string
  text: string
  type: 'hit' | 'crit' | 'miss' | 'info'
}

export const CombatArena: React.FC<CombatArenaProps> = ({
  combat,
  parties,
  onCombatUpdated,
  onStartNewCombat,
  reducedMotion,
  soundEnabled,
  onNavigateToTab,
}) => {
  // Estados de ação e combate
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null)
  const [selectedAttackId, setSelectedAttackId] = useState<string>('longsword')
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState<EventOut[]>([])
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [floatingTexts, setFloatingTexts] = useState<FloatingText[]>([])
  const [showLogDrawer, setShowLogDrawer] = useState(true)

  // Mapas e Áudio Ambiente (Dungeoneer Fusion)
  const [selectedScenario, setSelectedScenario] = useState<BattleMapScenario>(BATTLE_MAPS[0])
  const [ambientActive, setAmbientActive] = useState<boolean>(false)

  // Estados do Criador de Batalhas do Mestre
  const [showNewBattleModal, setShowNewBattleModal] = useState(false)
  const [selectedPartyId, setSelectedPartyId] = useState<string>(parties[0]?.id || '')
  const [monsterCount, setMonsterCount] = useState<number>(1)
  const [creatingBattle, setCreatingBattle] = useState(false)

  // Estados de animação
  const [animatingActorId, setAnimatingActorId] = useState<string | null>(null)
  const [animatingTargetId, setAnimatingTargetId] = useState<string | null>(null)

  const logEndRef = useRef<HTMLDivElement>(null)
  const attackHandlerRef = useRef<(() => void) | null>(null)
  const endTurnHandlerRef = useRef<(() => void) | null>(null)

  // Variáveis derivadas (sempre no topo para evitar Hook rules violation)
  const currentActor = combat?.combatants.find((c) => c.id === combat.current_actor_id) ?? null
  const isCombatActive = combat?.status === 'active'
  const isPartyActor = currentActor?.team === 'party'
  const isEnemyActor = currentActor?.team === 'enemy'
  const partyCombatants = combat?.combatants.filter((c) => c.team === 'party') ?? []
  const enemyCombatants = combat?.combatants.filter((c) => c.team === 'enemy') ?? []

  // Sincroniza party selecionada padrão
  useEffect(() => {
    if (parties.length > 0 && !selectedPartyId) {
      setSelectedPartyId(parties[0].id)
    }
  }, [parties, selectedPartyId])

  // Desativa áudio ambiente ao desmontar
  useEffect(() => {
    return () => {
      sfx.stopAmbience()
    }
  }, [])

  // Carrega histórico de eventos quando o combate for selecionado ou mudar
  useEffect(() => {
    if (!combat) return
    let isMounted = true

    api
      .getEvents(combat.id, 0)
      .then((evList) => {
        if (isMounted) setEvents(evList)
      })
      .catch((err) => {
        console.error('Falha ao carregar eventos:', err)
      })

    // Pré-seleciona um alvo e ataque válidos
    if (currentActor) {
      const opposingTeam = currentActor.team === 'party' ? 'enemy' : 'party'
      const firstValidTarget = combat.combatants.find(
        (c) => c.team === opposingTeam && c.current_hp > 0,
      )
      if (firstValidTarget) {
        setSelectedTargetId(firstValidTarget.id)
      }

      if (currentActor.attacks.length > 0) {
        setSelectedAttackId(currentActor.attacks[0].id)
      }
    }

    return () => {
      isMounted = false
    }
  }, [combat?.id, combat?.round, combat?.current_actor_id])

  // Rola log para o final
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  // Atalhos de teclado
  useEffect(() => {
    if (!combat) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (loading || !isCombatActive) return

      if (e.key === 'a' || e.key === 'A') {
        if (currentActor?.action_available && selectedTargetId) {
          attackHandlerRef.current?.()
        }
      }
      if (e.key === 'e' || e.key === 'E') {
        endTurnHandlerRef.current?.()
      }
      const num = parseInt(e.key, 10)
      const validTargets = combat.combatants.filter((c) => c.team !== currentActor?.team && c.current_hp > 0)
      if (num >= 1 && num <= validTargets.length) {
        setSelectedTargetId(validTargets[num - 1].id)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [combat, loading, isCombatActive, currentActor, selectedTargetId])

  // Dispara texto flutuante
  const spawnFloatingText = (
    targetId: string,
    text: string,
    type: 'hit' | 'crit' | 'miss' | 'info',
  ) => {
    const id = `${Date.now()}-${Math.random()}`
    setFloatingTexts((prev) => [...prev, { id, targetId, text, type }])
    setTimeout(() => {
      setFloatingTexts((prev) => prev.filter((item) => item.id !== id))
    }, 1800)
  }

  // Executa ataque (seja de Herói ou de Monstro controlado pelo Mestre)
  const handleAttack = async () => {
    if (!combat || !currentActor || !selectedTargetId) {
      setErrorMsg('Selecione um alvo válido para atacar.')
      return
    }

    setLoading(true)
    setErrorMsg(null)

    try {
      const result = await api.executeAction(combat.id, {
        type: 'attack',
        actor_id: currentActor.id,
        target_id: selectedTargetId,
        attack_id: selectedAttackId as any,
        expected_version: combat.version,
      })

      const attackEvent = result.events.find((e) => e.type === 'attack_resolved')
      if (attackEvent && attackEvent.payload) {
        const payload: AttackResolvedPayload = attackEvent.payload

        setAnimatingActorId(currentActor.id)
        setAnimatingTargetId(selectedTargetId)

        if (payload.critical) {
          if (soundEnabled) sfx.playCriticalHit()
          spawnFloatingText(selectedTargetId, `CRÍTICO! -${payload.damage} PV`, 'crit')
        } else if (payload.hit) {
          if (soundEnabled) sfx.playSwordSlash()
          spawnFloatingText(selectedTargetId, `ACERTOU! -${payload.damage} PV`, 'hit')
        } else {
          if (soundEnabled) sfx.playShieldBlock()
          spawnFloatingText(selectedTargetId, `ERROU!`, 'miss')
        }

        setTimeout(() => {
          setAnimatingActorId(null)
          setAnimatingTargetId(null)
        }, 700)
      }

      if (result.combat.status === 'completed' && soundEnabled) {
        sfx.playVictoryFanfare()
      }

      onCombatUpdated(result.combat)
      setEvents((prev) => [...prev, ...result.events])
    } catch (err: any) {
      handleActionError(err)
    } finally {
      setLoading(false)
    }
  }
  attackHandlerRef.current = handleAttack

  // Encerrar turno
  const handleEndTurn = async () => {
    if (!combat || !currentActor) return

    setLoading(true)
    setErrorMsg(null)

    try {
      const result = await api.executeAction(combat.id, {
        type: 'end_turn',
        actor_id: currentActor.id,
        expected_version: combat.version,
      })

      onCombatUpdated(result.combat)
      setEvents((prev) => [...prev, ...result.events])
    } catch (err: any) {
      handleActionError(err)
    } finally {
      setLoading(false)
    }
  }
  endTurnHandlerRef.current = handleEndTurn

  // Ação Rápida da IA para o Mestre
  const handleMonsterQuickAction = () => {
    if (!isEnemyActor || !currentActor?.action_available) return
    const livingHeroes = partyCombatants.filter((c) => c.current_hp > 0)
    if (livingHeroes.length === 0) return
    const target = [...livingHeroes].sort((a, b) => a.current_hp - b.current_hp)[0]
    setSelectedTargetId(target.id)
    if (currentActor.attacks.length > 0) {
      setSelectedAttackId(currentActor.attacks[0].id)
    }
    setTimeout(() => {
      handleAttack()
    }, 150)
  }

  // Criação de Batalha do Mestre
  const handleCreateEncounter = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedPartyId) {
      setErrorMsg('Selecione uma comitiva para o combate.')
      return
    }

    setCreatingBattle(true)
    setErrorMsg(null)

    try {
      const monsterIds = Array(monsterCount).fill('training-goblin')
      const newCombat = await api.createCombat({
        party_id: selectedPartyId,
        monster_ids: monsterIds,
        rule_set: 'dnd5e-2014',
      })
      onStartNewCombat(newCombat)
      setShowNewBattleModal(false)
    } catch (err: any) {
      setErrorMsg(err.message || 'Falha ao criar encontro')
    } finally {
      setCreatingBattle(false)
    }
  }

  // Tratamento do erro 409
  const handleActionError = async (err: any) => {
    if (!combat) return
    if (err instanceof ApiClientError && err.status === 409) {
      setErrorMsg('Sincronizando estado mais recente com o servidor...')
      try {
        const fresh = await api.getCombat(combat.id)
        const freshEvents = await api.getEvents(combat.id, 0)
        onCombatUpdated(fresh)
        setEvents(freshEvents)
        setErrorMsg(null)
      } catch (syncErr: any) {
        setErrorMsg(`Falha na sincronização: ${syncErr.message}`)
      }
    } else {
      setErrorMsg(err.message || 'Erro ao processar ação de combate')
    }
  }

  // ==================== TELA SE NÃO HOUVER COMBATE ATIVO ====================
  if (!combat) {
    return (
      <div className="tab-container empty-arena-container">
        <div className="dm-forge-card">
          <div className="forge-header">
            <Swords size={38} className="gold-icon" />
            <div>
              <h3>Mesa do Mestre: Criador de Batalhas</h3>
              <p className="forge-sub">
                Monte um encontro tático escolhendo o cenário, a comitiva de aventureiros e o número de monstros.
              </p>
            </div>
          </div>

          <form onSubmit={handleCreateEncounter} className="dm-forge-form">
            <div className="form-group">
              <label>Escolha o Cenário / Mapa de Batalha:</label>
              <select
                className="select-field"
                value={selectedScenario.id}
                onChange={(e) => {
                  const found = BATTLE_MAPS.find((m) => m.id === e.target.value) || BATTLE_MAPS[0]
                  setSelectedScenario(found)
                }}
              >
                {BATTLE_MAPS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.icon} {m.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Escolha a Comitiva de Heróis:</label>
              {parties.length === 0 ? (
                <div className="forge-notice">
                  Nenhum grupo formado. Crie primeiro uma comitiva na aba <strong>Comitivas</strong>.
                </div>
              ) : (
                <select
                  className="select-field"
                  value={selectedPartyId}
                  onChange={(e) => setSelectedPartyId(e.target.value)}
                  required
                >
                  {parties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.character_ids.length} membro(s))
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group">
              <label>Quantidade de Monstros (Goblins de Treino):</label>
              <div className="monster-count-selector">
                {[1, 2, 3, 4, 6].map((num) => (
                  <button
                    key={num}
                    type="button"
                    className={`monster-qty-btn ${monsterCount === num ? 'active' : ''}`}
                    onClick={() => setMonsterCount(num)}
                  >
                    <Skull size={14} />
                    <span>{num} {num === 1 ? 'Goblin' : 'Goblins'}</span>
                  </button>
                ))}
              </div>
            </div>

            {errorMsg && (
              <div className="error-alert">
                <AlertTriangle size={16} />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="forge-actions">
              <button
                type="submit"
                className="btn-primary btn-large"
                disabled={creatingBattle || parties.length === 0}
              >
                <Swords size={20} />
                <span>{creatingBattle ? 'Invocando Criaturas...' : '⚔️ Iniciar Batalha na Arena'}</span>
              </button>

              <button
                type="button"
                className="btn-secondary"
                onClick={() => onNavigateToTab('saved')}
              >
                Ver Batalhas Salvas
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  // ==================== ARENA ATIVA ====================
  return (
    <div className="tab-container combat-tab-container">
      {/* Barra de Controle Superior */}
      <div className="combat-top-bar">
        <div className="combat-meta">
          <span className="badge-tag round-badge">Rodada {combat.round}</span>
          <span className={`badge-tag status-badge ${combat.status}`}>
            {combat.status === 'active' ? '⚔️ Batalha em Andamento' : '✓ Concluído'}
          </span>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={() => setShowNewBattleModal(!showNewBattleModal)}
            title="Criar nova batalha"
          >
            <Plus size={14} />
            <span>Nova Batalha</span>
          </button>
        </div>

        {/* Ferramentas de Mapa e Som Ambiente (Fusão Dungeoneer) */}
        <div className="scenario-top-tools">
          <div className="scenario-select-wrapper">
            <Map size={14} className="gold-icon" />
            <select
              className="select-field scenario-dropdown"
              value={selectedScenario.id}
              onChange={(e) => {
                const found = BATTLE_MAPS.find((m) => m.id === e.target.value) || BATTLE_MAPS[0]
                setSelectedScenario(found)
                if (ambientActive) {
                  sfx.playAmbience(found.audio)
                }
              }}
              title="Trocar cenário e mapa tático da arena"
            >
              {BATTLE_MAPS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.icon} {m.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className={`btn-secondary btn-sm ${ambientActive ? 'active-ambience' : ''}`}
            onClick={() => {
              if (ambientActive) {
                sfx.stopAmbience()
                setAmbientActive(false)
              } else {
                sfx.playAmbience(selectedScenario.audio)
                setAmbientActive(true)
              }
            }}
            title={ambientActive ? 'Silenciar som ambiente' : 'Tocar som ambiente deste cenário'}
          >
            {ambientActive ? <Volume2 size={14} className="pulse" /> : <VolumeX size={14} />}
            <span>{ambientActive ? 'Ambiente Ativo' : 'Tocar Ambiente'}</span>
          </button>
        </div>

        {/* Trilha de Iniciativa */}
        <div className="initiative-track">
          <span className="track-label">Iniciativa:</span>
          {combat.combatants.map((c, idx) => {
            const isTurn = c.id === combat.current_actor_id
            const isDead = c.current_hp <= 0
            return (
              <div
                key={c.id}
                className={`init-token ${isTurn ? 'active-turn' : ''} ${isDead ? 'dead-token' : ''} ${c.team}`}
                title={`${c.name} (Iniciativa ${c.initiative})`}
              >
                <span className="init-order">{idx + 1}</span>
                <span className="init-name">{c.name.split(' ')[0]}</span>
                <span className="init-val">({c.initiative})</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Modal de Criação Rápida de Nova Batalha pelo Mestre */}
      {showNewBattleModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <div className="modal-title-row">
                <Swords size={22} className="gold-icon" />
                <h3>Forjar Nova Batalha do Mestre</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowNewBattleModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateEncounter} className="modal-body">
              <div className="form-group">
                <label>Cenário / Mapa de Batalha:</label>
                <select
                  className="select-field"
                  value={selectedScenario.id}
                  onChange={(e) => {
                    const found = BATTLE_MAPS.find((m) => m.id === e.target.value) || BATTLE_MAPS[0]
                    setSelectedScenario(found)
                  }}
                >
                  {BATTLE_MAPS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.icon} {m.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Comitiva:</label>
                <select
                  className="select-field"
                  value={selectedPartyId}
                  onChange={(e) => setSelectedPartyId(e.target.value)}
                  required
                >
                  {parties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.character_ids.length} membro(s))
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Quantidade de Monstros:</label>
                <div className="monster-count-selector">
                  {[1, 2, 3, 4, 6].map((num) => (
                    <button
                      key={num}
                      type="button"
                      className={`monster-qty-btn ${monsterCount === num ? 'active' : ''}`}
                      onClick={() => setMonsterCount(num)}
                    >
                      <Skull size={14} />
                      <span>{num} {num === 1 ? 'Monstro' : 'Monstros'}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={creatingBattle}
                >
                  <Swords size={18} />
                  <span>{creatingBattle ? 'Iniciando...' : 'Entrar na Arena'}</span>
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowNewBattleModal(false)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Desfecho da Batalha */}
      {!isCombatActive && (
        <div className={`combat-outcome-banner ${combat.winner}`}>
          <div className="outcome-content">
            <Sparkles size={28} />
            <div>
              <h3>
                {combat.winner === 'party'
                  ? 'Vitória da Comitiva! Os monstros foram derrotados.'
                  : 'Os heróis foram derrotados pelo poder dos monstros.'}
              </h3>
              <p>Os pontos de vida e os eventos foram salvos no banco de dados.</p>
            </div>
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={() => setShowNewBattleModal(true)}
          >
            <Swords size={16} />
            <span>Criar Nova Batalha</span>
          </button>
        </div>
      )}

      {/* Arena 2.5D com Projeção Perspectiva e Mapa Real (Fusão Dungeoneer) */}
      <div className={`arena-viewport ${reducedMotion ? 'reduced-motion' : ''}`}>
        <div className="arena-3d-stage">
          {/* Piso Tático com Mapa de Batalha Real */}
          <div
            className="arena-floor-grid"
            style={
              selectedScenario.image
                ? {
                    backgroundImage: `linear-gradient(rgba(10, 13, 20, 0.35), rgba(10, 13, 20, 0.55)), url("${selectedScenario.image}")`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    border: '2px solid rgba(212, 175, 55, 0.5)',
                    boxShadow: '0 0 35px rgba(0, 0, 0, 0.9), inset 0 0 60px rgba(0, 0, 0, 0.9)',
                  }
                : {}
            }
          ></div>

          {/* Lado da Comitiva */}
          <div className="arena-side party-side">
            <div className="side-banner party-banner">
              <Shield size={16} />
              <span>Comitiva ({partyCombatants.length})</span>
            </div>

            <div className="pedestals-container">
              {partyCombatants.map((c) => {
                const isActor = c.id === combat.current_actor_id
                const isSelected = c.id === selectedTargetId
                const isDead = c.current_hp <= 0

                return (
                  <div
                    key={c.id}
                    className={`combatant-pod party-pod ${isActor ? 'active-actor' : ''} ${
                      isSelected ? 'targeted' : ''
                    }`}
                    onClick={() => isEnemyActor && !isDead && setSelectedTargetId(c.id)}
                    title={isEnemyActor ? `Mestre: clique para selecionar ${c.name} como alvo do monstro` : undefined}
                  >
                    <div className="pedestal-stone"></div>

                    {floatingTexts
                      .filter((f) => f.targetId === c.id)
                      .map((f) => (
                        <div key={f.id} className={`floating-combat-text ${f.type}`}>
                          {f.text}
                        </div>
                      ))}

                    <FighterPortrait
                      name={c.name}
                      team="party"
                      isActor={isActor}
                      isSelectedTarget={isSelected}
                      isAttacking={animatingActorId === c.id}
                      isDamaged={animatingTargetId === c.id}
                      isDefeated={isDead}
                      reducedMotion={reducedMotion}
                      size={150}
                    />

                    <div className="combatant-hud">
                      <div className="hp-bar-container">
                        <div
                          className="hp-bar-fill party"
                          style={{
                            width: `${Math.max(0, Math.min(100, (c.current_hp / c.max_hp) * 100))}%`,
                          }}
                        ></div>
                        <span className="hp-text">
                          {c.current_hp} / {c.max_hp} PV
                        </span>
                      </div>
                      <div className="hud-badges">
                        <span className="hud-badge ac-badge">
                          <Shield size={11} /> CA {c.armor_class}
                        </span>
                        {isActor && <span className="hud-badge turn-badge">TURNO ATUAL</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="arena-clash-divider">
            <Swords size={28} className="gold-icon pulse" />
          </div>

          {/* Lado dos Monstros */}
          <div className="arena-side enemy-side">
            <div className="side-banner enemy-banner">
              <Skull size={16} />
              <span>Monstros ({enemyCombatants.length})</span>
            </div>

            <div className="pedestals-container">
              {enemyCombatants.map((c, idx) => {
                const isActor = c.id === combat.current_actor_id
                const isSelected = c.id === selectedTargetId
                const isDead = c.current_hp <= 0

                return (
                  <div
                    key={c.id}
                    className={`combatant-pod enemy-pod ${isActor ? 'active-actor' : ''} ${
                      isSelected ? 'targeted' : ''
                    }`}
                    onClick={() => isPartyActor && !isDead && setSelectedTargetId(c.id)}
                    title={isPartyActor ? `Clique para selecionar como alvo (ou tecla ${idx + 1})` : undefined}
                  >
                    <div className="pedestal-stone enemy-pedestal"></div>

                    {floatingTexts
                      .filter((f) => f.targetId === c.id)
                      .map((f) => (
                        <div key={f.id} className={`floating-combat-text ${f.type}`}>
                          {f.text}
                        </div>
                      ))}

                    <GoblinPortrait
                      name={c.name}
                      team="enemy"
                      isActor={isActor}
                      isSelectedTarget={isSelected}
                      isAttacking={animatingActorId === c.id}
                      isDamaged={animatingTargetId === c.id}
                      isDefeated={isDead}
                      reducedMotion={reducedMotion}
                      size={150}
                    />

                    <div className="combatant-hud">
                      <div className="hp-bar-container">
                        <div
                          className="hp-bar-fill enemy"
                          style={{
                            width: `${Math.max(0, Math.min(100, (c.current_hp / c.max_hp) * 100))}%`,
                          }}
                        ></div>
                        <span className="hp-text">
                          {c.current_hp} / {c.max_hp} PV
                        </span>
                      </div>
                      <div className="hud-badges">
                        <span className="hud-badge ac-badge">
                          <Shield size={11} /> CA {c.armor_class}
                        </span>
                        {isActor && <span className="hud-badge turn-badge">TURNO ATUAL</span>}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ================= PAINEL DE CONTROLE DE AÇÃO ================= */}
      <div className="combat-bottom-grid">
        {/* Painel de Turno: Diferenciação clara Herói vs Mestre (Monstro) */}
        <div className={`panel actions-panel ${isEnemyActor ? 'dm-monster-control-panel' : ''}`}>
          <div className="panel-title">
            {isEnemyActor ? (
              <>
                <Skull size={20} className="crimson-icon" />
                <h3 className="text-crimson">
                  Mestre: Controlando {currentActor?.name || 'Monstro'}
                </h3>
              </>
            ) : (
              <>
                <User size={20} className="gold-icon" />
                <h3>
                  Turno do Herói: {currentActor?.name || 'Aguardando'}
                </h3>
              </>
            )}
          </div>

          {isCombatActive && currentActor ? (
            <div className="actions-body">
              <div className={`current-turn-info ${isEnemyActor ? 'dm-turn-info' : ''}`}>
                <div className="turn-status-row">
                  <span>
                    Combatente ativo: <strong>{currentActor.name}</strong>
                  </span>
                  <span className="badge-tag">
                    {isEnemyActor ? '💀 Mestre controla' : '🛡️ Comitiva'}
                  </span>
                </div>
                <div className="action-availability">
                  {currentActor.action_available ? (
                    <span className="text-success">Ação disponível (1 ataque nesta rodada)</span>
                  ) : (
                    <span className="text-warning">Ação executada nesta rodada</span>
                  )}
                </div>
              </div>

              {/* Seleção do Ataque */}
              <div className="form-group">
                <label>{isEnemyActor ? 'Ataque do Monstro:' : 'Ataque do Herói:'}</label>
                <div className="attack-selection-chips">
                  {currentActor.attacks.map((atk) => (
                    <button
                      key={atk.id}
                      type="button"
                      className={`attack-chip ${selectedAttackId === atk.id ? 'active' : ''}`}
                      onClick={() => setSelectedAttackId(atk.id)}
                    >
                      <Swords size={14} />
                      <span>{atk.name}</span>
                      <small className="atk-sub">
                        ({atk.attack_bonus >= 0 ? `+${atk.attack_bonus}` : atk.attack_bonus} acerto • {atk.damage_expression})
                      </small>
                    </button>
                  ))}
                </div>
              </div>

              {/* Seleção do Alvo */}
              <div className="form-group">
                <label>
                  {isEnemyActor
                    ? 'Mestre: Escolha o Herói da Comitiva para Atacar:'
                    : 'Escolha o Monstro Alvo:'}
                </label>
                <select
                  className="select-field"
                  value={selectedTargetId || ''}
                  onChange={(e) => setSelectedTargetId(e.target.value)}
                >
                  <option value="" disabled>
                    -- Selecione o Alvo --
                  </option>
                  {combat.combatants
                    .filter((c) => c.team !== currentActor.team && c.current_hp > 0)
                    .map((target) => (
                      <option key={target.id} value={target.id}>
                        {target.name} (PV: {target.current_hp}/{target.max_hp} • CA: {target.armor_class})
                      </option>
                    ))}
                </select>
              </div>

              {errorMsg && (
                <div className="error-alert">
                  <AlertTriangle size={16} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Botões de Ação */}
              <div className="action-buttons-row">
                <button
                  type="button"
                  className={isEnemyActor ? 'btn-accent' : 'btn-primary'}
                  onClick={handleAttack}
                  disabled={loading || !currentActor.action_available || !selectedTargetId}
                >
                  <Swords size={18} />
                  <span>
                    {isEnemyActor
                      ? 'Executar Ataque do Monstro [A]'
                      : 'Executar Ataque do Herói [A]'}
                  </span>
                </button>

                {isEnemyActor && (
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleMonsterQuickAction}
                    disabled={loading || !currentActor.action_available}
                    title="O Mestre delega o ataque automaticamente ao herói mais fraco"
                  >
                    <Zap size={16} />
                    <span>Ação Rápida (IA)</span>
                  </button>
                )}

                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleEndTurn}
                  disabled={loading}
                >
                  <Play size={16} />
                  <span>Passar Turno [E]</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="combat-finished-state">
              <CheckCircle2 size={32} className="text-success" />
              <p>O combate foi encerrado.</p>
              <button
                type="button"
                className="btn-primary"
                onClick={() => setShowNewBattleModal(true)}
              >
                <Swords size={16} />
                <span>Nova Batalha</span>
              </button>
            </div>
          )}
        </div>

        {/* Registro de Batalha (Log Oficial) */}
        <div className="panel log-panel">
          <div className="panel-title log-panel-title">
            <div className="log-title-left">
              <Clock size={18} className="gold-icon" />
              <h3>Registro de Batalha ({events.length})</h3>
            </div>
            <button
              type="button"
              className="toggle-log-btn"
              onClick={() => setShowLogDrawer(!showLogDrawer)}
            >
              {showLogDrawer ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {showLogDrawer && (
            <div className="events-log-container">
              {events.length === 0 ? (
                <p className="empty-subtext">Aguardando início das ações...</p>
              ) : (
                events.map((ev) => {
                  const p = ev.payload

                  if (ev.type === 'combat_started') {
                    return (
                      <div key={ev.id} className="event-item event-started">
                        <span className="event-seq">#{ev.sequence}</span>
                        <span className="event-text">
                          ⚔️ <strong>Combate iniciado.</strong> Iniciativas geradas pelo servidor.
                        </span>
                      </div>
                    )
                  }

                  if (ev.type === 'turn_started') {
                    const actor = combat.combatants.find((c) => c.id === p.actor_id)
                    return (
                      <div key={ev.id} className="event-item event-turn">
                        <span className="event-seq">#{ev.sequence}</span>
                        <span className="event-text">
                          Turno de <strong>{actor ? actor.name : p.actor_id}</strong> (Rodada {p.round}).
                        </span>
                      </div>
                    )
                  }

                  if (ev.type === 'attack_resolved') {
                    const actor = combat.combatants.find((c) => c.id === p.actor_id)
                    const target = combat.combatants.find((c) => c.id === p.target_id)

                    return (
                      <div
                        key={ev.id}
                        className={`event-item event-attack ${p.critical ? 'crit' : p.hit ? 'hit' : 'miss'}`}
                      >
                        <span className="event-seq">#{ev.sequence}</span>
                        <div className="event-body">
                          <div className="event-header">
                            <strong>{actor ? actor.name : 'Atacante'}</strong> atacou{' '}
                            <strong>{target ? target.name : 'Alvo'}</strong>:
                          </div>
                          <div className="event-roll-details">
                            <span>
                              D20 [{p.attack_roll?.rolls?.join(', ')}] {p.attack_bonus >= 0 ? `+ ${p.attack_bonus}` : p.attack_bonus} = <strong>{p.attack_total}</strong> vs CA.
                            </span>
                            {p.hit ? (
                              <span className="event-damage-detail">
                                {p.critical ? '💥 CRÍTICO! ' : '⚔️ '} Dano: <strong>{p.damage}</strong> ({p.damage_type}). PV do alvo: {p.hp_before} → <strong>{p.hp_after}</strong>.
                              </span>
                            ) : (
                              <span className="event-miss-detail">🛡️ Errou! O ataque não superou a defesa.</span>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  }

                  if (ev.type === 'combat_completed') {
                    return (
                      <div key={ev.id} className="event-item event-completed">
                        <span className="event-seq">#{ev.sequence}</span>
                        <span className="event-text">
                          🏆 <strong>Encontro encerrado!</strong> Vencedor:{' '}
                          {p.winner === 'party' ? 'Comitiva' : 'Monstros'}.
                        </span>
                      </div>
                    )
                  }

                  return (
                    <div key={ev.id} className="event-item">
                      <span className="event-seq">#{ev.sequence}</span>
                      <span className="event-text">{ev.type}</span>
                    </div>
                  )
                })
              )}
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

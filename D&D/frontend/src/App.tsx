import { useState, useEffect, useCallback } from 'react'
import type { TabType } from './components/Navbar'
import { Navbar } from './components/Navbar'
import { CharacterCreator } from './components/CharacterCreator'
import { PartyManager } from './components/PartyManager'
import { CombatArena } from './components/CombatArena'
import { SavedCombats } from './components/SavedCombats'
import { DiceRoller } from './components/DiceRoller'
import { BookReader } from './components/BookReader'
import type { CharacterOut, CombatOut, PartyOut } from './types/api'
import { api } from './services/api'
import './index.css'

export function App() {
  const [currentTab, setCurrentTab] = useState<TabType>('combat')
  const [apiHealthy, setApiHealthy] = useState<boolean>(false)
  const [characters, setCharacters] = useState<CharacterOut[]>([])
  const [parties, setParties] = useState<PartyOut[]>([])
  const [currentCombat, setCurrentCombat] = useState<CombatOut | null>(null)

  // Acessibilidade e som
  const [reducedMotion, setReducedMotion] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return (
        localStorage.getItem('arcanum_reduced_motion') === 'true' ||
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
      )
    }
    return false
  })

  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('arcanum_sound_enabled') !== 'false'
    }
    return true
  })

  const handleToggleReducedMotion = () => {
    setReducedMotion((prev) => {
      const next = !prev
      localStorage.setItem('arcanum_reduced_motion', String(next))
      return next
    })
  }

  const handleToggleSound = () => {
    setSoundEnabled((prev) => {
      const next = !prev
      localStorage.setItem('arcanum_sound_enabled', String(next))
      return next
    })
  }

  // Carrega dados iniciais da API
  const refreshAll = useCallback(async () => {
    try {
      const health = await api.getHealth()
      setApiHealthy(health.ok)
    } catch {
      setApiHealthy(false)
    }

    try {
      const [chars, partyList, combats] = await Promise.all([
        api.getCharacters(100),
        api.getParties(100),
        api.getCombats(50),
      ])
      setCharacters(chars)
      setParties(partyList)

      // Seleciona o combate ativo mais recente se existir
      const active = combats.find((c) => c.status === 'active')
      if (active) {
        setCurrentCombat(active)
      } else if (combats.length > 0 && !currentCombat) {
        setCurrentCombat(combats[0])
      }
    } catch (err) {
      console.warn('Erro ao carregar dados:', err)
    }
  }, [currentCombat])

  useEffect(() => {
    refreshAll()
    const timer = setInterval(() => {
      api.getHealth().then((h) => setApiHealthy(h.ok)).catch(() => setApiHealthy(false))
    }, 15000)
    return () => clearInterval(timer)
  }, [refreshAll])

  const handleCharacterCreated = (char: CharacterOut) => {
    setCharacters((prev) => [char, ...prev])
  }

  const handleCharacterUpdated = (updated: CharacterOut) => {
    setCharacters((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
  }

  const handlePartyCreated = (party: PartyOut) => {
    setParties((prev) => [party, ...prev])
  }

  const handleCombatStarted = (combat: CombatOut) => {
    setCurrentCombat(combat)
    setCurrentTab('combat')
    refreshAll()
  }

  const handleCombatUpdated = (combat: CombatOut) => {
    setCurrentCombat(combat)
    if (combat.status === 'completed') {
      refreshAll()
    }
  }

  const handleSelectSavedCombat = (combat: CombatOut) => {
    setCurrentCombat(combat)
    setCurrentTab('combat')
  }

  return (
    <div className={`arcanum-app ${reducedMotion ? 'reduce-motion' : ''}`}>
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        apiHealthy={apiHealthy}
        reducedMotion={reducedMotion}
        onToggleReducedMotion={handleToggleReducedMotion}
        soundEnabled={soundEnabled}
        onToggleSound={handleToggleSound}
        activeCombatId={currentCombat?.status === 'active' ? currentCombat.id : null}
        onRefreshHealth={refreshAll}
      />

      <main className="main-content">
        {currentTab === 'combat' && (
          <CombatArena
            combat={currentCombat}
            parties={parties}
            onCombatUpdated={handleCombatUpdated}
            onStartNewCombat={handleCombatStarted}
            reducedMotion={reducedMotion}
            soundEnabled={soundEnabled}
            onNavigateToTab={setCurrentTab}
          />
        )}

        {currentTab === 'books' && <BookReader />}

        {currentTab === 'characters' && (
          <CharacterCreator
            characters={characters}
            onCharacterCreated={handleCharacterCreated}
            onCharacterUpdated={handleCharacterUpdated}
            onSelectForParty={() => setCurrentTab('parties')}
          />
        )}

        {currentTab === 'parties' && (
          <PartyManager
            characters={characters}
            parties={parties}
            onPartyCreated={handlePartyCreated}
            onCombatStarted={handleCombatStarted}
            onNavigateToTab={setCurrentTab}
          />
        )}

        {currentTab === 'saved' && (
          <SavedCombats
            onSelectCombat={handleSelectSavedCombat}
            currentCombatId={currentCombat?.id || null}
          />
        )}

        {currentTab === 'dice' && <DiceRoller soundEnabled={soundEnabled} />}
      </main>
    </div>
  )
}

export default App

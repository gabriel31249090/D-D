import React from 'react'
import { Shield, Swords, Users, History, Dices, BookOpen, BookMarked, Activity, Volume2, VolumeX, Eye } from 'lucide-react'

export type TabType = 'combat' | 'books' | 'journal' | 'characters' | 'parties' | 'saved' | 'dice'

interface NavbarProps {
  currentTab: TabType
  onSelectTab: (tab: TabType) => void
  apiHealthy: boolean
  reducedMotion: boolean
  onToggleReducedMotion: () => void
  soundEnabled: boolean
  onToggleSound: () => void
  activeCombatId: string | null
  onRefreshHealth: () => void
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  apiHealthy,
  reducedMotion,
  onToggleReducedMotion,
  soundEnabled,
  onToggleSound,
  activeCombatId,
  onRefreshHealth,
}) => {
  return (
    <header className="arcanum-header">
      <div className="header-brand">
        <div className="brand-logo" onClick={() => onSelectTab('combat')}>
          <Shield className="brand-icon" size={28} />
          <div className="brand-text">
            <span className="brand-title">ARCANUM</span>
            <span className="brand-subtitle">Plataforma D&D 5e</span>
          </div>
        </div>

        <div className="header-status">
          <button
            type="button"
            className={`api-status-badge ${apiHealthy ? 'healthy' : 'unhealthy'}`}
            onClick={onRefreshHealth}
            title={apiHealthy ? 'Motor Python Conectado (127.0.0.1:8000)' : 'Servidor desconectado. Clique para tentar reconectar'}
          >
            <Activity size={14} className={apiHealthy ? 'pulse' : ''} />
            <span>{apiHealthy ? 'Motor Ativo' : 'Motor Offline'}</span>
          </button>

          {activeCombatId && (
            <button
              type="button"
              className="active-combat-indicator"
              onClick={() => onSelectTab('combat')}
              title="Existe um combate em andamento. Clique para ir à arena."
            >
              <Swords size={14} />
              <span>Em Batalha</span>
            </button>
          )}
        </div>
      </div>

      <nav className="header-nav">
        <button
          type="button"
          className={`nav-btn ${currentTab === 'combat' ? 'active' : ''}`}
          onClick={() => onSelectTab('combat')}
        >
          <Swords size={18} />
          <span>Arena de Batalha</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'books' ? 'active' : ''}`}
          onClick={() => onSelectTab('books')}
        >
          <BookOpen size={18} />
          <span>Biblioteca & Livros</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'journal' ? 'active' : ''}`}
          onClick={() => onSelectTab('journal')}
        >
          <BookMarked size={18} />
          <span>Diário do Mestre</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'characters' ? 'active' : ''}`}
          onClick={() => onSelectTab('characters')}
        >
          <Shield size={18} />
          <span>Heróis & Fichas</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'parties' ? 'active' : ''}`}
          onClick={() => onSelectTab('parties')}
        >
          <Users size={18} />
          <span>Comitivas</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'saved' ? 'active' : ''}`}
          onClick={() => onSelectTab('saved')}
        >
          <History size={18} />
          <span>Batalhas Salvas</span>
        </button>

        <button
          type="button"
          className={`nav-btn ${currentTab === 'dice' ? 'active' : ''}`}
          onClick={() => onSelectTab('dice')}
        >
          <Dices size={18} />
          <span>Dados</span>
        </button>
      </nav>

      <div className="header-toggles">
        <button
          type="button"
          className={`toggle-btn ${reducedMotion ? 'active' : ''}`}
          onClick={onToggleReducedMotion}
          title={reducedMotion ? 'Animações Reduzidas: ATIVADO' : 'Animações Reduzidas: DESATIVADO'}
        >
          <Eye size={16} />
          <span>{reducedMotion ? 'Movimento Reduzido' : 'Animações'}</span>
        </button>

        <button
          type="button"
          className={`toggle-btn ${soundEnabled ? 'active' : ''}`}
          onClick={onToggleSound}
          title={soundEnabled ? 'Efeitos Sonoros: ATIVADO' : 'Efeitos Sonoros: DESATIVADO'}
        >
          {soundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
          <span>{soundEnabled ? 'Som Ativo' : 'Mudo'}</span>
        </button>
      </div>
    </header>
  )
}

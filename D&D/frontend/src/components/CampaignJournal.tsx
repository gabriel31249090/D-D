import React, { useState, useEffect } from 'react'
import { BookMarked, Plus, Trash2, Edit3, Save, CheckCircle, Search, Compass, MapPin, Users, Award, Shield } from 'lucide-react'

export interface CampaignNote {
  id: string
  title: string
  category: 'session' | 'npc' | 'location' | 'quest' | 'treasure'
  content: string
  updatedAt: string
}

const DEFAULT_NOTES: CampaignNote[] = [
  {
    id: '1',
    title: 'Sessão 1: O Ataque na Estrada de Valebruma',
    category: 'session',
    content: 'A comitiva partiu rumo às colinas ancestrais. Próximo à cachoeira, batedores goblins emboscaram a vanguarda. O guerreiro assumiu a frente com sua cota de malha e escudo, contendo os inimigos enquanto o grupo revidou.',
    updatedAt: new Date().toLocaleDateString('pt-BR'),
  },
  {
    id: '2',
    title: 'Missão: Limpar o Posto Avançado dos Goblins',
    category: 'quest',
    content: 'Objetivo: Eliminar as patrulhas de goblins de treino e coletar informações sobre o acampamento principal nas cavernas nevadas. Recompensa: 100 PO e a gratidão da guarnição de Valebruma.',
    updatedAt: new Date().toLocaleDateString('pt-BR'),
  },
  {
    id: '3',
    title: 'NPC: Mestre de Armas Eamon',
    category: 'npc',
    content: 'Instrutor veterano da arena de treino. Treina novos guerreiros nas artes do Duelismo e da Defesa blindada. Sempre tem poções de treino e conselhos sobre como derrubar goblins velozes.',
    updatedAt: new Date().toLocaleDateString('pt-BR'),
  },
  {
    id: '4',
    title: 'Local: A Caverna Congelada',
    category: 'location',
    content: 'Uma fenda glacial nas montanhas do norte. O piso é escorregadio e repleto de estalactites. Os ecos dificultam a percepção de emboscadas.',
    updatedAt: new Date().toLocaleDateString('pt-BR'),
  },
]

export const CampaignJournal: React.FC = () => {
  const [notes, setNotes] = useState<CampaignNote[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('arcanum_campaign_notes')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch {}
      }
    }
    return DEFAULT_NOTES
  })

  const [selectedNoteId, setSelectedNoteId] = useState<string>(notes[0]?.id || '')
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Edição
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editCategory, setEditCategory] = useState<CampaignNote['category']>('session')
  const [editContent, setEditContent] = useState('')

  useEffect(() => {
    localStorage.setItem('arcanum_campaign_notes', JSON.stringify(notes))
  }, [notes])

  const selectedNote = notes.find((n) => n.id === selectedNoteId) || notes[0]

  const handleSelectNote = (note: CampaignNote) => {
    setSelectedNoteId(note.id)
    setIsEditing(false)
  }

  const handleStartCreate = () => {
    const newNote: CampaignNote = {
      id: `${Date.now()}`,
      title: 'Nova Nota da Campanha',
      category: 'session',
      content: '',
      updatedAt: new Date().toLocaleDateString('pt-BR'),
    }
    setNotes([newNote, ...notes])
    setSelectedNoteId(newNote.id)
    setEditTitle(newNote.title)
    setEditCategory(newNote.category)
    setEditContent(newNote.content)
    setIsEditing(true)
  }

  const handleStartEdit = () => {
    if (!selectedNote) return
    setEditTitle(selectedNote.title)
    setEditCategory(selectedNote.category)
    setEditContent(selectedNote.content)
    setIsEditing(true)
  }

  const handleSave = () => {
    if (!selectedNote) return
    const updated = notes.map((n) =>
      n.id === selectedNote.id
        ? {
            ...n,
            title: editTitle.trim() || 'Nota sem Título',
            category: editCategory,
            content: editContent,
            updatedAt: new Date().toLocaleDateString('pt-BR'),
          }
        : n,
    )
    setNotes(updated)
    setIsEditing(false)
  }

  const handleDelete = (id: string) => {
    const remaining = notes.filter((n) => n.id !== id)
    setNotes(remaining)
    if (selectedNoteId === id) {
      setSelectedNoteId(remaining[0]?.id || '')
    }
    setIsEditing(false)
  }

  const filteredNotes = notes.filter((n) => {
    const matchesCat = activeCategory === 'all' || n.category === activeCategory
    const matchesSearch =
      n.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.content.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesCat && matchesSearch
  })

  return (
    <div className="tab-container journal-tab">
      <div className="section-header section-header-row">
        <div>
          <h2>Diário de Campanha & Crônicas do Mestre</h2>
          <p className="section-desc">
            Organização completa de sessões, NPCs, missões, locais e anotações táticas de Valebruma.
          </p>
        </div>

        <button type="button" className="btn-primary" onClick={handleStartCreate}>
          <Plus size={16} />
          <span>Nova Anotação</span>
        </button>
      </div>

      <div className="journal-grid">
        {/* Painel Esquerdo: Lista de Anotações */}
        <div className="panel journal-sidebar">
          {/* Barra de Busca */}
          <div className="journal-search-row">
            <Search size={16} className="gold-icon" />
            <input
              type="text"
              className="input-field journal-search-input"
              placeholder="Buscar em anotações..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Filtros de Categoria */}
          <div className="journal-categories-bar">
            <button
              type="button"
              className={`journal-cat-pill ${activeCategory === 'all' ? 'active' : ''}`}
              onClick={() => setActiveCategory('all')}
            >
              Todas ({notes.length})
            </button>
            <button
              type="button"
              className={`journal-cat-pill ${activeCategory === 'session' ? 'active' : ''}`}
              onClick={() => setActiveCategory('session')}
            >
              Sessões
            </button>
            <button
              type="button"
              className={`journal-cat-pill ${activeCategory === 'quest' ? 'active' : ''}`}
              onClick={() => setActiveCategory('quest')}
            >
              Missões
            </button>
            <button
              type="button"
              className={`journal-cat-pill ${activeCategory === 'npc' ? 'active' : ''}`}
              onClick={() => setActiveCategory('npc')}
            >
              NPCs
            </button>
            <button
              type="button"
              className={`journal-cat-pill ${activeCategory === 'location' ? 'active' : ''}`}
              onClick={() => setActiveCategory('location')}
            >
              Locais
            </button>
          </div>

          {/* Lista de Itens */}
          <div className="journal-notes-list">
            {filteredNotes.length === 0 ? (
              <p className="empty-subtext">Nenhuma nota encontrada.</p>
            ) : (
              filteredNotes.map((n) => {
                const isSelected = n.id === selectedNote?.id
                return (
                  <div
                    key={n.id}
                    className={`journal-note-item ${isSelected ? 'active' : ''}`}
                    onClick={() => handleSelectNote(n)}
                  >
                    <div className="note-item-top">
                      <strong className="note-item-title">{n.title}</strong>
                      <span className={`note-cat-badge ${n.category}`}>
                        {n.category === 'session' && 'Sessão'}
                        {n.category === 'quest' && 'Missão'}
                        {n.category === 'npc' && 'NPC'}
                        {n.category === 'location' && 'Local'}
                        {n.category === 'treasure' && 'Tesouro'}
                      </span>
                    </div>
                    <p className="note-item-snippet">{n.content.slice(0, 90) || 'Sem conteúdo...'}</p>
                    <span className="note-item-date">{n.updatedAt}</span>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Painel Direito: Leitor / Editor da Nota */}
        <div className="panel journal-content-panel">
          {selectedNote ? (
            isEditing ? (
              <div className="journal-editor-form">
                <div className="form-group">
                  <label>Título da Nota:</label>
                  <input
                    type="text"
                    className="input-field"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Categoria:</label>
                  <select
                    className="select-field"
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value as any)}
                  >
                    <option value="session">Sessão de Jogo</option>
                    <option value="quest">Missão / Quest</option>
                    <option value="npc">NPC / Personagem</option>
                    <option value="location">Local / Masmorra</option>
                    <option value="treasure">Tesouro / Recompensa</option>
                  </select>
                </div>

                <div className="form-group flex-1">
                  <label>Conteúdo da Anotação:</label>
                  <textarea
                    className="input-field journal-textarea"
                    rows={14}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    placeholder="Escreva os detalhes da campanha, acontecimentos da sessão, ganchos e segredos..."
                  />
                </div>

                <div className="editor-actions-row">
                  <button type="button" className="btn-primary" onClick={handleSave}>
                    <Save size={16} />
                    <span>Salvar Nota</span>
                  </button>
                  <button type="button" className="btn-secondary" onClick={() => setIsEditing(false)}>
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <div className="journal-reader-view">
                <div className="journal-reader-header">
                  <div>
                    <h3 className="reader-title">{selectedNote.title}</h3>
                    <div className="reader-meta">
                      <span className={`note-cat-badge ${selectedNote.category}`}>
                        {selectedNote.category === 'session' && 'Sessão'}
                        {selectedNote.category === 'quest' && 'Missão'}
                        {selectedNote.category === 'npc' && 'NPC'}
                        {selectedNote.category === 'location' && 'Local'}
                        {selectedNote.category === 'treasure' && 'Tesouro'}
                      </span>
                      <span className="reader-date">Atualizado em: {selectedNote.updatedAt}</span>
                    </div>
                  </div>

                  <div className="reader-actions">
                    <button type="button" className="btn-secondary btn-sm" onClick={handleStartEdit}>
                      <Edit3 size={14} />
                      <span>Editar</span>
                    </button>
                    <button
                      type="button"
                      className="btn-secondary btn-sm text-crimson"
                      onClick={() => handleDelete(selectedNote.id)}
                      title="Excluir anotação"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                <div className="journal-body-text">
                  {selectedNote.content ? (
                    selectedNote.content.split('\n').map((paragraph, i) => (
                      <p key={i} className="journal-paragraph">
                        {paragraph}
                      </p>
                    ))
                  ) : (
                    <p className="empty-subtext">Esta nota está vazia. Clique em Editar para escrever.</p>
                  )}
                </div>
              </div>
            )
          ) : (
            <div className="empty-state">
              <BookMarked size={40} className="gold-icon" />
              <p>Nenhuma nota selecionada.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

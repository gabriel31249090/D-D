import React, { useState, useEffect } from 'react'
import { BookOpen, FileText, Skull, Download, Maximize2, Search, Sparkles, Shield, Heart, User } from 'lucide-react'

interface BookSource {
  id: string
  title: string
  type: 'pdf' | 'json'
  path: string
  description: string
  category: 'core' | 'monsters' | 'sheets' | 'compendium'
}

const AVAILABLE_BOOKS: BookSource[] = [
  {
    id: 'phb',
    title: 'Livro do Jogador (Player’s Handbook 5e)',
    type: 'pdf',
    path: '/raw-books/dd-5e-livro-do-jogador-fundo-branco-biblioteca-elfica.pdf',
    description: 'Regras completas de D&D 5ª Edição: raças, classes, magias, perícias, equipamentos e combate.',
    category: 'core',
  },
  {
    id: 'mm',
    title: 'Manual dos Monstros (Monster Manual 5e)',
    type: 'pdf',
    path: '/raw-books/D.D.5E.-.Manual.dos.Monstros.pdf',
    description: 'Bestiário completo oficial com fichas, lore, ações e táticas de criaturas de D&D.',
    category: 'monsters',
  },
  {
    id: 'char_json',
    title: 'Compêndio de Fichas Prontas (Valebruma)',
    type: 'json',
    path: '/raw-books/Dados_e_Rolagens.json',
    description: 'Fichas completas geradas com atributos oficiais (4d6 descartando o menor) e histórico.',
    category: 'compendium',
  },
  {
    id: 'sheet_wizard',
    title: 'Ficha: Mago (Elfo Alto)',
    type: 'pdf',
    path: '/raw-books/01_Mago_Elfo_alto_sem_nome.pdf',
    description: 'Ficha completa de Mago Elfo Alto nível 1 pronta para uso e impressão.',
    category: 'sheets',
  },
  {
    id: 'sheet_cleric',
    title: 'Ficha: Clérigo (Anão da Colina)',
    type: 'pdf',
    path: '/raw-books/02_Clerigo_Anao_da_colina_sem_nome.pdf',
    description: 'Ficha completa de Clérigo Anão da Colina nível 1 pronta para uso e impressão.',
    category: 'sheets',
  },
  {
    id: 'sheet_rogue',
    title: 'Ficha: Ladino (Halfling Pés-Leves)',
    type: 'pdf',
    path: '/raw-books/03_Ladino_Halfling_pes-leves_sem_nome.pdf',
    description: 'Ficha completa de Ladino Halfling nível 1 pronta para uso e impressão.',
    category: 'sheets',
  },
  {
    id: 'sheet_barbarian',
    title: 'Ficha: Bárbaro (Meio-Orc)',
    type: 'pdf',
    path: '/raw-books/04_Bárbaro_Meio-orc_sem_nome.pdf',
    description: 'Ficha completa de Bárbaro Meio-Orc nível 1 pronta para uso e impressão.',
    category: 'sheets',
  },
  {
    id: 'sheet_bard',
    title: 'Ficha: Bardo (Tiefling)',
    type: 'pdf',
    path: '/raw-books/05_Bardo_Tiefling_sem_nome.pdf',
    description: 'Ficha completa de Bardo Tiefling nível 1 pronta para uso e impressão.',
    category: 'sheets',
  },
  {
    id: 'sheet_dragonborn',
    title: 'Ficha: Guerreiro (Draconato)',
    type: 'pdf',
    path: '/raw-books/Ficha_DnD5e_Guerreiro_Draconato_Preenchida.pdf',
    description: 'Ficha preenchida oficial de guerreiro nível 1.',
    category: 'sheets',
  },
  {
    id: 'sheet_editable',
    title: 'Ficha Oficial Editável D&D 5e',
    type: 'pdf',
    path: '/raw-books/D&D 5ed - Ficha Editável.pdf',
    description: 'Ficha oficial de personagem em PDF pronta para preenchimento ou impressão.',
    category: 'sheets',
  },
]

interface PreMadeHero {
  id: number
  race: string
  class: string
  hp: number
  ac: number
  final_attributes: Record<string, number>
  rolls: Array<{
    dice: number[]
    discard: number
    score: number
  }>
}

export const BookReader: React.FC = () => {
  const [selectedBook, setSelectedBook] = useState<BookSource>(AVAILABLE_BOOKS[0])
  const [filterCategory, setFilterCategory] = useState<'all' | 'core' | 'sheets' | 'compendium'>('all')
  const [jsonData, setJsonData] = useState<PreMadeHero[]>([])
  const [loadingJson, setLoadingJson] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    if (selectedBook.type === 'json') {
      setLoadingJson(true)
      fetch(selectedBook.path)
        .then((res) => res.json())
        .then((data: PreMadeHero[]) => {
          setJsonData(data)
          setLoadingJson(false)
        })
        .catch((err) => {
          console.error('Falha ao carregar compêndio JSON:', err)
          setLoadingJson(false)
        })
    }
  }, [selectedBook])

  const filteredHeroes = jsonData.filter((h) => {
    const term = searchTerm.toLowerCase()
    return (
      h.class.toLowerCase().includes(term) ||
      h.race.toLowerCase().includes(term) ||
      String(h.id).includes(term)
    )
  })

  const displayedBooks = AVAILABLE_BOOKS.filter((b) => {
    if (filterCategory === 'all') return true
    if (filterCategory === 'core') return b.category === 'core' || b.category === 'monsters'
    return b.category === filterCategory
  })

  return (
    <div className="tab-container book-reader-tab">
      {/* Barra de Seleção de Livros */}
      <div className="books-shelf-header">
        <div className="books-shelf-title">
          <BookOpen className="gold-icon" size={26} />
          <div>
            <h2>Biblioteca Oficial de Regras, Manuais & Fichas</h2>
            <p className="shelf-subtitle">
              Livros originais de D&D 5ª Edição, bestiários e fichas prontas das cinco classes clássicas.
            </p>
          </div>
        </div>

        {/* Filtro de Categoria */}
        <div className="category-filter-row">
          <button
            type="button"
            className={`cat-filter-btn ${filterCategory === 'all' ? 'active' : ''}`}
            onClick={() => setFilterCategory('all')}
          >
            Todos os Documentos ({AVAILABLE_BOOKS.length})
          </button>
          <button
            type="button"
            className={`cat-filter-btn ${filterCategory === 'core' ? 'active' : ''}`}
            onClick={() => setFilterCategory('core')}
          >
            Livros Oficiais (PHB & Bestiário)
          </button>
          <button
            type="button"
            className={`cat-filter-btn ${filterCategory === 'sheets' ? 'active' : ''}`}
            onClick={() => setFilterCategory('sheets')}
          >
            Fichas das Classes (Mago, Clérigo, Ladino, etc.)
          </button>
          <button
            type="button"
            className={`cat-filter-btn ${filterCategory === 'compendium' ? 'active' : ''}`}
            onClick={() => setFilterCategory('compendium')}
          >
            Compêndio Interativo Valebruma
          </button>
        </div>

        {/* Pílulas de Seleção dos Documentos */}
        <div className="books-selector-pills">
          {displayedBooks.map((book) => {
            const isSelected = book.id === selectedBook.id
            return (
              <button
                key={book.id}
                type="button"
                className={`book-pill-btn ${isSelected ? 'active' : ''}`}
                onClick={() => setSelectedBook(book)}
              >
                {book.category === 'core' && <BookOpen size={16} />}
                {book.category === 'monsters' && <Skull size={16} />}
                {book.category === 'sheets' && <User size={16} />}
                {book.category === 'compendium' && <Sparkles size={16} />}
                <span>{book.title.split('(')[0].replace('Ficha:', '').trim()}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Visualizador Principal do Livro / Documento */}
      <div className="book-viewer-card">
        <div className="viewer-toolbar">
          <div className="viewer-info">
            <span className="viewer-book-title">{selectedBook.title}</span>
            <span className="viewer-desc">{selectedBook.description}</span>
          </div>

          <div className="viewer-actions">
            <a
              href={selectedBook.path}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary btn-sm"
              title="Abrir em nova aba em tela cheia"
            >
              <Maximize2 size={14} />
              <span>Tela Cheia</span>
            </a>
            <a
              href={selectedBook.path}
              download
              className="btn-secondary btn-sm"
              title="Baixar arquivo oficial para o computador"
            >
              <Download size={14} />
              <span>Baixar</span>
            </a>
          </div>
        </div>

        <div className="viewer-frame-container">
          {selectedBook.type === 'pdf' ? (
            <iframe
              src={selectedBook.path}
              title={selectedBook.title}
              className="pdf-iframe-viewer"
            />
          ) : (
            <div className="compendium-json-view">
              <div className="compendium-search-bar">
                <Search size={18} className="gold-icon" />
                <input
                  type="text"
                  placeholder="Pesquisar por classe (ex: Mago, Guerreiro) ou raça (ex: Elfo, Anão)..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input-field compendium-input"
                />
              </div>

              {loadingJson ? (
                <div className="compendium-loading">Carregando fichas oficiais...</div>
              ) : (
                <div className="compendium-cards-grid">
                  {filteredHeroes.map((hero) => (
                    <div key={hero.id} className="compendium-hero-card">
                      <div className="compendium-hero-header">
                        <div>
                          <h4 className="compendium-hero-title">
                            {hero.class} • {hero.race}
                          </h4>
                          <span className="compendium-hero-id">Ficha #{hero.id} (Valebruma)</span>
                        </div>
                        <div className="compendium-vitals">
                          <span className="vital-badge hp-badge">
                            <Heart size={12} /> {hero.hp} PV
                          </span>
                          <span className="vital-badge ac-badge">
                            <Shield size={12} /> CA {hero.ac}
                          </span>
                        </div>
                      </div>

                      <div className="compendium-attributes">
                        {Object.entries(hero.final_attributes).map(([attr, val]) => (
                          <div key={attr} className="comp-attr-chip">
                            <span className="comp-attr-name">{attr.slice(0, 3).toUpperCase()}</span>
                            <span className="comp-attr-val">{val}</span>
                          </div>
                        ))}
                      </div>

                      <div className="compendium-rolls-preview">
                        <span className="detail-label">Rolagens de Origem (4d6 drop-lowest):</span>
                        <div className="comp-rolls-chips">
                          {hero.rolls.map((r, i) => (
                            <span key={i} className="comp-roll-item" title={`Descartou ${r.discard}`}>
                              [{r.dice.join(', ')}] → <strong>{r.score}</strong>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

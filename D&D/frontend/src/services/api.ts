import type {
  ActionResult,
  CharacterCreate,
  CharacterOut,
  CombatAction,
  CombatCreate,
  CombatOut,
  DiceOut,
  DiceRequest,
  EventOut,
  HealthOut,
  MonsterOut,
  PartyCreate,
  PartyOut,
} from '../types/api'

const API_BASE = 'http://127.0.0.1:8000'

export class ApiClientError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.status = status
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  let response: Response
  try {
    response = await fetch(url, { ...options, headers })
  } catch (err) {
    throw new ApiClientError(
      'Falha de conexão com a API local (http://127.0.0.1:8000). Verifique se o servidor FastAPI está ativo.',
      'network_error',
      0,
    )
  }

  if (!response.ok) {
    let errorDetail = 'Erro desconhecido'
    let errorCode = 'unknown_error'

    try {
      const data = await response.json()
      if (data?.detail) {
        if (typeof data.detail === 'object') {
          errorCode = data.detail.code || errorCode
          errorDetail = data.detail.message || JSON.stringify(data.detail)
        } else {
          errorDetail = String(data.detail)
        }
      }
    } catch {
      errorDetail = await response.text()
    }

    if (response.status === 409) {
      errorCode = errorCode === 'unknown_error' ? 'version_conflict' : errorCode
      errorDetail = errorDetail || 'Conflito de versão no combate. Recarregando estado atual...'
    }

    throw new ApiClientError(errorDetail, errorCode, response.status)
  }

  return response.json() as Promise<T>
}

export const api = {
  // Health
  getHealth: () => request<HealthOut>('/health'),

  // Characters
  getCharacters: (limit = 50, offset = 0) =>
    request<CharacterOut[]>(`/api/characters?limit=${limit}&offset=${offset}`),
  getCharacter: (id: string) => request<CharacterOut>(`/api/characters/${id}`),
  createCharacter: (data: CharacterCreate) =>
    request<CharacterOut>('/api/characters', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  restCharacter: (id: string) =>
    request<CharacterOut>(`/api/characters/${id}/rest`, {
      method: 'POST',
    }),

  // Parties
  getParties: (limit = 50, offset = 0) =>
    request<PartyOut[]>(`/api/parties?limit=${limit}&offset=${offset}`),
  getParty: (id: string) => request<PartyOut>(`/api/parties/${id}`),
  createParty: (data: PartyCreate) =>
    request<PartyOut>('/api/parties', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Monsters
  getMonsters: () => request<MonsterOut[]>('/api/monsters'),

  // Combats
  getCombats: (limit = 50, offset = 0) =>
    request<CombatOut[]>(`/api/combat?limit=${limit}&offset=${offset}`),
  getCombat: (id: string) => request<CombatOut>(`/api/combat/${id}`),
  createCombat: (data: CombatCreate) =>
    request<CombatOut>('/api/combat', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  executeAction: (combatId: string, action: CombatAction) =>
    request<ActionResult>(`/api/combat/${combatId}/actions`, {
      method: 'POST',
      body: JSON.stringify(action),
    }),
  getEvents: (combatId: string, afterSequence = 0, limit = 200) =>
    request<EventOut[]>(`/api/combat/${combatId}/events?after_sequence=${afterSequence}&limit=${limit}`),

  // Dice
  rollDice: (data: DiceRequest) =>
    request<DiceOut>('/api/dice/roll', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

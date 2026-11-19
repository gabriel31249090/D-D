export type RuleSet = 'dnd5e-2014'

export type ClassId = 'fighter'

export type FightingStyle = 'defense' | 'dueling'

export type ArmorType = 'chain_mail' | 'leather' | 'none'

export interface Abilities {
  strength: number
  dexterity: number
  constitution: number
  intelligence: number
  wisdom: number
  charisma: number
}

export interface Equipment {
  armor: ArmorType
  shield: boolean
  weapon: 'longsword'
}

export interface AttackProfile {
  id: string
  name: string
  attack_bonus: number
  damage_expression: string
  damage_type: string
  range_feet: number
}

export interface CharacterCreate {
  name: string
  rule_set: RuleSet
  class_id: ClassId
  level: 1
  abilities: Abilities
  equipment: Equipment
  fighting_style: FightingStyle
}

export interface CharacterOut extends CharacterCreate {
  id: string
  ability_modifiers: Record<string, number>
  proficiency_bonus: number
  max_hp: number
  current_hp: number
  armor_class: number
  saving_throws: Record<string, number>
  initiative_bonus: number
  attacks: AttackProfile[]
  active_combat_id: string | null
  scope: string
}

export interface PartyCreate {
  name: string
  character_ids: string[]
}

export interface PartyOut extends PartyCreate {
  id: string
}

export interface MonsterOut {
  id: string
  name: string
  rule_set: string
  is_example: boolean
  source: string
  max_hp: number
  armor_class: number
  dexterity_modifier: number
  attacks: AttackProfile[]
}

export interface CombatCreate {
  party_id: string
  monster_ids: ('training-goblin')[]
  rule_set: RuleSet
}

export interface CombatantOut {
  id: string
  character_id: string | null
  name: string
  team: 'party' | 'enemy'
  max_hp: number
  current_hp: number
  armor_class: number
  initiative: number
  initiative_roll: number
  action_available: boolean
  conditions: string[]
  attacks: AttackProfile[]
  is_example: boolean
}

export interface CombatOut {
  id: string
  party_id: string
  rule_set: string
  mode: 'local_arena'
  status: 'active' | 'completed'
  version: number
  round: number
  current_actor_id: string | null
  winner: 'party' | 'enemy' | null
  combatants: CombatantOut[]
}

export interface AttackResolvedPayload {
  actor_id: string
  target_id: string
  attack_id: string
  hit: boolean
  critical: boolean
  damage: number
  damage_type: string
  hp_before: number
  hp_after: number
  attack_roll: {
    rolls: number[]
    total: number
  }
  damage_roll: {
    rolls: number[]
    total: number
  } | null
  attack_bonus: number
  attack_total: number
  version: number
}

export interface EventOut {
  id: number
  combat_id: string
  sequence: number
  type: 'combat_started' | 'turn_started' | 'attack_resolved' | 'combat_completed' | string
  payload: any
}

export interface ActionResult {
  combat: CombatOut
  events: EventOut[]
}

export interface CombatAction {
  type: 'attack' | 'end_turn'
  actor_id: string
  expected_version: number
  target_id?: string
  attack_id?: 'longsword' | 'training-blade'
}

export interface DiceRequest {
  expression: string
  mode: 'normal' | 'advantage' | 'disadvantage'
}

export interface DiceOut {
  id: number
  expression: string
  mode: string
  rolls: number[]
  kept: number[]
  modifier: number
  total: number
}

export interface HealthOut {
  ok: boolean
  version: string
  mode: string
  authentication: string
}

export interface ApiError {
  detail: {
    code: string
    message: string
  }
}

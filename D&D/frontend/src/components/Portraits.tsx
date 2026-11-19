import React from 'react'

interface PortraitProps {
  name: string
  team: 'party' | 'enemy'
  isActor?: boolean
  isSelectedTarget?: boolean
  isAttacking?: boolean
  isDamaged?: boolean
  isDefeated?: boolean
  reducedMotion?: boolean
  size?: number
}

export const FighterPortrait: React.FC<PortraitProps> = ({
  name,
  isActor = false,
  isSelectedTarget = false,
  isAttacking = false,
  isDamaged = false,
  isDefeated = false,
  reducedMotion = false,
  size = 140,
}) => {
  return (
    <div
      className={`portrait-wrapper ${isActor ? 'is-actor' : ''} ${isSelectedTarget ? 'is-target' : ''} ${
        isAttacking && !reducedMotion ? 'anim-attack-party' : ''
      } ${isDamaged && !reducedMotion ? 'anim-damage' : ''} ${isDefeated ? 'is-defeated' : ''}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 100 100"
        className="portrait-svg"
        style={{ width: '100%', height: '100%', borderRadius: '12px' }}
      >
        <defs>
          <radialGradient id="fighter-bg" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#2c3440" />
            <stop offset="100%" stopColor="#10151c" />
          </radialGradient>
          <linearGradient id="armor-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7a889b" />
            <stop offset="50%" stopColor="#485563" />
            <stop offset="100%" stopColor="#2b323c" />
          </linearGradient>
          <linearGradient id="gold-trim" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffe27a" />
            <stop offset="100%" stopColor="#b38a2e" />
          </linearGradient>
          <filter id="glow-gold" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#d4af37" floodOpacity="0.8" />
          </filter>
        </defs>

        {/* Fundo de retrato gótico */}
        <rect width="100" height="100" rx="10" fill="url(#fighter-bg)" />
        <rect
          width="94"
          height="94"
          x="3"
          y="3"
          rx="8"
          fill="none"
          stroke="url(#gold-trim)"
          strokeWidth={isActor ? '2.5' : '1.5'}
          strokeDasharray={isActor ? 'none' : 'none'}
        />

        {/* Capa vermelha ao fundo */}
        <path d="M 28 45 Q 15 75 18 95 L 82 95 Q 85 75 72 45 Z" fill="#6b1d1d" />

        {/* Cota de malha / Armadura de ferro */}
        <path d="M 30 55 L 50 48 L 70 55 L 75 95 L 25 95 Z" fill="url(#armor-grad)" />

        {/* Detalhes da placa peitoral e brasão */}
        <path d="M 40 54 L 50 62 L 60 54 L 50 82 Z" fill="#252c35" stroke="url(#gold-trim)" strokeWidth="1" />
        <circle cx="50" cy="65" r="3" fill="#ffe27a" />

        {/* Ombreiras de guerreiro */}
        <path d="M 22 52 Q 32 44 40 53 L 34 68 Q 24 64 22 52 Z" fill="#546274" stroke="#1f242c" strokeWidth="1" />
        <path d="M 78 52 Q 68 44 60 53 L 66 68 Q 76 64 78 52 Z" fill="#546274" stroke="#1f242c" strokeWidth="1" />

        {/* Pescoço e queixo */}
        <rect x="44" y="38" width="12" height="14" fill="#a07d67" />

        {/* Cabeça / Elmo clássico D&D 2014 com viseira */}
        <path d="M 33 34 Q 32 12 50 12 Q 68 12 67 34 L 66 45 Q 50 50 34 45 Z" fill="url(#armor-grad)" stroke="#1a2028" strokeWidth="1" />
        {/* Crista dourada no elmo */}
        <path d="M 48 8 Q 50 5 52 8 L 52 24 L 48 24 Z" fill="url(#gold-trim)" />
        {/* Abertura T do elmo (estilo barbuta/sallet) */}
        <path d="M 42 28 L 58 28 L 58 32 L 52 32 L 52 42 L 48 42 L 48 32 L 42 32 Z" fill="#0d1015" />
        {/* Olhar firme dentro da fenda */}
        <circle cx="45" cy="30" r="1.2" fill="#88c0d0" />
        <circle cx="55" cy="30" r="1.2" fill="#88c0d0" />

        {/* Espada longa embainhada atrás do ombro */}
        <line x1="72" y1="18" x2="86" y2="4" stroke="#d8dee9" strokeWidth="3" strokeLinecap="round" />
        <line x1="68" y1="22" x2="76" y2="14" stroke="#ffe27a" strokeWidth="2.5" />
        <circle cx="88" cy="2" r="2.5" fill="#ffe27a" />

        {/* Escudo no antebraço */}
        <path d="M 12 60 Q 20 62 26 68 Q 22 84 14 90 Q 8 76 12 60 Z" fill="#3b4252" stroke="url(#gold-trim)" strokeWidth="1.2" />

        {/* Efeito de derrotado */}
        {isDefeated && (
          <g>
            <rect width="100" height="100" rx="10" fill="rgba(10, 10, 15, 0.75)" />
            <circle cx="50" cy="50" r="18" fill="#5c1010" stroke="#ff4d4d" strokeWidth="2" />
            <text x="50" y="56" fill="#fff" fontSize="16" fontWeight="bold" textAnchor="middle">✕</text>
          </g>
        )}
      </svg>
      <div className="portrait-name-tag">{name}</div>
    </div>
  )
}

export const GoblinPortrait: React.FC<PortraitProps> = ({
  name,
  isActor = false,
  isSelectedTarget = false,
  isAttacking = false,
  isDamaged = false,
  isDefeated = false,
  reducedMotion = false,
  size = 140,
}) => {
  return (
    <div
      className={`portrait-wrapper enemy ${isActor ? 'is-actor' : ''} ${isSelectedTarget ? 'is-target' : ''} ${
        isAttacking && !reducedMotion ? 'anim-attack-enemy' : ''
      } ${isDamaged && !reducedMotion ? 'anim-damage' : ''} ${isDefeated ? 'is-defeated' : ''}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 100 100"
        className="portrait-svg"
        style={{ width: '100%', height: '100%', borderRadius: '12px' }}
      >
        <defs>
          <radialGradient id="goblin-bg" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#30261e" />
            <stop offset="100%" stopColor="#14100c" />
          </radialGradient>
          <radialGradient id="skin-goblin" cx="45%" cy="35%" r="50%">
            <stop offset="0%" stopColor="#739a48" />
            <stop offset="100%" stopColor="#436323" />
          </radialGradient>
          <linearGradient id="leather-rag" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#5c442c" />
            <stop offset="100%" stopColor="#2c1e12" />
          </linearGradient>
        </defs>

        {/* Fundo sombrio de arena de treino */}
        <rect width="100" height="100" rx="10" fill="url(#goblin-bg)" />
        <rect
          width="94"
          height="94"
          x="3"
          y="3"
          rx="8"
          fill="none"
          stroke={isSelectedTarget ? '#ef4444' : '#854d0e'}
          strokeWidth={isSelectedTarget || isActor ? '2.5' : '1.5'}
        />

        {/* Orelhas pontudas compridas de goblin */}
        <path d="M 32 36 Q 10 24 4 30 Q 14 44 32 46 Z" fill="#587f2e" stroke="#2a4014" strokeWidth="1" />
        <path d="M 68 36 Q 90 24 96 30 Q 86 44 68 46 Z" fill="#587f2e" stroke="#2a4014" strokeWidth="1" />
        <path d="M 28 37 Q 16 30 12 34 Q 18 40 28 42 Z" fill="#7da350" />
        <path d="M 72 37 Q 84 30 88 34 Q 82 40 72 42 Z" fill="#7da350" />

        {/* Tronco com trapos de couro */}
        <path d="M 28 62 L 50 56 L 72 62 L 76 96 L 24 96 Z" fill="url(#leather-rag)" />
        {/* Costuras e cordas rústicas */}
        <line x1="42" y1="62" x2="58" y2="78" stroke="#a17446" strokeWidth="2" strokeDasharray="3 3" />
        <line x1="58" y1="62" x2="42" y2="78" stroke="#a17446" strokeWidth="2" strokeDasharray="3 3" />

        {/* Pescoço fino */}
        <rect x="43" y="48" width="14" height="12" fill="#436323" />

        {/* Cabeça angular de goblin */}
        <path d="M 32 34 Q 30 18 50 18 Q 70 18 68 34 Q 68 52 50 54 Q 32 52 32 34 Z" fill="url(#skin-goblin)" stroke="#223310" strokeWidth="1.2" />

        {/* Olhos amarelados e malévolos */}
        <ellipse cx="42" cy="32" rx="4.5" ry="3.5" fill="#facc15" />
        <ellipse cx="58" cy="32" rx="4.5" ry="3.5" fill="#facc15" />
        {/* Pupilas felinas */}
        <ellipse cx="42" cy="32" rx="1.2" ry="3.2" fill="#000" />
        <ellipse cx="58" cy="32" rx="1.2" ry="3.2" fill="#000" />

        {/* Nariz pontudo adunco */}
        <path d="M 48 32 L 50 42 L 44 41 Z" fill="#3c571f" />

        {/* Boca larga com presas afiadas */}
        <path d="M 38 45 Q 50 50 62 45 Q 50 47 38 45 Z" fill="#1f110b" />
        <polygon points="43,45 45,43 47,45" fill="#fdf6e2" />
        <polygon points="53,45 55,43 57,45" fill="#fdf6e2" />
        <polygon points="48,46 50,48 52,46" fill="#fdf6e2" />

        {/* Lâmina de treino na mão */}
        <line x1="22" y1="60" x2="10" y2="44" stroke="#9ca3af" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="24" y1="62" x2="20" y2="58" stroke="#78350f" strokeWidth="3" />

        {/* Efeito de derrotado / incapacitado */}
        {isDefeated && (
          <g>
            <rect width="100" height="100" rx="10" fill="rgba(10, 10, 15, 0.75)" />
            <circle cx="50" cy="50" r="18" fill="#5c1010" stroke="#ff4d4d" strokeWidth="2" />
            <text x="50" y="56" fill="#fff" fontSize="16" fontWeight="bold" textAnchor="middle">✕</text>
          </g>
        )}
      </svg>
      <div className="portrait-name-tag enemy">{name}</div>
    </div>
  )
}

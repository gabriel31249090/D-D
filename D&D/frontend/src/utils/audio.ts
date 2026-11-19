// Web Audio API Synthesizer and Ambient Soundscape player for ARCANUM

class SoundEffects {
  private ctx: AudioContext | null = null
  private ambientAudio: HTMLAudioElement | null = null

  private getContext(): AudioContext | null {
    if (typeof window === 'undefined') return null
    if (!this.ctx) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      if (AudioContextClass) {
        this.ctx = new AudioContextClass()
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume()
    }
    return this.ctx
  }

  // Reproduz som ambiente do mapa (Dungeoneer audio) em loop suave
  playAmbience(audioPath: string) {
    if (typeof window === 'undefined') return
    this.stopAmbience()
    try {
      this.ambientAudio = new Audio(audioPath)
      this.ambientAudio.loop = true
      this.ambientAudio.volume = 0.3
      this.ambientAudio.play().catch(() => {
        // Ignora política de autoplay se o usuário ainda não tiver interagido
      })
    } catch (e) {
      console.warn('Erro ao reproduzir áudio ambiente:', e)
    }
  }

  stopAmbience() {
    if (this.ambientAudio) {
      this.ambientAudio.pause()
      this.ambientAudio.currentTime = 0
      this.ambientAudio = null
    }
  }

  setAmbienceVolume(volume: number) {
    if (this.ambientAudio) {
      this.ambientAudio.volume = Math.max(0, Math.min(1, volume))
    }
  }

  // Som de golpe de espada (slashing)
  playSwordSlash() {
    const ctx = this.getContext()
    if (!ctx) return

    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    const now = ctx.currentTime

    osc.type = 'triangle'
    osc.frequency.setValueAtTime(440, now)
    osc.frequency.exponentialRampToValueAtTime(110, now + 0.15)

    gain.gain.setValueAtTime(0.3, now)
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.15)
  }

  // Som de impacto metálico / bloqueio de escudo
  playShieldBlock() {
    const ctx = this.getContext()
    if (!ctx) return

    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(320, now)
    osc.frequency.exponentialRampToValueAtTime(80, now + 0.2)

    gain.gain.setValueAtTime(0.4, now)
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.2)
  }

  // Som de acerto crítico
  playCriticalHit() {
    const ctx = this.getContext()
    if (!ctx) return

    const now = ctx.currentTime
    const osc1 = ctx.createOscillator()
    const osc2 = ctx.createOscillator()
    const gain = ctx.createGain()

    osc1.type = 'square'
    osc2.type = 'sine'

    osc1.frequency.setValueAtTime(587.33, now) // D5
    osc1.frequency.exponentialRampToValueAtTime(880, now + 0.3) // A5

    osc2.frequency.setValueAtTime(293.66, now)
    osc2.frequency.exponentialRampToValueAtTime(440, now + 0.3)

    gain.gain.setValueAtTime(0.4, now)
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35)

    osc1.connect(gain)
    osc2.connect(gain)
    gain.connect(ctx.destination)

    osc1.start(now)
    osc2.start(now)
    osc1.stop(now + 0.35)
    osc2.stop(now + 0.35)
  }

  // Som de clique de rolagem de dados
  playDiceRoll() {
    const ctx = this.getContext()
    if (!ctx) return

    const now = ctx.currentTime
    for (let i = 0; i < 4; i++) {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      const time = now + i * 0.05

      osc.type = 'sine'
      osc.frequency.setValueAtTime(600 + Math.random() * 400, time)

      gain.gain.setValueAtTime(0.15, time)
      gain.gain.exponentialRampToValueAtTime(0.01, time + 0.04)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(time)
      osc.stop(time + 0.04)
    }
  }

  // Som de vitória no encontro
  playVictoryFanfare() {
    const ctx = this.getContext()
    if (!ctx) return

    const notes = [261.63, 329.63, 392.0, 523.25] // C, E, G, C
    const now = ctx.currentTime

    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      const start = now + idx * 0.12

      osc.type = 'triangle'
      osc.frequency.setValueAtTime(freq, start)

      gain.gain.setValueAtTime(0.25, start)
      gain.gain.exponentialRampToValueAtTime(0.01, start + 0.3)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(start)
      osc.stop(start + 0.3)
    })
  }
}

export const sfx = new SoundEffects()

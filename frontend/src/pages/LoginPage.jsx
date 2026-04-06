import { useAuth } from '../contexts/AuthContext'
import { FcGoogle } from 'react-icons/fc'

export default function LoginPage() {
  const { signInWithGoogle } = useAuth()

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Marble gold veins — decorative */}
      <svg
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          opacity: 0.5,
        }}
      >
        <line x1="0" y1="30%" x2="100%" y2="65%" stroke="rgba(212,168,83,0.04)" strokeWidth="1" />
        <line x1="15%" y1="0" x2="85%" y2="100%" stroke="rgba(184,148,47,0.03)" strokeWidth="0.5" />
        <line x1="100%" y1="20%" x2="0" y2="85%" stroke="rgba(232,201,122,0.025)" strokeWidth="0.5" />
      </svg>

      {/* Central glow */}
      <div
        style={{
          position: 'absolute',
          top: '35%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 700,
          height: 700,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(212,168,83,0.06) 0%, transparent 60%)',
          pointerEvents: 'none',
        }}
      />

      <div
        className="animate-fade-in glass-heavy"
        style={{
          textAlign: 'center',
          padding: '56px 48px',
          position: 'relative',
          zIndex: 1,
          borderRadius: 'var(--radius-xl)',
          maxWidth: 440,
          width: '90%',
        }}
      >
        {/* Gold accent at top */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '20%',
            right: '20%',
            height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(212,168,83,0.4), transparent)',
          }}
        />

        {/* Logo */}
        <div style={{ marginBottom: 24 }}>
          <h1
            className="text-gold-gradient"
            style={{ fontSize: 44, fontWeight: 800, letterSpacing: '-1px' }}
          >
            Núcleo Digital
          </h1>
          <div
            style={{
              fontSize: 12,
              letterSpacing: '5px',
              textTransform: 'uppercase',
              color: 'var(--color-text-muted)',
              fontWeight: 600,
              marginTop: 6,
            }}
          >
            Task Manager
          </div>
        </div>

        {/* Subtitle */}
        <p
          style={{
            color: 'var(--color-text-secondary)',
            fontSize: 14,
            margin: '0 auto 36px',
            lineHeight: 1.7,
            maxWidth: 300,
          }}
        >
          Sistema interno de gestão de tarefas e produtividade da equipe NDMG.
        </p>

        {/* Google Login Button */}
        <button
          onClick={signInWithGoogle}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 32px',
            background: 'rgba(18, 18, 30, 0.6)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            border: '1px solid var(--color-border-light)',
            borderRadius: 'var(--radius-lg)',
            color: 'var(--color-text-primary)',
            fontSize: 15,
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.25s ease',
            fontFamily: 'var(--font-sans)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
            width: '100%',
            justifyContent: 'center',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'rgba(212, 168, 83, 0.4)'
            e.currentTarget.style.boxShadow = '0 8px 32px rgba(212,168,83,0.12)'
            e.currentTarget.style.transform = 'translateY(-2px)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border-light)'
            e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
          id="btn-google-login"
        >
          <FcGoogle size={22} />
          Entrar com Google Workspace
        </button>

        {/* Domain note */}
        <p
          style={{
            marginTop: 20,
            fontSize: 11,
            color: 'var(--color-text-muted)',
            letterSpacing: '0.3px',
          }}
        >
          Acesso restrito a contas <span style={{ color: 'var(--color-accent-gold)' }}>@mendoncagalvao.com.br</span>
        </p>
      </div>
    </div>
  )
}

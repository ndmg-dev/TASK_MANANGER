import { NavLink } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
  HiOutlineViewColumns,
  HiOutlineChartBarSquare,
  HiOutlineArrowLeftOnRectangle,
  HiOutlineShieldCheck,
} from 'react-icons/hi2'

const navItems = [
  { to: '/', icon: HiOutlineViewColumns, label: 'Kanban' },
  { to: '/dashboard', icon: HiOutlineChartBarSquare, label: 'Dashboard' },
]

export default function Sidebar() {
  const { user, session, signOut } = useAuth()

  return (
    <aside
      className="glass-heavy"
      style={{
        width: 250,
        height: '100vh',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '28px 0',
        flexShrink: 0,
        position: 'relative',
        zIndex: 10,
      }}
    >
      {/* Decorative gold line at top */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 1,
          background: 'linear-gradient(90deg, transparent 0%, rgba(212,168,83,0.3) 50%, transparent 100%)',
        }}
      />

      {/* Logo */}
      <div style={{ padding: '0 24px', marginBottom: 44 }}>
        <h1
          className="text-gold-gradient"
          style={{
            fontSize: 24,
            fontWeight: 800,
            letterSpacing: '-0.5px',
            lineHeight: 1,
          }}
        >
          Núcleo Digital
        </h1>
        <span
          style={{
            fontSize: 10,
            color: 'var(--color-text-muted)',
            fontWeight: 600,
            letterSpacing: '3px',
            textTransform: 'uppercase',
            marginTop: 6,
            display: 'block',
          }}
        >
          Task Manager
        </span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '0 12px' }}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: isActive ? 600 : 500,
              marginBottom: 4,
              transition: 'all 0.2s ease',
              color: isActive ? 'var(--color-accent-gold)' : 'var(--color-text-secondary)',
              background: isActive ? 'rgba(212, 168, 83, 0.08)' : 'transparent',
              borderLeft: isActive ? '2px solid var(--color-accent-gold)' : '2px solid transparent',
            })}
          >
            <Icon size={19} />
            {label}
          </NavLink>
        ))}

        {session?.dbUser?.role === 'admin' && (
          <NavLink
            to="/admin"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: isActive ? 600 : 500,
              marginTop: 16,
              transition: 'all 0.2s ease',
              color: isActive ? '#ef4444' : 'var(--color-danger)',
              background: isActive ? 'rgba(239, 68, 68, 0.08)' : 'transparent',
              borderLeft: isActive ? '2px solid #ef4444' : '2px solid transparent',
            })}
          >
            <HiOutlineShieldCheck size={19} />
            Painel Admin
          </NavLink>
        )}
      </nav>

      {/* User section */}
      <div
        style={{
          padding: '16px 16px',
          borderTop: '1px solid var(--color-border)',
          margin: '0 12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          {user?.user_metadata?.avatar_url ? (
            <img
              src={user.user_metadata.avatar_url}
              alt="Avatar"
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                border: '2px solid rgba(212, 168, 83, 0.4)',
                boxShadow: '0 0 12px rgba(212, 168, 83, 0.1)',
              }}
            />
          ) : (
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #d4a853, #b8942f)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 700,
                color: '#050508',
                boxShadow: '0 2px 10px rgba(212, 168, 83, 0.25)',
              }}
            >
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
          )}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
            </div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {user?.email}
            </div>
          </div>
        </div>
        <button
          onClick={signOut}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: 'none',
            border: 'none',
            color: 'var(--color-text-muted)',
            fontSize: 13,
            cursor: 'pointer',
            padding: '6px 0',
            transition: 'color 0.2s',
            width: '100%',
            fontFamily: 'var(--font-sans)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-danger)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
        >
          <HiOutlineArrowLeftOnRectangle size={16} />
          Sair
        </button>
      </div>
    </aside>
  )
}

import './Navbar.css';

/**
 * Page to Voice - Navigation Header Component
 *
 * @param {Object} props
 * @param {'login'|'register'|'account'} props.activeScreen
 * @param {Function} props.onNavigate
 * @param {Object|null} props.user
 */
export function Navbar({ activeScreen, onNavigate, user }) {
  return (
    <header className="navbar">
      <div
        className="nav-brand"
        onClick={() => onNavigate(user ? 'account' : 'login')}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onNavigate(user ? 'account' : 'login');
          }
        }}
        aria-label="Page to Voice Home"
      >
        <svg
          className="brand-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          {/* Audio wave / document voice icon */}
          <path d="M12 2v20M17 5v14M7 8v8M22 10v4M2 10v4" />
        </svg>
        <span>Page to Voice</span>
        <span className="brand-badge">Auth</span>
      </div>

      <nav aria-label="Main Navigation">
        <ul className="nav-items">
          {!user ? (
            <>
              <li>
                <button
                  type="button"
                  className={`nav-link ${activeScreen === 'login' ? 'active' : ''}`}
                  onClick={() => onNavigate('login')}
                  aria-current={activeScreen === 'login' ? 'page' : undefined}
                >
                  Sign In
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-link ${activeScreen === 'register' ? 'active' : ''}`}
                  onClick={() => onNavigate('register')}
                  aria-current={activeScreen === 'register' ? 'page' : undefined}
                >
                  Create Account
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <button
                  type="button"
                  className={`nav-link ${activeScreen === 'account' ? 'active' : ''}`}
                  onClick={() => onNavigate('account')}
                  aria-current={activeScreen === 'account' ? 'page' : undefined}
                >
                  Account Profile
                </button>
              </li>
              <li>
                <div className="nav-user-pill">
                  <span className="user-status-dot" aria-hidden="true" />
                  <span>{user.name || user.email}</span>
                </div>
              </li>
            </>
          )}
        </ul>
      </nav>
    </header>
  );
}

export default Navbar;

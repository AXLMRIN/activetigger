import cx from 'classnames';
import { FC, useState } from 'react';
import { Link } from 'react-router-dom';

import { useAppContext } from '../../core/context';

const PAGES: { id: string; label: string; href: string }[] = [
  { id: 'projects', label: 'Projects', href: '/projects' },
  { id: 'actions', label: 'Actions', href: '/actions' },
  { id: 'documentation', label: 'Documentation', href: '/documentation' },
  { id: 'login', label: 'Login', href: '/login' },
];

interface NavBarPropsType {
  currentPage?: string;
}

const NavBar: FC<NavBarPropsType> = ({ currentPage }) => {
  const { appContext } = useAppContext();
  const { user } = appContext;

  const [expanded, setExpanded] = useState<boolean>(false);

  return (
    <div className="bg-primary">
      <nav className="navbar navbar-dark navbar-expand-lg bg-primary">
        <div className="container">
          <Link className="navbar-brand" to="/">
            Active Tigger
          </Link>
          <button
            className="navbar-toggler"
            type="button"
            aria-controls="navbarSupportedContent"
            aria-expanded={expanded}
            aria-label="Toggle navigation"
            onClick={() => setExpanded((e) => !e)}
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div
            className={cx('navbar-collapse', expanded ? 'expanded' : 'collapse')}
            id="navbarSupportedContent"
          >
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              {PAGES.map(({ id, label, href }) => (
                <li key={id} className="nav-item">
                  <Link
                    className={cx('nav-link', currentPage === id && 'active')}
                    aria-current={currentPage === id ? 'page' : undefined}
                    to={href}
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
            {user && <span className="navbar-text">Logged as {user.username}</span>}
          </div>
        </div>
      </nav>
    </div>
  );
};

export default NavBar;

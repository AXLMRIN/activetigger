import { FC } from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/at.png';
import { useGetActiveUsers } from '../core/api';
import { useAuth } from '../core/auth';
import { LoginForm } from './forms/LoginForm';
import Notifications from './layout/Notifications';

export const HomePage: FC = () => {
  const { authenticatedUser } = useAuth();
  const { users } = useGetActiveUsers();
  return (
    <>
      <main className="container-fluid">
        <div className="row">
          <div className="col-0 col-lg-3" />
          <div className="col-12 col-lg-6">
            <center>
              <h1>Active Tigger</h1>
              <h3>Explore, Classify & Analyze Text</h3>

              <img
                src={logo}
                alt="ActiveTigger"
                className="me-2"
                style={{ width: '200px', height: '200px' }}
              />
              <div className="alert alert-warning fw-bold mt-3">
                ⚠️ Warning: This interface is in beta testing.
                <br></br>
                Continuity of service is not guaranteed, please save your data. <br></br>
                <a href="https://github.com/emilienschultz/activetigger/issues">
                  Please report any bug or problem on the Github of the project
                </a>
                .
              </div>
              {!authenticatedUser ? (
                <LoginForm />
              ) : (
                <div>
                  <div className="user-info">
                    You're logged in as <span>{authenticatedUser.username}</span> ( status :{' '}
                    {authenticatedUser.status})
                  </div>
                  <Link
                    to="/projects"
                    className="btn btn-primary btn-lg shadow-sm rounded-pill m-3"
                  >
                    Go to your projects
                  </Link>{' '}
                  <div className="explanations">Active users : {users?.length}</div>
                </div>
              )}

              <div className="general-info mt-3">
                <div>
                  Last update of the frontend<b> {__BUILD_DATE__}</b>
                </div>
                <div>For any information, please contact emilien.schultz [at] ensae.fr</div>
                <div className="text-muted">
                  Credits : Julien Boelaert & Étienne Ollion & Émilien Schultz & Ouestware
                </div>
              </div>
            </center>
          </div>
        </div>
        <footer className="footer mt-auto py-1 bg-primary text-white fixed-bottom">
          <div className="container text-center">
            <i className="fas fa-info-circle"></i>
            <span className="ml-2">
              CREST / CSS @ IPP © 2024 - <i>under development -</i>
            </span>
          </div>
        </footer>
      </main>
      <Notifications />
    </>
  );
};

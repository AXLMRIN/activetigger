import { FC } from 'react';
import { useLocation } from 'react-router-dom';

import { useAuth } from '../core/auth';
import { LoginForm } from './forms/LoginForm';
import { PageLayout } from './layout/PageLayout';

export const LoginPage: FC = () => {
  const { authenticatedUser } = useAuth();
  const { state } = useLocation();

  return (
    <PageLayout currentPage="login">
      <div className="container-fluid">
        {authenticatedUser?.username && (
          <div className="row">
            <div className="col-1"></div>

            <div className="col-11 col-lg-6">
              You're logged in as {authenticatedUser.username} ({authenticatedUser.status})
            </div>
          </div>
        )}
        <div className="row">
          <div className="col-1"></div>

          <div className="col-11 col-lg-6">
            <LoginForm redirectTo={state?.path || '/projects'} />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

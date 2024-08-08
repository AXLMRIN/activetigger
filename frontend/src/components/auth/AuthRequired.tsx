import { Middleware } from 'openapi-fetch';
import { FC, PropsWithChildren, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { api } from '../../core/api';
import { useAuth } from '../../core/auth';
import { useNotifications } from '../../core/notifications';

/**
 * AuthRequired
 * a component which protect private routes from access by unauthenticated user
 * @returns children or a redirection to the login form
 */
export const AuthRequired: FC<PropsWithChildren> = ({ children }) => {
  // first we get authenticated user state
  const { authenticatedUser } = useAuth();
  // location is provided by react-router library and contains the current page (i.e. in which URL path this component has been mounted)
  const location = useLocation();
  const navigate = useNavigate();
  const { notify } = useNotifications();

  const redirectToLogin = useCallback(
    (message: string) => {
      notify({
        type: 'error',
        message,
      });
      setTimeout(
        () => navigate('/login', { state: { path: location.pathname }, replace: true }),
        500,
      );
    },
    [navigate, notify, location],
  );

  useEffect(() => {
    const apiErrorMiddleware: Middleware = {
      // on response check if session is correct
      onResponse: async ({ response }) => {
        // if session is expired or invalid we catch the 401 and redirect to login page
        if (response.status === 401) {
          redirectToLogin('Invalid user session: redirecting you to login page...');
        } else {
          if (response.status !== 200) {
            //TODO : check error body is correct
            const { body, ...resOptions } = response;

            notify({ type: 'error', message: await response.json() });
            return new Response(body, resOptions);
          }
        }
      },
    };
    if (!authenticatedUser) {
      redirectToLogin('you must authenticate to view this page.');
    }
    api.use(apiErrorMiddleware);
    return () => {
      api.eject(apiErrorMiddleware);
    };
  }, []);

  if (authenticatedUser)
    // if the user is currently authenticated just let him go through its destination by mounting children (i.e. the requested page component)
    return children;
  else {
    // else ask him to first login and then redirects him back to where we wanted to go
    return null;
  }
};

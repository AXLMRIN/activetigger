import { createBrowserRouter } from 'react-router-dom';

import { HomePage } from '../components/HomePage';
import { LoginPage } from '../components/LoginPage';
import { ProjectNewPage } from '../components/ProjectNewPage';
import { ProjectPage } from '../components/ProjectPage';
import { ProjectsPage } from '../components/ProjectsPage';
import { AppContextValue } from './context';

export function getRouter(_appContext: AppContextValue) {
  return createBrowserRouter([
    {
      path: '/',
      element: <HomePage />,
    },
    {
      path: '/login',
      element: <LoginPage />,
    },
    { path: '/projects/new', element: <ProjectNewPage /> },
    {
      path: '/projects',
      element: <ProjectsPage />,
    },
    {
      path: '/projects/:projectName',
      element: <ProjectPage />,
    },
  ]);
}

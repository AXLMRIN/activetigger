import { Outlet, createBrowserRouter } from 'react-router-dom';

import { CurrentProjectMonitoring } from '../components/CurrentProjectMonitoring';
import { HelpPage } from '../components/HelpPage';
import { HomePage } from '../components/HomePage';
import { LoginPage } from '../components/LoginPage';
import { ProjectAnnotationPage } from '../components/ProjectAnnotationPage';
import { ProjectExploratePage } from '../components/ProjectExploratePage';
import { ProjectFeaturesPage } from '../components/ProjectFeaturesPage';
import { ProjectNewPage } from '../components/ProjectNewPage';
import { ProjectPage } from '../components/ProjectPage';
import { ProjectParametersPage } from '../components/ProjectParametersPage';
import { ProjectsPage } from '../components/ProjectsPage';
import { AuthRequired } from '../components/auth/AuthRequired';

export function getRouter() {
  return createBrowserRouter([
    {
      path: '/',
      element: <HomePage />,
    },
    {
      path: '/login',
      element: <LoginPage />,
    },
    {
      path: '/help',
      element: <HelpPage />,
    },
    {
      path: '/projects/new',
      element: (
        //AuthRequired makes sure that the user is currently authenticated before rendering this route page
        <AuthRequired>
          <ProjectNewPage />
        </AuthRequired>
      ),
    },
    {
      path: '/projects/',
      element: (
        <AuthRequired>
          <ProjectsPage />
        </AuthRequired>
      ),
    },
    {
      path: '/projects/:projectName',
      element: (
        <AuthRequired>
          <CurrentProjectMonitoring />
          <Outlet />
        </AuthRequired>
      ),
      children: [
        {
          path: '/projects/:projectName/',
          element: <ProjectPage />,
        },
        {
          path: '/projects/:projectName/annotate/:elementId',
          element: <ProjectAnnotationPage />,
        },
        {
          path: '/projects/:projectName/features/',
          element: <ProjectFeaturesPage />,
        },
        {
          path: '/projects/:projectName/annotate/',
          element: <ProjectAnnotationPage />,
        },
        {
          path: '/projects/:projectName/parameters',
          element: <ProjectParametersPage />,
        },
        {
          path: '/projects/:projectName/explorate',
          element: <ProjectExploratePage />,
        },
      ],
    },
  ]);
}

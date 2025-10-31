import { FC, PropsWithChildren } from 'react';

import { useAuth } from '../../core/auth';
import { useAppContext } from '../../core/context';
import { PageLayout } from './PageLayout';
import { ProjectActionsSidebar } from './ProjectActionsSideBar';
import { StatusNotch } from './StatusNotch';

export type PossibleProjectActions =
  | 'tag'
  | 'model'
  | 'validate'
  | 'explore'
  | 'curate'
  | 'monitor'
  | 'test'
  | 'generate'
  | 'export'
  | 'settings'
  | 'predict';

type ProjectPageLayoutProps = PropsWithChildren<{
  projectName: string | undefined;
  currentAction?: PossibleProjectActions;
}>;

/* On a specific project, add the ActionSideBar*/
export const ProjectPageLayout: FC<ProjectPageLayoutProps> = ({
  projectName,
  currentAction,
  children,
}) => {
  // get the current state of the project
  const {
    appContext: { currentProject: project, currentScheme, phase, developmentMode },
  } = useAppContext();

  // get current user
  const { authenticatedUser } = useAuth();
  if (!authenticatedUser) return '';

  return (
    <PageLayout currentPage="projects" projectName={projectName || null}>
      <div className="container-fluid">
        <div className="row">
          <div className="col-1 col-md-3 col-lg-2">
            <ProjectActionsSidebar
              projectState={project || null}
              currentProjectAction={currentAction}
              currentScheme={currentScheme}
              currentUser={authenticatedUser.username}
              currentMode={phase}
              developmentMode={developmentMode}
            />
          </div>
          <div className="col-11 col-md-9 col-lg-10">{children}</div>
        </div>
      </div>
      <StatusNotch
        projectState={project || null}
        currentUser={authenticatedUser.username}
        currentMode={phase}
        developmentMode={developmentMode}
      />
    </PageLayout>
  );
};

import classNames from 'classnames';
import { FC } from 'react';
import { FaCloudDownloadAlt } from 'react-icons/fa';
import { FaListCheck } from 'react-icons/fa6';
import { HiMiniRectangleGroup } from 'react-icons/hi2';
import { IoBookSharp, IoSettingsSharp } from 'react-icons/io5';
import { MdModelTraining, MdOutlineHomeMax } from 'react-icons/md';
import { PiTagDuotone } from 'react-icons/pi';
import { RiAiGenerate } from 'react-icons/ri';
import { Link } from 'react-router-dom';
import { useGetServer } from '../../core/api';
import { useAuth } from '../../core/auth';
import { useNotifications } from '../../core/notifications';
import { ProjectStateModel } from '../../types';
import { PossibleProjectActions } from './ProjectPageLayout';

import { useAppContext } from '../../core/context';

/* define a component for project action bar 
with the project & the current action*/
export const ProjectActionsSidebar: FC<{
  projectState: ProjectStateModel | null;
  currentProjectAction?: PossibleProjectActions;
  currentMode?: string;
  currentScheme?: string;
  currentUser: string;
  developmentMode?: boolean;
}> = ({
  currentProjectAction,
  projectState,
  currentUser,
  currentScheme,
  //  developmentMode,
}) => {
  const projectName = projectState ? projectState.params.project_slug : null;
  const { authenticatedUser } = useAuth();
  // const nbUsers = projectState ? projectState.users.length : 0;

  // 2 types of menu
  const onlyAnnotator = authenticatedUser?.status === 'annotator';

  // display the number of current processes on the server
  const { disk } = useGetServer(projectState || null);

  // notify if disk is full
  const { notify } = useNotifications();
  if (disk ? Number(disk['proportion']) > 98 : false) {
    notify({
      message: 'Disk is almost full, please delete some files or alert the admin',
      type: 'warning',
    });
  }

  return (
    <div className={`project-sidebar d-flex flex-column flex-shrink-0 bg-light`}>
      {!onlyAnnotator && (
        <ul className="nav nav-pills flex-column mb-auto">
          <li className="nav-item  d-none d-md-inline">
            <div
              className="nav-link d-inline-block rounded-pill px-3 py-1 bg-light"
              style={{ lineHeight: '1.1' }}
            >
              <div className="fw-semibold text-dark text-truncate">{projectName}</div>
              <div
                className="small text-primary"
                style={{
                  marginTop: '-2px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
                title={currentScheme}
              >
                {currentScheme && currentScheme.length > 15
                  ? `${currentScheme.substring(0, 15)}…`
                  : currentScheme}
              </div>
            </div>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}`}
              className={classNames('nav-link', !currentProjectAction && 'active')}
              aria-current="page"
              title="Access and modify your project parameters"
            >
              <IoBookSharp />
              <span className="ms-1 sidemenulabel">Codebook</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/explore`}
              className={classNames('nav-link', currentProjectAction === 'explore' && 'active')}
              aria-current="page"
              title="Explore your data"
            >
              <HiMiniRectangleGroup />
              <span className="ms-1 sidemenulabel">Explore</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/tag`}
              className={classNames('nav-link', currentProjectAction === 'tag' && 'active')}
              aria-current="page"
              title="Tag your data"
            >
              <PiTagDuotone />
              <span className="ms-1 sidemenulabel">Annotate</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/model`}
              className={classNames('nav-link', currentProjectAction === 'model' && 'active')}
              aria-current="page"
              title="Manage your models"
            >
              <MdModelTraining />
              <span className="ms-1 sidemenulabel">Model</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/validate`}
              className={classNames('nav-link', currentProjectAction === 'validate' && 'active')}
              aria-current="page"
              title="Test your model"
            >
              <FaListCheck />

              <span className="ms-1 sidemenulabel">Evaluate</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/export`}
              className={classNames('nav-link', currentProjectAction === 'export' && 'active')}
              aria-current="page"
              title="Export everything"
            >
              <FaCloudDownloadAlt />
              <span className="ms-1 sidemenulabel">Export</span>
            </Link>
          </li>

          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/generate`}
              className={classNames('nav-link', currentProjectAction === 'generate' && 'active')}
              aria-current="page"
              title="Use generative tools to annotate your data"
              style={{ color: '#e00eebff' }}
            >
              <RiAiGenerate />
              <span className="ms-1">Generative</span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/settings`}
              className={classNames('nav-link', currentProjectAction === 'settings' && 'active')}
              aria-current="page"
              title="Project settings"
            >
              <IoSettingsSharp />
              <span className="ms-1 sidemenulabel">Settings</span>
            </Link>
          </li>
        </ul>
      )}
      {onlyAnnotator && (
        <ul className="nav nav-pills flex-column mb-auto">
          <li className="nav-item mt-3">
            <Link
              to={`/projects/${projectName}`}
              className={classNames('nav-link', !currentProjectAction && 'active')}
              aria-current="page"
              title="Project"
            >
              <MdOutlineHomeMax className="m-2" />
              <span>
                <b>{projectName}</b>
              </span>
              <span
                className="mx-2 d-none d-md-inline"
                style={{ fontSize: '0.875rem', color: 'grey' }}
              >
                {currentScheme}
              </span>
            </Link>
          </li>
          <li className="nav-item">
            <Link
              to={`/projects/${projectName}/tag`}
              className={classNames('nav-link', currentProjectAction === 'tag' && 'active')}
              aria-current="page"
              title="Tag"
            >
              <PiTagDuotone />
              <span>Tag</span>
            </Link>
          </li>
        </ul>
      )}
    </div>
  );
};

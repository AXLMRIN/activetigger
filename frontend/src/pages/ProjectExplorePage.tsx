import { FC, useState } from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import { useParams } from 'react-router-dom';
import { BertopicPage } from '../pages/BertopicPage';

import { DataTabular } from '../components/DataTabular';
import { ProjectPageLayout } from '../components/layout/ProjectPageLayout';
import { ProjectionManagement } from '../components/ProjectionManagement';
import { useAppContext } from '../core/context';

/**
 * Component to display the export page
 */
export const ProjectExplorePage: FC = () => {
  const { projectName } = useParams();
  const {
    appContext: { currentScheme, currentProject: project, phase },
  } = useAppContext();
  const availableLabels =
    currentScheme && project && project.schemes.available[currentScheme]
      ? project.schemes.available[currentScheme].labels
      : [];
  const [kindScheme] = useState<string>(
    currentScheme && project && project.schemes.available[currentScheme]
      ? project.schemes.available[currentScheme].kind || 'multiclass'
      : 'multiclass',
  );
  const availableFeatures = project?.features.available ? project?.features.available : [];

  return (
    <ProjectPageLayout projectName={projectName} currentAction="explore">
      <div className="container-fluid">
        <div className="row">
          <div className="col-12">
            <Tabs className="mt-3" defaultActiveKey="tabular">
              <Tab eventKey="tabular" title="Tabular view">
                <DataTabular
                  projectSlug={projectName || ''}
                  currentScheme={currentScheme || ''}
                  phase={phase}
                  availableLabels={availableLabels}
                  kindScheme={kindScheme}
                />
              </Tab>
              <Tab eventKey="visualization" title="Visualization" unmountOnExit={true}>
                {phase != 'test' && (
                  <ProjectionManagement
                    projectName={projectName || null}
                    currentScheme={currentScheme || null}
                    availableFeatures={availableFeatures}
                    currentElementId={undefined}
                  />
                )}
                {phase == 'test' && (
                  <div className="alert alert-warning mt-3">
                    Test mode activated - vizualisation disabled
                  </div>
                )}
              </Tab>
              <Tab eventKey="bertopic" title="Topic model">
                <BertopicPage />
              </Tab>
            </Tabs>
          </div>
        </div>
      </div>
    </ProjectPageLayout>
  );
};

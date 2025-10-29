import { FC, useMemo, useState } from 'react';
import { Tab, Tabs } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import Select from 'react-select';
import { DisplayScoresMenu } from '../components/DisplayScoresMenu';
import { DisplayTrainingProcesses } from '../components/DisplayTrainingProcesses';
import { ProjectPageLayout } from '../components/layout/ProjectPageLayout';
import { useComputeModelPrediction, useModelInformations } from '../core/api';
import { useAppContext } from '../core/context';
import { MLStatisticsModel, ModelDescriptionModel } from '../types';

/**
 * Buttons
 */

interface validateButtonsProps {
  projectSlug: string | null;
  modelName: string | null;
  kind: string | null;
  currentScheme: string | null;
  isComputing: boolean;
  setCurrentModel: (val: null | string) => void;
}

export const ValidateButtons: FC<validateButtonsProps> = ({
  modelName,
  kind,
  isComputing,
  currentScheme,
  projectSlug,
  setCurrentModel,
}) => {
  const { computeModelPrediction } = useComputeModelPrediction(projectSlug || null, 16);
  return (
    <div>
      <button
        className="btn btn-primary my-2"
        onClick={() => {
          computeModelPrediction(modelName || '', 'annotable', currentScheme, kind);
          setCurrentModel(null);
        }}
        disabled={isComputing}
      >
        Compute statistics on annotations
      </button>
    </div>
  );
};

/**
 * Component to display the export page
 */
export const ProjectValidatePage: FC = () => {
  const { projectName } = useParams();
  const {
    appContext: { currentScheme, currentProject: project, isComputing },
  } = useAppContext();

  // model selected
  const [currentSimpleModelName, setCurrentSimpleModelName] = useState<string | null>(null);
  const [currentBertModelName, setCurrentBertModelName] = useState<string | null>(null);

  const { model: bertModelInformations } = useModelInformations(
    projectName || null,
    currentBertModelName || null,
    'bert',
    isComputing,
  );

  // get model information from api
  const { model: simpleModelInformations } = useModelInformations(
    projectName || null,
    currentSimpleModelName || null,
    'simple',
    isComputing,
  );

  const availableBertModels = useMemo(
    () =>
      project?.languagemodels.available
        ? project?.languagemodels.available[currentScheme || '']
        : [],
    [project?.languagemodels.available, currentScheme],
  );

  const availableSimpleModels = useMemo(
    () =>
      project?.simplemodel.available
        ? (project?.simplemodel.available[currentScheme || ''] as ModelDescriptionModel[])
        : [],
    [project?.simplemodel.available, currentScheme],
  );

  return (
    <ProjectPageLayout projectName={projectName} currentAction="validate">
      <div className="container-fluid">
        <div className="row">
          <div className="col-12">
            <Tabs id="panel" className="mt-3" defaultActiveKey="quick">
              <Tab eventKey="quick" title="Quick">
                <div className="explanations">
                  Compute statistics on annotations for machine learning models
                </div>
                <div>
                  <label htmlFor="selected-model">Existing models</label>
                  <Select
                    options={Object.values(availableSimpleModels || {}).map((e) => ({
                      value: e.name,
                      label: e.name,
                    }))}
                    value={
                      currentSimpleModelName
                        ? { value: currentSimpleModelName, label: currentSimpleModelName }
                        : null
                    }
                    onChange={(selectedOption) => {
                      setCurrentSimpleModelName(selectedOption ? selectedOption.value : null);
                    }}
                    isSearchable
                    className="w-50 mt-1"
                  />
                </div>
                <ValidateButtons
                  modelName={currentSimpleModelName}
                  kind="simple"
                  currentScheme={currentScheme || null}
                  projectSlug={projectName || null}
                  isComputing={isComputing}
                  setCurrentModel={setCurrentSimpleModelName}
                />

                {simpleModelInformations && (
                  <DisplayScoresMenu
                    scores={
                      simpleModelInformations.scores as unknown as Record<string, MLStatisticsModel>
                    }
                    modelName={currentSimpleModelName || ''}
                  />
                )}
              </Tab>
              <Tab eventKey="bert" title="BERT">
                <div className="explanations">
                  Compute statistics on annotations for BERT models
                </div>
                <div>
                  <label htmlFor="selected-model">Existing models</label>
                  <Select
                    options={Object.keys(availableBertModels || {}).map((e) => ({
                      value: e,
                      label: e,
                    }))}
                    value={
                      currentBertModelName
                        ? { value: currentBertModelName, label: currentBertModelName }
                        : null
                    }
                    onChange={(selectedOption) => {
                      setCurrentBertModelName(selectedOption ? selectedOption.value : null);
                    }}
                    isSearchable
                    className="w-50 mt-1"
                  />
                </div>
                <ValidateButtons
                  modelName={currentBertModelName}
                  kind="bert"
                  currentScheme={currentScheme || null}
                  projectSlug={projectName || null}
                  isComputing={isComputing}
                  setCurrentModel={setCurrentBertModelName}
                />
                <div>
                  <DisplayTrainingProcesses
                    projectSlug={projectName || null}
                    processes={project?.languagemodels.training}
                    processStatus="testing"
                    displayStopButton={isComputing}
                  />

                  {bertModelInformations && !project?.params.test && (
                    <div className="col-12">
                      <div className="alert alert-warning m-4">
                        No testset available for this project. Please create one to compute
                        predictions on the project main page
                      </div>
                    </div>
                  )}

                  {bertModelInformations && (
                    <DisplayScoresMenu
                      scores={
                        bertModelInformations.scores as unknown as Record<string, MLStatisticsModel>
                      }
                      modelName={currentSimpleModelName || ''}
                    />
                  )}

                  {/* {bertModelInformation && (
                    <DisplayScores
                      scores={
                        bertModelInformation.scores.valid_scores as unknown as Record<
                          string,
                          number
                        >
                      }
                      modelName={currentBertModelName || ''}
                      title="Validation scores"
                    />
                  )}

                  {bertModelInformation && (
                    <DisplayScores
                      scores={
                        bertModelInformation.scores.test_scores as unknown as Record<string, number>
                      }
                      modelName={currentBertModelName || ''}
                      title="Test scores"
                    />
                  )} */}
                </div>
              </Tab>
            </Tabs>
          </div>
        </div>
      </div>
    </ProjectPageLayout>
  );
};

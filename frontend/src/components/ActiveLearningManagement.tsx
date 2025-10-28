import { Dispatch, FC, SetStateAction, useEffect, useState } from 'react';

import Select from 'react-select';
import { useRetrainSimpleModel } from '../core/api';
import { AppContextValue } from '../core/context';
import { ModelDescriptionModel } from '../types';

/**
 * Component to manage one label
 */

interface ActiveLearningManagementProps {
  projectSlug: string | null;
  currentScheme: string | null;
  history: string[];
  availableSimpleModels: ModelDescriptionModel[];
  activeSimepleModel?: string | null;
  freqRefreshSimpleModel?: number;
  setAppContext: Dispatch<SetStateAction<AppContextValue>>;
}

export const ActiveLearningManagement: FC<ActiveLearningManagementProps> = ({
  projectSlug,
  currentScheme,
  availableSimpleModels,
  activeSimepleModel,
  freqRefreshSimpleModel,
  history,
  setAppContext,
}) => {
  const [currentSimpleModel, setCurrentSimpleModel] = useState<string | null>(null);
  // function to change refresh frequency
  const refreshFreq = (newValue: number) => {
    setAppContext((prev) => ({ ...prev, freqRefreshSimpleModel: newValue }));
  };
  const setActiveSimpleModel = (newValue: string | null) => {
    setAppContext((prev) => ({ ...prev, activeSimpleModel: newValue }));
  };
  const { retrainSimpleModel } = useRetrainSimpleModel(projectSlug, currentScheme);

  // manage retrain of the model
  const [updatedSimpleModel, setUpdatedSimpleModel] = useState(false);
  useEffect(() => {
    if (
      !updatedSimpleModel &&
      freqRefreshSimpleModel &&
      activeSimepleModel &&
      history.length > 0 &&
      history.length % freqRefreshSimpleModel == 0
    ) {
      setUpdatedSimpleModel(true);
      retrainSimpleModel(activeSimepleModel);
      console.log('RETRAIN');
    }
    if (
      updatedSimpleModel &&
      freqRefreshSimpleModel &&
      history.length % freqRefreshSimpleModel != 0
    ) {
      setUpdatedSimpleModel(false);
    }
  }, [
    freqRefreshSimpleModel,
    setUpdatedSimpleModel,
    activeSimepleModel,
    updatedSimpleModel,
    retrainSimpleModel,
    history,
  ]);

  return (
    <div className="container-fluid">
      <div>
        Current active learning model : {activeSimepleModel ? activeSimepleModel : 'No model used'}
      </div>
      <div>
        <div className="d-flex align-items-center ">
          <Select
            options={Object.values(availableSimpleModels || {}).map((e) => ({
              value: e.name,
              label: e.name,
            }))}
            value={
              currentSimpleModel ? { value: currentSimpleModel, label: currentSimpleModel } : null
            }
            onChange={(selectedOption) => {
              setCurrentSimpleModel(selectedOption ? selectedOption.value : null);
            }}
            isSearchable
            className="w-50"
            placeholder="Select a model for active learning"
          />
          <button
            className="btn btn-primary mx-2"
            onClick={() => setActiveSimpleModel(currentSimpleModel)}
          >
            Select
          </button>
        </div>
      </div>
      <div className="d-flex align-items-center">
        <label htmlFor="frequencySlider">Retrain model every</label>
        <input
          type="number"
          id="frequencySlider"
          min="0"
          max="500"
          value={freqRefreshSimpleModel}
          onChange={(e) => {
            refreshFreq(Number(e.currentTarget.value));
          }}
          step="1"
          style={{ width: '80px', margin: '10px' }}
        />
        annotations (0 for no refreshing)
      </div>
    </div>
  );
};

import { FC, useEffect } from 'react';
import { Tab, Tabs } from 'react-bootstrap';
import { Controller, SubmitHandler, useForm } from 'react-hook-form';
import Select from 'react-select';
import { useTrainSimpleModel } from '../core/api';
import { useAppContext } from '../core/context';
import { useNotifications } from '../core/notifications';
import { SimpleModelModel } from '../types';

// TODO: default values + avoid generic parameters

interface SimpleModelManagementProps {
  projectName: string | null;
  currentScheme: string | null;
  availableSimpleModels: Record<string, Record<string, number>>;
  availableFeatures: string[];
  availableLabels: string[];
  kindScheme: string;
  currentModel?: Record<string, never>;
}

export const SimpleModelManagement: FC<SimpleModelManagementProps> = ({
  projectName,
  currentScheme,
  availableSimpleModels,
  availableFeatures,
  availableLabels,
  kindScheme,
  currentModel,
}) => {
  // element from the context
  const {
    appContext: { freqRefreshSimpleModel },
    setAppContext,
  } = useAppContext();
  const { notify } = useNotifications();

  // hooks to update
  const { trainSimpleModel } = useTrainSimpleModel(projectName, currentScheme);

  // available features
  const features = availableFeatures.map((e) => ({ value: e, label: e }));

  // function to change refresh frequency
  const refreshFreq = (newValue: number) => {
    setAppContext((prev) => ({ ...prev, freqRefreshSimpleModel: newValue }));
  };

  function getRandomName() {
    return `Simplemodel-${currentScheme}-${Math.random().toString(36).substring(2, 8)}`;
  }

  // create form
  const { register, handleSubmit, control, watch, setValue } = useForm<SimpleModelModel>({
    defaultValues: {
      name: getRandomName(),
      model: 'liblinear',
      scheme: currentScheme || undefined,
      params: {
        cost: 1,
        C: 32,
        n_neighbors: 3,
        alpha: 1,
        n_estimators: 500,
        max_features: null,
      },
      dichotomize: kindScheme == 'multilabel' ? availableLabels[0] : undefined,
    },
  });

  // update the values from the current model if it exists
  useEffect(() => {
    if (currentModel?.params) {
      const filteredParams = Object.entries(currentModel.params)
        .filter(([key]) => key !== 'features') // key is the param name
        .reduce(
          (acc, [key, value]) => {
            if (
              typeof value === 'string' ||
              typeof value === 'number' ||
              typeof value === 'boolean'
            ) {
              acc[key] = value;
            }
            return acc;
          },
          {} as Record<string, string | number | boolean>,
        );

      setValue('params', filteredParams);
    }
  }, [currentModel, setValue]);

  // state for the model selected to modify parameters
  const selectedModel = watch('model');

  // action when form validated
  const onSubmit: SubmitHandler<SimpleModelModel> = async (formData) => {
    const watchedFeatures = watch('features');
    if (watchedFeatures.length == 0) {
      notify({ type: 'error', message: 'Please select at least one feature' });
      return;
    }
    await trainSimpleModel(formData);
    //    setShowForm(false);
  };

  // build default features selected
  // const default_features = features.filter((e) => e.label.includes(e.value));
  type Feature = {
    label: string;
    value: string;
  };
  const filterFeatures = (features: Feature[]) => {
    const filtered = features.filter((e) => /sbert|fasttext/i.test(e.label));
    const predictFeature = features.find((e) => /predict/i.test(e.label)); // Trouve le premier "predict"

    if (predictFeature) {
      filtered.push(predictFeature);
    }

    return filtered;
  };
  const predictions = filterFeatures(features);
  const defaultFeatures = [predictions[predictions.length - 1]];

  return (
    <Tabs id="simplemodels" className="mt-1" defaultActiveKey="existing">
      <Tab eventKey="existing" title="Existing"></Tab>
      <Tab eventKey="new" title="New">
        <div>
          <h5 className="subsection">Train a new quick model</h5>
          <form onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label htmlFor="name">Model name</label>
              <input
                type="text"
                id="name"
                placeholder="Model name"
                className="form-control"
                {...register('name')}
              />
            </div>
            <div>
              <label htmlFor="features">Features used to predict</label>
              {/* Specific management of the component with the react-form controller */}
              <Controller
                name="features"
                control={control}
                defaultValue={defaultFeatures.map((e) => (e ? e.value : null))}
                render={({ field: { onChange, value } }) => (
                  <Select
                    options={features}
                    isMulti
                    value={features.filter((option) => value.includes(option.value))}
                    onChange={(selectedOptions) => {
                      onChange(
                        selectedOptions ? selectedOptions.map((option) => option.value) : [],
                      );
                    }}
                  />
                )}
              />
            </div>
            <div className="d-flex align-items-center">
              <label htmlFor="frequencySlider">Refresh</label>
              Every
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
            <details className="custom-details">
              <summary>Advanced parameters</summary>

              <label htmlFor="model">Select a model</label>
              <select id="model" {...register('model')}>
                {Object.keys(availableSimpleModels).map((e) => (
                  <option key={e}>{e}</option>
                ))}{' '}
              </select>
              {kindScheme == 'multilabel' && (
                <>
                  <label htmlFor="dichotomize">Dichotomize on the label</label>
                  <select id="dichotomize" {...register('dichotomize')}>
                    {Object.values(availableLabels).map((e) => (
                      <option key={e}>{e}</option>
                    ))}{' '}
                  </select>
                </>
              )}
              {
                //generate_config(selectedSimpleModel)
                (selectedModel == 'liblinear' && (
                  <div key="liblinear">
                    <label htmlFor="cost">Cost</label>
                    <input
                      type="number"
                      step="1"
                      id="cost"
                      {...register('params.cost', { valueAsNumber: true })}
                    ></input>
                  </div>
                )) ||
                  (selectedModel == 'knn' && (
                    <div key="knn">
                      <label htmlFor="n_neighbors">Number of neighbors</label>
                      <input
                        type="number"
                        step="1"
                        id="n_neighbors"
                        {...register('params.n_neighbors', { valueAsNumber: true })}
                      ></input>
                    </div>
                  )) ||
                  (selectedModel == 'lasso' && (
                    <div key="lasso">
                      <label htmlFor="c">C</label>
                      <input
                        type="number"
                        step="1"
                        id="C"
                        {...register('params.C', { valueAsNumber: true })}
                      ></input>
                    </div>
                  )) ||
                  (selectedModel == 'multi_naivebayes' && (
                    <div key="multi_naivebayes">
                      <label htmlFor="alpha">Alpha</label>
                      <input
                        type="number"
                        id="alpha"
                        {...register('params.alpha', { valueAsNumber: true })}
                      ></input>
                      <label htmlFor="fit_prior">
                        Fit prior
                        <input
                          type="checkbox"
                          id="fit_prior"
                          {...register('params.fit_prior')}
                          className="mx-3"
                          checked
                        />
                      </label>
                    </div>
                  )) ||
                  (selectedModel == 'randomforest' && (
                    <div key="randomforest">
                      <label htmlFor="n_estimators">Number of estimators</label>
                      <input
                        type="number"
                        step="1"
                        id="n_estimators"
                        {...register('params.n_estimators', { valueAsNumber: true })}
                      ></input>
                      <label htmlFor="max_features">Max features</label>
                      <input
                        type="number"
                        step="1"
                        id="max_features"
                        {...register('params.max_features', { valueAsNumber: true })}
                      ></input>
                    </div>
                  ))
              }

              <div className="d-flex align-items-center">
                <label htmlFor="cv10">10-fold cross validation</label>
                <input type="checkbox" id="cv10" {...register('cv10')} className="mx-3" />
              </div>
            </details>

            <button className="btn btn-primary btn-validation">Train quick model</button>
          </form>
        </div>
      </Tab>
    </Tabs>
  );
};

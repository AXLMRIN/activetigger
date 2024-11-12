import { FC } from 'react';
import { Controller, SubmitHandler, useForm } from 'react-hook-form';
import Select from 'react-select';
import { useUpdateSimpleModel } from '../core/api';
import { useAppContext } from '../core/context';
import { useNotifications } from '../core/notifications';
import { SimpleModelModel } from '../types';

// TODO: default values + avoid generic parameters

interface SimpleModelManagementProps {
  projectName: string | null;
  currentScheme: string | null;
  availableSimpleModels: Record<string, Record<string, number>>;
  availableFeatures: string[];
}

export const SimpleModelManagement: FC<SimpleModelManagementProps> = ({
  projectName,
  currentScheme,
  availableSimpleModels,
  availableFeatures,
}) => {
  // element from the context
  const {
    appContext: { freqRefreshSimpleModel },
    setAppContext,
  } = useAppContext();
  const { notify } = useNotifications();

  // available features
  const features = availableFeatures.map((e) => ({ value: e, label: e }));

  // API call to get the current model with a set intervall
  // const { currentModel } = useGetSimpleModel(projectName, currentScheme, project);

  // useEffect(() => {
  //   const intervalId = setInterval(reFetchSimpleModel, 3000);
  //   reFetchSimpleModel();
  //   return () => {
  //     clearInterval(intervalId);
  //   };
  // }, [reFetchSimpleModel]);

  // function to change refresh frequency
  const refreshFreq = (newValue: number) => {
    setAppContext((prev) => ({ ...prev, freqRefreshSimpleModel: newValue }));
  };

  // create form
  const { register, handleSubmit, control, watch } = useForm<SimpleModelModel>({
    defaultValues: {
      model: 'liblinear',
      features: Object.values(availableFeatures),
      scheme: currentScheme || undefined,
      params: {
        cost: 1,
        C: 32,
        n_neighbors: 3,
        alpha: 1,
        n_estimators: 500,
        max_features: null,
      },
    },
  });

  // state for the model selected to modify parameters
  const selectedModel = watch('model');

  // Display the current model
  // useEffect(() => {
  //   if (currentModel && currentModel.params) {
  //     setValue('model', currentModel.model);
  //     toPairs(currentModel.params).map(([key, value]) => setValue(`params.${key}`, value));
  //   }
  // }, [currentModel, setValue]);

  // hooks to update
  const { updateSimpleModel } = useUpdateSimpleModel(projectName, currentScheme);

  // action when form validated
  const onSubmit: SubmitHandler<SimpleModelModel> = async (formData) => {
    const watchedFeatures = watch('features');
    console.log(watchedFeatures);
    if (watchedFeatures.length == 0) {
      notify({ type: 'error', message: 'Please select at least one feature' });
      return;
    }

    await updateSimpleModel(formData);
    //reset();
  };

  return (
    <div>
      <span className="explanations">
        Train a new prediction model on the current annotated data
      </span>

      {/* {currentModel && (
        <div>
          Current model : {currentModel.model} - Parameters : {JSON.stringify(currentModel.params)}{' '}
          - Statistics {JSON.stringify(currentModel.statistics)}
        </div>
      )} */}

      <form onSubmit={handleSubmit(onSubmit)}>
        <label htmlFor="model">Select a model</label>
        <select id="model" {...register('model')}>
          {Object.keys(availableSimpleModels).map((e) => (
            <option key={e}>{e}</option>
          ))}{' '}
        </select>
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
                {/* <label htmlFor="class_prior">Class prior</label>
                <input type="number" id="class_prior" {...register('params.class_prior')}></input> */}
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
        <div>
          <label htmlFor="features">Select features</label>
          {/* Specific management of the component with the react-form controller */}
          <Controller
            name="features"
            control={control}
            render={({ field: { value, onChange } }) => (
              <Select
                options={features}
                isMulti
                value={features.filter((feature) => value?.includes(feature.value))}
                onChange={(selectedOptions) => {
                  onChange(selectedOptions ? selectedOptions.map((option) => option.value) : []);
                }}
              />
            )}
          />
        </div>
        <button className="btn btn-primary btn-validation">Train</button>
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
      </form>
    </div>
  );
};

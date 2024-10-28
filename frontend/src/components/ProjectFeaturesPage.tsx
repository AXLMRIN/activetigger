import { FC } from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import { SubmitHandler, useForm } from 'react-hook-form';
import { MdOutlineDeleteOutline } from 'react-icons/md';
import { useParams } from 'react-router-dom';

import { useAddFeature, useDeleteFeature, useGetFeatureInfo } from '../core/api';
import { useAppContext } from '../core/context';
import { useNotifications } from '../core/notifications';
import { FeatureModelExtended } from '../types';
import { ProjectPageLayout } from './layout/ProjectPageLayout';

/**
 * Component to display the features page
 */

export const ProjectFeaturesPage: FC = () => {
  const { projectName } = useParams();

  // get element from the state
  const {
    appContext: { currentProject: project },
  } = useAppContext();

  // API calls
  const { featuresInfo } = useGetFeatureInfo(projectName || null, project);
  const addFeature = useAddFeature(projectName || null);
  const deleteFeature = useDeleteFeature(projectName || null);

  // hooks to use the objets
  const { register, handleSubmit, watch, reset } = useForm<FeatureModelExtended>({
    defaultValues: { parameters: { value: '' }, type: '' },
  });
  const { notify } = useNotifications();

  // state for the type of feature to create
  const selectedFeatureToCreate = watch('type');

  // action to create the new scheme
  const createNewFeature: SubmitHandler<FeatureModelExtended> = async (formData) => {
    try {
      addFeature(
        formData.type,
        formData.name,
        formData.parameters as unknown as Record<string, string | number | undefined>,
      );
    } catch (error) {
      notify({ type: 'error', message: error + '' });
    }
    reset();
  };

  // action to delete feature
  const deleteSelectedFeature = async (element: string) => {
    //TODO: try catch and throw
    await deleteFeature(element);
    //reFetch();
  };

  return (
    <ProjectPageLayout projectName={projectName || null} currentAction="features">
      {project && (
        <div className="container-fluid">
          <div className="row">
            <div className="col-12">
              <Tabs id="panel" className="mt-3" defaultActiveKey="existing">
                <Tab eventKey="existing" title="Existing">
                  <span className="explanations m-2">Features allow to train models.</span>
                  {Object.keys(featuresInfo || {}).map((element) => (
                    <div className="card text-bg-light mt-3" key={element as string}>
                      <div className="d-flex m-2 align-items-center">
                        <button
                          className="btn btn p-0 mx-4"
                          onClick={() => {
                            deleteSelectedFeature(element as string);
                          }}
                        >
                          <MdOutlineDeleteOutline size={20} />
                        </button>
                        <span className="w-25">{element as string}</span>
                        <span className="mx-2">{featuresInfo?.[element as string]['time']}</span>
                        <span className="mx-2">by {featuresInfo?.[element as string]['user']}</span>
                        {featuresInfo?.[element as string]['kind'] === 'regex' && (
                          <span>N={featuresInfo?.[element as string]['parameters']['count']}</span>
                        )}

                        {/* <span>{JSON.stringify(featuresInfo?.[element as string])}</span> */}
                      </div>
                    </div>
                  ))}{' '}
                  {Object.values(project?.features.training).map((element) => (
                    <div className="card text-bg-light mt-3 bg-warning" key={element as string}>
                      <div className="d-flex m-2 align-items-center">
                        <span className="w-25">Currently computing {element as string}</span>
                      </div>
                    </div>
                  ))}
                </Tab>
                <Tab eventKey="create" title="Create">
                  <div className="row">
                    <form onSubmit={handleSubmit(createNewFeature)}>
                      <div className="col-4">
                        <label className="form-label" htmlFor="newFeature">
                          Select the type of feature
                        </label>
                        <span className="explanations">
                          Regarding the number of elements in the corpus, some computation can takes
                          time (dozen of minutes).
                        </span>
                        <select className="form-control" id="newFeature" {...register('type')}>
                          <option key="empty"></option>
                          {Object.keys(project.features.options).map((element) => (
                            <option key={element} value={element}>
                              {element}
                            </option>
                          ))}{' '}
                        </select>

                        {selectedFeatureToCreate === 'regex' && (
                          <input
                            type="text"
                            className="form-control mt-3"
                            placeholder="Enter the regex"
                            {...register('parameters.value')}
                          />
                        )}

                        {selectedFeatureToCreate === 'dfm' && (
                          <div>
                            <div>
                              <label htmlFor="dfm_tfidf">TF-IDF</label>
                              <select id="dfm_tfidf" {...register('parameters.dfm_tfidf')}>
                                <option key="true">True</option>
                                <option key="false">False</option>
                              </select>
                            </div>
                            <div>
                              <label htmlFor="dfm_ngrams">Ngrams</label>
                              <input
                                type="number"
                                id="dfm_ngrams"
                                value={1}
                                {...register('parameters.dfm_ngrams')}
                              />
                            </div>
                            <div>
                              <label htmlFor="dfm_min_term_freq">Min term freq</label>
                              <input
                                type="number"
                                id="dfm_min_term_freq"
                                value={5}
                                {...register('parameters.dfm_min_term_freq')}
                              />
                            </div>
                            <div>
                              <label htmlFor="dfm_max_term_freq">Max term freq</label>
                              <input
                                type="number"
                                id="dfm_max_term_freq"
                                value={100}
                                {...register('parameters.dfm_max_term_freq')}
                              />
                            </div>
                            <div>
                              <label htmlFor="dfm_norm">Norm</label>
                              <select id="dfm_norm" {...register('parameters.dfm_norm')}>
                                <option key="true">True</option>
                                <option key="false">False</option>
                              </select>
                            </div>
                            <div>
                              <label htmlFor="dfm_log">Log</label>
                              <select id="dfm_log" {...register('parameters.dfm_log')}>
                                <option key="true">True</option>
                                <option key="false">False</option>
                              </select>
                            </div>
                          </div>
                        )}

                        {selectedFeatureToCreate === 'dataset' && (
                          <div>
                            <label htmlFor="dataset_col">Column to use</label>
                            <select id="dataset_col" {...register('parameters.dataset_col')}>
                              {(project?.params.all_columns || []).map((element) => (
                                <option key={element as string} value={element as string}>
                                  {element as string}
                                </option>
                              ))}
                            </select>
                            <label htmlFor="dataset_type">Type of the feature</label>
                            <select id="dataset_type" {...register('parameters.dataset_type')}>
                              <option key="numeric">Numeric</option>
                              <option key="categorical">Categorical</option>
                            </select>
                          </div>
                        )}

                        <button className="btn btn-primary btn-validation">Create</button>
                      </div>
                    </form>
                  </div>
                </Tab>
              </Tabs>
            </div>
          </div>
          <div></div>
        </div>
      )}
    </ProjectPageLayout>
  );
};

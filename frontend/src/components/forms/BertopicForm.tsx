import { Dispatch, FC, SetStateAction } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { HiOutlineQuestionMarkCircle } from 'react-icons/hi';
import { Tooltip } from 'react-tooltip';
import { useComputeBertopic, useStopProcesses } from '../../core/api';
import { ComputeBertopicModel } from '../../types';

interface BertopicCreationFormProps {
  projectSlug: string | null;
  availableModels: string[];
  isComputing?: boolean;
  setStatusDisplay?: Dispatch<SetStateAction<boolean>>;
}

export const BertopicForm: FC<BertopicCreationFormProps> = ({
  projectSlug,
  availableModels,
  isComputing = false,
  setStatusDisplay,
}) => {
  const { computeBertopic } = useComputeBertopic(projectSlug);
  const { stopProcesses } = useStopProcesses();
  const { handleSubmit: handleSubmitNewModel, register } = useForm<ComputeBertopicModel>({
    defaultValues: {
      name: 'bertopic',
      outlier_reduction: true,
      // min_topic_size: 10, // Removed because overridden by the hdbscan model - Axel
      // nr_topics: 'auto', // Removed to propose topic reduction later in the pipeline - Axel
      hdbscan_min_cluster_size: 15,
      umap_n_neighbors: 30,
      umap_n_components: 5,
      // umap_min_dist: 0.0, // Removed because 0.0 is the best value to use for clustering - Axel
      embedding_model: availableModels[0],
      force_compute_embeddings: false,
      filter_text_length: 50,
    },
  });

  const onSubmitNewModel: SubmitHandler<ComputeBertopicModel> = async (data) => {
    await computeBertopic(data);
    if (setStatusDisplay) setStatusDisplay(false);
  };
  return (
    <div>
      <form onSubmit={handleSubmitNewModel(onSubmitNewModel)}>
        <div className="d-flex items-center gap-2">
          <label className="form-label" htmlFor="name">
            Name
          </label>
          <input className="form-control" id="name" type="text" {...register('name')} />
        </div>
        <label className="form-label" htmlFor="embedding_model">
          Embedding model
          <a className="embedding_model">
            <HiOutlineQuestionMarkCircle />
          </a>
          <Tooltip anchorSelect=".embedding_model" place="top">
            Some models are quite bad for topic modelling tasks, consider changing the embedding
            <br />
            model if the results are unsatisfactory.
          </Tooltip>
          <select className="form-select" {...register('embedding_model')}>
            {availableModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
        <label className="form-label" htmlFor="umap_n_neighbors">
          Number of neighnors (dimension reduction parameter)
          <a className="umap_n_neighbors">
            <HiOutlineQuestionMarkCircle />
          </a>
          <Tooltip anchorSelect=".umap_n_neighbors" place="top">
            (UMAP) Choose small values to focus on local structures (ie specific topics) and large
            <br />
            values to focus on broader structures (ie broad topics)
            <br />
            <i>This value depends on how many elements you have in your corpus</i>
          </Tooltip>
          <input
            className="form-control"
            id="umap_n_neighbors"
            type="number"
            {...register('umap_n_neighbors')}
          />
        </label>
        <label className="form-label" htmlFor="min_topic_size">
          Min topic size (clustering parameter)
          <a className="min_topic_size">
            <HiOutlineQuestionMarkCircle />
          </a>
          <Tooltip anchorSelect=".min_topic_size" place="top">
            (HDBSCAN) Minimum number of elements in a group to be considered a cluster, otherwise,
            <br />
            it's considered as noise.
            <br />
            Small values will generate many small topics whereas larger values will generate few
            <br />
            topics and a lot of noise.
            <br />
            <i>This value depends on how many elements you have in your corpus</i>
          </Tooltip>
          <input
            className="form-control"
            id="minTopicSize"
            type="number"
            {...register('hdbscan_min_cluster_size')}
          />
        </label>
        <details className="custom-details">
          <summary>Advanced parameters</summary>
          <div className="explanations">Using UMAP (reduction) and HDBSCAN (clustering)</div>
          <label className="form-label" htmlFor="outlier_reduction">
            Outlier reduction
            <input
              id="outlier_reduction"
              type="checkbox"
              {...register('outlier_reduction')}
              className="mx-2"
            />
          </label>
          <label className="form-label" htmlFor="force_compute_embeddings">
            Force compute embeddings
            <input
              id="force_compute_embeddings"
              type="checkbox"
              {...register('force_compute_embeddings')}
              className="mx-2"
            />
          </label>
          <label className="form-label" htmlFor="filter_text_length">
            Filter out texts of length lower than
            <input
              className="form-control"
              id="filter_text_length"
              type="number"
              {...register('filter_text_length')}
            />
          </label>
          {/* <label className="form-label" htmlFor="nr_topics">
            Number of topics (auto if null)
            <input
            className="form-control"
            id="nr_topics"
            type="number"
            {...register('nr_topics')}
            />
          </label> */}
          <label className="form-label" htmlFor="umap_n_components">
            Number of components (dimension reduction parameter)
            <a className="umap_n_components">
              <HiOutlineQuestionMarkCircle />
            </a>
            <Tooltip anchorSelect=".umap_n_components" place="top">
              The number of dimensions to reduce the embedding space to.
              <br />
              There is not a quick way of tuning it. The lower the value the "flatter", ie the
              <br />
              embedding will lose information, however increasing this value does not guarantee
              <br />
              better results. Try changing the embedding model first.
              {/* waiting for better input on that matter - Axel */}
            </Tooltip>
            <input
              className="form-control"
              id="umap_n_components"
              type="number"
              {...register('umap_n_components')}
            />
          </label>
          {/* <label className="form-label" htmlFor="umap_min_dist">
            Min distance between points
            <input
              className="form-control"
              id="umap_min_dist"
              type="number"
              step="any"
              {...register('umap_min_dist')}
            />
          </label> */}
        </details>

        {!isComputing && <button className="btn btn-primary">Compute Bertopic</button>}
      </form>
      {isComputing && (
        <button className="btn btn-primary w-100" onClick={() => stopProcesses('all')}>
          Stop computation
        </button>
      )}
    </div>
  );
};

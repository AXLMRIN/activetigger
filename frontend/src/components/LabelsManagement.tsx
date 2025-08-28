import { FC, useEffect, useState } from 'react';
import { FaPlusCircle, FaRegTrashAlt } from 'react-icons/fa';

import { FaEdit } from 'react-icons/fa';
import { useAddLabel, useDeleteLabel, useRenameLabel, useStatistics } from '../core/api';
import { useNotifications } from '../core/notifications';

import { FaCheck } from 'react-icons/fa';
import { ReactSortable } from 'react-sortablejs';
import { AppContextValue } from '../core/context';

/**
 * Component to manage one label
 */

interface LabelsManagementProps {
  projectSlug: string | null;
  currentScheme: string | null;
  availableLabels: string[];
  kindScheme: string;
  setAppContext: React.Dispatch<React.SetStateAction<AppContextValue>>;
  deactivateModifications?: boolean;
}

interface LabelCardProps {
  label: string;
  countTrain: number;
  countTest?: number;
  removeLabel: (label: string) => void;
  renameLabel: (formerLabel: string, newLabel: string) => void;
  deactivateModifications?: boolean;
}

interface LabelType {
  id: number;
  label: string;
}

export const LabelCard: FC<LabelCardProps> = ({
  label,
  countTrain,
  countTest,
  removeLabel,
  renameLabel,
  deactivateModifications,
}) => {
  const [showRename, setShowRename] = useState(false);
  const [newLabel, setNewLabel] = useState(label);
  return (
    <tr key={label}>
      <td className="px-4 py-3">{label}</td>
      <td className="px-4 py-3 text-center">{countTrain ? countTrain : 0}</td>
      <td className="px-4 py-3 text-center">{countTest ? countTest : 0}</td>
      {!deactivateModifications && (
        <>
          <td className="flex justify-center gap-4">
            <div
              title="Delete"
              onClick={() => removeLabel(label)}
              className="cursor-pointer trash-wrapper"
            >
              <FaRegTrashAlt />
            </div>
          </td>
          <td className="flex justify-center gap-4">
            <div
              title="Rename"
              onClick={() => setShowRename(!showRename)}
              className="cursor-pointer"
            >
              <FaEdit />
            </div>
          </td>
        </>
      )}
      {showRename && (
        <td>
          <div className="d-flex align-items-center">
            <input
              type="text"
              className="form-control"
              placeholder="Enter new label"
              onChange={(e) => setNewLabel(e.target.value)}
            />
            <button
              onClick={() => {
                renameLabel(label, newLabel);
                setShowRename(false);
              }}
              className="btn btn p-0"
            >
              <FaCheck size={20} className="m-2" />
            </button>
          </div>
        </td>
      )}
    </tr>
  );
};

/**
 * Component to manage the labels of a project
 */

export const LabelsManagement: FC<LabelsManagementProps> = ({
  projectSlug,
  currentScheme,
  availableLabels,
  kindScheme,
  setAppContext,
  deactivateModifications,
}) => {
  const { notify } = useNotifications();

  const { statistics, reFetchStatistics } = useStatistics(projectSlug, currentScheme);

  // hooks to manage labels
  const { addLabel } = useAddLabel(projectSlug || null, currentScheme || null);
  const { deleteLabel } = useDeleteLabel(projectSlug || null, currentScheme || null);
  const { renameLabel } = useRenameLabel(projectSlug || null, currentScheme || null);

  const [labels, setLabels] = useState<LabelType[]>(
    availableLabels.map((label, index) => ({
      id: index,
      label: label,
    })),
  );

  // update labels when availableLabels change
  useEffect(() => {
    setLabels(
      availableLabels.map((label, index) => ({
        id: index,
        label: label,
      })),
    );
  }, [availableLabels]);

  // manage label creation
  const [createLabelValue, setCreateLabelValue] = useState('');
  const handleCreateLabelChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.value.includes('|')) {
      notify({ type: 'error', message: 'Label name cannot contain |' });
      return;
    }
    setCreateLabelValue(event.target.value);
  };
  const createLabel = () => {
    addLabel(createLabelValue);
    setCreateLabelValue('');
  };

  useEffect(() => {
    reFetchStatistics();
  }, [reFetchStatistics, currentScheme, availableLabels]);

  // update the labels in the state and context
  const updateLabels = (newLabels: LabelType[]) => {
    setLabels(newLabels);
    setAppContext((state) => ({
      ...state,
      displayConfig: {
        ...state.displayConfig,
        labelsOrder: newLabels.map((e) => e.label),
      },
    }));
  };

  return (
    <div className="row">
      <div className="col-12 rounded-2xl bg-white">
        {kindScheme === 'multiclass' ? (
          <div className="explanations">
            The current scheme is a <b>{kindScheme}</b> scheme.
          </div>
        ) : (
          <div className="alert alert-warning">
            The current scheme is a <b>{kindScheme}</b> scheme. It is experimental and some features
            does not work. Please read the documentation.
          </div>
        )}
        {!deactivateModifications && (
          <div className="d-flex align-items-center justify-content-between col-8 col-md-4">
            <input
              type="text"
              id="new-label"
              value={createLabelValue}
              onChange={handleCreateLabelChange}
              placeholder="Enter new label"
              className="form-control m-4"
            />
            <button onClick={createLabel} className="btn btn p-0">
              <FaPlusCircle size={20} />
            </button>
          </div>
        )}
        <table className="table table-hover">
          <thead className="text-xs text-gray-600 uppercase bg-gray-100">
            <tr>
              <th scope="col" className="px-4 py-3">
                Label
              </th>
              <th scope="col" className="px-4 py-3 text-center">
                Train
              </th>
              <th scope="col" className="px-4 py-3 text-center">
                Test
              </th>
              <th scope="col" className="px-4 py-3 text-center"></th>
              <th scope="col" className="px-4 py-3 text-center"></th>
            </tr>
          </thead>
          <ReactSortable list={labels} setList={updateLabels} tag="tbody">
            {labels.map((label) => (
              <LabelCard
                key={label.label}
                label={label.label}
                removeLabel={() => {
                  deleteLabel(label.label);
                }}
                renameLabel={renameLabel}
                countTrain={
                  statistics ? Number(statistics['train_annotated_distribution'][label.label]) : 0
                }
                countTest={
                  statistics && statistics['test_annotated_distribution']
                    ? Number(statistics['test_annotated_distribution'][label.label])
                    : 0
                }
                deactivateModifications={deactivateModifications}
              />
            ))}
          </ReactSortable>
          <tbody>
            <tr>
              <td className="px-4 py-3">
                <b>Annotated</b>
              </td>
              <td className="px-4 py-3 text-center">
                {statistics ? statistics['train_annotated_n'] : ''}
              </td>
              <td className="px-4 py-3 text-center">
                {statistics ? statistics['test_annotated_n'] : ''}
              </td>
            </tr>
            <tr>
              <td className="px-4 py-3">
                <b>Total</b>
              </td>
              <td className="px-4 py-3 text-center">
                {statistics ? statistics['train_set_n'] : ''}
              </td>
              <td className="px-4 py-3 text-center">
                {statistics ? statistics['test_set_n'] : ''}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

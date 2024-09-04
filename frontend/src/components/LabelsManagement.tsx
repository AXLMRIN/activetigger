import { FC, useState } from 'react';
import { FaPlusCircle, FaRegTrashAlt } from 'react-icons/fa';
import { RiFindReplaceLine } from 'react-icons/ri';

import { useAddLabel, useDeleteLabel, useRenameLabel } from '../core/api';

interface LabelsManagementProps {
  projectName: string | null;
  currentScheme: string | null;
  availableLabels: string[];
  reFetchCurrentProject: () => void;
}

export const LabelsManagement: FC<LabelsManagementProps> = ({
  projectName,
  currentScheme,
  availableLabels,
  reFetchCurrentProject,
}) => {
  // hooks to manage labels
  const { addLabel } = useAddLabel(projectName || null, currentScheme || null);
  const { deleteLabel } = useDeleteLabel(projectName || null, currentScheme || null);
  const { renameLabel } = useRenameLabel(projectName || null, currentScheme || null);

  // manage label creation
  const [createLabelValue, setCreateLabelValue] = useState('');
  const handleCreateLabelChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCreateLabelValue(event.target.value);
  };
  const createLabel = () => {
    addLabel(createLabelValue);
    if (reFetchCurrentProject) reFetchCurrentProject();
    setCreateLabelValue('');
  };

  // manage label deletion
  const [deleteLabelValue, setDeleteLabelValue] = useState('');
  const handleDeleteLabelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setDeleteLabelValue(event.target.value);
  };
  const removeLabel = () => {
    deleteLabel(deleteLabelValue);
    if (reFetchCurrentProject) reFetchCurrentProject();
  };

  // manage label replacement
  const replaceLabel = () => {
    renameLabel(deleteLabelValue, createLabelValue);
    setCreateLabelValue('');
    if (reFetchCurrentProject) reFetchCurrentProject();
  };

  return (
    <div>
      <span className="explanations">Create, delete or rename labels</span>
      <label htmlFor="select-label" className="form-label">
        Available labels
      </label>
      <div className="d-flex align-items-center w-100">
        <select id="select-label" onChange={handleDeleteLabelChange} className="form-select w-50">
          {availableLabels.map((e, i) => (
            <option key={i}>{e}</option>
          ))}{' '}
        </select>
        <button onClick={removeLabel} className="btn btn p-0">
          <FaRegTrashAlt size={20} className="m-2" />
        </button>
      </div>
      <label htmlFor="select-label" className="form-label">
        New label
      </label>
      <div className="d-flex align-items-center w-100 mt-2">
        <input
          type="text"
          id="new-label"
          value={createLabelValue}
          onChange={handleCreateLabelChange}
          placeholder="Enter new label"
          className="form-control w-50"
        />
        <button onClick={createLabel} className="btn btn p-0">
          <FaPlusCircle size={20} className="m-2" />
        </button>
      </div>
      <label htmlFor="select-label" className="form-label">
        Convert label
      </label>
      <div className="d-flex align-items-center">
        Replace selected label to the new one
        <button onClick={replaceLabel} className="btn btn p-0">
          <RiFindReplaceLine size={20} className="m-2" />
        </button>
      </div>
    </div>
  );
};

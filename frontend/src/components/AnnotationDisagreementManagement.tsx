import { FC, useState } from 'react';

import { useReconciliate, useTableDisagreement } from '../core/api';

import Select from 'react-select';
import { useAppContext } from '../core/context';

/*
 * Manage disagreement in annotations
 */

export const AnnotationDisagreementManagement: FC<{
  projectSlug: string;
}> = ({ projectSlug }) => {
  const {
    appContext: { currentScheme, currentProject: project },
  } = useAppContext();

  // type of scheme from context
  const kindScheme = currentScheme
    ? project?.schemes?.available?.[currentScheme]?.kind
    : 'multiclass';

  // available labels from context
  const availableLabels = currentScheme ? project?.schemes?.available?.[currentScheme]?.labels : [];

  // get disagreement table
  const { tableDisagreement, users, reFetchTable } = useTableDisagreement(
    projectSlug,
    currentScheme,
  );
  const { postReconciliate } = useReconciliate(projectSlug, currentScheme || null);

  // state elements to validate
  const [changes, setChanges] = useState<{ [key: string]: string }>({});

  // function to validate changes
  const validateChanges = () => {
    Object.entries(changes).map(([id, label]) => {
      postReconciliate(id, label, users || []);
      setChanges({});
    });
    reFetchTable();
  };

  return (
    <div className="container-fluid">
      <div className="row">
        <div className="col-12">
          <div className="explanations">
            Disagreements between users on annotations. Abitrate for the correct label.
          </div>
          <div>
            <div>
              <span>{users?.length}</span> user(s) involved in annotation
            </div>
            <div>
              <b>{tableDisagreement?.length} disagreements</b>
            </div>
          </div>
          {Object.entries(changes).length > 0 && (
            <button className="btn btn-warning my-3" onClick={validateChanges}>
              Validate changes
            </button>
          )}
        </div>
      </div>
      {tableDisagreement?.map((element, index) => (
        <div className="alert alert-info" role="alert" key={index}>
          <div className="row">
            <div>
              <span className="badge bg-light text-dark">{element.id as string}</span>
              <details>
                <summary>Text</summary>
                <span>{element.text as string}</span>
              </details>
            </div>

            {element.annotations && (
              <div className="d-inline-flex align-items-center  mt-2">
                {Object.entries(element.annotations).map(([key, value], _) => (
                  <div key={key}>
                    <span className="badge bg-info text-dark me-2">
                      {key}
                      <span className="badge rounded-pill bg-light text-dark m-1">{value}</span>
                    </span>
                  </div>
                ))}

                {kindScheme === 'multiclass' && (
                  <select
                    className="form-select w-25"
                    onChange={(event) =>
                      setChanges({ ...changes, [element.id as string]: event.target.value })
                    }
                  >
                    <option>Select a label to arbitrage</option>
                    {(availableLabels || []).map((e) => (
                      <option key={e}>{e}</option>
                    ))}
                  </select>
                )}
                {kindScheme === 'multilabel' && (
                  <Select
                    isMulti
                    className="flex-grow-1"
                    options={(availableLabels || []).map((e) => ({ value: e, label: e }))}
                    onChange={(e) => {
                      setChanges({
                        ...changes,
                        [element.id as string]: e.map((e) => e.value).join('|'),
                      });
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

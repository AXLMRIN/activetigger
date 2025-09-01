import io
from typing import Annotated

import pandas as pd  # type: ignore[import]
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from activetigger.app.dependencies import (
    ProjectAction,
    check_storage,
    get_project,
    test_rights,
    verified_user,
)
from activetigger.datamodels import (
    BertModelModel,
    LMInformationsModel,
    SimpleModelModel,
    SimpleModelOutModel,
    TextDatasetModel,
    UserInDBModel,
)
from activetigger.orchestrator import orchestrator
from activetigger.project import Project

router = APIRouter(tags=["models"])


@router.post("/models/simplemodel", dependencies=[Depends(verified_user)])
async def post_simplemodel(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    simplemodel: SimpleModelModel,
) -> None:
    """
    Compute simplemodel
    """
    try:
        project.update_simplemodel(simplemodel, current_user.username)
        orchestrator.log_action(current_user.username, "TRAIN MODEL: simplemodel", project.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/simplemodel", dependencies=[Depends(verified_user)])
async def get_simplemodel(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    scheme: str,
) -> SimpleModelOutModel | None:
    """
    Get available simplemodel for the project/user/scheme if any
    """
    try:
        return project.simplemodels.get(scheme, current_user.username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/bert", dependencies=[Depends(verified_user)])
async def get_bert(
    project: Annotated[Project, Depends(get_project)], name: str
) -> LMInformationsModel:
    """
    Get Bert parameters and statistics
    """
    try:
        return project.languagemodels.get_informations(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/predict", dependencies=[Depends(verified_user)])
async def predict(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    model_name: str,
    scheme: str,
    dataset: str = "all",
    batch_size: int = 32,
    external_dataset: TextDatasetModel | None = None,
) -> None:
    """
    Start prediction with a model
    """
    test_rights(ProjectAction.ADD, current_user.username, project.name)
    try:
        # get the data
        if dataset == "train":
            df = project.schemes.get_scheme_data(scheme=scheme, complete=True, kind=["train"])
            col_label = "labels"
            col_id = None
        elif dataset == "all":
            df = pd.DataFrame(project.features.get_column_raw("text", index="all"))
            df[project.params.col_id] = project.features.get_column_raw(
                project.params.col_id, index="all"
            )  # add original id
            col_label = None
            col_id = project.params.col_id
        elif dataset == "external":
            if external_dataset is None:
                raise HTTPException(status_code=400, detail="External dataset is missing")
            csv_buffer = io.StringIO(external_dataset.csv)
            df = pd.read_csv(
                csv_buffer,
            )
            df["text"] = df[external_dataset.text]
            df["index"] = df[external_dataset.id].apply(str)
            df.set_index("index", inplace=True)
            df = df[["text"]].dropna()
            col_label = None
            col_id = None
            # raise HTTPException(status_code=500, detail="Not implemented yet")
        else:
            raise Exception(f"dataset {dataset} not found")

        # start process to predict
        project.languagemodels.start_predicting_process(
            project_slug=project.name,
            name=model_name,
            user=current_user.username,
            df=df,
            col_text="text",
            col_label=col_label,
            col_id=col_id,
            dataset=dataset,
            batch_size=batch_size,
        )
        orchestrator.log_action(current_user.username, f"PREDICT MODEL: {model_name}", project.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/test", dependencies=[Depends(verified_user)])
async def start_test(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    scheme: str,
    model: str,
) -> None:
    """
    Start testing the model on the test set
    """
    test_rights(ProjectAction.ADD, current_user.username, project.name)
    if project.schemes.test is None:
        raise HTTPException(status_code=500, detail="No test dataset for this project")

    try:
        # get data labels + text
        df = project.schemes.get_scheme_data(scheme, complete=True, kind=["test"])

        # launch testing process : prediction
        project.languagemodels.start_testing_process(
            project_slug=project.name,
            name=model,
            user=current_user.username,
            df=df,
            col_text="text",
            col_labels="labels",
        )
        orchestrator.log_action(current_user.username, "PREDICT MODEL TEST", project.name)
        return None

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/train", dependencies=[Depends(verified_user)])
async def post_bert(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    bert: BertModelModel,
) -> None:
    """
    Compute bertmodel
    TODO : move the methods to specific class
    """
    test_rights(ProjectAction.ADD, current_user.username, project.name)
    try:
        check_storage(current_user.username)
        project.start_languagemodel_training(
            bert=bert,
            username=current_user.username,
        )
        orchestrator.log_action(current_user.username, f"TRAIN MODEL: {bert.name}", project.name)
        return None

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/stop", dependencies=[Depends(verified_user)])
async def stop_bert(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    specific_user: str | None = None,
) -> None:
    """
    Stop user process
    """
    test_rights(ProjectAction.ADD, current_user.username, project.name)
    try:
        if specific_user is not None:
            user = specific_user
        else:
            user = current_user.username

        orchestrator.stop_user_processes(kind=["train_bert", "predict_bert"], username=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/delete", dependencies=[Depends(verified_user)])
async def delete_bert(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    bert_name: str,
) -> None:
    """
    Delete trained bert model
    """
    test_rights(ProjectAction.DELETE, current_user.username, project.name)
    try:
        # delete the model
        project.languagemodels.delete(bert_name)
        # delete the features associated with the model
        for f in [i for i in project.features.map.keys() if bert_name.replace("__", "_") in i]:
            project.features.delete(f)
        orchestrator.log_action(
            current_user.username, f"DELETE MODEL + FEATURES: {bert_name}", project.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/bert/rename", dependencies=[Depends(verified_user)])
async def save_bert(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    former_name: str,
    new_name: str,
) -> None:
    """
    Rename bertmodel
    """
    test_rights(ProjectAction.UPDATE, current_user.username, project.name)
    try:
        project.languagemodels.rename(former_name, new_name)
        orchestrator.log_action(
            current_user.username,
            f"INFO RENAME MODEL: {former_name} -> {new_name}",
            project.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

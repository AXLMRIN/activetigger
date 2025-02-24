from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from activetigger.app.dependencies import (
    check_auth_exists,
    get_project,
    test_rights,
    verified_user,
)
from activetigger.datamodels import (
    AvailableProjectsModel,
    ProjectAuthsModel,
    ProjectDataModel,
    ProjectDescriptionModel,
    ProjectStateModel,
    TestSetDataModel,
    UserInDBModel,
)
from activetigger.orchestrator import orchestrator
from activetigger.project import Project

router = APIRouter(tags=["projects"])


@router.get(
    "/projects/{project_slug}/statistics", dependencies=[Depends(verified_user)]
)
async def get_project_statistics(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    scheme: str | None = None,
) -> ProjectDescriptionModel:
    """
    Statistics for a scheme and a user
    """
    try:
        r = project.get_statistics(scheme=scheme, user=current_user.username)
        return ProjectDescriptionModel(**r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/auth", dependencies=[Depends(verified_user)])
async def get_project_auth(project_slug: str) -> ProjectAuthsModel:
    """
    Users auth on a project
    """
    print("get_project_auth", project_slug)
    if not orchestrator.exists(project_slug):
        print("error")
        raise HTTPException(status_code=404, detail="Project doesn't exist")
    try:
        r = orchestrator.users.get_project_auth(project_slug)
        return ProjectAuthsModel(auth=r)
    except Exception as e:
        raise HTTPException(status_code=500) from e


@router.post("/projects/new", dependencies=[Depends(verified_user)])
async def new_project(
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    project: ProjectDataModel,
) -> str:
    """
    Load new project
    """
    # test rights to create project
    test_rights("create project", current_user.username)

    try:
        # create the project
        r = orchestrator.create_project(project, current_user.username)
        # log action
        orchestrator.log_action(
            current_user.username, "INFO create project", project.project_name
        )
        return r["success"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/projects/delete",
    dependencies=[Depends(verified_user), Depends(check_auth_exists)],
)
async def delete_project(
    project_slug: str,
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
) -> None:
    """
    Delete a project
    """
    test_rights("modify project", current_user.username, project_slug)
    try:
        print("start delete")
        orchestrator.delete_project(project_slug)
        orchestrator.log_action(
            current_user.username, "INFO delete project", project_slug
        )
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/trainset/add", dependencies=[Depends(verified_user)])
async def expand_project(
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    project_slug: str,
    n_elements: int,
) -> None:
    """
    Expand a project
    """
    test_rights("modify project", current_user.username, project_slug)
    try:
        orchestrator.add_elements_to_trainset(
            project_slug, n_elements, current_user.username
        )

        # get index for existing elements
        # get random elements
        # add them in the trainset with correct columns name
        # drop features

        # if not project.params.dir:
        #     raise Exception("Problem with project parameters - dir not found")

        # data_all = project.params.dir.joinpath("data_all.parquet")

        # # read only the columns
        # df_all = pd.read_parquet(
        #     data_all, columns=list(project.schemes.content.columns)
        # )

        # # index of elements used
        # elements_index = list(project.schemes.content.index)
        # if project.schemes.test:
        #     elements_index += list(project.schemes.test.index)

        # # take elements that are not in index
        # df_all = df_all[~df_all.index.isin(elements_index)]

        # # sample
        # elements_to_add = df_all.sample(n_elements)

        # # add them to the project
        # project.content = pd.concat([project.content, elements_to_add])

        # # write the new trainset
        # project.content.to_parquet(project.params.dir.joinpath("train.parquet"))

        # # update params
        # project.params.n_train = len(project.content)
        # orchestrator.set_project_parameters(project.params, current_user.username)
        # print(project.params)

        # # rebuild database + filesystem
        # project.content[[]].to_parquet(
        #     project.params.dir.joinpath("features.parquet"), index=True
        # )
        # project.features.projects_service.delete_all_features(project.name)

        # # restart the project
        # del df_all, elements_to_add
        # del orchestrator.projects[project.name]

        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/projects/testset/create", dependencies=[Depends(verified_user)])
async def add_testdata(
    project: Annotated[Project, Depends(get_project)],
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
    testset: TestSetDataModel,
) -> None:
    """
    Add a dataset for test when there is none available
    """
    try:
        # add the data
        project.add_testdata(testset, current_user.username, project.name)
        # update parameters of the project
        orchestrator.set_project_parameters(project.params, current_user.username)
        # log action
        orchestrator.log_action(
            current_user.username, "INFO add testdata project", project.name
        )
        return None
    except Exception as e:
        raise HTTPException(status_code=500) from e


@router.get("/projects")
async def get_projects(
    current_user: Annotated[UserInDBModel, Depends(verified_user)],
) -> AvailableProjectsModel:
    """
    Get general informations on the server
    depending of the status of connected user
    """
    try:
        r = orchestrator.get_auth_projects(current_user.username)
        return AvailableProjectsModel(projects=r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/projects/{project_slug}",
    dependencies=[Depends(verified_user), Depends(check_auth_exists)],
)
async def get_project_state(
    project: Annotated[Project, Depends(get_project)],
) -> ProjectStateModel:
    """
    Get the state of a specific project
    """
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    data = project.get_state()
    return ProjectStateModel(**data)

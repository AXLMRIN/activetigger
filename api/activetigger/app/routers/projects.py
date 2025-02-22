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
    r = project.get_statistics(scheme=scheme, user=current_user.username)
    if "error" in r:
        raise HTTPException(status_code=500, detail=r["error"])
    return ProjectDescriptionModel(**r)


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


@router.post("/projects/testset", dependencies=[Depends(verified_user)])
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


@router.get("/projects/auth", dependencies=[Depends(verified_user)])
async def get_project_auth(project_slug: str) -> ProjectAuthsModel:
    """
    Users auth on a project
    """
    if not orchestrator.exists(project_slug):
        raise HTTPException(status_code=404, detail="Project doesn't exist")
    try:
        r = orchestrator.users.get_project_auth(project_slug)
        return ProjectAuthsModel(auth=r)
    except Exception as e:
        raise HTTPException(status_code=500) from e

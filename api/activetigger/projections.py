import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi.responses import FileResponse
from pandas import DataFrame  # type: ignore[import]

from activetigger.datamodels import (
    ProjectionComputing,
    ProjectionDataModel,
    ProjectionParametersModel,
    ProjectionsProjectStateModel,
)
from activetigger.queue import Queue
from activetigger.tasks.compute_projection import ComputeProjection


class Projections:
    """
    Manage projections
    """

    # TODO: Transform available type to dict[str, UserProjection]
    path: Path
    available: dict[str, ProjectionDataModel]
    options: dict[str, dict[str, Any]]
    computing: list
    queue: Queue

    def __init__(self, path: Path, computing: list, queue: Queue) -> None:
        self.path = path
        self.computing = computing
        self.queue = queue
        self.available = {}
        self.options = {
            "umap": {
                "n_neighbors": 15,
                "min_dist": 0.1,
                "n_components": 2,
                "metric": ["cosine", "euclidean"],
            },
            "tsne": {
                "n_components": 2,
                "learning_rate": "auto",
                "init": "random",
                "perplexity": 3,
            },
        }
        self.load()

    def load(self) -> None:
        """
        Load available projections in pickle file
        """
        if self.path.joinpath("projections.pickle").exists():
            try:
                self.available = pickle.load(open(self.path.joinpath("projections.pickle"), "rb"))
            except Exception as e:
                print(e)

    def current_computing(self):
        return [e.name for e in self.computing if e.kind == "projection"]

    def training(self) -> dict[str, str]:
        """
        Currently under training
        """
        r = {e.user: e.method for e in self.computing if e.kind == "projection"}
        return r

    def add(self, element: ProjectionComputing, results: DataFrame) -> None:
        """
        Add projection after computation
        """
        self.available[element.user] = ProjectionDataModel(
            id=element.unique_id,
            data=results,
            parameters=element.params,
        )

        try:
            pickle.dump(self.available, open(self.path.joinpath("projections.pickle"), "wb"))
        except Exception as e:
            print("Error in saving projections", e)

    def compute(
        self,
        project_slug: str,
        username: str,
        projection: ProjectionParametersModel,
        features: DataFrame,
    ) -> None:
        """
        Launch the projection computation in the queue
        """

        unique_id = self.queue.add_task(
            "projection",
            project_slug,
            ComputeProjection(
                kind=projection.method, features=features, params=projection.parameters
            ),
        )
        self.computing.append(
            ProjectionComputing(
                unique_id=unique_id,
                name=f"Projection by {username}",
                user=username,
                time=datetime.now(),
                kind="projection",
                method=projection.method,
                params=projection,
            )
        )

    def get(self, user_name: str) -> ProjectionDataModel | None:
        """
        Get the projection for a user
        """
        if user_name not in self.available:
            return None

        return self.available[user_name]

    def state(self) -> ProjectionsProjectStateModel:
        return ProjectionsProjectStateModel(
            options=self.options,
            available={i: self.available[i].id for i in self.available},
            training=self.training(),
        )

    def export(
        self,
        user_name: str,
        format: str = "csv",
    ) -> FileResponse:
        """
        Export the projection for a user
        """
        if user_name not in self.available:
            raise Exception("No projection available")
        data = self.available[user_name].data
        file_name = f"projection_{user_name}.{format}"
        if format == "csv":
            data.to_csv(self.path.joinpath(file_name))
        if format == "parquet":
            data.to_parquet(self.path.joinpath(file_name))
        if format == "xlsx":
            data.to_excel(self.path.joinpath(file_name))

        return FileResponse(
            path=self.path.joinpath(file_name),
            filename=file_name,
        )

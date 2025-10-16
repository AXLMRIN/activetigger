import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import]
import pyarrow.parquet as pq  # type: ignore[import]
import yaml  # type: ignore[import]
from pandas import DataFrame, Series

from activetigger.config import config
from activetigger.datamodels import (
    FeatureComputing,
    FeatureDescriptionModel,
    FeaturesProjectStateModel,
)
from activetigger.db.projects import ProjectsService
from activetigger.queue import Queue
from activetigger.tasks.compute_dfm import ComputeDfm
from activetigger.tasks.compute_fasttext import ComputeFasttext
from activetigger.tasks.compute_sbert import ComputeSbert


class Features:
    """
    Manage project features
    Comment :
    - for the moment as a file
    - database for informations
    - use "__" as separator
    - add a column dataset to separate train, valid, test
    """

    project_slug: str
    path_features: Path
    path_model: Path
    path_all: Path
    queue: Queue
    computing: list
    informations: dict
    content: DataFrame
    map: dict
    options: dict
    lang: str
    projects_service: ProjectsService
    n: int

    def __init__(
        self,
        project_slug: str,
        path_features: Path,
        path_all: Path,
        path_train: Path,
        path_valid: Path,
        path_test: Path,
        models_path: Path,
        queue: Any,
        computing: list,
        db_manager,
        lang: str,
    ) -> None:
        """
        Initit features
        """
        self.project_slug = project_slug
        self.projects_service = db_manager.projects_service
        self.path_features = path_features
        self.path_all = path_all
        self.path_train = path_train
        self.path_valid = path_valid
        self.path_test = path_test
        self.path_models = models_path
        self.queue = queue
        self.informations = {}

        self.lang = lang
        self.computing = computing

        # load possible embeddings models
        fasttext_models = [f for f in os.listdir(self.path_models) if f.endswith(".bin")]
        # possibility to create a sbert.yaml file to add models
        sbert_models = [
            "jinaai/jina-embeddings-v3",
            "Alibaba-NLP/gte-multilingual-base",
            "all-mpnet-base-v2",
        ]
        if Path(config.data_path).joinpath("projects/sbert.yaml").exists():
            content = yaml.safe_load(
                open(
                    str(Path(config.data_path).joinpath("projects/sbert.yaml")),
                    "r",
                )
            )
            sbert_models = content.get("models", sbert_models)
        else:
            # create the file
            with open(
                str(Path(config.data_path).joinpath("projects/sbert.yaml")),
                "w",
            ) as f:
                yaml.dump({"models": sbert_models}, f)

        # options
        self.options: dict = {
            "sbert": {"models": sbert_models},
            "fasttext": {"models": fasttext_models},
            "dfm": {
                "tfidf": False,
                "ngrams": 1,
                "min_term_freq": 5,
                "max_term_freq": 100,
                "norm": None,
                "log": None,
            },
            "regex": {"formula": None},
            "dataset": {},
        }

        # create the features file if not exist
        if not self.path_features.exists():
            self.create_features_file()
        self.map, self.n = self.get_map()

    def create_features_file(self):
        """
        Create the features file with the dataset information
        based on train, valid, test files
        """

        # clear database
        self.projects_service.delete_project_features(self.project_slug)

        # read file to create the structure
        train = pd.read_parquet(self.path_train, columns=[])
        train = pd.DataFrame(index=train.index)
        train["dataset"] = "train"

        to_concat = [train]

        if self.path_valid.exists():
            valid = pd.read_parquet(self.path_valid, columns=[])
            valid = pd.DataFrame(index=valid.index)
            valid["dataset"] = "valid"
            to_concat.append(valid)
        if self.path_test.exists():
            test = pd.read_parquet(self.path_test, columns=[])
            test = pd.DataFrame(index=test.index)
            test["dataset"] = "test"
            to_concat.append(test)

        df = pd.DataFrame(pd.concat(to_concat))
        df.to_parquet(self.path_features, index=True)
        del df

    def reset_features_file(self):
        """
        Reset the features file with only the dataset information
        based on train, valid, test files
        """
        if self.path_features.exists():
            self.path_features.unlink()
        self.projects_service.delete_project_features(self.project_slug)
        self.create_features_file()
        self.map, self.n = self.get_map()

    def get_map(self) -> tuple[dict, int]:
        """
        Get the structure of features from the parquet file
        """
        parquet_file = pq.ParquetFile(self.path_features)
        column_names = [i for i in parquet_file.schema.names if i != "dataset"]

        def find_strings_with_pattern(strings, pattern):
            matching_strings = [s for s in strings if re.match(pattern, s)]
            return matching_strings

        var = set([i.split("__")[0] for i in column_names if "__index" not in i and i != "id"])
        dic = {i: find_strings_with_pattern(column_names, i) for i in var}
        num_rows = parquet_file.metadata.num_rows
        return dic, num_rows

    def exists(self, name: str) -> bool:
        """
        Check if a feature exists
        """
        return name in self.map

    def add(
        self,
        name: str,
        kind: str,
        username: str,
        parameters: dict[str, Any],
        new_content: DataFrame | Series,
    ):
        """
        Add feature(s) after computing
        """
        # test name
        if name in self.map:
            raise Exception("Feature already exists")

        # test length
        print("New content shape", new_content.shape, self.n)
        if len(new_content) != self.n:
            raise ValueError("Features don't have the right shape")

        # change type for series
        if type(new_content) is Series:
            new_content = pd.DataFrame(new_content)

        # change column name with a prefix
        new_content.columns = [f"{name}__{i}" for i in new_content.columns]

        # read data, add the feature to the dataset and save
        content = pd.read_parquet(self.path_features)
        content = pd.concat(
            [
                content[[i for i in content.columns if i not in new_content.columns]],
                new_content,
            ],
            axis=1,
        )
        content.to_parquet(self.path_features)
        del content

        # add informations to database
        self.projects_service.add_feature(
            project_slug=self.project_slug,
            kind=kind,
            name=name,
            parameters=parameters,
            user_name=username,
            data=list(new_content.columns),
        )

        # refresh the map
        self.map = self.get_map()[0]

    def delete(self, name: str):
        """
        Delete feature
        """
        if name not in self.map:
            raise Exception("Feature doesn't exist")

        if self.projects_service.get_feature(self.project_slug, name) is None:
            raise Exception("Feature doesn't exist in database")

        col = self.get([name])

        # read data, delete columns and save
        content = pd.read_parquet(self.path_features)
        content[[i for i in content.columns if i not in col]].to_parquet(self.path_features)
        del content

        # delete from database
        self.projects_service.delete_feature(self.project_slug, name)

        # refresh the map
        self.map = self.get_map()[0]

    def get(self, features: list | str = "all", dataset: str = "train") -> DataFrame:
        """
        Get content for specific features
        """
        features = [i for i in features if i is not None]
        if features == "all":
            features = list(self.map.keys())
        if type(features) is str:
            features = [features]

        cols = ["dataset"]
        missing = []
        for i in features:
            if i in self.map:
                cols += self.map[i]
            else:
                missing.append(i)

        if len(i) > 0:
            print("Missing features:", missing)

        # load only needed data from file
        data = pd.read_parquet(self.path_features, columns=cols)

        # filter on dataset
        if dataset in {"train", "valid", "test"}:
            data = data.loc[data["dataset"] == dataset]
        elif dataset != "all":
            raise Exception("Dataset not recognized")

        # drop the dataset column
        data = data.drop(columns=["dataset"])

        return data

    def info(self, name: str):
        feature = self.projects_service.get_feature(self.project_slug, name)
        if feature is None:
            raise Exception("Feature doesn't exist in database")
        return {
            "time": feature.time,
            "name": name,
            "kind": feature.kind,
            "username": feature.user,
            "parameters": feature.parameters,
            "columns": json.loads(feature.data),
        }

    def get_available(self) -> dict[str, FeatureDescriptionModel]:
        """
        Informations on features + update
        Comments:
            Maybe not the best solution
            Database ? How to avoid a loop ...
        """
        return self.projects_service.get_project_features(self.project_slug)

    def get_column_raw(
        self, column_name: str, index: str = "train", add_real_index: bool = True
    ) -> Series:
        """
        Get column raw dataset
        """
        parquet_file = pq.ParquetFile(self.path_all)
        column_names = parquet_file.schema.names
        if column_name not in list(column_names):
            raise Exception("Column doesn't exist")
        df = pd.read_parquet(self.path_all, columns=[column_name])
        if index == "train":  # filter only train id
            df_train = pd.read_parquet(self.path_features, columns=[])  # only the index
            return df.loc[df_train.index][column_name]
        elif index == "all":
            return df[column_name]
        else:
            raise Exception("Index not recognized")

    def current_user_processes(self, user: str):
        return [e for e in self.computing if e.user == user]

    def current_computing(self) -> dict[str, dict[str, str | None]]:
        return {
            e.name: {"progress": self.computing_progress(e.unique_id), "name": e.name}
            for e in self.computing
            if e.kind == "feature"
        }

    def compute(self, df: pd.Series, name: str, kind: str, parameters: dict, username: str):
        """
        Compute new feature
        TODO : manage better the queue launching
        """
        if len(self.current_user_processes(username)) > 0:
            raise ValueError("A process is already running")

        if kind not in {"sbert", "fasttext", "dfm", "regex", "dataset"}:
            raise ValueError("Kind not recognized")

        # features without queue

        if kind == "regex":
            if "value" not in parameters:
                raise ValueError("No value for regex")

            regex_name = f"regex_[{parameters['value']}]_by_{username}"
            if self.exists(regex_name):
                raise ValueError("This regex already exists")
            pattern = re.compile(parameters["value"])
            f = df.apply(lambda x: bool(pattern.search(x)))
            parameters["count"] = int(f.sum())
            self.add(regex_name, kind, username, parameters, f)
            return {"success": "regex added"}

        if kind == "dataset":
            # get the raw column for the train set
            column = self.get_column_raw(parameters["dataset_col"])

            # convert the column to a specific format
            if len(column.dropna()) != len(column):
                raise ValueError("Column contains null values")
            if parameters["dataset_type"] == "Numeric":
                try:
                    column = column.apply(float)
                except Exception:
                    raise Exception("The column can't be transform into numerical feature")
            else:
                column = column.apply(str)

            # add the feature to the project
            dataset_name = (
                f"dataset_{parameters['dataset_col']}_{parameters['dataset_type']}".lower()
            )
            if self.exists(dataset_name):
                raise ValueError("This dataset feature already exists")
            self.add(dataset_name, kind, username, parameters, column)
            return {"success": "Feature added"}

        # features with queue

        unique_id = None

        if kind == "sbert":
            if (
                "model" not in parameters
                or parameters["model"] is None
                or parameters["model"] == "generic"
            ):
                model = self.options["sbert"]["models"][0]
            else:
                model = parameters["model"]
            name = f"sbert_{model.replace('/', '_')}"
            if self.exists(name):
                raise ValueError("This sbert model already exists")
            unique_id = self.queue.add_task(
                "feature",
                self.project_slug,
                ComputeSbert(
                    texts=df,
                    path_process=self.path_all.parent,
                    model=model,
                ),
                queue="gpu",
            )

        if kind == "fasttext":
            name = f"fasttext_{parameters['model']}"
            if self.exists(name):
                raise ValueError("This fasttext model already exists")
            unique_id = self.queue.add_task(
                "feature",
                self.project_slug,
                ComputeFasttext(
                    texts=df,
                    language=self.lang,
                    path_process=self.path_all.parent,
                    path_models=self.path_models,
                    model=parameters["model"],
                ),
            )
            if parameters["model"] is not None and parameters["model"] != "":
                name = f"{name}_{parameters['model']}"

        if kind == "dfm":
            name = "dfm"
            if self.exists(name):
                raise ValueError("This dfm model already exists")
            args = parameters.copy()
            args["texts"] = df
            args["language"] = self.lang
            unique_id = self.queue.add_task("feature", self.project_slug, ComputeDfm(**args))
            del args

        if unique_id:
            self.computing.append(
                FeatureComputing(
                    unique_id=unique_id,
                    kind="feature",
                    parameters=parameters,
                    type=kind,
                    user=username,
                    name=name,
                    time=datetime.now(),
                )
            )
            return {"success": "Feature in training"}
        raise ValueError("Error in the process")

    def computing_progress(self, unique_id: str) -> str | None:
        """
        Get the progress of a computing feature
        """
        try:
            with open(self.path_all.parent.joinpath(unique_id), "r") as f:
                r = f.read()
            return r
        except Exception:
            return None

    def state(self) -> FeaturesProjectStateModel:
        return FeaturesProjectStateModel(
            options=self.options,
            available=list(self.map.keys()),
            training=self.current_computing(),
        )

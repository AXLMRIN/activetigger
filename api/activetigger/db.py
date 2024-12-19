import datetime
import json
import logging
from json.decoder import JSONDecodeError
from pathlib import Path

from sqlalchemy import (
    TIMESTAMP,
    Column,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from activetigger.functions import get_hash, get_root_pwd

Base = declarative_base()


class Projects(Base):
    __tablename__ = "projects"
    project_slug = Column(String, primary_key=True)
    time_created = Column(TIMESTAMP(timezone=True), server_default=func.now())
    parameters = Column(Text)
    time_modified = Column(TIMESTAMP(timezone=True))
    user = Column(String)


class Schemes(Base):
    __tablename__ = "schemes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_created = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    time_modified = Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    user = Column(String)
    project = Column(String)
    name = Column(String)
    params = Column(Text)


class Annotations(Base):
    __tablename__ = "annotations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    dataset = Column(String)
    user = Column(String)
    project = Column(String)
    element_id = Column(String)
    scheme = Column(String)
    annotation = Column(String)
    comment = Column(Text)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    user = Column(String)
    key = Column(Text)
    description = Column(Text)
    contact = Column(Text)
    created_by = Column(String)


class Auths(Base):
    __tablename__ = "auth"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String)
    project = Column(String)
    status = Column(String)
    created_by = Column(String)


class Logs(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    user = Column(String)
    project = Column(String)
    action = Column(String)
    connect = Column(String)


class Tokens(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_created = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    token = Column(Text)
    status = Column(String)
    time_revoked = Column(TIMESTAMP(timezone=True))


class Generations(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    user = Column(String)
    project = Column(String)
    element_id = Column(String)
    endpoint = Column(String)
    prompt = Column(Text)
    answer = Column(Text)


class Features(Base):
    __tablename__ = "features"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    user = Column(String)
    project = Column(String)
    name = Column(String)
    kind = Column(String)
    parameters = Column(Text)
    data = Column(String)


class Models(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    time_modified = Column(TIMESTAMP(timezone=True))
    user = Column(String)
    project = Column(String)
    scheme = Column(String)
    kind = Column(String)
    name = Column(String)
    parameters = Column(Text)
    path = Column(String)
    status = Column(String)
    statistics = Column(Text)
    test = Column(String)


class DatabaseManager:
    """
    Database management with SQLAlchemy
    """

    def __init__(self, path_db: str):
        self.db_url = f"sqlite:///{path_db}"

        # test if the db exists, else create it
        if not Path(path_db).exists():
            self.create_db()

        # connect the session
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.default_user = "server"

        # check if there is a root user, add it
        session = self.Session()
        if not session.query(Users).filter_by(user="root").first():
            self.create_root_session()
        session.close()

    def create_db(self):
        print("Create database")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)

    def create_root_session(self) -> None:
        """
        Create root session
        :return: None
        """
        pwd: str = get_root_pwd()
        hash_pwd: bytes = get_hash(pwd)
        self.add_user("root", hash_pwd, "root", "system")

    def add_user(
        self,
        username: str,
        password: str,
        role: str,
        created_by: str,
        contact: str = "",
    ):
        session = self.Session()
        user = Users(
            user=username,
            key=password,
            description=role,
            created_by=created_by,
            time=datetime.datetime.now(),
            contact=contact,
        )
        session.add(user)
        session.commit()
        session.close()

    def add_log(self, user: str, action: str, project_slug: str, connect: str):
        session = self.Session()
        log = Logs(
            user=user,
            project=project_slug,
            action=action,
            connect=connect,
            time=datetime.datetime.now(),
        )
        session.add(log)
        session.commit()
        session.close()

    def get_logs(self, username: str, project_slug: str, limit: int):
        session = self.Session()
        if project_slug == "all":
            logs = (
                session.query(Logs)
                .filter_by(user=username)
                .order_by(Logs.time.desc())
                .limit(limit)
                .all()
            )
        elif username == "all":
            logs = (
                session.query(Logs)
                .filter_by(project=project_slug)
                .order_by(Logs.time.desc())
                .limit(limit)
                .all()
            )
        else:
            logs = (
                session.query(Logs)
                .filter_by(user=username, project=project_slug)
                .order_by(Logs.time.desc())
                .limit(limit)
                .all()
            )
        session.close()
        return [
            {
                "id": log.id,
                "time": log.time,
                "user": log.user,
                "project": log.project,
                "action": log.action,
                "connect": log.connect,
            }
            for log in logs
        ]

    def get_project(self, project_slug: str):
        session = self.Session()
        project = session.query(Projects).filter_by(project_slug=project_slug).first()
        session.close()
        if project:
            return project.__dict__
        else:
            return None

    def add_project(self, project_slug: str, parameters: dict, username: str):
        session = self.Session()
        project = Projects(
            project_slug=project_slug,
            parameters=json.dumps(parameters),
            time_created=datetime.datetime.now(),
            time_modified=datetime.datetime.now(),
            user=username,
        )
        session.add(project)
        session.commit()
        session.close()
        print("CREATE PROJECT", datetime.datetime.now())

    def update_project(self, project_slug: str, parameters: dict):
        session = self.Session()
        project = session.query(Projects).filter_by(project_slug=project_slug).first()
        project.time_modified = datetime.datetime.now()
        project.parameters = json.dumps(parameters)
        session.commit()
        session.close()

    def existing_projects(self) -> list:
        session = self.Session()
        projects = session.query(Projects).all()
        session.close()
        return [project.project_slug for project in projects]

    def add_token(self, token: str, status: str):
        session = self.Session()
        token = Tokens(token=token, status=status, time_created=datetime.datetime.now())
        session.add(token)
        session.commit()
        session.close()

    def get_token_status(self, token: str):
        session = self.Session()
        token = session.query(Tokens).filter_by(token=token).first()
        session.close()
        if token:
            return token.status
        else:
            return None

    def revoke_token(self, token: str):
        session = self.Session()
        token = session.query(Tokens).filter_by(token=token).first()
        token.time_revoked = datetime.datetime.now()
        token.status = "revoked"
        session.commit()
        session.close()

    def add_scheme(self, project_slug: str, name: str, labels: list, kind: str, username: str):
        if not labels:
            labels = []
        params = json.dumps({"labels": labels, "codebook": None, "kind": kind})
        session = self.Session()
        scheme = Schemes(
            project=project_slug,
            name=name,
            params=params,
            user=username,
            time_created=datetime.datetime.now(),
            time_modified=datetime.datetime.now(),
        )
        session.add(scheme)
        session.commit()
        session.close()

    def update_scheme_labels(self, project_slug: str, name: str, labels: list):
        """
        Update the labels in the database
        """
        session = self.Session()
        scheme = session.query(Schemes).filter_by(project=project_slug, name=name).first()
        params = json.loads(scheme.params)
        params["labels"] = labels
        scheme.params = json.dumps(params)
        scheme.time_modified = datetime.datetime.now()
        session.commit()
        session.close()

    def update_scheme_codebook(self, project_slug: str, scheme: str, codebook: str):
        """
        Update the codebook in the database
        """
        print("update_scheme_codebook", project_slug, scheme, codebook)
        session = self.Session()
        scheme = session.query(Schemes).filter_by(project=project_slug, name=scheme).first()
        try:
            params = json.loads(scheme.params)
            params["codebook"] = codebook
            scheme.params = json.dumps(params)
            scheme.time_modified = datetime.datetime.now()
            session.commit()
            session.close()
            return True
        except JSONDecodeError as e:
            logging.warning("Unable to parse codebook scheme: %", e)
            return None

    def get_scheme_codebook(self, project_slug: str, name: str):
        session = self.Session()
        scheme = session.query(Schemes).filter_by(project=project_slug, name=name).first()
        session.close()
        try:
            return {
                "codebook": json.loads(scheme.params)["codebook"],
                "time": str(scheme.time_modified),
            }
        except JSONDecodeError as e:
            logging.warning("Unable to parse codebook scheme: %", e)
            return None

    def delete_project(self, project_slug: str):
        session = self.Session()
        session.query(Projects).filter(Projects.project_slug == project_slug).delete()
        session.query(Schemes).filter(Schemes.project == project_slug).delete()
        session.query(Annotations).filter(Annotations.project == project_slug).delete()
        session.query(Auths).filter(Auths.project == project_slug).delete()
        session.query(Generations).filter(Generations.project == project_slug).delete()
        session.query(Logs).filter(Logs.project == project_slug).delete()
        session.query(Features).filter(Features.project == project_slug).delete()
        session.query(Models).filter(Models.project == project_slug).delete()
        session.commit()
        session.close()

    def add_generated(
        self,
        user: str,
        project_slug: str,
        element_id: str,
        endpoint: str,
        prompt: str,
        answer: str,
    ):
        session = self.Session()
        generation = Generations(
            user=user,
            time=datetime.datetime.now(),
            project=project_slug,
            element_id=element_id,
            endpoint=endpoint,
            prompt=prompt,
            answer=answer,
        )
        session.add(generation)
        session.commit()
        session.close()

    def get_generated(self, project_slug: str, username: str, n_elements: int = 10):
        """
        Get elements from generated table by order desc
        """
        session = self.Session()
        generated = (
            session.query(Generations)
            .filter(Generations.project == project_slug, Generations.user == username)
            .order_by(Generations.time.desc())
            .limit(n_elements)
            .all()
        )
        session.close()
        return [[el.time, el.element_id, el.prompt, el.answer, el.endpoint] for el in generated]

    def get_distinct_users(self, project_slug: str, timespan: int | None):
        session = self.Session()
        if timespan:
            time_threshold = datetime.datetime.now() - datetime.timedelta(seconds=timespan)
            users = (
                session.query(Annotations.user)
                .filter(
                    Annotations.project == project_slug,
                    Annotations.time > time_threshold,
                )
                .distinct()
                .all()
            )
        else:
            users = (
                session.query(Annotations.user)
                .filter(Annotations.project == project_slug)
                .distinct()
                .all()
            )
        session.close()
        return [u.user for u in users]

    def get_current_users(self, timespan: int = 600):
        session = self.Session()
        time_threshold = datetime.datetime.now() - datetime.timedelta(seconds=timespan)
        users = session.query(Logs.user).filter(Logs.time > time_threshold).distinct().all()
        session.close()
        return [u.user for u in users]

    def get_project_auth(self, project_slug: str):
        session = self.Session()
        auth = session.query(Auths).filter(Auths.project == project_slug).all()
        session.close()
        return {el.user: el.status for el in auth}

    def add_auth(self, project_slug: str, user: str, status: str):
        session = self.Session()
        auth = (
            session.query(Auths).filter(Auths.project == project_slug, Auths.user == user).first()
        )
        if auth:
            auth.status = status
        else:
            auth = Auths(project=project_slug, user=user, status=status)
            session.add(auth)
        session.commit()
        session.close()

    def delete_auth(self, project_slug: str, user: str):
        session = self.Session()
        session.query(Auths).filter(Auths.project == project_slug, Auths.user == user).delete()
        session.commit()
        session.close()

    def get_user_projects(self, username: str):
        session = self.Session()
        result = (
            session.query(
                Auths.project,
                Auths.status,
                Projects.parameters,
                Projects.user,
                Projects.time_created,
            )
            .join(Projects, Auths.project == Projects.project_slug)
            .filter(Auths.user == username)
            .all()
        )
        session.close()
        return [row for row in result]

    def get_user_auth(self, username: str, project_slug: str = None):
        session = self.Session()
        if project_slug is None:
            result = session.query(Auths.user, Auths.status).filter(Auths.user == username).all()
        else:
            result = (
                session.query(Auths.user, Auths.status)
                .filter(Auths.user == username, Auths.project == project_slug)
                .all()
            )
        session.close()
        return [[row[0], row[1]] for row in result]

    def get_users_created_by(self, username: str):
        """
        get users created by *username*
        """
        session = self.Session()
        if username == "all":
            result = session.query(Users.user, Users.contact).distinct().all()
        else:
            result = (
                session.query(Users.user, Users.contact)
                .filter(Users.created_by == username)
                .distinct()
                .all()
            )
        session.close()
        return {row.user: {"contact": row.contact} for row in result}

    def delete_user(self, username: str):
        session = self.Session()
        session.query(Users).filter(Users.user == username).delete()
        session.commit()
        session.close()

    def get_user(self, username: str):
        session = self.Session()
        user = session.query(Users).filter(Users.user == username).first()
        session.close()
        return {"key": user.key, "description": user.description}

    def change_password(self, username: str, password: str):
        session = self.Session()
        user = session.query(Users).filter(Users.user == username).first()
        user.key = password
        session.commit()
        session.close()

    def get_scheme_elements(self, project_slug: str, scheme: str, dataset: list[str]):
        """
        Get last annotation for each element id for a project/scheme
        """
        session = self.Session()
        query = (
            session.query(
                Annotations.element_id,
                Annotations.annotation,
                Annotations.user,
                Annotations.time,
                Annotations.comment,
                func.max(Annotations.time),
            )
            .filter(
                Annotations.scheme == scheme,
                Annotations.project == project_slug,
                Annotations.dataset.in_(dataset),
            )
            .group_by(Annotations.element_id)
            .order_by(func.max(Annotations.time).desc())
        )

        # Execute the query and fetch all results
        results = query.all()
        session.close()
        return [
            [row.element_id, row.annotation, row.user, row.time, row.comment] for row in results
        ]

    def get_coding_users(self, scheme: str, project_slug: str):
        session = self.Session()
        distinct_users = (
            session.query(Annotations.user)
            .filter(Annotations.project == project_slug, Annotations.scheme == scheme)
            .distinct()
            .all()
        )
        session.close()
        return [u for u in distinct_users]

    def get_recent_annotations(self, project_slug: str, user: str, scheme: str, limit: int):
        session = self.Session()
        if user == "all":
            recent_annotations = (
                session.query(Annotations.element_id)
                .filter(
                    Annotations.project == project_slug,
                    Annotations.scheme == scheme,
                    Annotations.dataset == "train",
                )
                .order_by(Annotations.time.desc())
                .limit(limit)
                .distinct()
                .all()
            )

        else:
            recent_annotations = (
                session.query(Annotations.element_id)
                .filter(
                    Annotations.project == project_slug,
                    Annotations.scheme == scheme,
                    Annotations.user == user,
                    Annotations.dataset == "train",
                )
                .order_by(Annotations.time.desc())
                .limit(limit)
                .distinct()
                .all()
            )
        return [u[0] for u in recent_annotations]

    def get_annotations_by_element(
        self, project_slug: str, scheme: str, element_id: str, limit: int = 10
    ):
        session = self.Session()
        annotations = (
            session.query(
                Annotations.annotation,
                Annotations.dataset,
                Annotations.user,
                Annotations.time,
            )
            .filter(
                Annotations.project == project_slug,
                Annotations.scheme == scheme,
                Annotations.element_id == element_id,
            )
            .order_by(Annotations.time.desc())
            .limit(limit)
            .all()
        )
        return [[a.annotation, a.dataset, a.user, a.time] for a in annotations]

    def add_annotations(
        self,
        dataset: str,
        user: str,
        project_slug: str,
        scheme: str,
        elements: list[dict],  # [{"element_id": str, "annotation": str, "comment": str}]
    ):
        session = self.Session()
        for e in elements:
            annotation = Annotations(
                time=datetime.datetime.now(),
                dataset=dataset,
                user=user,
                project=project_slug,
                element_id=e["element_id"],
                scheme=scheme,
                annotation=e["annotation"],
                comment=e["comment"],
            )
            session.add(annotation)
        session.commit()
        session.close()

    def add_annotation(
        self,
        dataset: str,
        user: str,
        project_slug: str,
        element_id: str,
        scheme: str,
        annotation: str,
        comment: str = "",
    ):
        session = self.Session()
        annotation = Annotations(
            time=datetime.datetime.now(),
            dataset=dataset,
            user=user,
            project=project_slug,
            element_id=element_id,
            scheme=scheme,
            annotation=annotation,
            comment=comment,
        )
        session.add(annotation)
        session.commit()
        session.close()

    def available_schemes(self, project_slug: str):
        session = self.Session()
        schemes = (
            session.query(Schemes.name, Schemes.params)
            .filter(Schemes.project == project_slug)
            .distinct()
            .all()
        )
        session.close()
        r = []
        for s in schemes:
            params = json.loads(s.params)
            kind = params["kind"] if "kind" in params else "multiclass"  # temporary hack
            r.append(
                {
                    "name": s.name,
                    "labels": params["labels"],
                    "codebook": params["codebook"],
                    "kind": kind,
                }
            )
        return r

    def delete_scheme(self, project_slug: str, name: str):
        session = self.Session()
        session.query(Schemes).filter(
            Schemes.name == name, Schemes.project == project_slug
        ).delete()
        session.commit()
        session.close()

    def get_table_annotations_users(self, project_slug: str, scheme: str):
        session = self.Session()
        subquery = (
            select(
                Annotations.id,
                Annotations.user,
                func.max(Annotations.time).label("last_timestamp"),
            )
            .where(Annotations.project == project_slug, Annotations.scheme == scheme)
            .group_by(Annotations.element_id, Annotations.user)
            .subquery()
        )
        query = select(
            Annotations.element_id,
            Annotations.annotation,
            Annotations.user,
            Annotations.time,
        ).join(subquery, Annotations.id == subquery.c.id)

        results = session.execute(query).fetchall()
        session.close()
        return [[row.element_id, row.annotation, row.user, row.time] for row in results]

    # feature management

    def add_feature(
        self,
        project: str,
        kind: str,
        name: str,
        parameters: str,
        user: str,
        data: str = None,
    ):
        session = self.Session()
        feature = Features(
            project=project,
            time=datetime.datetime.now(),
            kind=kind,
            name=name,
            parameters=parameters,
            user=user,
            data=data,
        )
        session.add(feature)
        session.commit()
        session.close()

    def delete_feature(self, project: str, name: str):
        session = self.Session()
        session.query(Features).filter(Features.name == name, Features.project == project).delete()
        session.commit()
        session.close()

    def get_feature(self, project: str, name: str):
        session = self.Session()
        feature = (
            session.query(Features)
            .filter(Features.name == name, Features.project == project)
            .first()
        )
        session.close()
        return feature

    def get_project_features(self, project: str):
        session = self.Session()
        features = session.query(Features).filter(Features.project == project).all()
        session.close()
        return {
            i.name: {
                "time": i.time.strftime("%Y-%m-%d %H:%M:%S"),
                "kind": i.kind,
                "parameters": json.loads(i.parameters),
                "user": i.user,
                "data": json.loads(i.data),
            }
            for i in features
        }

    def add_model(
        self,
        kind: str,
        project: str,
        name: str,
        user: str,
        status: str,
        scheme: str,
        params: dict,
        path: str,
    ):
        session = self.Session()

        # test if the name does not exist
        models = session.query(Models).filter(Models.name == name).all()
        if len(models) > 0:
            return False

        model = Models(
            project=project,
            time=datetime.datetime.now(),
            kind=kind,
            name=name,
            user=user,
            parameters=json.dumps(params),
            scheme=scheme,
            status=status,
            path=path,
        )
        session.add(model)
        session.commit()
        session.close()

        print("available", self.available_models(project))

        return True

    def change_model_status(self, project: str, name: str, status: str):
        session = self.Session()
        model = session.query(Models).filter(Models.name == name, Models.project == project).first()
        model.status = "trained"
        session.commit()
        session.close()

    def available_models(self, project: str):
        session = self.Session()
        models = (
            session.query(Models.name, Models.parameters, Models.path, Models.scheme)
            .filter(
                Models.project == project,
                Models.status == "trained",
            )
            .distinct()
            .all()
        )
        session.close()
        return [
            {
                "name": m.name,
                "scheme": m.scheme,
                "path": m.path,
                "parameters": json.loads(m.parameters),
            }
            for m in models
        ]

    def model_exists(self, project: str, name: str):
        session = self.Session()
        models = session.query(Models).filter(Models.name == name, Models.project == project).all()
        session.close()
        return len(models) > 0

    def delete_model(self, project: str, name: str):
        session = self.Session()
        # test if the name does not exist
        models = session.query(Models).filter(Models.name == name, Models.project == project).all()
        if len(models) == 0:
            print("Model does not exist")
            return False
        # delete the model
        session.query(Models).filter(Models.name == name, Models.project == project).delete()
        session.commit()
        session.close()
        return True

    def get_model(self, project: str, name: str):
        session = self.Session()
        model = session.query(Models).filter(Models.name == name, Models.project == project).first()
        session.close()
        return model

    def rename_model(self, project: str, old_name: str, new_name: str):
        session = self.Session()

        # test if the name does not exist
        models = (
            session.query(Models).filter(Models.name == new_name, Models.project == project).all()
        )
        if len(models) > 0:
            return {"error": "The new name already exists"}
        # get and rename
        model = (
            session.query(Models).filter(Models.name == old_name, Models.project == project).first()
        )
        model.name = new_name
        model.path = model.path.replace(old_name, new_name)
        session.commit()
        session.close()
        return {"success": "model renamed"}

    def set_model_params(self, project: str, name: str, flag: str, value):
        session = self.Session()
        model = session.query(Models).filter(Models.name == name, Models.project == project).first()
        parameters = json.loads(model.parameters)
        parameters[flag] = value
        model.parameters = json.dumps(parameters)
        session.commit()

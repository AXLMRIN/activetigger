import os
from pathlib import Path
import yaml
import pandas as pd
import numpy as np

import functions
from functions import SimpleModel
from pandas import DataFrame

import logging
logging.basicConfig(filename='log.log', 
                    encoding='utf-8', 
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# use Pydantic & BaseModel to type data in API and automatically
# generate the JSON content https://realpython.com/api-integration-in-python/ 

# plus précisémment définir le format des objets qui circulent entre le back et le front
# - element
# - options
# - liste d'éléments

class Project():
    """
    Project (database/params)
    """

    def __init__(self, project_name : str, **kwargs):
        """
        Initialize a project (load or create)
        """

        self.name = project_name
        self.schemes:None|Schemes = None
        self.features = Features(project_name=self.name)
        self.params: None|list = None
        self.content = None
        self.simplemodel:None|SimpleModel = None

        # If project exist
        if self.exists(project_name):
             self.load_params()
             self.load_data()
        # If not
        else:
             self.create(project_name, **kwargs)

        # Compute embeddings as features
        if self.params["embeddings"]["sbert"]:
            self.features.add("sbert",
                              self.compute_embeddings(emb="sbert"))
        if self.params["embeddings"]["fasttext"]:
            self.features.add("fasttext",
                              self.compute_embeddings(emb="fasttext"))
    
    def exists(self, project_name):
        return Path(f"{project_name}/{project_name}.yaml").exists()

    def create(self, project_name, **kwargs):
        """
        Create new project
        """

        ## TO DO : tests que tous les paramètres ont bien été renseignés
        
        if not Path(project_name).exists():
            os.makedirs(project_name)
        else:
            print("Erreur, le dossier existe") # gérer la gestion des erreurs

        # Manage parameters
        if not "col_text" in kwargs:
            kwargs["col_text"] = "text"
        if not "sbert" in kwargs:
            kwargs["sbert"] = False
        if not "fasttext" in kwargs:
            kwargs["fasttext"] = False
            
        self.params = {
                    "project_name":project_name,
                    "origin_file":kwargs["file"],
                    "n_rows":kwargs["n_rows"],
                    "cat":{"default":kwargs["cat"]},
                    "col_text":kwargs["col_text"],
                    "embeddings":{
                        "sbert":kwargs["sbert"],
                        "fasttext":kwargs["fasttext"],
                    }
                  }
        
        self.schemes = Schemes(self.name)
        self.schemes.add("default",kwargs["cat"])
        self.schemes.select("default")
        
        self.save_params()

        # Manage data
        self.content = pd.read_csv(kwargs["file"],
                                   index_col=0,
                                   low_memory=False,
                                   nrows=kwargs["n_rows"])
        
        self.content[self.schemes.col] = None
        self.load_predictions()
        self.save_data()

    def load_predictions(self):
        file = f"{self.name}/{self.name}.pred"
        if Path(file).exists():
            proba = pd.read_csv(file,index_col=0)
            self.content["proba"] = proba
        else:
            self.content["proba"] = None
        return True
    
    def compute_embeddings(self,
                           emb:None|str = None):
        """
        Compute embeddings (and save it)
        """
        if emb == "fasttext":
            file = f"{self.name}/fastext"
            if Path(file).exists():
                print("Fasttext embeddings already exist")
                emb_fasttext = pd.read_csv(file,index_col=0)
            else:
                print("Starting to compute fasttext embeddings")
                emb_fasttext = functions.to_fasttext(self.content[self.params["col_text"]])
                emb_fasttext.to_csv(file)
            return emb_fasttext
        if emb == "sbert":
            file = f"{self.name}/sbert"
            if Path(file).exists():
                print("Sbert embeddings already exist")
                emb_sbert = pd.read_csv(file,index_col=0)
            else:
                print("Starting to compute sbert embeddings")
                emb_sbert = functions.to_sbert(self.content[self.params["col_text"]])
                emb_sbert.to_csv(file)
            return emb_sbert
            
    def fit_simplemodel(self,
                        predictors:list,
                        model:str="liblinear",
                        **kwargs):
        """
        Create and fit a simple model on current data
        """
        s = SimpleModel(model,
                        data = self.content,
                        label = self.schemes.col,
                        predictors=predictors,
                        **kwargs)
        return s

    def load_params(self):
        """
        Load YAML configuration file
        """
        with open(f"{self.name}/{self.name}.yaml","r") as f:
            self.params =  yaml.safe_load(f)

        # load also schemes (TO CHANGE IN THE FUTURE)
        self.schemes = Schemes(self.name)
        self.schemes.load({
            "project_name":self.name,
            "name":"default",
            "labels":self.params["cat"]["default"],
            "available":self.params["cat"]
            })

    def save_params(self,params=None):
        """
        Save YAML configuration file
        """
        if params is None:
            params = self.params
        with open(f"{self.name}/{self.name}.yaml", 'w') as f:
            yaml.dump(params, f)

    def update_schemes(self,json):
        self.schemes.load(json)
        self.params["cat"] = self.schemes.available
        self.save_params()

    def load_data(self):
        """
        Load data
        """
        self.content = pd.read_csv(f"{self.name}/{self.name}.csv",
                                   index_col=0,
                                   low_memory=False
                                   )
    def save_data(self):
        """
        Save data
        """
        self.content.to_csv(f"{self.name}/{self.name}.csv")
    
    def delete_label(self,element_id):
        """
        Delete a recorded tag
        """
        self.content.loc[element_id,self.schemes.col] = None
        return True

    def add_label(self,element_id,label):
        """
        Record a tag
        """
        self.content.loc[element_id,self.schemes.col] = label
        return True

    def get_next(self,
                 mode:str = "deterministic",
                 on:str = "untagged") -> dict:
        """
        Get next item

        TODO : gérer les cases tagguées/non tagguées etc.
        """
        
        # Pour le moment uniquement les cases non nulles
        f = self.content[self.schemes.col].isnull()

        if mode == "deterministic":
            element_id = self.content[f].index[0]
        if mode == "random":
            element_id = self.content[f].sample(random_state=42).index[0]
        if mode == "maxprob":
            element_id = self.content[f].sort_values("prob",ascending=False).index[0]

        # TODO : put a lock on the element when sent ?

        # Pour le moment uniquement l'id et le texte (dans le futur ajouter tous les éléments)
        return  {
                 "element_id":element_id,
                 "content":self.get_element(element_id)
                }
    
    def get_element(self,element_id):
        """
        Get an element of the database
        """
        columns = ["text"]
        return self.content.loc[element_id,columns]

    def get_params(self):
        """
        Send parameters
        """
        return self.params
    
class Features():
    """
    Managing data features
    Specific to a project

    TODO : test for the length of the data
    """
    def __init__(self, project_name:str) -> None:
        self.project_name = project_name
        self.available:list = []
        self.content = None

    def __repr__(self) -> str:
        return f"Available features : {self.available}"

    def add(self, name:str, content:DataFrame):
        self.available.append(name)
        if self.content is None:
            self.content = content
        else:
            self.content = pd.concat([self.content,content],
                                     axis=1)

class Schemes():
    """
    Managing project schemes
    """
    def __init__(self,project_name):
        self.project_name = project_name
        self.name = None
        self.labels = None
        self.col = None
        self.available = {}

    def __repr__(self) -> str:
        return f"Coding schemes available {self.available}"

    def col_name(self):
        return "labels_" + self.name

    def select(self, name):
        if name in self.available:
            self.name = name
            self.labels = self.available[name]
            self.col = self.col_name()
        else:
            raise IndexError

    def add(self, name: str, modalities: list):
        if not name in self.available:
            self.available[name] = modalities
            return True
        else:
            raise IndexError

    def load(self,json):
        self.project_name = json["project_name"]
        self.name = json["name"]
        self.labels = json["labels"]
        self.available = json["available"]    
        self.col = self.col_name()    
    
    def dump(self):
        return {
                "project_name":self.project_name,
                "name":self.name,
                "labels":self.labels,
                "available":self.available
                }
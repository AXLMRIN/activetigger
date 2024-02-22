import ipywidgets as widgets
from IPython.display import display, clear_output
import json
import requests as rq
from pathlib import Path
import pandas as pd
import io
import re
import time

URL_SERVER = "http://127.0.0.1:8000"
headers = {'x-token': 'your_token'}


class ConnexionError(Exception):
    def __init__(self, message="Error during the connexion"):
        self.message = message
        super().__init__(self.message)

class Widget():
    """
    Widget
    """
    def __init__(self) -> None:
        self.user = "local"
        self.project_name: None|str = None
        #self.scheme: dict = {
        #                    "current":None,
        #                    "mode":None,
        #                    "on":None,
        #                    "tag":None,
        #                    }
        self.current_element = None
        self.screen = None

    def _post(self,
             route:str, 
             params:dict|None = None, 
             files:str|None = None,
             data:dict|None = None):
        url = URL_SERVER + route
        r = rq.post(url, 
                    params = params,
                    json = data,
                    files=files,
                    headers=headers)
        return json.loads(r.content)
    
    def _get(self,
             route:str, 
             params:dict|None = None, 
             data:dict|None = None):
        url = URL_SERVER + route
        r = rq.get(url, 
                    params = params,
                    data = data,
                    headers=headers)
        return json.loads(r.content)

    def start(self):
        """
        Menu to start the widget
        - connect existing project
        - start a new one
        Add -> delete ?
        """
        # Get existing projects
        existing = self._get("/projects")

        # Existing projects
        existing_projects = widgets.Dropdown(
            options=existing["existing projects"],
            description='Available :',
            #value = "",
            layout={'width': '300px'},
            disabled=False)

        # Start existing project
        start = widgets.Button(description="Connecter")
        def start_project(b):
            self.project_name = existing_projects.value
            self.state = self.get_state()
            self.interface()
        start.on_click(start_project)

        # Create a new project
        create = widgets.Button(description="Nouveau projet")
        def create_project(b):
            self._create_new_project()
        create.on_click(create_project)

        # Display
        clear_output()
        self.output = widgets.HBox([existing_projects, start, create])
        display(self.output)

    def get_state(self):
        state = self._get(route = f"/state/{self.project_name}")
        return state

    def _create_new_project(self):
        """
        Create a new project
        """
        clear_output()
        # project name
        project_name = widgets.Text(disabled=False,
                                    description="Name:",
                                    layout={'width': '200px'})
        
        # select columns
        column_text = widgets.Dropdown(
            options=[],
            description='Text:',
            disabled=False)

        column_id = widgets.Dropdown(
            options=[],
            description='Id:',
            disabled=False)

        # load file
        file = widgets.Text(disabled=False,
                            description="Path:",
                            layout={'width': '200px'})
        load = widgets.Button(description="Load",
                              layout={'width': '100px'})
        def load_file(b):
            df = self._load_file(file.value)
            column_text.options = df.columns
            column_id.options = df.columns
        load.on_click(load_file)
        # WARNING : BUG dans VS Code sur l'upload donc utiliser un
        # chemin
        #file = widgets.FileUpload(
        #    accept='.csv',
        #    multiple=False
        #)
        #def on_upload_change(change):
        #    print("chargé")
        #    input_file = list(file.value.values())[0]
        #    content = input_file['content']
        #    content = io.StringIO(content.decode('utf-8'))
        #    df = pd.read_csv(content)
        #file.observe(on_upload_change, names='value')
        # nom de la colonne texte
        # nom de la colonne identifiant

        validate = widgets.Button(description="Create",
                              layout={'width': '100px'})
        def create_project(b):
            data = {
                    "project_name": project_name.value,
                    "col_text": column_text.value,
                    "col_id":column_id.value,
                    }
            files = {'file': (file.value,
                              open(file.value, 'rb'))}
            self._post(route="/projects/new", 
                       data=data,
                       files=files)
            print("créer le projet")
            self.start()
        validate.on_click(create_project)

        self.output = widgets.VBox([project_name, 
                                    widgets.HBox([file, load]),
                                    widgets.HBox([column_text, column_id]),
                                    validate
                                    ])
        display(self.output)

    def _load_file(self,path):
        """
        Load file
        """
        path = Path(path)
        if not path.exists():
            return "File doesn't exist"
        if not path.suffix == '.csv':
            return "File not csv"
        df = pd.read_csv(path)
        return df
    
    def _send_tag(self,tag):
        # envoyer le tag
        # récupérer un nouveau text à coder 
        # actualiser
        return None
    
    def _display_next(self):

        params = {
                          "project_name":self.project_name,
                          "scheme":self._schemes.value,
                          "selection":self._mode_selection.value,
                          "sample":self._mode_sample.value,
                          "tag":None
                      }
        r = self._get(route = "/elements/next",
                      params = params)
        
        self.current_element = r
        self._textarea.value = r["text"]

        return True

    def _display_buttons_labels(self):
        buttons = []
        labels = self.state["schemes"]["available"][self._schemes.value]
        def send_tag(v):
            data = {
                    "project_name":self.project_name,
                    "scheme":self._schemes.value,
                    "element_id":self.current_element["element_id"],
                    "tag":v.description,
                    }
            self._post(route = "/tags/add",
                       params = {"project_name":self.project_name},
                       data = data)
            # gérer les erreurs d'envoi ?
            self._display_next()
        for t in labels:
            b = widgets.Button(description=t)
            b.on_click(send_tag)
            buttons.append(b)
        self._labels.children = buttons
        return True

    def update_global(self):
        self._display_buttons_labels()
        self.update_tab_annotations()
        self.update_tab_schemes()

    def update_tab_annotations(self):
        self.state = self.get_state()
        self._schemes.options = list(self.state["schemes"]["available"].keys())
        self._mode_selection.options = self.state["next"]["methods"]
        self._mode_sample.options = self.state["next"]["sample"]

    def update_tab_schemes(self): 
        self.state = self.get_state()
        self.select_scheme.options = list(self.state["schemes"]["available"].keys())
        self.select_label.options = self.state["schemes"]["available"][self.select_scheme.value]
        self._display_buttons_labels() # and tagging buttons

    def update_tab_simplemodel(self):
        self.state = self.get_state()
        self.simplemodel_state.value = f"Scheme : {self._schemes.value} - Current model: {self.state['simplemodel']['current']}"


    def update_tab_data(self):
        params = {"project_name":self.project_name,
                            "scheme":self._schemes.value,
                            "min":self.sample_min.value,
                            "max":self.sample_max.value,
                            "mode":self.sample_type.value
                            }
        r = self._get("/elements/table", params = params)
        df = pd.DataFrame(r)
        buttons = []
        for i,j in df.iterrows():
            buttons.append(widgets.HBox([
                #widgets.Checkbox(value=False, description=str(i), layout = {"width":"100px"}),
                widgets.HTML(value=f"<small>{j['text']}</small>"),
                widgets.Dropdown(options = ["test","lol"], layout = {"width":"100px"})
            ]))
        self.display_table.children = buttons

    def create_scheme(self, s):
        if s == "":
            return "Empty"
        params = {"project_name":self.project_name}
        data = {
                "project_name":self.project_name,
                "name":s,
                "tags":[]
                }
        r = self._post("/schemes/add", params = params, data = data)
        print(r)
        self.update_tab_schemes()
        return r
    
    def delete_scheme(self, s):
        if s == "":
            return "Empty"
        params = {"project_name":self.project_name}
        data = {
                "project_name":self.project_name,
                "name":s,
                }
        r = self._post("/schemes/delete", params = params, data = data)
        print(r)
        self.update_tab_schemes()
        return r
    
    def delete_label(self, label):
        if label == "":
            return "Empty"
        tags = self.state["schemes"]["available"][self.select_scheme.value].copy()
        tags.remove(label)
        params = {"project_name":self.project_name}
        data = {
                "project_name":self.project_name,
                "name":self.select_scheme.value,
                "tags":tags
                }
        r = self._post("/schemes/update", params = params, data = data)
        print(r)
        self.update_tab_schemes()
        return r

    def create_label(self, label):
        if label == "":
            return "Empty"
        if label in self.state["schemes"]["available"][self.select_scheme.value]:
            return "Label already exists"
        tags = self.state["schemes"]["available"][self.select_scheme.value].copy()
        tags.append(label)
        params = {"project_name":self.project_name}
        data = {
                "project_name":self.project_name,
                "name":self.select_scheme.value,
                "tags":list(tags)
                }
        r = self._post("/schemes/update", params = params, data = data)
        print(tags)
        print(r)
        self.update_tab_schemes()
        return r
    
    def train_simplemodel(self, scheme, model, parameters, features):
        if model is None:
            return "Model missing"
        if parameters is None:
            return "Parameters missing"
        if (features is None) or (len(features)==0):
            return "Need at least one feature" 
        # TODO : test if parameters is valid
        params = {"project_name":self.project_name}
        print(parameters)
        data = {
                "model":model,
                "features":features,
                "params":json.loads(parameters),
                "scheme":scheme
                }
        
        r = self._post("/models/simplemodel", 
                       params = params, 
                       data = data)
        print(r)
        self.update_tab_simplemodel()
        return True

    def interface(self):
        #-----------
        # Tab codage
        #-----------
        self._textarea = widgets.Textarea(value="",
                                   layout=widgets.Layout(width='600px',height='150px'), 
                                   description='')
        self._schemes = widgets.Dropdown()
        def on_change_scheme(change):
            if change['type'] == 'change' and change['name'] == 'value':
                self._display_buttons_labels()
        self._schemes.observe(on_change_scheme)
        self._back = widgets.Button(description = "back")
        self._mode_selection = widgets.Dropdown()
        self._mode_sample = widgets.Dropdown()
        self._mode_label = widgets.Dropdown()
        self._labels = widgets.HBox()

        # Populate
        self.update_tab_annotations()
        self._schemes.value = self._schemes.options[0]
        self._mode_selection.value = self._mode_selection.options[0]
        self._mode_sample.value = self._mode_sample.options[0]

        # group in tab
        tab_annotate = widgets.VBox([
                            self._schemes,
                             widgets.HBox([self._back,
                                    self._mode_selection,
                                    self._mode_sample,
                                    self._mode_label]),
                              self._textarea,
                              self._labels
             ])

        #---------
        # Tab data
        #---------
        self.sample_type = widgets.Dropdown(description="On: ", value="all", options=["all","tagged","untagged"], layout={'width': '200px'})
        self.sample_min = widgets.IntText(value=0, description='Min:', disabled=False, layout={'width': '200px'})
        self.sample_max = widgets.IntText(value=0, description='Max:', disabled=False, layout={'width': '200px'})
        self.display_table = widgets.VBox()
        valid_sample = widgets.Button(description = "Get")
        valid_sample.on_click(lambda b : self.update_tab_data())
        modify_table = widgets.Button(description = "Modify (to implement)")
        modify_table.on_click(lambda b : print("to implement"))

        # Populate
        self.sample_min.value = 0
        self.sample_max.value = 10
        self.sample_type.value = "all"
        self.update_tab_data()

        # Group in tab
        tab_data = widgets.VBox([widgets.HBox([
                                    self.sample_type, 
                                    self.sample_min, 
                                    self.sample_max, 
                                    valid_sample
                                    ]),
                                 self.display_table,
                                 modify_table
                                  ])

        #------------
        # Tab schemes
        #------------
        new_scheme = widgets.Text(description="New scheme: ")
        valid_new_scheme = widgets.Button(description = "Create")
        valid_new_scheme.on_click(lambda b : self.create_scheme(new_scheme.value))
        self.select_scheme = widgets.Dropdown(description="Schemes: ", value="", options=[""])
        valid_delete_scheme = widgets.Button(description = "Delete")
        valid_delete_scheme.on_click(lambda b : self.delete_scheme(self.select_scheme.value))
        self.select_label = widgets.Dropdown(description="Labels: ")
        valid_delete_label = widgets.Button(description = "Delete")
        valid_delete_label.on_click(lambda b : self.delete_label(self.select_label.value))
        new_label = widgets.Text(description="New label: ")
        valid_new_label = widgets.Button(description = "Create")
        valid_new_label.on_click(lambda b : self.create_label(new_label.value))

        # Populate
        self.update_tab_schemes()
        self.select_scheme.value = self._schemes.value
        if len(self.select_label.options)>0:
            self.select_label.value = self.select_label.options[0]
        # change labels if scheme change
        def on_change_scheme(change):
            if change['type'] == 'change' and change['name'] == 'value':
                print("change to ",self.select_scheme.value)
                self.update_tab_schemes()
        self.select_scheme.observe(on_change_scheme)
        self._display_next()
        self._display_buttons_labels()

        # group in tab
        tab_schemes = widgets.VBox([
                            widgets.HBox([self.select_scheme, valid_delete_scheme]),
                            widgets.HBox([new_scheme, valid_new_scheme]),
                            widgets.HBox([self.select_label, valid_delete_label]),
                            widgets.HBox([new_label, valid_new_label]),
                        ])

        #----------------
        # Tab SimpleModel
        #----------------
        print(self.state)
        self.simplemodel_state = widgets.Text(disabled=True)
        self.simplemodel_statistics= widgets.Text(disabled=True,
                                                  value = "to implement")

        select_simplemodel =  widgets.Dropdown(description = "models")
        def on_change_scheme(change):
            if change['type'] == 'change' and change['name'] == 'value':
                simplemodel_params.value = json.dumps(self.state["simplemodel"]["available"][select_simplemodel.value])
        select_simplemodel.observe(on_change_scheme)
        select_features = widgets.SelectMultiple()
        simplemodel_params = widgets.Textarea(value="")
        valid_model = widgets.Button(description = "⚙️Train")
        valid_model.on_click(lambda b : self.train_simplemodel(scheme=self._schemes.value, #attention il faudra revoir le choix du scheme
                                                               model = select_simplemodel.value,
                                                               parameters = simplemodel_params.value,
                                                               features = select_features.value))

        # Populate
        self.simplemodel_state.value = f"Scheme : {self._schemes.value} - Current model: {self.state['simplemodel']['current']}"
        select_simplemodel.options = list(self.state["simplemodel"]["available"].keys())
        select_features.options = self.state["features"]["available"]
        if not self.state['simplemodel']['parameters'] is None:
            simplemodel_params.value = json.dumps(self.state['simplemodel']['parameters'])

        # Group in tab
        tab_simplemodel = widgets.VBox([
                            widgets.HBox([self.simplemodel_state,self.simplemodel_statistics]),
                            select_simplemodel,
                             widgets.HBox([select_features,
                                    simplemodel_params]),
                              valid_model
             ])


        # display global widget
        self.output = widgets.Tab([tab_annotate,
                                   tab_data,
                                   tab_schemes,
                                   tab_simplemodel],
                                  titles = ["Annotate",
                                            "Data",
                                            "Schemes",
                                            "SimpleModel"])
        
        # update state on tab change
        def on_tab_selected(change):
            self.state = self.get_state()
            self.update_tab_annotations()
            self.update_tab_schemes()
        self.output.observe(on_tab_selected, names='selected_index')

        # Afficher
        clear_output()
        display(self.output)

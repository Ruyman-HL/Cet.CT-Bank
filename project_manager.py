"""
-------------------------------------------------------------------------------------------
 -- Project: Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of Stranded 
 --          Cetaceans from the Canary Islands
 -- 
 -- File:    project_manager.py
 -- Module:  project_manager
 -- Author:  Ruymán Hernández-López <ruyman.hernandez@ulpgc.es>
 -- Date:    10/06/2025
 -- Version: 1.0
 -- 
 -- Citation: 
 --    Suárez-Santana, C.M., Consoli, F., Rivero, M.A., Fernández, A. & 
 --    Hernández-López, R. Cet.CT-Bank: Postmortem Computed Tomography Dataset of 
 --    Stranded Cetaceans in the Canary Islands. Zenodo (v1). 
 --    https://doi.org/10.5281/zenodo.19709352 (2026).
 -- 
 -- License: 
 --    Creative Commons Attribution 4.0 International (CC BY 4.0).
 --    This code is freely available for use, modification, and redistribution, 
 --    including for commercial purposes, provided that appropriate credit is given 
 --    to the original authors, a link to the license is provided, and any changes 
 --    made are indicated. No additional restrictions may be applied that limit 
 --    others from doing anything the license permits.
 --    Full license text: https://creativecommons.org/licenses/by/4.0/
 --    SPDX-License-Identifier: CC-BY-4.0
 --    When reusing this code, please cite both the dataset and the associated 
 --    publication (see below).
 -- 
 -- Funding:
 --    This research was supported by the Universidad de Las Palmas de Gran Canaria 
 --    under the competitive public funding programme PRECOMP03, grant reference 
 --    SD-24/03, awarded to Principal Investigator Cristian Manuel Suárez Santana.
 --    The contribution of R. Hernández-López was supported by the Research Training 
 --    Personnel Programme of the Universidad de Las Palmas de Gran Canaria, 
 --    Call 2023-2 (3rd phase), under reference FPI2024010053. This programme is 
 --    sponsored by Banco Santander and funded by the Cabildo de Gran Canaria and 
 --    the Ministerio de Ciencia, Innovación y Sociedad de la Información of the 
 --    Gobierno de Canarias.
 -- 
 -- Published in:
 --    Suárez-Santana, C.M., Consoli, F.M.A., Alonso-Almorox, P., Reyes-Matute, A., 
 --    Arbelo, M., Hernández-López, R., Travieso-González, C.M., Rivero, M.A. & 
 --    Fernández, A. Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of 
 --    Stranded Cetaceans from the Canary Islands. Sci Data (2026).
 --    DOI: https://doi.org/10.1038/s41597-026-07896-8
 -- 
 -- Description:
 --     "project_manager" is a comprehensive module for managing application projects and
 --     their associated data. It provides functionality to:
 --     - Create and organize project directory structures
 --     - Store and retrieve application variables in a persistent dictionary
 --     - Save assets to organized subdirectories
 --     - Load existing projects from disk with full data restoration
 --     - List available projects in a given location
 --     - Manage project data lifecycle with automatic serialization
 --     
 --     The module creates a flexible workspace structure with on-demand directory
 --     creation for different asset types (exports, cache, etc.), making it
 --     suitable for any type of application that needs persistent project storage.
 --     
 -- Dependencies:
 --     - adact_path: Custom path handling utility
 --     - shelve: Persistent dictionary storage
 --     - Standard libraries: os
 --     
 -- Main Class:
 --     - ProjectManager: Main class for project creation, loading, and management
 --     
 -- Key Methods:
 --     - save_data(): Store application variables
 --     - get_data(): Retrieve stored variables
 --     - save_asset(): Save generic files to appropriate directories
 --     - save_project(): Persist all project data to disk
 --     - open_project(): Class method to load existing projects
 --     - list_projects(): Static method to list available projects
 --     
 -- Modifications:
 --  Who:   <name><<email>>
 --  Date:   <date>
 --  Changes: <Indication of changes in this version>
-------------------------------------------------------------------------------------------
"""

import os
from adact_path import adact_path
import shelve

class ProjectManager:
    # Directory constants
    PROJECTS_DIR = "Projects"
    DATA_DIR = "data"
    EXPORTS_DIR = "exports"
    CACHE_DIR = "cache"
    DATA_FILE = "data"
    
    def __init__(self, project_name, projects_path, load_existing=False, overwrite=False):
        """
        Initialize a ProjectManager instance
        
        Args:
            project_name (str): Name of the project
            projects_path (str): Base path where projects are stored
            load_existing (bool): If True, load existing project; if False, create new
            *args, **kwargs: Additional arguments for inheritance
        """
        
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty")
        if not projects_path:
            raise ValueError("Projects path cannot be empty")
            
        self.project_name = project_name
        self.data_dict = {}
        
        if load_existing:
            self.project_path = self.load_project(project_name, adact_path(projects_path))
        else:
            self.project_path = self.create_project_dir(adact_path(projects_path))
            self.save_data("Project Name", self.project_name)
            
    def create_project_dir(self, projects_path):
        """
        Create the main project directory structure
        
        Args:
            projects_path (str): Base path where projects are stored
            
        Returns:
            str: Absolute path of the created project directory
        """
        # Create "Projects" directory
        prjs_path = os.path.join(projects_path, self.PROJECTS_DIR)
        if not os.path.exists(prjs_path):
            os.makedirs(prjs_path)
        
        # Create the specific project directory
        project_path = os.path.join(prjs_path, self.project_name)
        os.makedirs(project_path) 
        abs_project_path = os.path.abspath(project_path)
        print(f"Creating project in:\n{abs_project_path}")
        
        self.save_data("Project Path", abs_project_path)
        
        return project_path
    
    def load_project(self, project_name, projects_path):
        """
        Load an existing project from disk
        
        Args:
            project_name (str): Name of the project to load
            projects_path (str): Base path where projects are located
            
        Returns:
            str: Path of the loaded project
            
        Raises:
            FileNotFoundError: If the project doesn't exist
            Exception: If there's an error loading project data
        """
        # Build project path
        prjs_path = os.path.join(projects_path, self.PROJECTS_DIR)
        project_path = os.path.join(prjs_path, project_name)
        
        # Check if project directory exists
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project '{project_name}' doesn't exist at path: {project_path}")
        
        # Check if data file exists
        data_path = os.path.join(project_path, self.DATA_DIR)
        data_file = os.path.join(data_path, self.DATA_FILE)
        
        if not (os.path.exists(data_file + ".db") or  # shelve adds .db, .dat or .bak to filename
                os.path.exists(data_file + ".dat") or
                os.path.exists(data_file + ".bak")):
            raise FileNotFoundError(f"Project data not found at: {data_file}")
        
        # Load project data
        try:
            with shelve.open(data_file, flag='r') as data_project:
                self.data_dict = data_project["data_dict"].copy()
            
            abs_project_path = os.path.abspath(project_path)
            print(f"Project loaded from:\n{abs_project_path}")
            
            return project_path
            
        except Exception as e:
            raise Exception(f"Error loading project data: {e}")
    
    @classmethod
    def open_project(cls, project_name, projects_path):
        """
        Class method to open an existing project in a more intuitive way
        
        Args:
            project_name (str): Name of the project to open
            projects_path (str): Base path where projects are located
            
        Returns:
            ProjectManager: Instance of the class with the loaded project
        """
        return cls(project_name, projects_path, load_existing=True)
     
    @staticmethod
    def list_projects(projects_path):
        """
        List all available projects in the specified path
        
        Args:
            projects_path (str): Base path where projects are located
            
        Returns:
            list: List of available project names
        """
        prjs_path = os.path.join(adact_path(projects_path), ProjectManager.PROJECTS_DIR)
        
        if not os.path.exists(prjs_path):
            return []
        
        projects = []
        for item in os.listdir(prjs_path):
            item_path = os.path.join(prjs_path, item)
            if os.path.isdir(item_path):
                # Check if it has expected structure (data directory)
                data_path = os.path.join(item_path, ProjectManager.DATA_DIR)
                if os.path.exists(data_path):
                    projects.append(item)
        
        return projects
    
    def save_data(self, key, value, overwrite=True):
        """
        Store a variable in the project's data dictionary
        
        Args:
            key (str): Key to identify the variable
            value: Value to store (any serializable object)
            overwrite (bool): If False, ask user before overwriting existing keys
        """
        if not overwrite and key in self.data_dict:
            response = input(f"Key '{key}' already exists with value: {self.data_dict[key]}\n"
                            f"Do you want to overwrite it with: {value}? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                print(f"Key '{key}' was not overwritten.")
                return
        
        self.data_dict[key] = value
    
    def get_data(self, key):
        """
        Retrieve a variable from the project's data dictionary
        
        Args:
            key (str): Key of the variable to retrieve
            
        Returns:
            The stored value associated with the key
            
        Raises:
            KeyError: If the key doesn't exist
        """
        return self.data_dict[key]
    
    def _ensure_directory_exists(self, directory_name):
        """
        Ensure a subdirectory exists within the project, create if necessary
        
        Args:
            directory_name (str): Name of the subdirectory
            
        Returns:
            str: Full path to the directory
        """
        dir_path = os.path.join(self.project_path, directory_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path            

    def save_asset(self, data, filename, key, asset_type='exports'):
        """
        Save a generic asset to the appropriate project directory
        
        Args:
            data: Data to save (file content, binary data, etc.)
            filename (str): Name of the file
            key (str): Key to store the file path in data dictionary
            asset_type (str): Type of asset ('exports', 'cache', or custom directory)
        """
        try:
            # Ensure asset directory exists
            asset_path = self._ensure_directory_exists(asset_type)
            
            file_path = os.path.join(asset_path, filename)
            
            # Handle different types of data
            if isinstance(data, str):
                # Text data
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif isinstance(data, bytes):
                # Binary data
                with open(file_path, 'wb') as f:
                    f.write(data)
            else:
                # Try to handle other types (e.g., pandas DataFrames, numpy arrays)
                if hasattr(data, 'to_csv') and filename.endswith('.csv'):
                    data.to_csv(file_path, index=False)
                elif hasattr(data, 'save') and (filename.endswith('.npy') or filename.endswith('.npz')):
                    data.save(file_path)
                else:
                    raise ValueError(f"Unsupported data type: {type(data)}")
            
            self.data_dict[key] = file_path
            
        except Exception as e:
            raise Exception(f"Error saving asset: {e}")
    
    def save_project(self, overwrite=False):
        """
        Persist all project data to disk using shelve
        
        Args:
            overwrite (bool): If False, ask user before overwriting existing project data
        """
        try:
            # Ensure data directory exists
            data_path = self._ensure_directory_exists(self.DATA_DIR)
            file_name = os.path.join(data_path, self.DATA_FILE)
            
            # Check if project data already exists
            if not overwrite and os.path.exists(file_name + ".db"):
                response = input(f"Project data already exists at: {file_name}\n"
                            f"Do you want to overwrite the existing project? (y/n): ").lower().strip()
                if response not in ['y', 'yes']:
                    print("Project was not saved.")
                    return
            
            with shelve.open(file_name, flag='c', writeback=True) as data_project:
                data_project["data_dict"] = self.data_dict
                print(f"Project saved successfully to: {file_name}")
                
        except Exception as e:
            raise Exception(f"Error saving project: {e}")
    
    def get_project_info(self):
        """
        Get basic information about the project
        
        Returns:
            dict: Dictionary containing project information
        """
        info = {
            'name': self.project_name,
            'path': os.path.abspath(self.project_path),
            'data_keys': list(self.data_dict.keys()),
            'subdirectories': []
        }
        
        # Check which subdirectories exist
        for dir_name in [self.DATA_DIR, self.FIGS_DIR, self.EXPORTS_DIR, self.CACHE_DIR]:
            dir_path = os.path.join(self.project_path, dir_name)
            if os.path.exists(dir_path):
                info['subdirectories'].append(dir_name)
        
        return info
"""
-------------------------------------------------------------------------------------
 -- Project: Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of Stranded 
 --          Cetaceans from the Canary Islands
 -- 
 -- File:    dicom_processor.py
 -- Module:  dicom_processor
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
 --     Main entry point for DICOM metadata extraction and processing. This script
 --     orchestrates the complete workflow for analyzing CT scan DICOM datasets:
 --     
 --     1. Loads configuration parameters from config.yml
 --     2. Processes DICOM directories using the dicom_data_manager module
 --     3. Optionally displays and saves extracted metadata
 --     
 --     The script is designed to work with stranded cetacean CT scan datasets,
 --     extracting hierarchical DICOM structures (Patient/Study/Series/Image) and
 --     additional metadata from individual image files. Results can be saved as
 --     project files for further analysis or inclusion in research databases.
 --     
 --     Configuration (config.yml):
 --       - dicom_path: Path to directory containing DICOMDIR and DICOM images
 --       - projects_root_path: Base directory for saving processed project data
 --     
 -- Dependencies:
 --     - yaml: Configuration file parsing
 --     - adact_path: File system path normalization
 --     - dicom_data_manager: DICOM metadata extraction and processing
 --     
 -- Usage Example:
 --     # Configure paths in config.yml:
 --     dicom_path: "D:/Data/Cetaceans/CET1147/DICOM"
 --     projects_root_path: "./projects"
 --     
 --     # Run the processor:
 --     python dicom_processor.py
 --     
 --     # The process_dicom function accepts parameters for:
 --     - print_metadata: Displays extracted metadata in the console and an html file
 --     - show_sensitive_data: Includes sensitive information
 --     - show_private_data: Includes dicom specific private tags
 --     
 -- Modifications:
 --  Who:   <name><<email>>
 --  Date:   <date>
 --  Changes: <Indication of changes in this version>
-------------------------------------------------------------------------------------
"""
import yaml
from adact_path import adact_path
from dicom_data_manager import process_dicom

def main():    
    # Load configuration from YAML file
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    
    # Normalize paths for cross-platform compatibility
    dicom_path = adact_path(config["dicom_path"])
    projects_root_path = adact_path(config["projects_root_path"])

    # Process DICOM directory and extract metadata
    dicom_records = process_dicom(
        dicom_path, 
        projects_root_path, 
        print_metadata=True, 
        show_sensitive_data=True, 
        show_private_data=True
    )

if __name__ == "__main__": main()
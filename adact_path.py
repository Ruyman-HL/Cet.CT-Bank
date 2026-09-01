"""
-------------------------------------------------------------------------------------
 -- Project: Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of Stranded 
 --          Cetaceans from the Canary Islands
 -- 
 -- File:    adact_path.py
 -- Module:  adact_path
 -- Author:  Ruymán Hernández-López <ruyman.hernandez@ulpgc.es>
 -- Date:    16/06/2023
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
 --    This function adapts and normalizes file system paths by converting them into
 --    standardized Path objects. It takes a path string as input, normalizes it using
 --    os.normpath() to resolve any redundant separators and up-level references, and 
 --    then converts it to a pathlib.Path object for more convenient path manipulation.
 --    This is useful for ensuring consistent path formatting across different operating
 --    systems and simplifying subsequent path operations.
 --
 -- Dependencies:
 --     - Standard libraries: os, pathlib
 --
 -- Modifications:
 --  Who:   <name><<email>>
 --  Date:   <date>
 --  Changes: <Indication of changes in this version>
-------------------------------------------------------------------------------------
"""
import os
from pathlib import Path

def adact_path(old_path):

    new_path = Path(os.path.normpath(old_path))
    
    return new_path
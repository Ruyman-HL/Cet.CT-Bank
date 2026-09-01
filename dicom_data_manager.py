"""
-------------------------------------------------------------------------------------------
 -- Project: Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of Stranded 
 --          Cetaceans from the Canary Islands
 -- 
 -- File:    dicom_data_manager.py
 -- Module:  dicom_data_manager
 -- Author:  Ruymán Hernández López <ruyman.hernandez@ulpgc.es>
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
 --     "dicom_data_manager" is a comprehensive module for processing and analyzing DICOM
 --     medical imaging data. It provides functionality to:
 --     - Parse DICOMDIR files and extract hierarchical patient/study/series/image structures
 --     - Extract additional metadata from individual DICOM image files
 --     - Organize data using shared elements analysis to reduce redundancy
 --     - Display formatted DICOM metadata with color-coded output
 --     - Handle orphaned records and validate DICOM data integrity
 --     - Provide high-level API functions for complete DICOM directory processing
 --     
 --     The module supports both detailed analysis and summary views, with options to
 --     control the display of sensitive and private DICOM elements.
 --     
 -- Dependencies:
 --     - pydicom: DICOM file reading and parsing
 --     - colorama: Cross-platform colored terminal output
 --     - adapt_path: Normalizes file system paths
 --     - project_manager: Manages application projects and their associated data
 --     - dual_logger: Dual output logging to console and HTML file with ANSI color support
 --     - Standard libraries: os, datetime
 --     
 -- Main Functions:
 --     - process_dicom(): High-level function for complete DICOM processing
 --     - get_dicomdir_records(): Extract DICOMDIR structure
 --     - extract_dicom_images_data(): Extract individual image metadata
 --     - print_dicom_records(): Display formatted DICOM data
 --     
 -- Modifications:
 --  Who:   <name><<email>>
 --  Date:   <date>
 --  Changes: <Indication of changes in this version>
-------------------------------------------------------------------------------------------
"""

import pydicom
import os
from colorama import Fore, Style, init
from datetime import datetime
from adact_path import adact_path
from project_manager import ProjectManager
from dual_logger import start_logging, stop_logging


# Initialize colorama for cross-platform colored output
init(autoreset=True)


# =============================================================================
#                            UTILITY FUNCTIONS
# =============================================================================

def _format_date(date_value):
    """Format DICOM date (YYYYMMDD) to DD/MM/YYYY format."""
    if not date_value or date_value == 'Unknown':
        return date_value
    try:
        return datetime.strptime(str(date_value), "%Y%m%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(date_value)


def _format_time(time_value):
    """Format DICOM time (HHMMSS) to HH:MM:SS format."""
    if not time_value or time_value == 'Unknown':
        return time_value
    try:
        time_str = str(time_value)[:6]  # Take first 6 digits (HHMMSS)
        time_obj = datetime.strptime(time_str, "%H%M%S")
        return time_obj.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return str(time_value)


def _format_patient_age(patient_age):
    """Format patient age from DICOM format (e.g., '031Y') to readable format."""
    if not patient_age or patient_age == 'Unknown':
        return patient_age
    
    try:
        age_num = int(patient_age[:3])  # First 3 digits
        age_unit = patient_age[3]       # Last character
        
        unit_map = {'Y': 'years', 'M': 'months', 'W': 'weeks', 'D': 'days'}
        formatted_unit = unit_map.get(age_unit, age_unit)
        
        return f"{age_num} {formatted_unit}"
    except (ValueError, IndexError):
        return str(patient_age)
    
    
def _get_uid_description(uid_value):
    """Get human-readable description for UID using pydicom dictionaries."""
    if not uid_value:
        return 'Unknown'
    
    try:
        from pydicom.uid import UID_dictionary
        uid_str = str(uid_value).strip()
        return UID_dictionary.get(uid_str, (uid_str,))[0]
    except Exception:
        return str(uid_value)
    

def _is_record_valid(record):
    """Check if a DICOM record is valid using RecordInUseFlag (should be 65535)."""
    return getattr(record, 'RecordInUseFlag', None) == 65535

      
def _values_are_equal(val1, val2):
    """Compare two values handling different data types (lists, None, numbers, strings)."""
    # Handle None/Unknown cases
    if (val1 is None or val1 == 'Unknown') and (val2 is None or val2 == 'Unknown'):
        return val1 == val2
    
    # Handle list comparisons
    if isinstance(val1, list) and isinstance(val2, list):
        return (len(val1) == len(val2) and 
                all(_values_are_equal(v1, v2) for v1, v2 in zip(val1, val2)))
    
    # Handle numeric comparisons with floating point tolerance
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        try:
            return abs(float(val1) - float(val2)) < 1e-10
        except (ValueError, TypeError):
            pass
    
    # Handle string comparisons
    try:
        return str(val1) == str(val2)
    except Exception:
        return val1 == val2       

# =============================================================================
#                        PRIVATE ELEMENTS HANDLING
# =============================================================================

def _add_private_elements(record, target_dict):
    """
    Extract private DICOM elements and add them to target dictionary.
    Private elements are stored under 'Private Elements' key with format:
    '_p_(GGGG,EEEE) ElementName'
    
    Excludes specific elements, like (7005,1010).
    """
    private_elements = {}
    
    # Define the tag(s) to exclude
    excluded_tags = {(0x7005, 0x1010)}
    
    for elem in record:
        if elem.tag.is_private:
            # Skip excluded tags
            if (elem.tag.group, elem.tag.element) in excluded_tags:
                continue
            
            group = elem.tag.group
            element = elem.tag.element
            tag_str = f"({group:04X},{element:04X})"
            name = getattr(elem, 'name', 'PrivateElement') or 'PrivateElement'
            key = f"_p_{tag_str} {name}"
            private_elements[key] = elem.value
    
    if private_elements:
        target_dict['Private Elements'] = private_elements 


# =============================================================================
#                        RECORD CREATION FUNCTIONS
# =============================================================================

def _create_dicom_header(file_meta):
    """Extract DICOM header information."""
    return {
        '(0002,0001) File Meta Information Version': getattr(file_meta, 'FileMetaInformationVersion', 'Unknown'),
        '(0002,0002) Media Storage SOP Class UID': _get_uid_description(getattr(file_meta, 'MediaStorageSOPClassUID', 'Unknown')),
        '(0002,0003) Media Storage SOP Instance UID': getattr(file_meta, 'MediaStorageSOPInstanceUID', 'Unknown'),
        '(0002,0010) Transfer Syntax UID': _get_uid_description(getattr(file_meta, 'TransferSyntaxUID', 'Unknown')),
        '(0002,0012) Implementation Class UID': getattr(file_meta, 'ImplementationClassUID', 'Unknown'),
        '(0002,0013) Implementation Version Name': getattr(file_meta, 'ImplementationVersionName', 'Unknown')
    }


def _create_dicomdir_dataset(dataset):
    """Extract DICOM dataset information."""
    return {
        '(0004,1130) File-set ID': getattr(dataset, 'FileSetID', 'Unknown'),
        '(0004,1212) File-set Consistency Flag': getattr(dataset, 'FileSetConsistencyFlag', 'Unknown')
    }


def _create_patient_record(record):
    """Create a patient record dictionary from DICOM record."""
    patient_record = {
        '(0010,0020) Patient ID': getattr(record, 'PatientID', 'Unknown'),
        '_s_(0010,0010) Patients Name': getattr(record, 'PatientName', 'Unknown'),
        '(0010,0040) Patients Sex': getattr(record, 'PatientSex', 'Unknown'),
        '(0010,0030) Patients Birth Date': _format_date(getattr(record, 'PatientBirthDate', 'Unknown'))
    }
    _add_private_elements(record, patient_record)
    patient_record['Studies']={}
    return patient_record


def _create_study_record(record):
    """Create a study record dictionary from DICOM record."""
    study_record = {
        '(0020,0010) Study ID': getattr(record, 'StudyID', 'Unknown'),
        '(0020,000D) Study Instance UID': getattr(record, 'StudyInstanceUID', 'Unknown'),
        '(0008,0050) Accession Number': getattr(record, 'AccessionNumber', 'Unknown'),
        '(0008,0020) Study Date': _format_date(getattr(record, 'StudyDate', 'Unknown')),
        '(0008,0030) Study Time': _format_time(getattr(record, 'StudyTime', 'Unknown')),
        '(0010,1010) Patients Age': _format_patient_age(getattr(record, 'PatientAge', 'Unknown')),
        '(0008,1030) Study Description': getattr(record, 'StudyDescription', 'Unknown')
    }
    _add_private_elements(record, study_record)
    study_record['Series']={}
    return study_record


def _create_series_record(record):
    """Create a series record dictionary from DICOM record."""
    series_record = {
        '(0020,0011) Series Number': getattr(record, 'SeriesNumber', 'Unknown'),
        '(0020,000E) Series Instance UID': getattr(record, 'SeriesInstanceUID', 'Unknown'),
        '(0008,0021) Series Date': _format_date(getattr(record, 'SeriesDate', 'Unknown')),
        '(0008,0031) Series Time': _format_time(getattr(record, 'SeriesTime', 'Unknown')),
        '(0008,0060) Modality': getattr(record, 'Modality', 'Unknown'),
        '(0008,103E) Series Description': getattr(record, 'SeriesDescription', 'Unknown')
    }
    _add_private_elements(record, series_record)
    series_record['Images']={}
    return series_record


def _create_image_record(record):
    """Create an image record dictionary from DICOM record."""
    image_record = {
        # Basic Image Information
        '(0020,0013) Instance Number': getattr(record, 'InstanceNumber', 'Unknown'),
        '(0004,1500) Referenced File ID': getattr(record, 'ReferencedFileID', 'Unknown'),
        '(0008,0008) Image Type': getattr(record, 'ImageType', 'Unknown'),
        '(0008,0023) Content Date': _format_date(getattr(record, 'ContentDate', 'Unknown')),
        '(0008,0033) Content Time': _format_time(getattr(record, 'ContentTime', 'Unknown')),
        
        # Reference Information
        '(0004,1511) Referenced SOP Instance UID in File': getattr(record, 'ReferencedSOPInstanceUIDInFile', 'Unknown'),
        '(0004,1510) Referenced SOP Class UID in File': _get_uid_description(getattr(record, 'ReferencedSOPClassUIDInFile', 'Unknown')),
        
        # Acquisition Parameters
        '(0020,0012) Acquisition Number': getattr(record, 'AcquisitionNumber', 'Unknown'),
        '(0008,0022) Acquisition Date': _format_date(getattr(record, 'AcquisitionDate', 'Unknown')),
        '(0008,0032) Acquisition Time': _format_time(getattr(record, 'AcquisitionTime', 'Unknown')),
        '(0018,0060) KVP': getattr(record, 'KVP', 'Unknown'),
        '(0018,1120) Gantry/Detector Tilt': getattr(record, 'GantryDetectorTilt', 'Unknown'),
        '(0018,1151) X-Ray Tube Current': getattr(record, 'XRayTubeCurrent', 'Unknown'),
        '(0018,1210) Convolution Kernel': getattr(record, 'ConvolutionKernel', 'Unknown'),
        '(0018,1100) Reconstruction Diameter': getattr(record, 'ReconstructionDiameter', 'Unknown'),
        '(0018,0050) Slice Thickness': getattr(record, 'SliceThickness', 'Unknown'),
        
        # Spatial Information
        '(0020,0052) Frame of Reference UID': getattr(record, 'FrameOfReferenceUID', 'Unknown'),
        '(0028,0010) Rows': getattr(record, 'Rows', 'Unknown'),
        '(0028,0011) Columns': getattr(record, 'Columns', 'Unknown'),
        '(0020,0032) Image Position (Patient)': getattr(record, 'ImagePositionPatient', 'Unknown'),
        '(0020,0037) Image Orientation (Patient)': getattr(record, 'ImageOrientationPatient', 'Unknown'),
        '(0020,1041) Slice Location': getattr(record, 'SliceLocation', 'Unknown'),
        '(0028,0030) Pixel Spacing': getattr(record, 'PixelSpacing', 'Unknown')
    }
    _add_private_elements(record, image_record)
    return image_record


# =============================================================================
#                       SHARED ELEMENTS PROCESSING
# =============================================================================

def _extract_shared_elements(records_dict, exclude_keys=None):
    """
    Extract elements that are shared across all records with the same value.
    
    Args:
        records_dict: Dictionary of records (with integer keys)
        exclude_keys: Keys to exclude from sharing (e.g., nested dictionaries)
    
    Returns:
        tuple: (shared_data, shared_private_data, updated_records)
    """
    # Get integer-keyed records only (exclude shared data dictionaries)  
    record_keys = [k for k in records_dict.keys() if isinstance(k, int)]
    
    # Need at least 2 records to find shared elements
    if len(record_keys) < 2:
        return {}, {}, records_dict

    exclude_keys = exclude_keys or set()
    shared_data = {}
    shared_private_data = {}
    
    # Collect all possible element keys from all records
    all_keys = set()
    for record_idx in record_keys:
        record = records_dict[record_idx]
        if isinstance(record, dict):
            all_keys.update(record.keys())
            # Include private elements keys
            if 'Private Elements' in record and isinstance(record['Private Elements'], dict):
                all_keys.update(record['Private Elements'].keys())
    
    # Check each key for sharing across all records
    for element_key in all_keys:
        if element_key in exclude_keys or element_key == 'Private Elements':
            continue
        
        # Collect values from all records
        values = []
        found_in_all = True
        
        for record_idx in record_keys:
            record = records_dict[record_idx]
            if not isinstance(record, dict):
                found_in_all = False
                break
            
            # Check direct keys first, then private elements
            if element_key in record:
                values.append(record[element_key])
            elif ('Private Elements' in record and 
                  isinstance(record['Private Elements'], dict) and 
                  element_key in record['Private Elements']):
                values.append(record['Private Elements'][element_key])
            else:
                found_in_all = False
                break
        
        # If found in all records and all values are identical
        if found_in_all and len(set(str(v) for v in values)) == 1:
            first_value = values[0]
            
            if element_key.startswith('_p_'):
                shared_private_data[element_key] = first_value
            else:
                shared_data[element_key] = first_value
    
    # Create updated records without shared elements
    updated_records = {}
    for record_idx in record_keys:
        updated_record = {}
        original_record = records_dict[record_idx]
        
        for element_key, element_value in original_record.items():
            if element_key in exclude_keys:
                # Keep excluded keys as-is
                updated_record[element_key] = element_value
            elif element_key == 'Private Elements' and isinstance(element_value, dict):
                # Handle private elements specially
                remaining_private = {k: v for k, v in element_value.items() 
                                   if k not in shared_private_data}
                if remaining_private:
                    updated_record['Private Elements'] = remaining_private
            elif element_key not in shared_data and element_key not in shared_private_data:
                # Keep non-shared elements
                updated_record[element_key] = element_value
        
        updated_records[record_idx] = updated_record
    
    return shared_data, shared_private_data, updated_records


def _process_child_level(child_dict, child_key):
    """Route child processing based on hierarchy level."""
    child_processors = {
        'Studies': lambda d: _process_level_recursively(
            d, 'Series', 'Shared Studies Data', 'Shared Studies Private Data'
        ),
        'Series': lambda d: _process_level_recursively(
            d, 'Images', 'Shared Series Data', 'Shared Series Private Data'
        ),
        'Images': lambda d: _process_level_recursively(
            d, None, 'Shared Images Data', 'Shared Images Private Data'
        )
    }
    
    processor = child_processors.get(child_key)
    return processor(child_dict) if processor else child_dict


def _process_level_recursively(records_dict, child_key, shared_data_name, shared_private_name):
    """
    Process a hierarchical level recursively to extract shared elements.
    
    Args:
        records_dict: Dictionary containing records at current level
        child_key: Key for child records ('Studies', 'Series', 'Images', or None)
        shared_data_name: Name for shared data dictionary
        shared_private_name: Name for shared private data dictionary
    """
    if not isinstance(records_dict, dict):
        return records_dict
    
    # Process child levels first (recursive descent)
    processed_records = {}
    for record_idx, record_data in records_dict.items():
        if isinstance(record_idx, int) and isinstance(record_data, dict) and child_key in record_data:
            processed_records[record_idx] = record_data.copy()
            processed_records[record_idx][child_key] = _process_child_level(
                record_data[child_key], child_key
            )
        else:
            processed_records[record_idx] = record_data
    
    # Extract shared elements at current level
    exclude_keys = {child_key} if child_key else set()
    shared_data, shared_private_data, updated_records = _extract_shared_elements(
        processed_records, exclude_keys=exclude_keys
    )
    
    # Build result dictionary
    result_dict = {}
    if shared_data:
        result_dict[shared_data_name] = shared_data
    if shared_private_data:
        result_dict[shared_private_name] = shared_private_data
    
    result_dict.update(updated_records)
    return result_dict


def process_shared_elements(dicomdir_records):
    """
    Process DICOMDIR records to extract shared elements at each hierarchical level.
    This reduces redundancy by moving common elements to shared dictionaries.
    """
    if not dicomdir_records or 'error' in dicomdir_records:
        return dicomdir_records
    
    updated_records = dicomdir_records.copy()
    
    # Process each top-level category
    level_configs = {
        'Patients': ('Studies', 'Shared Patients Data', 'Shared Patients Private Data'),
        'Orphaned Studies': ('Series', 'Shared Studies Data', 'Shared Studies Private Data'),
        'Orphaned Series': ('Images', 'Shared Series Data', 'Shared Series Private Data'),
        'Orphaned Images': (None, 'Shared Images Data', 'Shared Images Private Data')
    }
    
    for category, (child_key, shared_name, private_name) in level_configs.items():
        if category in updated_records:
            updated_records[category] = _process_level_recursively(
                updated_records[category], child_key, shared_name, private_name
            )
    
    return updated_records

# =============================================================================
#                               STATISTICS
# =============================================================================

def _initialize_statistics():
    """Initialize record statistics structure."""
    return {
        'PATIENT': {'total': 0, 'valid': 0, 'invalid': 0},
        'STUDY': {'total': 0, 'valid': 0, 'invalid': 0},
        'SERIES': {'total': 0, 'valid': 0, 'invalid': 0},
        'IMAGE': {'total': 0, 'valid': 0, 'invalid': 0, 'available': 0, 'missing': 0}
    }

def _update_statistics(statistics, record_type, is_valid, im_file_exists=None):
    """Update record statistics for given record type."""
    statistics[record_type]['total'] += 1
    if is_valid:
        statistics[record_type]['valid'] += 1
    else:
        statistics[record_type]['invalid'] += 1
    
    # Update availability statistics for IMAGE records
    if record_type == 'IMAGE' and im_file_exists is not None:
        if im_file_exists:
            statistics['IMAGE']['available'] += 1
        else:
            statistics['IMAGE']['missing'] += 1
            
def _check_image_file_exists(file_id, dicom_base_path):
    """Check if the image file exists at the specified path."""
    try:
        if file_id and file_id != 'Unknown':            
            im_fpath = os.path.join(dicom_base_path, *file_id)
            return os.path.isfile(im_fpath)
        return False
    except (TypeError, OSError):
        return False

# =============================================================================
#                         HIERARCHY TRACKING
# =============================================================================

class HierarchyTracker:
    """Track current position in DICOM hierarchy and handle orphaned records."""
    
    def __init__(self):
        self.current_patient_idx = -1
        self.current_study_idx = -1
        self.current_series_idx = -1
        self.orphaned_study_idx = -1
        self.orphaned_series_idx = -1
        self.orphaned_image_idx = -1
        self.image_idx = -1
        
        # Flags to skip invalid hierarchies
        self.skip_current_patient = False
        self.skip_current_study = False
        self.skip_current_series = False
        
    
    def _reset_skip_flags(self):
        """Reset all skip flags."""
        self.skip_current_patient = False
        self.skip_current_study = False
        self.skip_current_series = False
    
    def _set_skip_all(self):
        """Set all skip flags to True."""
        self.skip_current_patient = True
        self.skip_current_study = True
        self.skip_current_series = True
    
    def _determine_series_location(self):
        """Determine where to place the series record."""
        if self.current_patient_idx >= 0 and self.current_study_idx >= 0:
            return 'patient_study'
        elif self.orphaned_study_idx >= 0:
            return 'orphaned_study'
        else:
            self.orphaned_series_idx += 1
            self.current_series_idx = -1
            return 'orphaned'
    
    def _determine_image_location(self):
        """Determine where to place the image record."""
        if self.current_patient_idx >= 0 and self.current_study_idx >= 0 and self.current_series_idx >= 0:
            return 'patient_study_series'
        elif self.orphaned_study_idx >= 0 and self.current_series_idx >= 0:
            return 'orphaned_study_series'
        elif self.orphaned_series_idx >= 0:
            return 'orphaned_series'
        else:
            self.orphaned_image_idx += 1
            return 'orphaned'
    
    def process_patient(self, is_valid):
        """Process patient record and update tracking."""
        if is_valid:
            self.current_patient_idx += 1
            self.current_study_idx = -1
            self._reset_skip_flags()
        else:
            self._set_skip_all()
    
    def process_study(self, is_valid):
        """Process study record and update tracking."""
        if self.skip_current_patient:
            return None
            
        if is_valid:
            self.current_study_idx += 1
            self.current_series_idx = -1
            self.skip_current_study = False
            self.skip_current_series = False
            return 'normal'
        else:
            self.skip_current_study = True
            self.skip_current_series = True
            return None
    
    def process_series(self, is_valid):
        """Process series record and update tracking."""
        if self.skip_current_patient or self.skip_current_study:
            return None
            
        if is_valid:
            self.current_series_idx += 1
            self.image_idx = -1
            self.skip_current_series = False
            return self._determine_series_location()
        else:
            self.skip_current_series = True
            return None
    
    def process_image(self, is_valid):
        """Process image record and update tracking."""
        if self.skip_current_patient or self.skip_current_study or self.skip_current_series:
            return None
        
        if is_valid:
            self.image_idx += 1
            return self._determine_image_location()
        return None
    
    def handle_orphaned_study(self):
        """Handle orphaned study (no parent patient)."""
        self.orphaned_study_idx += 1
        self.current_study_idx = -1


# =============================================================================
#                       IMAGE DATA EXTRACTION
# =============================================================================

def _extract_image_data(dicom_file_path):
    """
    Extract additional DICOM metadata from individual image files.
    
    Args:
        dicom_file_path (str): Path to the DICOM image file
        
    Returns:
        dict: Dictionary containing extracted DICOM metadata, or None if error occurs
    """
    try:
        ds = pydicom.dcmread(dicom_file_path)        
        
        # Create dictionary with additional DICOM elements
        additional_data = _create_dicom_header(ds.file_meta)
        additional_data.update({
            '(0008,0016) SOP Class UID': getattr(ds, 'SOPClassUID', 'Unknown'),
            '(0008,0018) SOP Instance UID': getattr(ds, 'SOPInstanceUID', 'Unknown'),            
            
            # Institution Information (sensitive data with _s_ prefix)
            '_s_(0008,0080) Institution Name': getattr(ds, 'InstitutionName', 'Unknown'),
            '_s_(0008,0081) Institution Address': getattr(ds, 'InstitutionAddress', 'Unknown'), 
            '_s_(0008,1040) Institutional Department Name': getattr(ds, 'InstitutionalDepartmentName', 'Unknown'),
            '_s_(0008,0090) Referring Physician Name': getattr(ds, 'ReferringPhysicianName', 'Unknown'),
            
            # Equipment Information
            '(0008,0070) Manufacturer': getattr(ds, 'Manufacturer', 'Unknown'),
            '(0008,1010) Station Name': getattr(ds, 'StationName', 'Unknown'),
            '(0008,1090) Manufacturers Model Name': getattr(ds, 'ManufacturerModelName', 'Unknown'),
            '(0018,1000) Device Serial Number': getattr(ds, 'DeviceSerialNumber', 'Unknown'),
            '(0018,1020) Software Versions': getattr(ds, 'SoftwareVersions', 'Unknown'),
            
            # Patient Information
            '(0010,1030) Patient Weight': getattr(ds, 'PatientWeight', 'Unknown'),
            
            # Acquisition Parameters
            '(0018,0022) Scan Options': getattr(ds, 'ScanOptions', 'Unknown'),
            '(0018,0090) Data Collection Diameter': getattr(ds, 'DataCollectionDiameter', 'Unknown'),
            '(0018,1030) Protocol Name': getattr(ds, 'ProtocolName', 'Unknown'),
            '(0018,1130) Table Height': getattr(ds, 'TableHeight', 'Unknown'),
            '(0018,1140) Rotation Direction': getattr(ds, 'RotationDirection', 'Unknown'),
            '(0018,1150) Exposure Time': getattr(ds, 'ExposureTime', 'Unknown'),
            '(0018,1152) Exposure': getattr(ds, 'Exposure', 'Unknown'),
            '(0018,1160) Filter Type': getattr(ds, 'FilterType', 'Unknown'),
            '(0018,1170) Generator Power': getattr(ds, 'GeneratorPower', 'Unknown'),
            '(0018,1190) Focal Spot(s)': getattr(ds, 'FocalSpots', 'Unknown'),
            '(0018,9302) Acquisition Type': getattr(ds, 'AcquisitionType', 'Unknown'),
            '(0018,9305) Revolution Time': getattr(ds, 'RevolutionTime', 'Unknown'),
            '(0018,9306) Single Collimation Width': getattr(ds, 'SingleCollimationWidth', 'Unknown'),
            '(0018,9307) Total Collimation Width': getattr(ds, 'TotalCollimationWidth', 'Unknown'),
            '(0018,9310) Table Feed per Rotation': getattr(ds, 'TableFeedperRotation', 'Unknown'),
            '(0018,9311) Spiral Pitch Factor': getattr(ds, 'SpiralPitchFactor', 'Unknown'),
            '(0018,9318) Reconstruction Target Center (Patient)': getattr(ds, 'ReconstructionTargetCenterPatient', 'Unknown'),
            '(0018,9327) Table Position': getattr(ds, 'TablePosition', 'Unknown'),
            '(0018,9334) Fluoroscopy Flag': getattr(ds, 'FluoroscopyFlag', 'Unknown'),
            '(0018,9345) CTDIvol': getattr(ds, 'CTDIvol', 'Unknown'),
            
            # Positioning Information
            '(0020,0020) Patient Orientation': getattr(ds, 'PatientOrientation', 'Unknown'),
            '(0018,5100) Patient Position': getattr(ds, 'PatientPosition', 'Unknown'),
            '(0020,1040) Position Reference Indicator': getattr(ds, 'PositionReferenceIndicator', 'Unknown'),
            '(0020,9056) Stack ID': getattr(ds, 'StackID', 'Unknown'),
            '(0020,9057) In-Stack Position Number': getattr(ds, 'InStackPositionNumber', 'Unknown'),
            '(0020,9128) Temporal Position Index': getattr(ds, 'TemporalPositionIndex', 'Unknown'),
            
            # Image Parameters
            '(0028,0002) Samples per Pixel': getattr(ds, 'SamplesPerPixel', 'Unknown'),
            '(0028,0004) Photometric Interpretation': getattr(ds, 'PhotometricInterpretation', 'Unknown'),
            '(0028,0100) Bits Allocated': getattr(ds, 'BitsAllocated', 'Unknown'),
            '(0028,0101) Bits Stored': getattr(ds, 'BitsStored', 'Unknown'),
            '(0028,0102) High Bit': getattr(ds, 'HighBit', 'Unknown'),
            '(0028,0103) Pixel Representation': getattr(ds, 'PixelRepresentation', 'Unknown'),
            '(0028,1050) Window Center': getattr(ds, 'WindowCenter', 'Unknown'),
            '(0028,1051) Window Width': getattr(ds, 'WindowWidth', 'Unknown'),
            '(0028,1052) Rescale Intercept': getattr(ds, 'RescaleIntercept', 'Unknown'),
            '(0028,1053) Rescale Slope': getattr(ds, 'RescaleSlope', 'Unknown'),
            
            # Procedure Information
            '(0040,0002) Scheduled Procedure Step Start Date': _format_date(getattr(ds, 'ScheduledProcedureStepStartDate', 'Unknown')),
            '(0040,0003) Scheduled Procedure Step Start Time': _format_time(getattr(ds, 'ScheduledProcedureStepStartTime', 'Unknown')),
            '(0040,0004) Scheduled Procedure Step End Date': _format_date(getattr(ds, 'ScheduledProcedureStepEndDate', 'Unknown')),
            '(0040,0005) Scheduled Procedure Step End Time': _format_time(getattr(ds, 'ScheduledProcedureStepEndTime', 'Unknown')),
            '(0040,0253) Performed Procedure Step ID': getattr(ds, 'PerformedProcedureStepID', 'Unknown'),
            '(0040,0244) Performed Procedure Step Start Date': _format_date(getattr(ds, 'PerformedProcedureStepStartDate', 'Unknown')),
            '(0040,0245) Performed Procedure Step Start Time': _format_time(getattr(ds, 'PerformedProcedureStepStartTime', 'Unknown')),
            
            # Additional Information
            '(0020,4000) Image Comments': getattr(ds, 'ImageComments', 'Unknown')
        })
        
        # Add private elements
        _add_private_elements(ds, additional_data)
        
        return additional_data
        
    except Exception as e:
        print(f"{Fore.RED + Style.BRIGHT}Warning: Could not read DICOM file{Style.RESET_ALL} {dicom_file_path}: {e}")
        return None


def _process_series_images(series_data, dicom_base_path, series_path):
    """
    Process all images in a series and extract additional DICOM metadata.
    
    Args:
        series_data (dict): Series data dictionary containing images
        dicom_base_path (str): Base path to DICOM files directory
        series_path (str): Path description for logging purposes
    """
    if 'Images' not in series_data:
        return
    
    print(f"Processing images in {series_path}")
    
    # Extract additional data from each image
    for img_idx, image_data in series_data['Images'].items():
        if isinstance(img_idx, int) and '(0004,1500) Referenced File ID' in image_data:
            file_id = image_data['(0004,1500) Referenced File ID']
            im_fpath = os.path.join(dicom_base_path, *file_id)
            # Extract additional DICOM data
            additional_data = _extract_image_data(im_fpath)
            
            if additional_data:
                # Merge additional data with existing image data
                series_data['Images'][img_idx].update(additional_data)
                
    # Process shared elements for images in this series
    if len([k for k in series_data['Images'].keys() if isinstance(k, int)]) > 1:
        shared_data, shared_private_data, updated_images = _extract_shared_elements(
            series_data['Images'], exclude_keys=set()
        )
        
        # Update the series with shared data and processed images
        if shared_data:
            series_data['Images']['Shared Images Data'].update(shared_data)
        if shared_private_data:
            series_data['Images']['Shared Images Private Data'].update(shared_private_data)        
        
        # Update images with non-shared elements only
        for img_idx, updated_image in updated_images.items():
            if isinstance(img_idx, int):
                series_data['Images'][img_idx] = updated_image


def _process_orphaned_images(orphaned_images, dicom_base_path):
    """
    Process orphaned images and extract additional DICOM metadata.
    
    Args:
        orphaned_images (dict): Dictionary of orphaned image data
        dicom_base_path (str): Base path to DICOM files directory
    """
    print("Processing orphaned images")
    
    for img_idx, image_data in orphaned_images.items():
        if isinstance(img_idx, int) and '(0004,1500) Referenced File ID' in image_data:
            file_id = image_data['(0004,1500) Referenced File ID']
            im_fpath = os.path.join(dicom_base_path, *file_id)
            # Extract additional DICOM data
            additional_data = _extract_image_data(im_fpath)
            
            if additional_data:
                # Merge additional data with existing image data
                orphaned_images[img_idx].update(additional_data)
    
    # Process shared elements for orphaned images
    if len([k for k in orphaned_images.keys() if isinstance(k, int)]) > 1:
        shared_data, shared_private_data, updated_images = _extract_shared_elements(
            orphaned_images, exclude_keys=set()
        )
        
        # Update with shared data and processed images
        if shared_data:
            orphaned_images['Shared Images Data'].update(shared_data)
        if shared_private_data:
            orphaned_images['Shared Images Private Data'].update(shared_private_data)
        
        # Update images with non-shared elements only
        for img_idx, updated_image in updated_images.items():
            if isinstance(img_idx, int):
                orphaned_images[img_idx] = updated_image


# =============================================================================
#                        DATA CATEGORIZATION
# =============================================================================

def _categorize_shared_images_data(shared_data):
    """
    Reorganize shared images data into predefined categories.
    
    Args:
        shared_data (dict): Original shared data dictionary
        
    Returns:
        dict: Categorized shared data dictionary
    """
    # Define the categorization structure
    categories = {
        'Institution Info': {
            '_s_(0008,0080) Institution Name',
            '_s_(0008,0081) Institution Address', 
            '_s_(0008,1040) Institutional Department Name',
            '_s_(0008,0090) Referring Physician Name'
        },
        
        'Equipment Info': {
            '(0008,1010) Station Name',
            '(0008,0070) Manufacturer',
            '(0008,1090) Manufacturers Model Name',
            '(0018,1000) Device Serial Number',
            '(0018,1020) Software Versions'
        },
        
        'Procedure Info': {
            '(0018,1030) Protocol Name',
            '(0020,4000) Image Comments',
            '(0040,0002) Scheduled Procedure Step Start Date',
            '(0040,0003) Scheduled Procedure Step Start Time',
            '(0040,0004) Scheduled Procedure Step End Date',
            '(0040,0005) Scheduled Procedure Step End Time',
            '(0040,0244) Performed Procedure Step Start Date',
            '(0040,0245) Performed Procedure Step Start Time',
            '(0040,0253) Performed Procedure Step ID'
        },
        
        'Acquisition Parameters': {
            '(0008,0022) Acquisition Date',
            '(0008,0032) Acquisition Time',
            '(0020,0012) Acquisition Number',
            '(0018,9302) Acquisition Type',
            '(0018,0022) Scan Options',
            '(0018,0060) KVP',
            '(0018,1151) X-Ray Tube Current',
            '(0018,1150) Exposure Time',
            '(0018,1152) Exposure',
            '(0018,9305) Revolution Time',
            '(0018,1170) Generator Power',
            '(0018,1190) Focal Spot(s)',
            '(0018,1160) Filter Type',
            '(0018,9334) Fluoroscopy Flag'
        },
        
        'Geometric Parameters': {
            '(0018,1120) Gantry/Detector Tilt',
            '(0018,1140) Rotation Direction',
            '(0018,9306) Single Collimation Width',
            '(0018,9307) Total Collimation Width',
            '(0018,9311) Spiral Pitch Factor',
            '(0018,9310) Table Feed per Rotation',
            '(0018,1130) Table Height',
            '(0018,0090) Data Collection Diameter',
            '(0018,1100) Reconstruction Diameter',
            '(0018,1210) Convolution Kernel'
        },
        
        'Patient Positioning': {
            '(0018,5100) Patient Position',
            '(0020,0020) Patient Orientation',
            '(0020,0037) Image Orientation (Patient)',
            '(0020,1040) Position Reference Indicator',
            '(0010,1030) Patient Weight'
        },
        
        'Image Parameters': {
            '(0028,0010) Rows',
            '(0028,0011) Columns',
            '(0018,0050) Slice Thickness',
            '(0028,0030) Pixel Spacing',
            '(0028,0100) Bits Allocated',
            '(0028,0101) Bits Stored',
            '(0028,0102) High Bit',
            '(0028,0103) Pixel Representation',
            '(0028,0002) Samples per Pixel',
            '(0028,0004) Photometric Interpretation'
        },
        
        'HU Conversion & Display': {
            '(0028,1051) Window Width',
            '(0028,1050) Window Center',
            '(0028,1052) Rescale Intercept',
            '(0028,1053) Rescale Slope'
        },
        
        'Dose Information': {
            '(0018,9345) CTDIvol'
        },
        
        'Series Organization': {
            '(0008,0008) Image Type',
            '(0008,0023) Content Date',
            '(0020,0052) Frame of Reference UID',
            '(0020,9056) Stack ID',
            '(0020,9128) Temporal Position Index'
        },
        
        'DICOM Technical': {
            '(0002,0013) Implementation Version Name',
            '(0002,0012) Implementation Class UID',
            '(0002,0001) File Meta Information Version',
            '(0002,0002) Media Storage SOP Class UID',
            '(0002,0010) Transfer Syntax UID',
            '(0004,1510) Referenced SOP Class UID in File',
            '(0008,0016) SOP Class UID'
        }
    }
    
    # Initialize categorized structure
    categorized_data = {}
    others = {}
    
    # Create all known element keys set for quick lookup
    all_known_keys = set()
    for category_keys in categories.values():
        all_known_keys.update(category_keys)
    
    # Categorize existing shared data
    for category_name, category_keys in categories.items():
        category_data = {}
        
        # Check each key in this category
        for key in category_keys:
            if key in shared_data:
                category_data[key] = shared_data[key]
        
        # Only add category if it has data
        if category_data:
            categorized_data[category_name] = category_data
    
    # Add elements not in any predefined category to 'Others'
    for key, value in shared_data.items():
        if key not in all_known_keys:
            others[key] = value
    
    # Add 'Others' category if it has data
    if others:
        categorized_data['Others'] = others
    
    return categorized_data


def _apply_categorization_to_images_data(records_dict):
    """
    Apply categorization to all 'Shared Images Data' in the records structure.
    
    Args:
        records_dict (dict): The complete DICOM records dictionary
        
    Returns:
        dict: Updated records dictionary with categorized shared images data
    """
    def _process_images_dict(images_dict):
        """Process an Images dictionary and categorize its shared data."""
        if not isinstance(images_dict, dict):
            return images_dict
            
        # Check if there's shared images data to categorize
        if 'Shared Images Data' in images_dict:
            shared_data = images_dict['Shared Images Data']
            if isinstance(shared_data, dict) and shared_data:
                images_dict['Shared Images Data'] = _categorize_shared_images_data(shared_data)
        
        return images_dict
    
    # Process the entire records structure
    updated_records = records_dict.copy()
    
    # Process Patients hierarchy
    if 'Patients' in updated_records:
        for patient_idx, patient_data in updated_records['Patients'].items():
            if isinstance(patient_idx, int) and isinstance(patient_data, dict):
                # Process studies in patient
                if 'Studies' in patient_data:
                    for study_idx, study_data in patient_data['Studies'].items():
                        if isinstance(study_idx, int) and isinstance(study_data, dict):
                            # Process series in study
                            if 'Series' in study_data:
                                for series_idx, series_data in study_data['Series'].items():
                                    if isinstance(series_idx, int) and isinstance(series_data, dict):
                                        if 'Images' in series_data:
                                            series_data['Images'] = _process_images_dict(series_data['Images'])
    
    # Process Orphaned Studies
    if 'Orphaned Studies' in updated_records:
        for study_idx, study_data in updated_records['Orphaned Studies'].items():
            if isinstance(study_idx, int) and isinstance(study_data, dict):
                if 'Series' in study_data:
                    for series_idx, series_data in study_data['Series'].items():
                        if isinstance(series_idx, int) and isinstance(series_data, dict):
                            if 'Images' in series_data:
                                series_data['Images'] = _process_images_dict(series_data['Images'])
    
    # Process Orphaned Series
    if 'Orphaned Series' in updated_records:
        for series_idx, series_data in updated_records['Orphaned Series'].items():
            if isinstance(series_idx, int) and isinstance(series_data, dict):
                if 'Images' in series_data:
                    series_data['Images'] = _process_images_dict(series_data['Images'])
    
    # Process Orphaned Images
    if 'Orphaned Images' in updated_records:
        updated_records['Orphaned Images'] = _process_images_dict(updated_records['Orphaned Images'])
    
    return updated_records


# =============================================================================
#                         DISPLAY FUNCTIONS
# =============================================================================

def print_dicom_records(dicom_records, show_sensitive_data=False, show_private_data=False, max_value_length=80):
    """
    Print DICOM records in a hierarchical, formatted way with color coding.
    
    Args:
        dicom_records (dict): Dictionary returned by get_dicomdir_records() and enhanced by extract_dicom_images_data()
        show_sensitive_data (bool): Whether to show sensitive data (keys starting with '_s_')
        show_private_data (bool): Whether to show private data (keys starting with '_p_')
        max_value_length (int): Maximum length for displayed values before truncation
    """
    
    def _should_show_key(key):
        """Determine if a key should be displayed based on filtering options."""
        if key.startswith('_s_') and not show_sensitive_data:
            return False
        if key.startswith('_p_') and not show_private_data:
            return False
        return True
    
    def _format_value(value, indent_level=0):
        """Format a value for display, handling different data types."""
        if isinstance(value, dict):
            return _format_dict(value, indent_level + 1)
        elif isinstance(value, (list, tuple)):
            if len(value) == 0:
                return "[]"
            elif len(value) == 1:
                return str(value[0])
            else:
                return f"[{', '.join(str(v) for v in value[:3])}{'...' if len(value) > 3 else ''}]"
        else:
            str_value = str(value)
            if len(str_value) > max_value_length:
                return str_value[:max_value_length] + "..."
            return str_value
    
    def _format_dict(data_dict, indent_level=0, prefix=""):
        """Format a dictionary for display."""
        indent = "  " * indent_level
        result = []
        
        for key, value in data_dict.items():
            if not _should_show_key(key):
                continue
                
            formatted_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict) and value:
                result.append(f"{indent}{Fore.CYAN}{formatted_key}:{Style.RESET_ALL}")
                result.append(_format_dict(value, indent_level + 1))
            else:
                formatted_value = _format_value(value, indent_level)
                result.append(f"{indent}{formatted_key}: {formatted_value}")
        
        return "\n".join(result)    
    
    def _print_statistics(stats):
        """Print record statistics in a formatted table."""
        print(f"{Fore.CYAN + Style.BRIGHT}RECORD STATISTICS:{Style.RESET_ALL}")
        print("┌─────────────┬───────┬───────┬─────────┬───────────┬─────────┐")
        print("│ Record Type │ Total │ Valid │ Invalid │ Available │ Missing │")
        print("├─────────────┼───────┼───────┼─────────┼───────────┼─────────┤")
        
        for rec_type, counts in stats.items():
            if rec_type == 'IMAGE':
                # Special formatting for IMAGE records with availability info
                print(f"│ {rec_type:<11} │ {counts['total']:>5} │ {counts['valid']:>5} │ {counts['invalid']:>7} │ {counts.get('available', 'N/A'):>9} │ {counts.get('missing', 'N/A'):>7} │")
            else:
                # Standard formatting for other record types
                print(f"│ {rec_type:<11} │ {counts['total']:>5} │ {counts['valid']:>5} │ {counts['invalid']:>7} │ {'N/A':>9} │ {'N/A':>7} │")
        
        print("└─────────────┴───────┴───────┴─────────┴───────────┴─────────┘")
        print()
    
    def _print_shared_data(data_dict, data_type, indent_level):
        """Print shared data section for any level (Patient, Study, Series, Images)."""
        indent = "  " * indent_level
        
        # Define shared data keys for different levels
        shared_keys = {
            'Patient': ['Shared Patient Data', 'Shared Patient Private Data'],
            'Study': ['Shared Study Data', 'Shared Study Private Data'],
            'Series': ['Shared Series Data', 'Shared Series Private Data'],
            'Images': ['Shared Images Data', 'Shared Images Private Data']
        }
        
        if data_type not in shared_keys:
            return
        
        shared_data_key, shared_private_key = shared_keys[data_type]
        
        # Print shared non-private data
        if shared_data_key in data_dict and data_dict[shared_data_key]:
            shared_data = data_dict[shared_data_key]
            print(f"{indent}🔗 {Fore.GREEN + Style.BRIGHT}Shared {data_type} Data:{Style.RESET_ALL}")
            
            if isinstance(shared_data, dict):
                # Handle categorized shared data
                for category, category_data in shared_data.items():
                    if isinstance(category_data, dict) and category_data:
                        filtered_data = {k: v for k, v in category_data.items() if _should_show_key(k)}
                        if filtered_data:
                            print(f"{indent}  {Fore.YELLOW}📂 {category}:{Style.RESET_ALL}")
                            for key, value in filtered_data.items():
                                formatted_value = _format_value(value)
                                print(f"{indent}    {key}: {formatted_value}")
                    else:
                        # Handle direct key-value pairs
                        if _should_show_key(category):
                            formatted_value = _format_value(category_data)
                            print(f"{indent}  {category}: {formatted_value}")
            print()
        
        # Print shared private data
        if shared_private_key in data_dict and data_dict[shared_private_key] and show_private_data:
            private_data = data_dict[shared_private_key]
            if private_data:
                print(f"{indent}🔒 {Fore.RED + Style.BRIGHT}Shared {data_type} Private Data:{Style.RESET_ALL}")
                for key, value in private_data.items():
                    if _should_show_key(key):
                        formatted_value = _format_value(value)
                        print(f"{indent}  {key}: {formatted_value}")
                print()
    
    def _print_private_elements(private_data, indent_level):
        """Print private elements with proper formatting and line breaks."""
        if not private_data or not show_private_data:
            return
            
        indent = "  " * indent_level
        print(f"{indent}Private Elements:")  # Added proper line break here
        
        for key, value in private_data.items():
            if _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"{indent}  {key}: {formatted_value}")
    
    def _analyze_shared_vs_individual_data(images_dict):
        """Analyze what data is shared vs individual in images."""
        if not isinstance(images_dict, dict):
            return None, None, 0
            
        # Count actual image records (integer keys)
        image_count = len([k for k in images_dict.keys() if isinstance(k, int)])
        
        shared_data = {}
        individual_keys = set()
        
        # Check for explicit shared data
        if 'Shared Images Data' in images_dict:
            shared_data = images_dict['Shared Images Data']
        
        # Analyze individual images for varying data
        individual_images = {k: v for k, v in images_dict.items() if isinstance(k, int)}
        if len(individual_images) > 1:
            all_keys = set()
            for img_data in individual_images.values():
                all_keys.update(img_data.keys())
            
            for key in all_keys:
                if not _should_show_key(key):
                    continue
                    
                values = []
                for img_data in individual_images.values():
                    if key in img_data:
                        values.append(str(img_data[key]))
                
                if len(set(values)) > 1:  # Values vary across images
                    individual_keys.add(key)
        
        return shared_data, individual_keys, image_count
    
    def _print_images_section(images_dict, indent_level):
        """Print images section with shared/individual data analysis."""
        if not isinstance(images_dict, dict):
            return
            
        indent = "  " * indent_level
        shared_data, varying_keys, image_count = _analyze_shared_vs_individual_data(images_dict)
        
        print(f"{indent}{Fore.MAGENTA + Style.BRIGHT}📁 IMAGES ({image_count} total):{Style.RESET_ALL}")
        
        # Print shared data using the centralized function
        _print_shared_data(images_dict, 'Images', indent_level + 1)
        
        # Print varying data summary
        if varying_keys:
            print(f"{indent}  {Fore.YELLOW + Style.BRIGHT}📊 Data That Varies Across Images:{Style.RESET_ALL}")
            for key in sorted(varying_keys):
                print(f"{indent}    {key}: [VARIES BY IMAGE]")
            print()
        
        # Print individual images (only if requested or if there are few images)
        individual_images = {k: v for k, v in images_dict.items() if isinstance(k, int)}
        if len(individual_images) <= 3:  # Show details only for few images
            for img_idx, img_data in individual_images.items():
                print(f"{indent}  {Fore.MAGENTA}🖼️  Image {img_idx}:{Style.RESET_ALL}")
                for key, value in img_data.items():
                    if key == 'Private Elements':
                        _print_private_elements(value, indent_level + 2)
                    elif _should_show_key(key):
                        formatted_value = _format_value(value)
                        print(f"{indent}    {key}: {formatted_value}")
                print()
    
    def _print_series_data(series_data, series_idx, indent_level):
        """Print series data with proper formatting."""
        indent = "  " * indent_level
        print(f"{indent}{Fore.GREEN + Style.BRIGHT}📊 Series {series_idx}:{Style.RESET_ALL}")
        
        # Print shared series data first
        _print_shared_data(series_data, 'Series', indent_level + 1)
        
        # Print series metadata (excluding Images and shared data)
        exclude_keys = ['Images', 'Shared Series Data', 'Shared Series Private Data', 'Private Elements']
        for key, value in series_data.items():
            if key not in exclude_keys and _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"{indent}  {key}: {formatted_value}")
        
        # Print private elements
        if 'Private Elements' in series_data:
            _print_private_elements(series_data['Private Elements'], indent_level + 1)
        
        # Print images if present
        if 'Images' in series_data:
            _print_images_section(series_data['Images'], indent_level + 1)
        
        print()  # Add spacing after each series
    
    def _print_study_data(study_data, study_idx, indent_level):
        """Print study data with proper formatting."""
        indent = "  " * indent_level
        print(f"{indent}{Fore.BLUE + Style.BRIGHT}🏥 Study {study_idx}:{Style.RESET_ALL}")
        
        # Print shared study data first
        _print_shared_data(study_data, 'Study', indent_level + 1)
        
        # Print study metadata (excluding Series and shared data)
        exclude_keys = ['Series', 'Shared Study Data', 'Shared Study Private Data', 'Private Elements']
        for key, value in study_data.items():
            if key not in exclude_keys and _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"{indent}  {key}: {formatted_value}")
        
        # Print private elements
        if 'Private Elements' in study_data:
            _print_private_elements(study_data['Private Elements'], indent_level + 1)
        
        # Print series if present
        if 'Series' in study_data:
            # FIXED: First print shared series data if it exists
            _print_shared_data(study_data['Series'], 'Series', indent_level + 1)
            
            # Then print individual series
            for series_idx, series_data in study_data['Series'].items():
                if isinstance(series_idx, int):
                    _print_series_data(series_data, series_idx, indent_level + 1)
    
    def _print_patient_data(patient_data, patient_idx):
        """Print patient data with proper formatting."""
        print(f"{Fore.RED + Style.BRIGHT}👤 Patient {patient_idx}:{Style.RESET_ALL}")
        
        # Print shared patient data first
        _print_shared_data(patient_data, 'Patient', 1)
        
        # Print patient metadata (excluding Studies, Orphaned Series, and shared data)
        exclude_keys = ['Studies', 'Orphaned Series in Patient', 'Shared Patient Data', 'Shared Patient Private Data', 'Private Elements']
        for key, value in patient_data.items():
            if key not in exclude_keys and _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"  {key}: {formatted_value}")
        
        # Print private elements
        if 'Private Elements' in patient_data:
            _print_private_elements(patient_data['Private Elements'], 1)
        
        # Print studies
        if 'Studies' in patient_data:
            # FIXED: First print shared studies data if it exists
            _print_shared_data(patient_data['Studies'], 'Study', 2)
            
            # Then print individual studies
            for study_idx, study_data in patient_data['Studies'].items():
                if isinstance(study_idx, int):
                    _print_study_data(study_data, study_idx, 1)
        
        # Print orphaned series in patient
        if 'Orphaned Series in Patient' in patient_data:
            print(f"  {Fore.YELLOW + Style.BRIGHT}⚠️  Orphaned Series in Patient:{Style.RESET_ALL}")
            for series_idx, series_data in patient_data['Orphaned Series in Patient'].items():
                if isinstance(series_idx, int):
                    _print_series_data(series_data, series_idx, 2)
    
    # Start printing
    print("\n" + "="*120)
    print(f"{Fore.YELLOW + Style.BRIGHT}DICOM DIRECTORY RECORDS ANALYSIS".center(120) + Style.RESET_ALL)
    print("="*120)
    
    # Print filter status
    filter_status = []
    if not show_sensitive_data:
        filter_status.append("sensitive data hidden")
    if not show_private_data:
        filter_status.append("private data hidden")
    
    if filter_status:
        print(f"{Fore.YELLOW}🔒 Filter Status: {', '.join(filter_status).title()}{Style.RESET_ALL}")
        print()
    
    # Handle error case
    if 'error' in dicom_records:
        print(f"{Fore.RED + Style.BRIGHT}❌ ERROR: {dicom_records['error']}{Style.RESET_ALL}")
        return
    
    # Print statistics
    if 'Record Statistics' in dicom_records:
        _print_statistics(dicom_records['Record Statistics'])
    
    # Print DICOMDIR header
    if 'DICOMDIR Header' in dicom_records and dicom_records['DICOMDIR Header']:
        print(f"{Fore.CYAN + Style.BRIGHT}📋 DICOMDIR HEADER:{Style.RESET_ALL}")
        for key, value in dicom_records['DICOMDIR Header'].items():
            if _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"  {key}: {formatted_value}")
        print()
    
    # Print DICOMDIR dataset
    if 'DICOMDIR Dataset' in dicom_records and dicom_records['DICOMDIR Dataset']:
        print(f"{Fore.CYAN + Style.BRIGHT}📦 DICOMDIR DATASET:{Style.RESET_ALL}")
        for key, value in dicom_records['DICOMDIR Dataset'].items():
            if _should_show_key(key):
                formatted_value = _format_value(value)
                print(f"  {key}: {formatted_value}")
        print()
    
    # Print patients
    if 'Patients' in dicom_records and dicom_records['Patients']:
        print(f"{Fore.RED + Style.BRIGHT}👥 PATIENTS:{Style.RESET_ALL}")
        
        # FIXED: First print shared patients data if it exists
        _print_shared_data(dicom_records['Patients'], 'Patient', 1)
        
        # Then print individual patients
        for patient_idx, patient_data in dicom_records['Patients'].items():
            if isinstance(patient_idx, int):
                _print_patient_data(patient_data, patient_idx)
                print()
    
    # Print orphaned records
    orphan_sections = [
        ('Orphaned Studies', '🏥', 'STUDIES'),
        ('Orphaned Series', '📊', 'SERIES'), 
        ('Orphaned Images', '🖼️', 'IMAGES')
    ]
    
    for section_key, icon, title in orphan_sections:
        if section_key in dicom_records and dicom_records[section_key]:
            print(f"{Fore.YELLOW + Style.BRIGHT}⚠️  ORPHANED {title}:{Style.RESET_ALL}")
            
            for idx, record_data in dicom_records[section_key].items():
                if isinstance(idx, int):
                    if section_key == 'Orphaned Studies':
                        _print_study_data(record_data, idx, 1)
                    elif section_key == 'Orphaned Series':
                        _print_series_data(record_data, idx, 1)
                    elif section_key == 'Orphaned Images':
                        print(f"  {icon} Image {idx}:")
                        for key, value in record_data.items():
                            if key == 'Private Elements':
                                _print_private_elements(value, 2)
                            elif _should_show_key(key):
                                formatted_value = _format_value(value)
                                print(f"    {key}: {formatted_value}")
            print()
    
    print("="*120)
    print(f"{Fore.GREEN + Style.BRIGHT}✅ Analysis completed successfully{Style.RESET_ALL}")
    print("="*120 + "\n")


def print_dicom_records_summary(dicom_records, show_sensitive_data=False, show_private_data=False):
    """
    Print a concise summary of DICOM records without detailed image data.
    
    Args:
        dicom_records (dict): Dictionary returned by get_dicomdir_records()
        show_sensitive_data (bool): Whether to show sensitive data
        show_private_data (bool): Whether to show private data
    """
    
    def _should_show_key(key):
        if key.startswith('_s_') and not show_sensitive_data:
            return False
        if key.startswith('_p_') and not show_private_data:
            return False
        return True
    
    print("\n" + "="*100)
    print(f"{Fore.YELLOW + Style.BRIGHT}DICOM RECORDS SUMMARY".center(100) + Style.RESET_ALL)
    print("="*100)
    
    if 'error' in dicom_records:
        print(f"{Fore.RED + Style.BRIGHT}❌ ERROR: {dicom_records['error']}{Style.RESET_ALL}")
        return
    
    # Statistics
    if 'Record Statistics' in dicom_records:
        stats = dicom_records['Record Statistics']
        total_records = sum(s['total'] for s in stats.values())
        valid_records = sum(s['valid'] for s in stats.values())
        
        print(f"{Fore.CYAN + Style.BRIGHT}📊 SUMMARY STATISTICS:{Style.RESET_ALL}")
        print(f"  Total Records: {total_records}")
        print(f"  Valid Records: {valid_records}")
        print(f"  Patients: {stats.get('PATIENT', {}).get('total', 0)}")
        print(f"  Studies: {stats.get('STUDY', {}).get('total', 0)}")
        print(f"  Series: {stats.get('SERIES', {}).get('total', 0)}")
        print(f"  Images: {stats.get('IMAGE', {}).get('total', 0)}")
        
        # Add file availability summary
        image_stats = stats.get('IMAGE', {})
        if 'available' in image_stats:
            available = image_stats.get('available', 0)
            missing = image_stats.get('missing', 0)
            total_images = image_stats.get('total', 0)
            
            print(f"  Available Image Files: {available}")
            print(f"  Missing Image Files: {missing}")
            
            # Calculate availability percentage
            if total_images > 0:
                availability_percent = (available / total_images) * 100
                print(f"  File Availability: {availability_percent:.1f}%")
                
        print()
    
    # Patient overview
    if 'Patients' in dicom_records and dicom_records['Patients']:
        print(f"{Fore.RED + Style.BRIGHT}👥 PATIENTS OVERVIEW:{Style.RESET_ALL}")
        for patient_idx, patient_data in dicom_records['Patients'].items():
            if isinstance(patient_idx, int):
                patient_id = patient_data.get('(0010,0020) Patient ID', 'Unknown')
                patient_name = patient_data.get('_s_(0010,0010) Patients Name', 'Unknown')
                
                # Count studies and series
                study_count = len([k for k in patient_data.get('Studies', {}).keys() if isinstance(k, int)])
                series_count = 0
                for study_data in patient_data.get('Studies', {}).values():
                    if isinstance(study_data, dict) and 'Series' in study_data:
                        series_count += len([k for k in study_data['Series'].keys() if isinstance(k, int)])
                
                name_display = patient_name if show_sensitive_data else "[HIDDEN]"
                print(f"  👤 Patient {patient_idx}: ID={patient_id}, Name={name_display}")
                print(f"     Studies: {study_count}, Series: {series_count}")
        print()
    
    # Orphaned records summary
    orphan_counts = {}
    for section in ['Orphaned Studies', 'Orphaned Series', 'Orphaned Images']:
        if section in dicom_records and dicom_records[section]:
            count = len([k for k in dicom_records[section].keys() if isinstance(k, int)])
            if count > 0:
                orphan_counts[section] = count
    
    if orphan_counts:
        print(f"{Fore.YELLOW + Style.BRIGHT}⚠️  ORPHANED RECORDS:{Style.RESET_ALL}")
        for section, count in orphan_counts.items():
            print(f"  {section}: {count}")
        print()
    
    print("="*100 + "\n")

# =============================================================================
#                        HIGH-LEVEL API FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
#                        DICOMDIR PROCESSING
# -----------------------------------------------------------------------------

def get_dicomdir_records(dicomdir_fpath):
    """
    Extract and structure directory records from a DICOMDIR file.
    
    This function parses a DICOMDIR file and creates a hierarchical dictionary structure
    containing patients, studies, series, and images. It handles orphaned records
    (records without proper parent hierarchy) and validates records using RecordInUseFlag.
    
    Args:
        dicomdir_fpath (str): Path to the DICOMDIR file
        print_metadata (bool): If True, prints metadata to console (unused currently)
        show_sensitive_data (bool): If True, shows sensitive data (unused currently)
    
    Returns:
        dict: Structured metadata dictionary containing:
            - Record Statistics: Counts of valid/invalid records by type
            - DICOMDIR Header: File meta information
            - DICOMDIR Dataset: Dataset-level information
            - Patients: Hierarchical patient->study->series->image structure
            - Orphaned Studies/Series/Images: Records without proper parents
    
    Raises:
        FileNotFoundError: If DICOMDIR file doesn't exist
        ValueError: If required DICOM tags are missing or other parsing errors occur
    """
    
    # Initialize result structure
    dicomdir_records = {
        'Record Statistics': _initialize_statistics(),
        'DICOMDIR Header': {},
        'DICOMDIR Dataset': {},
        'Patients': {},
        'Orphaned Studies': {},
        'Orphaned Series': {},
        'Orphaned Images': {}
    }
    
    try:
        # Read DICOMDIR file
        ds = pydicom.dcmread(dicomdir_fpath)
        
        # Add header and dataset information
        dicomdir_records['DICOMDIR Header'] = _create_dicom_header(ds.file_meta)
        dicomdir_records['DICOMDIR Dataset'] = _create_dicomdir_dataset(ds)
        
        # Initialize hierarchy tracker
        tracker = HierarchyTracker()
        
        # Process each directory record
        for record in ds.DirectoryRecordSequence:
            record_type = record.DirectoryRecordType
            is_valid = _is_record_valid(record)
    
            im_file_exists = None  # Initialize for IMAGE records
            
            # Process based on record type
            if record_type == "PATIENT":
                tracker.process_patient(is_valid)
                if is_valid:
                    patient_record = _create_patient_record(record)
                    dicomdir_records['Patients'][tracker.current_patient_idx] = patient_record
                    
            elif record_type == "STUDY":
                study_location = tracker.process_study(is_valid)
                if study_location and is_valid:
                    study_record = _create_study_record(record)
                    
                    if tracker.current_patient_idx >= 0:
                        dicomdir_records['Patients'][tracker.current_patient_idx]['Studies'][tracker.current_study_idx] = study_record
                    else:
                        tracker.handle_orphaned_study()
                        dicomdir_records['Orphaned Studies'][tracker.orphaned_study_idx] = study_record
                        
            elif record_type == "SERIES":
                series_location = tracker.process_series(is_valid)
                if series_location and is_valid:
                    series_record = _create_series_record(record)
                    
                    if series_location == 'patient_study':
                        dicomdir_records['Patients'][tracker.current_patient_idx]['Studies'][tracker.current_study_idx]['Series'][tracker.current_series_idx] = series_record
                    elif series_location == 'orphaned_study':
                        dicomdir_records['Orphaned Studies'][tracker.orphaned_study_idx]['Series'][tracker.current_series_idx] = series_record
                    elif series_location == 'orphaned':
                        dicomdir_records['Orphaned Series'][tracker.orphaned_series_idx] = series_record
                        
            elif record_type == "IMAGE":
                image_location = tracker.process_image(is_valid)
                if image_location and is_valid:
                    image_record = _create_image_record(record)
                    
                    # Check file availability
                    file_id = image_record.get('(0004,1500) Referenced File ID', 'Unknown')
                    dicom_base_path = os.path.dirname(dicomdir_fpath)
                    im_file_exists = _check_image_file_exists(file_id, dicom_base_path)
                    
                    if image_location == 'patient_study_series':
                        dicomdir_records['Patients'][tracker.current_patient_idx]['Studies'][tracker.current_study_idx]['Series'][tracker.current_series_idx]['Images'][tracker.image_idx] = image_record
                    elif image_location == 'orphaned_study_series':
                        dicomdir_records['Orphaned Studies'][tracker.orphaned_study_idx]['Series'][tracker.current_series_idx]['Images'][tracker.image_idx] = image_record
                    elif image_location == 'orphaned_series':
                        dicomdir_records['Orphaned Series'][tracker.orphaned_series_idx]['Images'][tracker.image_idx] = image_record
                    elif image_location == 'orphaned':
                        dicomdir_records['Orphaned Images'][tracker.orphaned_image_idx] = image_record

            else:
                print(f'Another record type has been found. Record type: {record_type}')
            
            # Update statistics
            _update_statistics(dicomdir_records['Record Statistics'], record_type, is_valid, im_file_exists)
                
    except FileNotFoundError:
        error_msg = f"DICOMDIR file not found: {dicomdir_fpath}"
        dicomdir_records["error"] = error_msg
        raise FileNotFoundError(error_msg)
    
    except AttributeError as e:
        error_msg = f"Missing required DICOM tag: {e}"
        dicomdir_records["error"] = error_msg
        raise ValueError(error_msg)
    
    except Exception as e:
        error_msg = f"Error reading DICOMDIR file: {e}"
        dicomdir_records["error"] = error_msg
        raise ValueError(error_msg)
    
    # Process shared elements if no errors occurred
    if 'error' not in dicomdir_records:
        dicomdir_records = process_shared_elements(dicomdir_records)
    
    return dicomdir_records


# -----------------------------------------------------------------------------
#                        DICOM SLICES PROCESSING
# -----------------------------------------------------------------------------

def extract_dicom_images_data(dicom_records, dicom_base_path):
    """
    Extract additional metadata from individual DICOM image files and integrate
    it into the existing DICOMDIR records structure.
    
    This function processes all images referenced in the DICOMDIR structure,
    reads the individual DICOM files, extracts additional metadata, and
    organizes it using the same shared elements approach as get_dicomdir_records().
    
    Args:
        dicom_records (dict): Dictionary returned by get_dicomdir_records()
        dicom_base_path (str): Base path to the directory containing DICOM files
        
    Returns:
        dict: Updated dicom_records dictionary with additional image metadata
    """
    if 'error' in dicom_records:
        print("Error found in DICOM records, skipping image processing")
        return dicom_records
    
    print(f"Starting DICOM image data extraction from: {dicom_base_path}")
    
    # Process all patients
    if 'Patients' in dicom_records:
        for patient_idx, patient_data in dicom_records['Patients'].items():
            if not isinstance(patient_idx, int):
                continue
                
            patient_path = f"Patient {patient_idx}"
            print(f"Processing {patient_path}")
            
            # Process studies in patient
            if 'Studies' in patient_data:
                for study_idx, study_data in patient_data['Studies'].items():
                    if not isinstance(study_idx, int):
                        continue
                        
                    study_path = f"{patient_path} -> Study {study_idx}"
                    
                    # Process series in study
                    if 'Series' in study_data:
                        for series_idx, series_data in study_data['Series'].items():
                            if not isinstance(series_idx, int):
                                continue
                                
                            series_path = f"{study_path} -> Series {series_idx}"
                            _process_series_images(series_data, dicom_base_path, series_path)
            
            # Process orphaned series in patient if any
            if 'Orphaned Series in Patient' in patient_data:
                for series_idx, series_data in patient_data['Orphaned Series in Patient'].items():
                    if not isinstance(series_idx, int):
                        continue
                        
                    series_path = f"{patient_path} -> Orphaned Series {series_idx}"
                    _process_series_images(series_data, dicom_base_path, series_path)
    
    # Process orphaned studies
    if 'Orphaned Studies' in dicom_records and dicom_records['Orphaned Studies']:
        for study_idx, study_data in dicom_records['Orphaned Studies'].items():
            if not isinstance(study_idx, int):
                continue
                
            study_path = f"Orphaned Study {study_idx}"
            print(f"Processing {study_path}")
            
            if 'Series' in study_data:
                for series_idx, series_data in study_data['Series'].items():
                    if not isinstance(series_idx, int):
                        continue
                        
                    series_path = f"{study_path} -> Series {series_idx}"
                    _process_series_images(series_data, dicom_base_path, series_path)
    
    # Process orphaned series
    if 'Orphaned Series' in dicom_records and dicom_records['Orphaned Series']:
        for series_idx, series_data in dicom_records['Orphaned Series'].items():
            if not isinstance(series_idx, int):
                continue
                
            series_path = f"Orphaned Series {series_idx}"
            print(f"Processing {series_path}")
            _process_series_images(series_data, dicom_base_path, series_path)
    
    # Process orphaned images
    if 'Orphaned Images' in dicom_records and dicom_records['Orphaned Images']:
        _process_orphaned_images(dicom_records['Orphaned Images'], dicom_base_path)
        
    # Remove empty orphan sections at the end of processing
    for orphan_key in ['Orphaned Studies', 'Orphaned Series', 'Orphaned Images']:
        if not dicom_records[orphan_key]:
            del dicom_records[orphan_key]
            
    # Apply categorization to shared images data
    dicom_records = _apply_categorization_to_images_data(dicom_records)
    
    print("DICOM image data extraction completed")
    return dicom_records


# -----------------------------------------------------------------------------
#                        ALL DICOM FILES PROCESSING
# -----------------------------------------------------------------------------

def process_dicom(dicom_path, dicom_data_path=False, print_metadata=False, show_sensitive_data=False, show_private_data=False):
    """
    Process a DICOM directory by extracting metadata from DICOMDIR and individual image files.
    
    This is the main high-level function that combines DICOMDIR parsing and individual 
    image metadata extraction into a single operation. It can optionally display the 
    results and save them to a project file.
    
    Args:
        dicom_path (str): Path to the directory containing the DICOMDIR file and DICOM images
        dicom_data_path (str or False): Path where to save the processed data as a project.
                                       If False, data is not saved to disk
        print_metadata (bool): If True, prints the extracted metadata to console
        show_sensitive_data (bool): If True, includes sensitive data in display/output
                                   (keys starting with '_s_')
        show_private_data (bool): If True, includes private data in display/output
                                 (keys starting with '_p_')
    
    Returns:
        dict: Complete DICOM records dictionary containing:
            - DICOMDIR structure with patients, studies, series, and images
            - Additional metadata extracted from individual DICOM files
            - Shared elements analysis to reduce data redundancy
            - Statistics and error information if applicable
    
    Raises:
        FileNotFoundError: If DICOMDIR file is not found in the specified path
        ValueError: If DICOM parsing fails or required tags are missing
        OSError: If path operations or file I/O operations fail
        
    Example:
        # Basic usage - just extract data
        records = process_dicom('/path/to/dicom/folder')
        
        # Extract, display, and save
        records = process_dicom(
            dicom_path='/path/to/dicom/folder',
            dicom_data_path='/path/to/save/projects',
            print_metadata=True,
            show_sensitive_data=True
        )
    """
    dicom_records = None
    
    try:
        # Step 1: Validate and adapt the DICOM path
        print(f"{Fore.CYAN}Processing DICOM directory: {dicom_path}")
        dicom_path = adact_path(dicom_path)
        dicomdir_fpath = os.path.join(dicom_path, 'DICOMDIR')
        
        # Step 2: Extract DICOMDIR records
        print(f"{Fore.YELLOW}Extracting DICOMDIR records...")
        dicom_records = get_dicomdir_records(dicomdir_fpath)
        
        # Check if DICOMDIR processing had errors
        if 'error' in dicom_records:
            print(f"{Fore.RED}Error in DICOMDIR processing: {dicom_records['error']}")
            return dicom_records
        
        # Step 3: Extract additional image metadata
        print(f"{Fore.YELLOW}Extracting individual image metadata...")
        dicom_records = extract_dicom_images_data(dicom_records, dicom_path)

        # Step 4 and 5:
        if dicom_data_path:
            try:
                # Validate and adapt the save path
                dicom_data_path = adact_path(dicom_data_path)
                
                # Generate project name with timestamp and directory name
                prj_name = datetime.now().strftime("Prj_" +"%Y-%m-%d_%H-%M-%S") + "_" + os.path.basename(os.path.normpath(dicom_path))
        
                # Create the project
                project = ProjectManager(prj_name, dicom_data_path)

                # Enable dual logging to save the report in HTML format
                logger = start_logging('report', project.project_path)                

                # Step 4: Display metadata if requested
                if print_metadata:
                    print(f"{Fore.GREEN}Displaying DICOM metadata...")
                    try:
                        print_dicom_records(dicom_records, show_sensitive_data, show_private_data)                
                        # print_dicom_records_summary(dicom_records, show_sensitive_data, show_private_data)
                    except Exception as e:
                        print(f"{Fore.RED}Warning: Could not display metadata: {e}")
                        # Continue processing even if display fails

                # Disable dual logging
                stop_logging(logger)

                # Step 5: Save project data if requested
                print(f"{Fore.YELLOW}Saving project data...")

                project.save_data("Dicom Records", dicom_records)        
                project.save_project()
                
                print(f"{Fore.GREEN}Project saved successfully: {prj_name}")
                
            except Exception as e:
                print(f"{Fore.RED}Warning: Could not save project data: {e}")
                print(f"{Fore.YELLOW}DICOM processing completed, but data was not saved to disk")
                # Continue and return the processed data even if saving fails
        
        print(f"{Fore.GREEN}DICOM processing completed successfully!")
        return dicom_records
        
    except FileNotFoundError as e:
        error_msg = f"DICOMDIR file not found: {e}"
        print(f"{Fore.RED}Error: {error_msg}")
        if dicom_records is None:
            dicom_records = {"error": error_msg}
        else:
            dicom_records["error"] = error_msg
        raise FileNotFoundError(error_msg)
        
    except ValueError as e:
        error_msg = f"DICOM parsing error: {e}"
        print(f"{Fore.RED}Error: {error_msg}")
        if dicom_records is None:
            dicom_records = {"error": error_msg}
        else:
            dicom_records["error"] = error_msg
        raise ValueError(error_msg)
        
    except OSError as e:
        error_msg = f"File system error: {e}"
        print(f"{Fore.RED}Error: {error_msg}")
        if dicom_records is None:
            dicom_records = {"error": error_msg}
        else:
            dicom_records["error"] = error_msg
        raise OSError(error_msg)
        
    except Exception as e:
        error_msg = f"Unexpected error during DICOM processing: {e}"
        print(f"{Fore.RED}Error: {error_msg}")
        if dicom_records is None:
            dicom_records = {"error": error_msg}
        else:
            dicom_records["error"] = error_msg
        raise Exception(error_msg)
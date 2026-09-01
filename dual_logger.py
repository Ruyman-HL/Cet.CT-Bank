"""
-------------------------------------------------------------------------------------
 -- Project: Cet.CT-Bank: A Postmortem Computed Tomography Imaging Data of Stranded 
 --          Cetaceans from the Canary Islands
 -- 
 -- File:    dual_logger.py
 -- Module:  dual_logger
 -- Author:  Ruymán Hernández-López <ruyman.hernandez@ulpgc.es>
 -- Date:    29/10/2025
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
 --    This module provides dual output functionality for logging, allowing simultaneous
 --    printing to both console and an HTML file. It captures all print() statements
 --    and redirects them to maintain console output while also saving them to a 
 --    formatted HTML log file with UTF-8 encoding support for special characters. 
 --    The HTML output includes styling for improved readability.
 --
 -- Dependencies:
 --     - Standard libraries: sys, os, re
 --
 -- Modifications:
 --  Who:   <name><<email>>
 --  Date:   <date>
 --  Changes: <Indication of changes in this version>
-------------------------------------------------------------------------------------
"""
import sys
import os
import re

class DualOutputHTML:
    # ANSI color code mappings to CSS colors
    ANSI_COLORS = {
        '30': '#000000',  # Black
        '31': '#cd3131',  # Red
        '32': '#0dbc79',  # Green
        '33': '#e5e510',  # Yellow
        '34': '#2472c8',  # Blue
        '35': '#bc3fbc',  # Magenta
        '36': '#11a8cd',  # Cyan
        '37': '#e5e5e5',  # White
        '90': '#666666',  # Bright Black (Gray)
        '91': '#f14c4c',  # Bright Red
        '92': '#23d18b',  # Bright Green
        '93': '#f5f543',  # Bright Yellow
        '94': '#3b8eea',  # Bright Blue
        '95': '#d670d6',  # Bright Magenta
        '96': '#29b8db',  # Bright Cyan
        '97': '#ffffff',  # Bright White
    }
    
    def __init__(self, filename, directory):
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Add .html extension to filename
        filename_with_ext = f"{filename}.html"
        
        # Full path
        filepath = os.path.join(directory, filename_with_ext)
        
        self.terminal = sys.stdout
        self.log = open(filepath, 'w', encoding='utf-8')
        self.original_stdout = sys.stdout
        
        # Write HTML header
        self.log.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Log</title>
    <style>
        body { font-family: monospace; white-space: pre-wrap; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
        .bold { font-weight: bold; }
    </style>
</head>
<body>''')
        self.log.flush()
    
    def convert_ansi_to_html(self, text):
        """Convert ANSI color codes to HTML spans"""
        # Escape HTML characters but preserve emojis
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Pattern to match ANSI codes: \033[XXm or \x1b[XXm
        ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m')
        
        result = []
        last_end = 0
        open_spans = 0
        
        for match in ansi_pattern.finditer(text):
            # Add text before this code
            result.append(text[last_end:match.start()])
            
            codes = match.group(1).split(';')
            
            for code in codes:
                if code == '0':  # Reset
                    result.append('</span>' * open_spans)
                    open_spans = 0
                elif code == '1':  # Bold
                    result.append('<span class="bold">')
                    open_spans += 1
                elif code in self.ANSI_COLORS:  # Color
                    color = self.ANSI_COLORS[code]
                    result.append(f'<span style="color: {color};">')
                    open_spans += 1
            
            last_end = match.end()
        
        # Add remaining text
        result.append(text[last_end:])
        
        # Close any remaining spans
        result.append('</span>' * open_spans)
        
        return ''.join(result)
    
    def write(self, message):
        self.terminal.write(message)
        # Convert ANSI codes to HTML
        message_html = self.convert_ansi_to_html(message)
        self.log.write(message_html)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.write('</body></html>')
        self.log.close()
        sys.stdout = self.original_stdout

def start_logging(filename, directory):
    """Starts dual logging (console + HTML)"""
    dual_output = DualOutputHTML(filename, directory)
    sys.stdout = dual_output
    return dual_output

def stop_logging(dual_output):
    """Stops logging and closes HTML file. Returns to console-only printing"""
    dual_output.close()
"""
Robust DWG to DXF Converter - Multiple Methods with Validation
Maximizes data retention during conversion
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
import tempfile
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DWGConverter:
    """
    Multi-strategy DWG to DXF converter with validation
    Tries multiple methods to ensure maximum data retention
    """
    
    # Free/Open-Source conversion tools
    CONVERTERS = {
        'libredwg': {
            'binary': 'dwg2dxf',
            'install': 'apt-get install libredwg-utils (Linux) or brew install libredwg (Mac)',
            'priority': 1
        },
        'dwg2dxf': {
            'binary': 'dwg2dxf',
            'install': 'Part of LibreDWG',
            'priority': 1
        },
        'oda': {
            'binary': 'ODAFileConverter',
            'install': 'https://www.opendesign.com/guestfiles/oda_file_converter',
            'priority': 2,
            'commercial_license': True
        }
    }
    
    def __init__(self, converter_path: Optional[str] = None):
        """
        Initialize converter
        
        Args:
            converter_path: Path to specific converter binary (optional)
        """
        self.converter_path = converter_path
        self.available_converters = self._detect_converters()
        
        if not self.available_converters:
            logger.warning("⚠️ No converters detected! Please install LibreDWG or ODA FileConverter")
    
    def _detect_converters(self) -> Dict[str, str]:
        """Detect available converters on system"""
        available = {}
        
        # Check for LibreDWG
        for cmd in ['dwg2dxf', 'dwg2dxf.exe']:
            if shutil.which(cmd):
                available['libredwg'] = cmd
                logger.info(f"✅ Found LibreDWG: {cmd}")
                break
        
        # Check for ODA FileConverter
        oda_paths = [
            'ODAFileConverter',
            'ODAFileConverter.exe',
            r'C:\Program Files\ODA\ODAFileConverter.exe',
            r'C:\Program Files (x86)\ODA\ODAFileConverter.exe',
            '/usr/local/bin/ODAFileConverter',
            self.converter_path
        ]
        
        for path in oda_paths:
            if path and os.path.exists(path):
                available['oda'] = path
                logger.info(f"✅ Found ODA FileConverter: {path}")
                break
            elif path and shutil.which(path):
                available['oda'] = shutil.which(path)
                logger.info(f"✅ Found ODA FileConverter: {shutil.which(path)}")
                break
        
        return available
    
    def convert(self, dwg_path: str, output_dir: Optional[str] = None, 
                dxf_version: str = 'ACAD2018') -> Tuple[bool, str, Dict]:
        """
        Convert DWG to DXF using best available method
        
        Args:
            dwg_path: Path to input DWG file
            output_dir: Output directory (if None, uses temp directory)
            dxf_version: Target DXF version
            
        Returns:
            Tuple of (success, dxf_path, metadata)
        """
        
        if not os.path.exists(dwg_path):
            logger.error(f"❌ DWG file not found: {dwg_path}")
            return False, "", {"error": "File not found"}
        
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        dwg_name = Path(dwg_path).stem
        dxf_path = os.path.join(output_dir, f"{dwg_name}.dxf")
        
        metadata = {
            'input_file': dwg_path,
            'input_size': os.path.getsize(dwg_path),
            'converter_used': None,
            'conversion_time': 0,
            'warnings': []
        }
        
        # Try converters in priority order
        converters_to_try = sorted(
            self.available_converters.items(),
            key=lambda x: self.CONVERTERS.get(x[0], {}).get('priority', 99)
        )
        
        for converter_name, converter_path in converters_to_try:
            logger.info(f"🔄 Attempting conversion with {converter_name}...")
            
            try:
                import time
                start = time.time()
                
                if converter_name == 'libredwg':
                    success = self._convert_libredwg(dwg_path, dxf_path, converter_path)
                elif converter_name == 'oda':
                    success = self._convert_oda(dwg_path, output_dir, dxf_version, converter_path)
                    # ODA might produce different filename
                    if not os.path.exists(dxf_path):
                        candidates = [f for f in os.listdir(output_dir) if f.endswith('.dxf')]
                        if candidates:
                            dxf_path = os.path.join(output_dir, candidates[0])
                            success = True
                else:
                    success = False
                
                metadata['conversion_time'] = time.time() - start
                
                if success and os.path.exists(dxf_path):
                    metadata['converter_used'] = converter_name
                    metadata['output_file'] = dxf_path
                    metadata['output_size'] = os.path.getsize(dxf_path)
                    
                    # Validate conversion
                    validation = self._validate_conversion(dwg_path, dxf_path)
                    metadata.update(validation)
                    
                    if validation['is_valid']:
                        logger.info(f"✅ Conversion successful with {converter_name}")
                        logger.info(f"📊 Size ratio: {validation['size_ratio']:.2%}")
                        return True, dxf_path, metadata
                    else:
                        logger.warning(f"⚠️ Conversion produced invalid DXF, trying next method...")
                        metadata['warnings'].append(f"{converter_name} produced invalid DXF")
                        
            except Exception as e:
                logger.warning(f"⚠️ {converter_name} failed: {str(e)}")
                metadata['warnings'].append(f"{converter_name}: {str(e)}")
                continue
        
        # All converters failed
        logger.error("❌ All conversion methods failed!")
        metadata['error'] = "All converters failed"
        return False, "", metadata
    
    def _convert_libredwg(self, dwg_path: str, dxf_path: str, binary: str) -> bool:
        """Convert using LibreDWG"""
        try:
            # LibreDWG command: dwg2dxf input.dwg -o output.dxf
            cmd = [binary, dwg_path, '-o', dxf_path, '--as', 'r2018']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"LibreDWG warnings: {result.stderr}")
            
            return os.path.exists(dxf_path) and os.path.getsize(dxf_path) > 0
            
        except subprocess.TimeoutExpired:
            logger.error("LibreDWG conversion timed out")
            return False
        except Exception as e:
            logger.error(f"LibreDWG error: {e}")
            return False
    
    def _convert_oda(self, dwg_path: str, output_dir: str, version: str, binary: str) -> bool:
        """Convert using ODA FileConverter"""
        try:
            # ODA Command: ODAFileConverter <inDir> <outDir> <outVer> <outType> <recurse> <audit>
            input_dir = os.path.dirname(dwg_path)
            
            cmd = [
                binary,
                input_dir,
                output_dir,
                version,
                'DXF',
                '0',  # Don't recurse
                '1'   # Audit and recover
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # ODA returns 0 even with warnings
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("ODA conversion timed out")
            return False
        except Exception as e:
            logger.error(f"ODA error: {e}")
            return False
    
    def _validate_conversion(self, dwg_path: str, dxf_path: str) -> Dict:
        """Validate DXF output"""
        validation = {
            'is_valid': False,
            'size_ratio': 0,
            'entity_count': 0,
            'errors': []
        }
        
        try:
            # Size check (DXF should be larger than DWG due to ASCII format)
            dwg_size = os.path.getsize(dwg_path)
            dxf_size = os.path.getsize(dxf_path)
            validation['size_ratio'] = dxf_size / dwg_size
            
            # DXF should typically be 2-10x larger than DWG
            if validation['size_ratio'] < 0.5:
                validation['errors'].append("DXF suspiciously small")
            
            # Try to parse DXF to verify it's valid
            try:
                import ezdxf
                doc = ezdxf.readfile(dxf_path)
                msp = doc.modelspace()
                
                # Count entities
                validation['entity_count'] = len(list(msp))
                
                if validation['entity_count'] == 0:
                    validation['errors'].append("No entities found in DXF")
                else:
                    validation['is_valid'] = True
                    
            except Exception as e:
                validation['errors'].append(f"DXF parse error: {str(e)}")
                
        except Exception as e:
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation
    
    def batch_convert(self, dwg_files: list, output_dir: str) -> Dict:
        """Convert multiple DWG files"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(dwg_files)
        }
        
        for dwg_path in dwg_files:
            success, dxf_path, metadata = self.convert(dwg_path, output_dir)
            
            if success:
                results['successful'].append({
                    'dwg': dwg_path,
                    'dxf': dxf_path,
                    'metadata': metadata
                })
            else:
                results['failed'].append({
                    'dwg': dwg_path,
                    'metadata': metadata
                })
        
        logger.info(f"📊 Batch conversion: {len(results['successful'])}/{results['total']} successful")
        return results


# Alternative: Pure Python DXF reading (for already-converted files)
def read_dxf_comprehensive(dxf_path: str) -> Dict:
    """
    Read DXF with maximum data extraction
    Better than basic ezdxf usage
    """
    import ezdxf
    from ezdxf import recover
    
    try:
        # Try normal reading first
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        logger.warning(f"Normal read failed, attempting recovery: {e}")
        try:
            # Use recovery mode for damaged files
            doc, auditor = recover.readfile(dxf_path)
            if auditor.has_errors:
                logger.warning(f"⚠️ DXF has {len(auditor.errors)} errors")
        except Exception as e2:
            logger.error(f"❌ Recovery also failed: {e2}")
            raise
    
    # Extract all data
    data = {
        'header': {},
        'layers': {},
        'blocks': {},
        'tables': {},
        'entities': {}
    }
    
    # Header variables
    for varname in doc.header:
        try:
            data['header'][varname] = doc.header[varname]
        except:
            pass
    
    # Layers
    for layer in doc.layers:
        data['layers'][layer.dxf.name] = {
            'name': layer.dxf.name,
            'color': layer.dxf.color,
            'linetype': layer.dxf.linetype,
            'locked': layer.is_locked(),
            'frozen': layer.is_frozen()
        }
    
    # Blocks
    for block in doc.blocks:
        if not block.name.startswith('*'):
            data['blocks'][block.name] = {
                'name': block.name,
                'entities': len(block)
            }
    
    # Tables (styles, linetypes, etc.)
    for table_name in ['styles', 'linetypes', 'dimstyles']:
        if hasattr(doc, table_name):
            data['tables'][table_name] = list(getattr(doc, table_name))
    
    # Modelspace entities
    msp = doc.modelspace()
    entity_types = {}
    for entity in msp:
        entity_type = entity.dxftype()
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    data['entities'] = entity_types
    data['total_entities'] = len(msp)
    
    return data


# Usage Example
if __name__ == "__main__":
    # Initialize converter
    converter = DWGConverter()
    
    # Convert single file
    success, dxf_path, metadata = converter.convert(
        dwg_path="input.dwg",
        output_dir="output",
        dxf_version='ACAD2018'
    )
    
    if success:
        print(f"✅ Converted to: {dxf_path}")
        print(f"📊 Metadata: {metadata}")
        
        # Now extract comprehensive data
        from comprehensive_extractor import ComprehensiveCADExtractor
        extractor = ComprehensiveCADExtractor(dxf_path)
        data = extractor.extract_all()
    else:
        print(f"❌ Conversion failed: {metadata}")
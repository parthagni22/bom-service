"""
backend/app/workers/pipeline.py - UPDATED VERSION
Replace your existing pipeline.py with this
"""

import os
import json
import logging
from pathlib import Path

# Import the new comprehensive modules
from .dwg_converter import DWGConverter
from .comprehensive_extractor import ComprehensiveCADExtractor
from .boq_generator import BOQGenerator, ExcelBOQWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_pipeline(job_id: str, in_path: str, base_dir: str) -> dict:
    """
    Enhanced pipeline with comprehensive data extraction
    
    Pipeline stages:
    1. DWG → DXF conversion (with validation)
    2. Comprehensive entity extraction
    3. Spatial analysis
    4. BOQ generation with intelligent categorization
    5. Professional Excel output
    """
    
    job_root = os.path.join(base_dir, job_id)
    in_dir = os.path.join(job_root, "in")
    out_dir = os.path.join(job_root, "out")
    tmp_dir = os.path.join(job_root, "tmp")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    
    try:
        # STAGE 1: DWG → DXF Conversion
        logger.info(f"[{job_id}] 🔄 Stage 1: Converting DWG to DXF...")
        
        converter = DWGConverter(
            converter_path=os.getenv("CONVERTER_BIN", None)
        )
        
        success, dxf_path, conv_metadata = converter.convert(
            dwg_path=in_path,
            output_dir=tmp_dir,
            dxf_version=os.getenv("DXF_VERSION", "ACAD2018")
        )
        
        if not success:
            raise RuntimeError(f"DWG conversion failed: {conv_metadata.get('error', 'Unknown error')}")
        
        logger.info(f"[{job_id}] ✅ Conversion successful with {conv_metadata['converter_used']}")
        logger.info(f"[{job_id}] 📊 Size ratio: {conv_metadata.get('size_ratio', 0):.2%}")
        
        # STAGE 2: Comprehensive Data Extraction
        logger.info(f"[{job_id}] 🔍 Stage 2: Extracting comprehensive CAD data...")
        
        extractor = ComprehensiveCADExtractor(dxf_path)
        cad_data = extractor.extract_all()
        
        # Validate cad_data
        if cad_data is None:
            raise RuntimeError("Data extraction returned None")
        
        # Ensure all required keys exist
        if 'entities' not in cad_data:
            cad_data['entities'] = {}
        if 'measurements' not in cad_data:
            cad_data['measurements'] = {}
        if 'layers' not in cad_data:
            cad_data['layers'] = {}
        if 'blocks' not in cad_data:
            cad_data['blocks'] = {}
        
        # Save extracted data for debugging/reference
        data_json_path = os.path.join(out_dir, "extracted_data.json")
        extractor.save_to_json(data_json_path)
        
        logger.info(f"[{job_id}] ✅ Extracted {cad_data['measurements'].get('block_count', 0)} blocks, "
                   f"{cad_data['measurements'].get('text_count', 0)} texts, "
                   f"{cad_data['measurements'].get('dimension_count', 0)} dimensions")
        
        # STAGE 3: BOQ Generation
        logger.info(f"[{job_id}] 🔨 Stage 3: Generating BOQ...")
        
        boq_generator = BOQGenerator(cad_data)
        boq_data = boq_generator.generate()
        
        logger.info(f"[{job_id}] ✅ Generated {len(boq_data['items'])} BOQ line items across "
                   f"{boq_data['statistics']['categories']} categories")
        
        # STAGE 4: Excel Export
        logger.info(f"[{job_id}] 📊 Stage 4: Creating Excel BOQ...")
        
        project_info = {
            'Project Name': 'Automated BOQ Generation',
            'Source File': Path(in_path).name,
            'Job ID': job_id,
            'Generated': str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')),
            'Total Items': len(boq_data['items']),
            'Converter Used': conv_metadata['converter_used']
        }
        
        excel_path = os.path.join(out_dir, "BOQ_Output.xlsx")
        excel_writer = ExcelBOQWriter(boq_data, project_info)
        excel_writer.write(excel_path)
        
        logger.info(f"[{job_id}] ✅ BOQ Excel created successfully")
        
        # STAGE 5: Generate Summary Report
        summary = {
            'job_id': job_id,
            'status': 'success',
            'output_files': {
                'boq_excel': excel_path,
                'extracted_data_json': data_json_path,
                'dxf_file': dxf_path
            },
            'statistics': {
                'conversion': conv_metadata,
                'extraction': {
                    'total_entities': sum(len(entities) for entities in (cad_data.get('entities') or {}).values()),
                    'layers': len(cad_data.get('layers', {})),
                    'blocks': len(cad_data.get('blocks', {})),
                    'measurements': cad_data.get('measurements', {})
                },
                'boq': boq_data.get('statistics', {})
            },
            'quality_metrics': {
                'conversion_size_ratio': conv_metadata.get('size_ratio', 0),
                'extraction_entity_count': cad_data['measurements'].get('block_count', 0),
                'boq_high_confidence_items': boq_data['statistics'].get('high_confidence', 0),
                'boq_total_items': len(boq_data['items'])
            }
        }
        
        # Save summary
        summary_path = os.path.join(out_dir, "processing_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"[{job_id}] 🎉 Pipeline completed successfully!")
        
        return summary
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Pipeline failed: {str(e)}", exc_info=True)
        
        error_summary = {
            'job_id': job_id,
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }
        
        # Save error details
        error_path = os.path.join(out_dir, "error_report.json")
        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_summary, f, indent=2)
        
        raise
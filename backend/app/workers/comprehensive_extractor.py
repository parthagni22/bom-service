"""
Simplified but working extractor - NO method references
"""
import ezdxf
import math
import json
from typing import Dict, List

class ComprehensiveCADExtractor:
    def __init__(self, dxf_path: str):
        self.doc = ezdxf.readfile(dxf_path)
        self.msp = self.doc.modelspace()
        self.data = {
            'metadata': {},
            'layers': {},
            'blocks': {},
            'entities': {
                'inserts': [],
                'lines': [],
                'lwpolylines': [],
                'arcs': [],
                'circles': [],
                'mtexts': [],
                'dimensions': [],
                'hatches': [],
            },
            'measurements': {},
            'spatial_analysis': {}
        }
    
    def extract_all(self) -> Dict:
        print("🔍 Starting comprehensive extraction...")
        self._extract_layers()
        self._extract_inserts()
        self._extract_lines()
        self._extract_lwpolylines()
        self._extract_arcs()
        self._extract_circles()
        self._extract_mtexts()
        self._extract_dimensions()
        self._extract_hatches()
        self._calculate_measurements()
        print(f"✅ Extraction complete: {self._get_statistics()}")
        return self.data
    
    def _extract_layers(self):
        for layer in self.doc.layers:
            self.data['layers'][layer.dxf.name] = {
                'name': layer.dxf.name,
                'color': int(layer.dxf.color),
                'linetype': str(layer.dxf.linetype)
            }
    
    def _extract_inserts(self):
        for insert in self.msp.query('INSERT'):
            attrs = {}
            for attrib in insert.attribs:
                attrs[str(attrib.dxf.tag)] = str(attrib.dxf.text)
            
            self.data['entities']['inserts'].append({
                'handle': str(insert.dxf.handle),
                'block_name': str(insert.dxf.name),
                'layer': str(insert.dxf.layer),
                'insertion_point': [float(insert.dxf.insert[0]), float(insert.dxf.insert[1]), float(insert.dxf.insert[2] if len(insert.dxf.insert) > 2 else 0)],
                'rotation': float(insert.dxf.rotation),
                'attributes': attrs
            })
    
    def _extract_lines(self):
        for line in self.msp.query('LINE'):
            self.data['entities']['lines'].append({
                'handle': str(line.dxf.handle),
                'layer': str(line.dxf.layer),
                'start': [float(line.dxf.start[0]), float(line.dxf.start[1]), float(line.dxf.start[2] if len(line.dxf.start) > 2 else 0)],
                'end': [float(line.dxf.end[0]), float(line.dxf.end[1]), float(line.dxf.end[2] if len(line.dxf.end) > 2 else 0)],
                'length': float(math.sqrt(sum((a - b) ** 2 for a, b in zip(line.dxf.start, line.dxf.end))))
            })
    
    def _extract_lwpolylines(self):
        for lwp in self.msp.query('LWPOLYLINE'):
            points = [[float(p[0]), float(p[1])] for p in lwp.get_points('xy')]
            self.data['entities']['lwpolylines'].append({
                'handle': str(lwp.dxf.handle),
                'layer': str(lwp.dxf.layer),
                'closed': bool(lwp.closed),
                'points': points,
                'point_count': int(len(points))
            })
    
    def _extract_arcs(self):
        for arc in self.msp.query('ARC'):
            self.data['entities']['arcs'].append({
                'handle': str(arc.dxf.handle),
                'layer': str(arc.dxf.layer),
                'center': [float(arc.dxf.center[0]), float(arc.dxf.center[1])],
                'radius': float(arc.dxf.radius)
            })
    
    def _extract_circles(self):
        for circle in self.msp.query('CIRCLE'):
            self.data['entities']['circles'].append({
                'handle': str(circle.dxf.handle),
                'layer': str(circle.dxf.layer),
                'center': [float(circle.dxf.center[0]), float(circle.dxf.center[1])],
                'radius': float(circle.dxf.radius)
            })
    
    def _extract_mtexts(self):
        for mtext in self.msp.query('MTEXT'):
            self.data['entities']['mtexts'].append({
                'handle': str(mtext.dxf.handle),
                'layer': str(mtext.dxf.layer),
                'text': str(mtext.text)
            })
    
    def _extract_dimensions(self):
        for dim in self.msp.query('DIMENSION'):
            self.data['entities']['dimensions'].append({
                'handle': str(dim.dxf.handle),
                'layer': str(dim.dxf.layer),
                'text': str(getattr(dim.dxf, 'text', ''))
            })
    
    def _extract_hatches(self):
        for hatch in self.msp.query('HATCH'):
            self.data['entities']['hatches'].append({
                'handle': str(hatch.dxf.handle),
                'layer': str(hatch.dxf.layer),
                'pattern_name': str(hatch.dxf.pattern_name)
            })
    
    def _calculate_measurements(self):
        self.data['measurements'] = {
            'block_count': int(len(self.data['entities']['inserts'])),
            'text_count': int(len(self.data['entities']['mtexts'])),
            'dimension_count': int(len(self.data['entities']['dimensions']))
        }
    
    def _get_statistics(self) -> str:
        stats = []
        for entity_type, entity_list in self.data['entities'].items():
            if entity_list:
                stats.append(f"{entity_type}={len(entity_list)}")
        return ", ".join(stats)
    
    def save_to_json(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"💾 Data saved to {output_path}")
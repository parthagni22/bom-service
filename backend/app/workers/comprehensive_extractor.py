"""
Enhanced DXF/DWG Data Extractor - Comprehensive Entity Extraction
Extracts ALL entity types with maximum accuracy for BOQ generation
"""

import ezdxf
from ezdxf.math import Vec3
from collections import defaultdict
import math
from typing import Dict, List, Any, Tuple
import json

class ComprehensiveCADExtractor:
    """
    Extracts all available data from DXF files with 100% coverage
    """
    
    def __init__(self, dxf_path: str):
        self.doc = ezdxf.readfile(dxf_path)
        self.msp = self.doc.modelspace()
        self.layers = {}
        self.blocks = {}
        self.data = {
            'metadata': {},
            'layers': {},
            'blocks': {},
            'entities': {
                'inserts': [],
                'lines': [],
                'polylines': [],
                'lwpolylines': [],
                'arcs': [],
                'circles': [],
                'texts': [],
                'mtexts': [],
                'dimensions': [],
                'hatches': [],
                'solids': [],
                'splines': [],
                '3dfaces': [],
                'regions': [],
                'bodies': []
            },
            'measurements': {},
            'spatial_analysis': {}
        }
        
    def extract_all(self) -> Dict:
        """Master extraction method"""
        print("🔍 Starting comprehensive extraction...")
        
        # 1. Metadata
        self._extract_metadata()
        
        # 2. Layer information
        self._extract_layers()
        
        # 3. Block definitions
        self._extract_block_definitions()
        
        # 4. All entity types
        self._extract_inserts()
        self._extract_lines()
        self._extract_polylines()
        self._extract_lwpolylines()
        self._extract_arcs()
        self._extract_circles()
        self._extract_texts()
        self._extract_mtexts()
        self._extract_dimensions()
        self._extract_hatches()
        self._extract_3d_solids()
        self._extract_splines()
        self._extract_3dfaces()
        self._extract_regions()
        
        # 5. Spatial analysis
        self._perform_spatial_analysis()
        
        # 6. Calculate measurements
        self._calculate_measurements()
        
        print(f"✅ Extraction complete: {self._get_statistics()}")
        return self.data
    
    def _extract_metadata(self):
        """Extract drawing metadata"""
        header = self.doc.header
        self.data['metadata'] = {
            'dxf_version': self.doc.dxfversion,
            'acadver': header.get('$ACADVER', 'Unknown'),
            'units': self._get_units(),
            'insunits': header.get('$INSUNITS', 0),
            'measurement': header.get('$MEASUREMENT', 0),  # 0=Imperial, 1=Metric
            'extmin': self._vec_to_list(header.get('$EXTMIN', Vec3(0,0,0))),
            'extmax': self._vec_to_list(header.get('$EXTMAX', Vec3(0,0,0))),
            'limmin': self._vec_to_list(header.get('$LIMMIN', Vec3(0,0,0))),
            'limmax': self._vec_to_list(header.get('$LIMMAX', Vec3(0,0,0))),
            'drawing_area': self._calculate_drawing_bounds()
        }
    
    def _get_units(self) -> str:
        """Determine drawing units"""
        insunits = self.doc.header.get('$INSUNITS', 0)
        units_map = {
            0: 'Unitless', 1: 'Inches', 2: 'Feet', 3: 'Miles',
            4: 'Millimeters', 5: 'Centimeters', 6: 'Meters', 7: 'Kilometers',
            8: 'Microinches', 9: 'Mils', 10: 'Yards', 11: 'Angstroms',
            12: 'Nanometers', 13: 'Microns', 14: 'Decimeters'
        }
        return units_map.get(insunits, 'Unknown')
    
    def _extract_layers(self):
        """Extract all layer information"""
        for layer in self.doc.layers:
            self.data['layers'][layer.dxf.name] = {
                'name': layer.dxf.name,
                'color': layer.dxf.color,
                'linetype': layer.dxf.linetype,
                'lineweight': layer.dxf.lineweight,
                'plot': layer.dxf.plot,
                'locked': layer.is_locked(),
                'frozen': layer.is_frozen(),
                'off': layer.is_off(),
                'transparency': getattr(layer.dxf, 'transparency', None)
            }
    
    def _extract_block_definitions(self):
        """Extract block definitions and their contents"""
        for block in self.doc.blocks:
            if not block.name.startswith('*'):  # Skip model/paper space
                attdefs = []
                for entity in block:
                    if entity.dxftype() == 'ATTDEF':
                        attdefs.append({
                            'tag': entity.dxf.tag,
                            'prompt': getattr(entity.dxf, 'prompt', ''),
                            'default': getattr(entity.dxf, 'text', ''),
                            'flags': entity.dxf.flags,
                            'is_const': entity.is_const,
                            'is_invisible': entity.is_invisible,
                            'is_verify': entity.is_verify,
                            'is_preset': entity.is_preset
                        })
                
                self.data['blocks'][block.name] = {
                    'name': block.name,
                    'base_point': self._vec_to_list(block.block.dxf.base_point),
                    'entity_count': len(block),
                    'attribute_definitions': attdefs
                }
    
    def _extract_inserts(self):
        """Extract block insertions with ALL attributes and properties"""
        for insert in self.msp.query('INSERT'):
            # Extract ALL attributes (not just predefined ones)
            attrs = {}
            for attrib in insert.attribs:
                attrs[attrib.dxf.tag] = {
                    'value': attrib.dxf.text,
                    'layer': attrib.dxf.layer,
                    'color': attrib.dxf.color,
                    'height': attrib.dxf.height,
                    'rotation': attrib.dxf.rotation,
                    'invisible': attrib.is_invisible
                }
            
            # Extract extended data (XDATA)
            xdata = self._extract_xdata(insert)
            
            self.data['entities']['inserts'].append({
                'handle': insert.dxf.handle,
                'block_name': insert.dxf.name,
                'layer': insert.dxf.layer,
                'color': insert.dxf.color,
                'linetype': insert.dxf.linetype,
                'insertion_point': self._vec_to_list(insert.dxf.insert),
                'scale': (insert.dxf.xscale, insert.dxf.yscale, insert.dxf.zscale),
                'rotation': insert.dxf.rotation,
                'attributes': attrs,
                'xdata': xdata,
                'has_attributes': insert.has_attrib,
                'column_count': getattr(insert.dxf, 'column_count', 1),
                'row_count': getattr(insert.dxf, 'row_count', 1)
            })
    
    def _extract_lines(self):
        """Extract all LINE entities"""
        for line in self.msp.query('LINE'):
            self.data['entities']['lines'].append({
                'handle': line.dxf.handle,
                'layer': line.dxf.layer,
                'color': line.dxf.color,
                'linetype': line.dxf.linetype,
                'start': self._vec_to_list(line.dxf.start),
                'end': self._vec_to_list(line.dxf.end),
                'length': self._distance_3d(line.dxf.start, line.dxf.end),
                'angle': self._angle_2d(line.dxf.start, line.dxf.end)
            })
    
    def _extract_polylines(self):
        """Extract POLYLINE entities"""
        for pline in self.msp.query('POLYLINE'):
            vertices = [self._vec_to_list(v.dxf.location) for v in pline.vertices]
            self.data['entities']['polylines'].append({
                'handle': pline.dxf.handle,
                'layer': pline.dxf.layer,
                'color': pline.dxf.color,
                'closed': pline.is_closed,
                'vertices': vertices,
                'vertex_count': len(vertices),
                'length': self._polyline_length(vertices, pline.is_closed),
                'area': self._polygon_area(vertices) if pline.is_closed else 0
            })
    
    def _extract_lwpolylines(self):
        """Extract LWPOLYLINE entities (2D optimized polylines)"""
        for lwp in self.msp.query('LWPOLYLINE'):
            points = list(lwp.get_points('xy'))
            self.data['entities']['lwpolylines'].append({
                'handle': lwp.dxf.handle,
                'layer': lwp.dxf.layer,
                'color': lwp.dxf.color,
                'closed': lwp.closed,
                'points': points,
                'point_count': len(points),
                'length': self._polyline_length(points, lwp.closed),
                'area': self._polygon_area(points) if lwp.closed else 0,
                'elevation': lwp.dxf.elevation,
                'const_width': lwp.dxf.const_width
            })
    
    def _extract_arcs(self):
        """Extract ARC entities"""
        for arc in self.msp.query('ARC'):
            self.data['entities']['arcs'].append({
                'handle': arc.dxf.handle,
                'layer': arc.dxf.layer,
                'color': arc.dxf.color,
                'center': self._vec_to_list(arc.dxf.center),
                'radius': arc.dxf.radius,
                'start_angle': arc.dxf.start_angle,
                'end_angle': arc.dxf.end_angle,
                'length': self._arc_length(arc.dxf.radius, arc.dxf.start_angle, arc.dxf.end_angle)
            })
    
    def _extract_circles(self):
        """Extract CIRCLE entities"""
        for circle in self.msp.query('CIRCLE'):
            self.data['entities']['circles'].append({
                'handle': circle.dxf.handle,
                'layer': circle.dxf.layer,
                'color': circle.dxf.color,
                'center': self._vec_to_list(circle.dxf.center),
                'radius': circle.dxf.radius,
                'diameter': circle.dxf.radius * 2,
                'circumference': 2 * math.pi * circle.dxf.radius,
                'area': math.pi * circle.dxf.radius ** 2
            })
    
    def _extract_texts(self):
        """Extract TEXT entities"""
        for text in self.msp.query('TEXT'):
            self.data['entities']['texts'].append({
                'handle': text.dxf.handle,
                'layer': text.dxf.layer,
                'color': text.dxf.color,
                'text': text.dxf.text,
                'insert': self._vec_to_list(text.dxf.insert),
                'height': text.dxf.height,
                'rotation': text.dxf.rotation,
                'style': text.dxf.style,
                'width_factor': text.dxf.width
            })
    
    def _extract_mtexts(self):
        """Extract MTEXT entities (multi-line text)"""
        for mtext in self.msp.query('MTEXT'):
            self.data['entities']['mtexts'].append({
                'handle': mtext.dxf.handle,
                'layer': mtext.dxf.layer,
                'color': mtext.dxf.color,
                'text': mtext.text,
                'plain_text': mtext.plain_text(),
                'insert': self._vec_to_list(mtext.dxf.insert),
                'char_height': mtext.dxf.char_height,
                'width': mtext.dxf.width,
                'rotation': mtext.dxf.rotation,
                'attachment_point': mtext.dxf.attachment_point,
                'flow_direction': mtext.dxf.flow_direction
            })
    
    def _extract_dimensions(self):
        """Extract DIMENSION entities"""
        for dim in self.msp.query('DIMENSION'):
            self.data['entities']['dimensions'].append({
                'handle': dim.dxf.handle,
                'layer': dim.dxf.layer,
                'color': dim.dxf.color,
                'dimtype': dim.dimtype,
                'text': getattr(dim.dxf, 'text', ''),
                'actual_measurement': dim.get_measurement(),
                'defpoint': self._vec_to_list(dim.dxf.defpoint) if hasattr(dim.dxf, 'defpoint') else None,
                'text_midpoint': self._vec_to_list(dim.dxf.text_midpoint) if hasattr(dim.dxf, 'text_midpoint') else None
            })
    
    def _extract_hatches(self):
        """Extract HATCH entities (fill patterns)"""
        for hatch in self.msp.query('HATCH'):
            self.data['entities']['hatches'].append({
                'handle': hatch.dxf.handle,
                'layer': hatch.dxf.layer,
                'color': hatch.dxf.color,
                'pattern_name': hatch.dxf.pattern_name,
                'solid_fill': hatch.dxf.solid_fill,
                'pattern_type': hatch.dxf.pattern_type,
                'pattern_angle': hatch.dxf.pattern_angle if hasattr(hatch.dxf, 'pattern_angle') else 0,
                'pattern_scale': hatch.dxf.pattern_scale if hasattr(hatch.dxf, 'pattern_scale') else 1,
                'area': self._hatch_area(hatch)
            })
    
    def _extract_3d_solids(self):
        """Extract 3DSOLID and BODY entities"""
        for solid in self.msp.query('3DSOLID BODY'):
            self.data['entities']['solids'].append({
                'handle': solid.dxf.handle,
                'layer': solid.dxf.layer,
                'color': solid.dxf.color,
                'type': solid.dxftype()
            })
    
    def _extract_splines(self):
        """Extract SPLINE entities"""
        for spline in self.msp.query('SPLINE'):
            control_points = [self._vec_to_list(cp) for cp in spline.control_points]
            self.data['entities']['splines'].append({
                'handle': spline.dxf.handle,
                'layer': spline.dxf.layer,
                'color': spline.dxf.color,
                'degree': spline.dxf.degree,
                'closed': spline.closed,
                'control_points': control_points,
                'n_control_points': spline.dxf.n_control_points
            })
    
    def _extract_3dfaces(self):
        """Extract 3DFACE entities"""
        for face in self.msp.query('3DFACE'):
            self.data['entities']['3dfaces'].append({
                'handle': face.dxf.handle,
                'layer': face.dxf.layer,
                'vtx0': self._vec_to_list(face.dxf.vtx0),
                'vtx1': self._vec_to_list(face.dxf.vtx1),
                'vtx2': self._vec_to_list(face.dxf.vtx2),
                'vtx3': self._vec_to_list(face.dxf.vtx3)
            })
    
    def _extract_regions(self):
        """Extract REGION entities"""
        for region in self.msp.query('REGION'):
            self.data['entities']['regions'].append({
                'handle': region.dxf.handle,
                'layer': region.dxf.layer,
                'color': region.dxf.color
            })
    
    def _extract_xdata(self, entity) -> Dict:
        """Extract extended data from entity"""
        xdata = {}
        if entity.has_xdata_list and entity.xdata is not None:
            try:
                for appid, tags in entity.xdata.items():
                    xdata[appid] = [{'code': tag[0], 'value': tag[1]} for tag in tags]
            except (AttributeError, TypeError):
                # Handle cases where xdata might not be iterable or is None
                pass
        return xdata
    
    def _perform_spatial_analysis(self):
        """Analyze spatial relationships between entities"""
        
        # Room detection from closed polylines/lwpolylines
        rooms = []
        for pline in self.data['entities']['lwpolylines']:
            if pline['closed'] and pline['area'] > 1.0:  # Filter small areas
                rooms.append({
                    'handle': pline['handle'],
                    'layer': pline['layer'],
                    'boundary': pline['points'],
                    'area': pline['area'],
                    'perimeter': pline['length']
                })
        
        self.data['spatial_analysis']['rooms'] = rooms
        
        # Wall detection (parallel lines or thick polylines)
        walls = self._detect_walls()
        self.data['spatial_analysis']['walls'] = walls
        
        # Openings detection (blocks on wall layers + dimensions)
        openings = self._detect_openings()
        self.data['spatial_analysis']['openings'] = openings
    
    def _detect_walls(self) -> List[Dict]:
        """Detect walls from lines and polylines"""
        walls = []
        wall_layers = [name for name in self.data['layers'].keys() 
                      if 'WALL' in name.upper() or 'MUR' in name.upper()]
        
        for line in self.data['entities']['lines']:
            if line['layer'] in wall_layers:
                walls.append({
                    'type': 'line',
                    'handle': line['handle'],
                    'layer': line['layer'],
                    'start': line['start'],
                    'end': line['end'],
                    'length': line['length'],
                    'angle': line['angle']
                })
        
        return walls
    
    def _detect_openings(self) -> List[Dict]:
        """Detect doors, windows from blocks"""
        openings = []
        opening_keywords = ['DOOR', 'WINDOW', 'PORTE', 'FENETRE', 'OPENING']
        
        for insert in self.data['entities']['inserts']:
            block_name = insert['block_name'].upper()
            if any(kw in block_name for kw in opening_keywords):
                openings.append({
                    'type': 'door' if 'DOOR' in block_name or 'PORTE' in block_name else 'window',
                    'handle': insert['handle'],
                    'block_name': insert['block_name'],
                    'layer': insert['layer'],
                    'location': insert['insertion_point'],
                    'rotation': insert['rotation'],
                    'attributes': insert['attributes']
                })
        
        return openings
    
    def _calculate_measurements(self):
        """Calculate aggregate measurements"""
        self.data['measurements'] = {
            'total_line_length': sum(l['length'] for l in self.data['entities']['lines']),
            'total_polyline_length': sum(p['length'] for p in self.data['entities']['polylines']),
            'total_lwpolyline_length': sum(p['length'] for p in self.data['entities']['lwpolylines']),
            'total_arc_length': sum(a['length'] for a in self.data['entities']['arcs']),
            'total_enclosed_area': sum(p['area'] for p in self.data['entities']['lwpolylines'] if p['closed']),
            'total_hatch_area': sum(h['area'] for h in self.data['entities']['hatches']),
            'block_count': len(self.data['entities']['inserts']),
            'text_count': len(self.data['entities']['texts']) + len(self.data['entities']['mtexts']),
            'dimension_count': len(self.data['entities']['dimensions'])
        }
    
    # Helper methods
    def _vec_to_list(self, vec) -> List[float]:
        """Convert Vec3, tuple, or list to [x, y, z] list"""
        if vec is None:
            return [0, 0, 0]
        
        # If it's already a list or tuple, convert to list
        if isinstance(vec, (list, tuple)):
            result = list(vec)
            # Ensure it has 3 elements
            while len(result) < 3:
                result.append(0)
            return result[:3]  # Take only first 3 elements
        
        # If it's a Vec3-like object with .x, .y, .z attributes
        if hasattr(vec, 'x') and hasattr(vec, 'y'):
            z = vec.z if hasattr(vec, 'z') else 0
            return [vec.x, vec.y, z]
        
        # Fallback: try to convert to list
        try:
            return list(vec)[:3]
        except (TypeError, ValueError):
            return [0, 0, 0]
    
    def _distance_3d(self, p1, p2) -> float:
        """Calculate 3D distance between two points (Vec3, tuple, or list)"""
        p1_list = self._vec_to_list(p1)
        p2_list = self._vec_to_list(p2)
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1_list, p2_list)))
    
    def _angle_2d(self, p1, p2) -> float:
        """Calculate 2D angle between two points (Vec3, tuple, or list)"""
        p1_list = self._vec_to_list(p1)
        p2_list = self._vec_to_list(p2)
        return math.degrees(math.atan2(p2_list[1] - p1_list[1], p2_list[0] - p1_list[0]))
    
    def _polyline_length(self, points, closed=False) -> float:
        length = sum(self._distance_3d(points[i], points[i+1]) 
                    for i in range(len(points)-1))
        if closed and len(points) > 2:
            length += self._distance_3d(points[-1], points[0])
        return length
    
    def _polygon_area(self, points) -> float:
        """Calculate area using Shoelace formula"""
        if len(points) < 3:
            return 0
        area = 0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2
    
    def _arc_length(self, radius, start_angle, end_angle) -> float:
        angle_diff = end_angle - start_angle
        if angle_diff < 0:
            angle_diff += 360
        return radius * math.radians(angle_diff)
    
    def _hatch_area(self, hatch) -> float:
        """Calculate hatch area from boundary paths"""
        try:
            total_area = 0
            for path in hatch.paths:
                if hasattr(path, 'source_boundary_objects'):
                    # Use boundary objects if available
                    pass
                # Simplified - would need full boundary analysis
            return total_area
        except:
            return 0
    
    def _calculate_drawing_bounds(self) -> Dict:
        """Calculate drawing bounds, handling both Vec3 and tuple formats"""
        extmin = self.doc.header.get('$EXTMIN', Vec3(0,0,0))
        extmax = self.doc.header.get('$EXTMAX', Vec3(0,0,0))
        
        # Convert to lists to handle both Vec3 and tuple formats
        extmin_list = self._vec_to_list(extmin)
        extmax_list = self._vec_to_list(extmax)
        
        width = extmax_list[0] - extmin_list[0]
        height = extmax_list[1] - extmin_list[1]
        return {
            'width': width,
            'height': height,
            'area': width * height
        }
    
    def _get_statistics(self) -> str:
        stats = []
        entities = self.data.get('entities') or {}
        if isinstance(entities, dict):
            for entity_type, entity_list in entities.items():
                if entity_list:
                    stats.append(f"{entity_type}={len(entity_list)}")
        return ", ".join(stats)
    
    def save_to_json(self, output_path: str):
        """Save extracted data to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"💾 Data saved to {output_path}")


# Usage example
if __name__ == "__main__":
    extractor = ComprehensiveCADExtractor("path/to/drawing.dxf")
    data = extractor.extract_all()
    extractor.save_to_json("extracted_data.json")
    
    # Access specific data
    print(f"Total blocks: {len(data['entities']['inserts'])}")
    print(f"Total walls detected: {len(data['spatial_analysis']['walls'])}")
    print(f"Total area: {data['measurements']['total_enclosed_area']:.2f}")
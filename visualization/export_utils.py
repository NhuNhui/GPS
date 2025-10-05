"""
export_utils.py
Module xuất dữ liệu sang các định dạng khác nhau

Chức năng:
- Xuất dữ liệu sang GeoJSON
- Tạo style cho các đối tượng trên bản đồ
- Chuyển đổi định dạng dữ liệu

"""

import json
from pathlib import Path
from datetime import datetime

class GeoJSONExporter:
    """
    Lớp xuất dữ liệu sang định dạng GeoJSON
    """
    
    def __init__(self):
        """Khởi tạo exporter"""
        self.features = []
        
    def add_point(self, lat, lon, alt=None, properties=None):
        """
        Thêm điểm vào collection
        
        Input:
            lat: Vĩ độ (độ)
            lon: Kinh độ (độ)
            alt: Độ cao (mét), có thể None
            properties: Dict các thuộc tính bổ sung
        """
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat] if alt is None else [lon, lat, alt]
            },
            "properties": properties or {}
        }
        self.features.append(feature)
        
    def add_line(self, coordinates, properties=None):
        """
        Thêm đường vào collection
        
        Input:
            coordinates: List các điểm [(lon, lat), ...]
            properties: Dict các thuộc tính bổ sung
        """
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": properties or {}
        }
        self.features.append(feature)
        
    def export_target_scenario(self, observer_pos, target_pos, output_path):
        """
        Xuất kịch bản quan sát-mục tiêu sang file GeoJSON
        
        Input:
            observer_pos: tuple (lat, lon, alt) vị trí quan sát
            target_pos: tuple (lat, lon, alt) vị trí mục tiêu
            output_path: Đường dẫn file xuất
        """
        # Reset features
        self.features = []
        
        # Thêm điểm quan sát
        self.add_point(
            observer_pos[0], observer_pos[1], observer_pos[2],
            properties={
                "name": "Observer",
                "type": "observer",
                "altitude": observer_pos[2],
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Thêm điểm mục tiêu
        self.add_point(
            target_pos[0], target_pos[1], target_pos[2],
            properties={
                "name": "Target",
                "type": "target",
                "altitude": target_pos[2],
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Thêm đường nối
        self.add_line(
            [[observer_pos[1], observer_pos[0]],
             [target_pos[1], target_pos[0]]],
            properties={
                "name": "Line of sight",
                "type": "sight_line"
            }
        )
        
        # Tạo GeoJSON Feature Collection
        geojson = {
            "type": "FeatureCollection",
            "features": self.features
        }
        
        # Tạo thư mục output nếu chưa có
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ghi file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2)
            
def test_geojson_export():
    """Test xuất GeoJSON với dữ liệu mẫu"""
    # Tạo thư mục output nếu chưa có
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Khởi tạo exporter
    exporter = GeoJSONExporter()
    
    # Dữ liệu test (khu vực TP.HCM)
    observer_pos = (10.762622, 106.660172, 10.0)  # Đại học Bách Khoa
    target_pos = (10.773456, 106.674512, 15.0)    # Công viên Tao Đàn
    
    # Xuất file
    exporter.export_target_scenario(
        observer_pos=observer_pos,
        target_pos=target_pos,
        output_path="output/test_scenario.geojson"
    )
    
if __name__ == "__main__":
    test_geojson_export()
"""
target_calculator.py
Thuật toán tính toán tọa độ mục tiêu từ:
- Tọa độ GPS người quan sát
- Góc ngắm (azimuth, elevation) 
- Khoảng cách laser rangefinder

Chức năng chính:
- Chuyển đổi góc thành vector định hướng 3D
- Tính toán vị trí mục tiêu trong không gian
- Chuyển đổi về tọa độ địa lý (lat, lon, alt)

"""

import math
import numpy as np
from .coordinate_transforms import CoordinateTransforms

class DirectionVectors:
    """
    Lớp xử lý chuyển đổi góc azimuth/elevation thành vector định hướng 3D
    """
    
    def __init__(self, coordinate_system='ENU'):
        if coordinate_system not in ['ENU', 'NED']:
            raise ValueError("coordinate_system must be 'ENU' or 'NED'")
        self.coordinate_system = coordinate_system
    
    def angles_to_vector_enu(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc azimuth/elevation thành vector định hướng trong hệ ENU

        Quy ước:
        - Azimuth: 0° = Bắc (Y+), 90° = Đông (X+), đo theo chiều kim đồng hồ
        - Elevation: 0° = ngang, +90° = thẳng đứng lên (Z+), -90° = thẳng đứng xuống (Z-)
        
        Input:
            azimuth_deg: Góc azimuth (độ)
            elevation_deg: Góc elevation (độ)
            
        Output:
            np.ndarray: [x, y, z] vector đơn vị
        """
        # Chuyển đổi sang radian
        az_rad = math.radians(azimuth_deg)
        el_rad = math.radians(elevation_deg)

        cos_el = math.cos(el_rad)
        
        # Công thức chuyển đổi cho hệ ENU
        x_enu = cos_el * math.sin(az_rad)   # East
        y_enu = cos_el * math.cos(az_rad)   # North  
        z_enu = math.sin(el_rad)            # Up
        
        return np.array([x_enu, y_enu, z_enu])
    
    def angles_to_vector_ned(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc azimuth/elevation thành vector định hướng trong hệ NED

        Quy ước:
        - Azimuth: 0° = Bắc (X+), 90° = Đông (Y+)
        - Elevation: 0° = ngang, +90° = lên, -90° = xuống
        - Z_ned = -sin(elevation) vì Down là hướng xuống
        """
        az_rad = math.radians(azimuth_deg)
        el_rad = math.radians(elevation_deg)

        cos_el = math.cos(el_rad)
        
        # Công thức chuyển đổi cho hệ NED
        x_ned = cos_el * math.cos(az_rad)   # North
        y_ned = cos_el * math.sin(az_rad)   # East
        z_ned = -math.sin(el_rad)           # Down (âm)
        
        return np.array([x_ned, y_ned, z_ned])
    
    def angles_to_vector(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc thành vector định hướng theo hệ đã chọn
        """
        if self.coordinate_system == 'ENU':
            return self.angles_to_vector_enu(azimuth_deg, elevation_deg)
        else:
            return self.angles_to_vector_ned(azimuth_deg, elevation_deg)
    
    def vector_to_angles(self, direction_vector):
        """
        Chuyển đổi vector định hướng thành góc azimuth/elevation
        
        Input:
            direction_vector: np.ndarray [x, y, z]
            
        Output:
            tuple: (azimuth_deg, elevation_deg)
        """
        if not isinstance(direction_vector, np.ndarray):
            direction_vector = np.array(direction_vector)

        x, y, z = direction_vector
        
        if self.coordinate_system == 'ENU':
            # ENU: x=East, y=North, z=Up
            azimuth_rad = math.atan2(x, y)  # atan2(East, North)
            horizontal_dist = math.sqrt(x**2 + y**2)
            elevation_rad = math.atan2(z, horizontal_dist)
        else:
            # NED: x=North, y=East, z=Down
            azimuth_rad = math.atan2(y, x)  # atan2(East, North)
            horizontal_dist = math.sqrt(x**2 + y**2)
            elevation_rad = math.atan2(-z, horizontal_dist)
        
        # Chuyển về độ và đảm bảo azimuth trong [0, 360)
        azimuth_deg = math.degrees(azimuth_rad)
        if azimuth_deg < 0:
            azimuth_deg += 360
            
        elevation_deg = math.degrees(elevation_rad)
        
        return (azimuth_deg, elevation_deg)
    
    def normalize_vector(self, vector):
        """Chuẩn hóa vector về độ dài 1"""
        if not isinstance(vector, np.ndarray):
            vector = np.array(vector)
        magnitude = np.linalg.norm(vector)
        if magnitude == 0:
            return vector
        return vector / magnitude
    
class TargetCalculator:
    """
    Tính toán tọa độ mục tiêu
    """
    
    def __init__(self, coordinate_system='ENU'):
        self.coord_transform = CoordinateTransforms()
        self.direction_vectors = DirectionVectors(coordinate_system)
        self.coordinate_system = coordinate_system
    
    def calculate_target_position(self, observer_geodetic, azimuth_deg, elevation_deg, distance_m):
        """
        Tính toán tọa độ mục tiêu từ dữ liệu đầu vào
        
        Input:
            observer_geodetic: tuple (lat_deg, lon_deg, alt_m) tọa độ người quan sát
            azimuth_deg: Góc azimuth (độ)
            elevation_deg: Góc elevation (độ)
            distance_m: Khoảng cách đo bằng laser (mét)
            
        Output:
            dict: Kết quả chi tiết
        """
        # Validate input
        if distance_m <= 0:
            raise ValueError("Distance phải > 0")
        
        # 1. Chuyển đổi góc thành vector định hướng (đơn vị)
        direction_vector = self.direction_vectors.angles_to_vector(azimuth_deg, elevation_deg)
        
        # 2. Tính vị trí mục tiêu trong hệ địa phương
        # Quan trọng: đây là tọa độ TƯƠNG ĐỐI so với observer
        target_local = distance_m * direction_vector
        
        # 3. Chuyển đổi từ hệ địa phương sang ECEF
        if self.coordinate_system == 'ENU':
            target_ecef = self.coord_transform.enu_to_ecef(target_local, observer_geodetic)
        else:
            target_ecef = self.coord_transform.ned_to_ecef(target_local, observer_geodetic)
        
        # 4. Chuyển đổi từ ECEF sang Geodetic
        target_geodetic = self.coord_transform.ecef_to_geodetic(*target_ecef)
        
        # === VERIFICATION (kiểm tra độ chính xác) ===
        observer_ecef = self.coord_transform.geodetic_to_ecef(*observer_geodetic)
        actual_distance = np.linalg.norm(target_ecef - observer_ecef)
        
        # Tính lại góc từ vị trí tính được
        if self.coordinate_system == 'ENU':
            verify_local = self.coord_transform.ecef_to_enu(target_ecef, observer_geodetic)
        else:
            verify_local = self.coord_transform.ecef_to_ned(target_ecef, observer_geodetic)
        
        verify_direction = self.direction_vectors.normalize_vector(verify_local)
        verify_azimuth, verify_elevation = self.direction_vectors.vector_to_angles(verify_direction)
        
        return {
            'target_geodetic': {
                'latitude': target_geodetic[0],
                'longitude': target_geodetic[1], 
                'altitude': target_geodetic[2]
            },
            'target_ecef': {
                'X': float(target_ecef[0]),
                'Y': float(target_ecef[1]),
                'Z': float(target_ecef[2])
            },
            'target_local': {
                'coordinates': target_local.tolist(),
                'coordinate_system': self.coordinate_system
            },
            'input_parameters': {
                'observer_lat': observer_geodetic[0],
                'observer_lon': observer_geodetic[1],
                'observer_alt': observer_geodetic[2],
                'azimuth': azimuth_deg,
                'elevation': elevation_deg,
                'distance': distance_m
            },
            'verification': {
                'actual_distance': actual_distance,
                'distance_error': abs(actual_distance - distance_m),
                'verify_azimuth': verify_azimuth,
                'verify_elevation': verify_elevation,
                'azimuth_error': abs(verify_azimuth - azimuth_deg),
                'elevation_error': abs(verify_elevation - elevation_deg)
            },
            'direction_vector': direction_vector.tolist()
        }
    
    def calculate_multiple_targets(self, observer_geodetic, measurements):
        """
        Tính toán nhiều mục tiêu cùng lúc
            
        Output:
            list: Danh sách kết quả cho từng mục tiêu
        """
        results = []
        for i, m in enumerate(measurements):
            try:
                result = self.calculate_target_position(
                    observer_geodetic,
                    m['azimuth'],
                    m['elevation'], 
                    m['distance']
                )
                result['target_id'] = i + 1
                results.append(result)
            except Exception as e:
                print(f"Error target {i+1}: {e}")
                results.append(None)
        
        return results
    
    def calculate_bearing_distance(self, observer_geodetic, target_geodetic):
        """
        Bài toán ngược: Tính góc và khoảng cách từ 2 điểm geodetic
            
        Output:
            dict: azimuth, elevation, distance
        """
        observer_ecef = self.coord_transform.geodetic_to_ecef(*observer_geodetic)
        target_ecef = self.coord_transform.geodetic_to_ecef(*target_geodetic)
        
        # Chuyển target về hệ địa phương
        if self.coordinate_system == 'ENU':
            target_local = self.coord_transform.ecef_to_enu(target_ecef, observer_geodetic)
        else:
            target_local = self.coord_transform.ecef_to_ned(target_ecef, observer_geodetic)
        
        # Tính khoảng cách
        distance = np.linalg.norm(target_local)
        
        # Tính direction vector và chuyển về góc
        if distance > 0:
            direction_vector = target_local / distance
            azimuth, elevation = self.direction_vectors.vector_to_angles(direction_vector)
        else:
            azimuth, elevation = 0, 90
            direction_vector = np.array([0, 0, 1])
        
        return {
            'azimuth': azimuth,
            'elevation': elevation,
            'distance': distance,
            'target_local': target_local.to_list(),
            'direction_vector': direction_vector.to_list()
        }
    
"""
gps_target_system.py
Module chính của hệ thống, kết hợp các thành phần để tính toán tọa độ mục tiêu

Chức năng:
- Khởi tạo và quản lý các thành phần của hệ thống
- Tính toán tọa độ mục tiêu từ dữ liệu đầu vào
- Xử lý và kiểm tra tính hợp lệ của dữ liệu
"""

from .coordinate_transforms import CoordinateTransforms
from .target_calculator import DirectionVectors
from .sensor_fusion import SensorFusion

class GPSTargetSystem:
    """
    Lớp chính của hệ thống, tích hợp các module để tính toán tọa độ mục tiêu
    """
    
    def __init__(self, coordinate_system='ENU'):
        """
        Khởi tạo hệ thống với các thành phần cần thiết
        
        Input:
            coordinate_system: Hệ tọa độ sử dụng ('ENU' hoặc 'NED')
        """
        self.coordinate_transforms = CoordinateTransforms()
        self.direction_vectors = DirectionVectors(coordinate_system)
        self.sensor_fusion = SensorFusion()
        
    def calculate_target_position(self, observer_lat, observer_lon, observer_alt,
                                azimuth, elevation, distance):
        """
        Tính toán tọa độ mục tiêu từ vị trí quan sát và dữ liệu đo
        
        Input:
            observer_lat: Vĩ độ người quan sát (độ)
            observer_lon: Kinh độ người quan sát (độ)
            observer_alt: Độ cao người quan sát (mét)
            azimuth: Góc phương vị (độ)
            elevation: Góc ngẩng (độ)
            distance: Khoảng cách đến mục tiêu (mét)
            
        Output:
            tuple: (target_lat, target_lon, target_alt) - Tọa độ mục tiêu
        """
        # 1. Chuyển tọa độ quan sát viên sang ECEF
        observer_ecef = self.coordinate_transforms.geodetic_to_ecef(
            observer_lat, observer_lon, observer_alt
        )
        
        # 2. Tính vector định hướng từ góc ngắm
        direction_vector = self.direction_vectors.angles_to_vector(azimuth, elevation)
        
        # 3. Tính vector dịch chuyển trong hệ cục bộ (ENU/NED)
        displacement_local = tuple(d * distance for d in direction_vector)
        
        # 4. Chuyển vector dịch chuyển sang ECEF
        observer_geodetic = (observer_lat, observer_lon, observer_alt)
        if self.direction_vectors.coordinate_system == 'ENU':
            displacement_ecef = self.coordinate_transforms.enu_to_ecef(
                displacement_local,
                observer_geodetic
            )
        else:  # NED
            displacement_ecef = self.coordinate_transforms.ned_to_ecef(
                displacement_local,
                observer_geodetic
            )
            
        # 5. Tính tọa độ mục tiêu trong ECEF
        target_ecef = tuple(o + d for o, d in zip(observer_ecef, displacement_ecef))
        
        # 6. Chuyển về tọa độ địa lý
        target_position = self.coordinate_transforms.ecef_to_geodetic(*target_ecef)
        
        return target_position
    
    def validate_input_data(self, lat, lon, alt, azimuth, elevation, distance):
        """
        Kiểm tra tính hợp lệ của dữ liệu đầu vào
        
        Raises:
            ValueError nếu dữ liệu không hợp lệ
        """
        # Kiểm tra vĩ độ
        if not -90 <= lat <= 90:
            raise ValueError(f"Vĩ độ {lat} nằm ngoài khoảng hợp lệ [-90, 90]")
            
        # Kiểm tra kinh độ
        if not -180 <= lon <= 180:
            raise ValueError(f"Kinh độ {lon} nằm ngoài khoảng hợp lệ [-180, 180]")
            
        # Kiểm tra độ cao
        if alt < -1000:  # Giả sử độ cao tối thiểu là -1000m (Biển Chết ~ -430m)
            raise ValueError(f"Độ cao {alt}m quá thấp")
            
        # Kiểm tra góc phương vị
        if not 0 <= azimuth < 360:
            raise ValueError(f"Góc phương vị {azimuth} phải nằm trong khoảng [0, 360)")
            
        # Kiểm tra góc ngẩng
        if not -90 <= elevation <= 90:
            raise ValueError(f"Góc ngẩng {elevation} phải nằm trong khoảng [-90, 90]")
            
        # Kiểm tra khoảng cách
        if distance <= 0:
            raise ValueError(f"Khoảng cách {distance} phải lớn hơn 0")
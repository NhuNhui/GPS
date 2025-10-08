"""
gps_target_system.py
Module chính của hệ thống - wrapper đơn giản cho TargetCalculator

Chức năng:
- Khởi tạo và quản lý các thành phần của hệ thống
- Tính toán tọa độ mục tiêu từ dữ liệu đầu vào
- Xử lý và kiểm tra tính hợp lệ của dữ liệu
"""

from .coordinate_transforms import CoordinateTransforms
from .target_calculator import TargetCalculator
from .sensor_fusion import SensorFusion

class GPSTargetSystem:
    """
    Lớp wrapper chính của hệ thống -> Giảm độ phức tạp, tránh trùng lặp logic
    """
    
    def __init__(self, coordinate_system='ENU'):
        """
        Khởi tạo hệ thống
        
        Input:
            coordinate_system: Hệ tọa độ sử dụng ('ENU' hoặc 'NED')
        """
        self.calculator = TargetCalculator(coordinate_system)
        self.sensor_fusion = SensorFusion()
        self.coordinate_system = coordinate_system
        
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
            dict: Kết quả tính toán chi tiết
        """
        # Validate input
        self.validate_input_data(observer_lat, observer_lon, observer_alt, azimuth, elevation, distance)

        # Gọi trực tiếp TargetCalculator
        observer_geodetic = (observer_lat, observer_lon, observer_alt)
        result = self.calculator.calculate_target_position(observer_geodetic, azimuth, elevation, distance)
        
        return result
    
    def calculate_target_with_fusion(self, gps_data, imu_data, range_data):
        """
        Tính tọa độ mục tiêu với sensor fusion

        Input:
            gps_data: dict {'latitude', 'longitude', 'altitude', ...}
            imu_data: dict {'azimuth', 'elevation'}
            range_data: dict {'distance'}

        Output:
            dict: Kết quả với thông tin fusion
        """
        # Process qua sensor fusion
        if 'nmea_sentence' in gps_data:
            processed_gps = self.sensor_fusion.process_gps_data(gps_data['nmea_sentence'])
        else:
            processed_gps = gps_data

        if not processed_gps:
            raise ValueError("GPS data không hợp lệ")
        
        # Process IMU và Range
        filtered_angles = self.sensor_fusion.process_imu_data(
            imu_data['azimuth'],
            imu_data['elevation']
        )
        
        filtered_distance = self.sensor_fusion.process_range_data(
            range_data['distance']
        )
        
        if filtered_distance is None:
            raise ValueError("Range data không hợp lệ")
        
        # Tính toán với dữ liệu đã lọc
        result = self.calculate_target_position(
            processed_gps['latitude'],
            processed_gps['longitude'],
            processed_gps['altitude'],
            filtered_angles[0],
            filtered_angles[1],
            filtered_distance
        )
        
        # Thêm thông tin fusion
        result['sensor_fusion'] = {
            'data_quality': self.sensor_fusion._assess_data_quality(),
            'gps_filtered': processed_gps.get('filtered', False),
            'original_azimuth': imu_data['azimuth'],
            'original_elevation': imu_data['elevation'],
            'original_distance': range_data['distance']
        }
        
        return result
    
    def validate_input_data(self, lat, lon, alt, azimuth, elevation, distance):
        """
        Kiểm tra tính hợp lệ của dữ liệu đầu vào
        
        Raises:
            ValueError nếu dữ liệu không hợp lệ
        """
        if not -90 <= lat <= 90:
            raise ValueError(f"Vĩ độ {lat} nằm ngoài [-90, 90]")
            
        if not -180 <= lon <= 180:
            raise ValueError(f"Kinh độ {lon} nằm ngoài [-180, 180]")
            
        if alt < -1000:
            raise ValueError(f"Độ cao {alt}m quá thấp")
            
        if not 0 <= azimuth < 360:
            raise ValueError(f"Azimuth {azimuth} phải trong [0, 360)")
            
        if not -90 <= elevation <= 90:
            raise ValueError(f"Elevation {elevation} phải trong [-90, 90]")
            
        if distance <= 0:
            raise ValueError(f"Distance {distance} phải > 0")
    
    def calculate_inverse(self, observer_lat, observer_lon, observer_alt,
                         target_lat, target_lon, target_alt):
        """
        Bài toán ngược: Tính góc và khoảng cách từ 2 điểm
        
        Output:
            dict: {azimuth, elevation, distance, ...}
        """
        observer_geodetic = (observer_lat, observer_lon, observer_alt)
        target_geodetic = (target_lat, target_lon, target_alt)
        
        return self.calculator.calculate_bearing_distance(
            observer_geodetic, 
            target_geodetic
        )

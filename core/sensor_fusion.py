"""
sensor_fusion.py
Mô-đun xử lý và hợp nhất dữ liệu từ các cảm biến:
- GPS (NMEA data parsing)
- IMU/Compass (azimuth, elevation angles)
- Laser Rangefinder (distance measurement)

Chức năng: Lọc nhiễu, hợp nhất dữ liệu (sensor fusion), xử lý NMEA

"""

import numpy as np
import math
import statistics
from datetime import datetime
from collections import deque

class NMEAParser:
    """
    Xử lý dữ liệu GPS định dạng NMEA-0183
    Hỗ trợ các loại message: GGA, RMC
    """

    def __init__(self):
        self.last_fix = None

    def parse_gga(self, nmea_sentence):
        """
        Phân tích NMEA GGA sentence (GPS Fix Data)
        Format: $GPGGA,time,lat,lat_dir,lon,lon_dir,quality,num_sat,hdop,alt,alt_unit,geoid_height,geoid_unit,dgps_age,dgps_id*checksum
        
        Input:
            nmea_sentence: Chuỗi NMEA GGA
            
        Output:
            dict: Dữ liệu GPS đã phân tích hoặc None nếu lỗi
        """
        try:
            # Kiểm tra checksum
            if not self._verify_checksum(nmea_sentence):
                return None
            
            parts = nmea_sentence.strip().split(',')

            if len(parts) < 15 or not parts[1]: # Không có thời gian
                return None
            
            # Phân tích vĩ độ
            if parts[2] and parts[3]:
                lat_raw = float(parts[2])
                lat_deg = int(lat_raw / 100)
                lat_min = lat_raw - (lat_deg * 100)
                latitude = lat_deg + (lat_min / 60.0)
                if parts[3] == 'S':
                    latitude = -latitude
            else:
                return None
            
            # Phân tích kinh độ
            if parts[4] and parts[5]:
                lon_raw = float(parts[4])
                lon_deg = int(lon_raw / 100)
                lon_min = lon_raw - (lon_deg * 100)
                longitude = lon_deg + (lon_min / 60.0)
                if parts[5] == 'W':
                    longitude = -longitude
            else:
                return None
            
            gps_data = {
                'timestamp': parts[1],
                'latitude': latitude,
                'longitude': longitude,
                'fix_quality': int(parts[6]) if parts[6] else 0,
                'num_satellites': int(parts[7]) if parts[7] else 0,
                'hdop': float(parts[8]) if parts[8] else 99.9,
                'altitude': float(parts[9]) if parts[9] else 0.0,
                'altitude_unit': parts[10] if parts[10] else 'M',
                'geoid_height': float(parts[11]) if parts[11] else 0.0
            }
            
            self.last_fix = gps_data
            return gps_data
        
        except (ValueError, IndexError) as e:
            print(f"Lỗi phân tích GGA: {e}")
            return None
        
    def parse_rmc(self, nmea_sentence):
        """
        Phân tích NMEA RMC sentence (Recommended Minimum Course)
        Cung cấp thêm thông tin về vận tốc và hướng di chuyển
        
        Input:
            nmea_sentence: Chuỗi NMEA RMC
            
        Output:
            dict: Dữ liệu GPS với velocity và course
        """
        try:
            if not self._verify_checksum(nmea_sentence):
                return None
                
            parts = nmea_sentence.strip().split(',')
            
            if len(parts) < 12 or parts[2] != 'A':  # Status phải là 'A' (Active)
                return None
            
            # Tương tự GGA cho lat/lon
            lat_raw = float(parts[3])
            lat_deg = int(lat_raw / 100)
            lat_min = lat_raw - (lat_deg * 100)
            latitude = lat_deg + (lat_min / 60.0)
            if parts[4] == 'S':
                latitude = -latitude
                
            lon_raw = float(parts[5])
            lon_deg = int(lon_raw / 100)
            lon_min = lon_raw - (lon_deg * 100)
            longitude = lon_deg + (lon_min / 60.0)
            if parts[6] == 'W':
                longitude = -longitude
            
            return {
                'timestamp': parts[1],
                'status': parts[2],
                'latitude': latitude,
                'longitude': longitude,
                'speed_knots': float(parts[7]) if parts[7] else 0.0,
                'course_deg': float(parts[8]) if parts[8] else 0.0,
                'date': parts[9]
            }
            
        except (ValueError, IndexError) as e:
            print(f"Lỗi phân tích RMC: {e}")
            return None
        
    def _verify_checksum(self, nmea_sentence):
        """
        Kiểm tra checksum của chuỗi NMEA
        
        Input:
            nmea_sentence: Chuỗi NMEA
            
        Output:
            bool: True nếu checksum đúng
        """
        if '*' not in nmea_sentence:
            return False
            
        try:
            sentence, checksum = nmea_sentence.split('*')
            sentence = sentence[1:]  # Bỏ ký tự '
            
            # Tính checksum bằng XOR
            calc_checksum = 0
            for char in sentence:
                calc_checksum ^= ord(char)
            
            return format(calc_checksum, '02X') == checksum.upper()
            
        except ValueError:
            return False
        
class SensorFilter:
    """
    Lớp lọc nhiễu và làm mịn dữ liệu cảm biến
    Sử dụng Moving Average và Kalman Filter đơn giản
    """
    
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.gps_buffer = deque(maxlen=window_size)
        self.imu_buffer = deque(maxlen=window_size)
        self.range_buffer = deque(maxlen=window_size)
    
    def filter_gps_position(self, gps_data):
        """
        Lọc vị trí GPS bằng moving average
        
        Args:
            gps_data: dict chứa latitude, longitude, altitude
            
        Returns:
            dict: GPS data đã lọc
        """
        if not gps_data or gps_data.get('fix_quality', 0) == 0:
            return None
        
        self.gps_buffer.append(gps_data)
        
        if len(self.gps_buffer) < 2:
            return gps_data
        
        # Lọc bằng trung bình có trọng số (dữ liệu mới có trọng số cao hơn)
        weights = np.array([i+1 for i in range(len(self.gps_buffer))])
        weights = weights / np.sum(weights)
        
        filtered_lat = np.average([d['latitude'] for d in self.gps_buffer], weights=weights)
        filtered_lon = np.average([d['longitude'] for d in self.gps_buffer], weights=weights)
        filtered_alt = np.average([d['altitude'] for d in self.gps_buffer], weights=weights)
        
        filtered_data = gps_data.copy()
        filtered_data.update({
            'latitude': filtered_lat,
            'longitude': filtered_lon,
            'altitude': filtered_alt,
            'filtered': True
        })
        
        return filtered_data
    
    def filter_imu_angles(self, azimuth, elevation):
        """
        Lọc góc từ IMU/compass bằng circular mean cho azimuth
        
        Args:
            azimuth: Góc azimuth (độ)
            elevation: Góc elevation (độ)
            
        Returns:
            tuple: (filtered_azimuth, filtered_elevation)
        """
        imu_data = {'azimuth': azimuth, 'elevation': elevation}
        self.imu_buffer.append(imu_data)
        
        if len(self.imu_buffer) < 2:
            return (azimuth, elevation)
        
        # Lọc azimuth bằng circular mean (do tính chất tuần hoàn 0-360°)
        azimuths = [d['azimuth'] for d in self.imu_buffer]
        azimuth_rad = [math.radians(a) for a in azimuths]
        
        sin_sum = sum(math.sin(a) for a in azimuth_rad)
        cos_sum = sum(math.cos(a) for a in azimuth_rad)
        filtered_azimuth = math.degrees(math.atan2(sin_sum, cos_sum))
        
        if filtered_azimuth < 0:
            filtered_azimuth += 360
        
        # Lọc elevation bằng trung bình thông thường
        elevations = [d['elevation'] for d in self.imu_buffer]
        filtered_elevation = statistics.mean(elevations)
        
        return (filtered_azimuth, filtered_elevation)
    
    def filter_range_distance(self, distance):
        """
        Lọc khoảng cách từ laser rangefinder
        
        Args:
            distance: Khoảng cách đo được (mét)
            
        Returns:
            float: Khoảng cách đã lọc
        """
        if distance <= 0 or distance > 10000:  # Giới hạn hợp lý
            return None
        
        self.range_buffer.append(distance)
        
        if len(self.range_buffer) < 2:
            return distance
        
        # Loại bỏ outliers bằng median filter
        distances = list(self.range_buffer)
        distances.sort()
        
        # Lấy median
        n = len(distances)
        if n % 2 == 0:
            median = (distances[n//2 - 1] + distances[n//2]) / 2
        else:
            median = distances[n//2]
        
        # Lọc các giá trị quá xa median (outlier detection)
        threshold = median * 0.1  # 10% threshold
        filtered_distances = [d for d in distances if abs(d - median) <= threshold]
        
        if not filtered_distances:
            return distance
        
        return statistics.mean(filtered_distances)
    
class SensorFusion:
    """
    Lớp hợp nhất dữ liệu từ nhiều cảm biến
    Kết hợp GPS + IMU + Laser Rangefinder
    """
    
    def __init__(self):
        self.nmea_parser = NMEAParser()
        self.sensor_filter = SensorFilter()
        self.last_valid_position = None
        self.last_valid_angles = None
        self.last_valid_range = None
    
    def process_gps_data(self, nmea_sentence):
        """
        Xử lý dữ liệu GPS từ NMEA sentence
        
        Args:
            nmea_sentence: Chuỗi NMEA
            
        Returns:
            dict: GPS data đã xử lý hoặc None
        """
        gps_data = None
        
        if nmea_sentence.startswith('$GPGGA') or nmea_sentence.startswith('$GNGGA'):
            gps_data = self.nmea_parser.parse_gga(nmea_sentence)
        elif nmea_sentence.startswith('$GPRMC') or nmea_sentence.startswith('$GNRMC'):
            gps_data = self.nmea_parser.parse_rmc(nmea_sentence)
        
        if gps_data:
            # Áp dụng filter
            filtered_data = self.sensor_filter.filter_gps_position(gps_data)
            if filtered_data:
                self.last_valid_position = filtered_data
            return filtered_data
        
        return None
    
    def process_imu_data(self, azimuth_raw, elevation_raw):
        """
        Xử lý dữ liệu IMU/Compass
        
        Args:
            azimuth_raw: Góc azimuth thô (độ)
            elevation_raw: Góc elevation thô (độ)
            
        Returns:
            tuple: (azimuth, elevation) đã lọc
        """
        # Validate input ranges
        if not (0 <= azimuth_raw <= 360):
            print(f"Warning: Azimuth {azimuth_raw}° ngoài phạm vi [0, 360]")
            azimuth_raw = azimuth_raw % 360
        
        if not (-90 <= elevation_raw <= 90):
            print(f"Warning: Elevation {elevation_raw}° ngoài phạm vi [-90, 90]")
            elevation_raw = max(-90, min(90, elevation_raw))
        
        # Áp dụng filter
        filtered_angles = self.sensor_filter.filter_imu_angles(azimuth_raw, elevation_raw)
        self.last_valid_angles = filtered_angles
        
        return filtered_angles
    
    def process_range_data(self, distance_raw):
        """
        Xử lý dữ liệu laser rangefinder
        
        Args:
            distance_raw: Khoảng cách thô (mét)
            
        Returns:
            float: Khoảng cách đã lọc hoặc None
        """
        filtered_distance = self.sensor_filter.filter_range_distance(distance_raw)
        if filtered_distance:
            self.last_valid_range = filtered_distance
        
        return filtered_distance
    
    def get_fused_sensor_data(self):
        """
        Lấy dữ liệu cảm biến đã hợp nhất gần nhất
        
        Returns:
            dict: Dữ liệu hợp nhất hoặc None nếu thiếu dữ liệu
        """
        if not all([self.last_valid_position, self.last_valid_angles, self.last_valid_range]):
            missing = []
            if not self.last_valid_position: missing.append("GPS")
            if not self.last_valid_angles: missing.append("IMU")
            if not self.last_valid_range: missing.append("Range")
            
            print(f"Warning: Thiếu dữ liệu từ: {', '.join(missing)}")
            return None
        
        return {
            'gps': {
                'latitude': self.last_valid_position['latitude'],
                'longitude': self.last_valid_position['longitude'],
                'altitude': self.last_valid_position['altitude'],
                'fix_quality': self.last_valid_position.get('fix_quality', 0),
                'num_satellites': self.last_valid_position.get('num_satellites', 0),
                'hdop': self.last_valid_position.get('hdop', 99.9)
            },
            'imu': {
                'azimuth': self.last_valid_angles[0],
                'elevation': self.last_valid_angles[1]
            },
            'range': {
                'distance': self.last_valid_range
            },
            'timestamp': datetime.now().isoformat(),
            'data_quality': self._assess_data_quality()
        }
    
    def _assess_data_quality(self):
        """
        Đánh giá chất lượng dữ liệu cảm biến
        
        Returns:
            str: 'good', 'fair', 'poor'
        """
        if not self.last_valid_position:
            return 'poor'
        
        hdop = self.last_valid_position.get('hdop', 99.9)
        num_sats = self.last_valid_position.get('num_satellites', 0)
        fix_quality = self.last_valid_position.get('fix_quality', 0)
        
        if hdop <= 2.0 and num_sats >= 6 and fix_quality >= 1:
            return 'good'
        elif hdop <= 5.0 and num_sats >= 4 and fix_quality >= 1:
            return 'fair'
        else:
            return 'poor'

def test_sensor_fusion():
    """Hàm test xử lý dữ liệu cảm biến"""
    fusion = SensorFusion()
    
    print("=== TEST XỬ LÝ DỮ LIỆU CẢM BIẾN ===")
    
    # Test NMEA parsing
    test_gga = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    gps_data = fusion.process_gps_data(test_gga)
    
    if gps_data:
        print(f"GPS data: {gps_data['latitude']:.6f}°, {gps_data['longitude']:.6f}°, {gps_data['altitude']}m")
        print(f"Fix quality: {gps_data['fix_quality']}, Satellites: {gps_data['num_satellites']}, HDOP: {gps_data['hdop']}")
    
    # Test IMU data
    for i in range(5):
        # Simulate noisy IMU data
        azimuth = 45.0 + np.random.normal(0, 2)  # 45° ± 2° noise
        elevation = 10.0 + np.random.normal(0, 1)  # 10° ± 1° noise
        
        filtered_angles = fusion.process_imu_data(azimuth, elevation)
        print(f"IMU {i+1}: Raw({azimuth:.2f}°, {elevation:.2f}°) -> Filtered({filtered_angles[0]:.2f}°, {filtered_angles[1]:.2f}°)")
    
    # Test Range data
    for i in range(5):
        # Simulate laser rangefinder data
        distance = 1000.0 + np.random.normal(0, 5)  # 1000m ± 5m noise
        
        filtered_distance = fusion.process_range_data(distance)
        print(f"Range {i+1}: Raw({distance:.2f}m) -> Filtered({filtered_distance:.2f}m)")
    
    # Test fused data
    fused_data = fusion.get_fused_sensor_data()
    if fused_data:
        print("\n=== FUSED SENSOR DATA ===")
        print(f"GPS: {fused_data['gps']['latitude']:.6f}°, {fused_data['gps']['longitude']:.6f}°")
        print(f"IMU: Az={fused_data['imu']['azimuth']:.2f}°, El={fused_data['imu']['elevation']:.2f}°")
        print(f"Range: {fused_data['range']['distance']:.2f}m")
        print(f"Data quality: {fused_data['data_quality']}")

if __name__ == "__main__":
    test_sensor_fusion()
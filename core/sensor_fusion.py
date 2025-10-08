"""
sensor_fusion.py
Xử lý và hợp nhất dữ liệu từ các cảm biến:
- GPS (NMEA data parsing)
- IMU/Compass (azimuth, elevation angles)
- Laser Rangefinder (distance measurement)

Chức năng: Lọc nhiễu, hợp nhất dữ liệu (sensor fusion), xử lý NMEA

"""

import numpy as np
import math

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

            if len(parts) < 15 or not parts[1]:
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
        """
        if '*' not in nmea_sentence:
            return False
            
        try:
            sentence, checksum = nmea_sentence.split('*')
            sentence = sentence[1:]  # Bỏ '$'
            
            calc_checksum = 0
            for char in sentence:
                calc_checksum ^= ord(char)
            
            return format(calc_checksum, '02X') == checksum.upper()
            
        except ValueError:
            return False
        
class SensorFilter:
    """
    Bộ lọc cảm biến
    Sử dụng numpy vectorization
    """
    
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.gps_buffer = deque(maxlen=window_size)
        self.imu_buffer = deque(maxlen=window_size)
        self.range_buffer = deque(maxlen=window_size)

        # Pre-compute weights cho weighted average (OPTIMIZATION)
        self.weights = self._compute_weights(window_size)
    
    def _compute_weights(self, n):
        """Pre-compute weights để tái sử dụng"""
        w = np.arange(1, n + 1, dtype=np.float32)
        return w / w.sum()
    
    def filter_gps_position(self, gps_data):
        """
        Lọc vị trí GPS bằng moving average
        """
        if not gps_data or gps_data.get('fix_quality', 0) == 0:
            return None
        
        self.gps_buffer.append(gps_data)
        
        if len(self.gps_buffer) < 2:
            return gps_data
        
        # Lấy weights phù hợp với số lượng data hiện tại
        n = len(self.gps_buffer)
        weights = self.weights[:n] / self.weights[:n].sum()
        
        # Vectorized calculation
        lats = np.array([d['latitude'] for d in self.gps_buffer])
        lons = np.array([d['longitude'] for d in self.gps_buffer])
        alts = np.array([d['altitude'] for d in self.gps_buffer])
        
        filtered_data = gps_data.copy()
        filtered_data.update({
            'latitude': float(np.dot(lats, weights)),
            'longitude': float(np.dot(lons, weights)),
            'altitude': float(np.dot(alts, weights)),
            'filtered': True
        })
        
        return filtered_data
    
    def filter_imu_angles(self, azimuth, elevation):
        """
        Lọc góc từ IMU/Compass
        """
        imu_data = {'azimuth': azimuth, 'elevation': elevation}
        self.imu_buffer.append(imu_data)
        
        if len(self.imu_buffer) < 2:
            return (azimuth, elevation)
        
        # Lọc azimuth bằng circular mean
        azimuths = np.array([d['azimuth'] for d in self.imu_buffer])
        azimuth_rad = np.radians(azimuths)
        
        # Vectorized sin/cos
        sin_sum = np.sin(azimuth_rad).sum()
        cos_sum = np.cos(azimuth_rad).sum()
        filtered_azimuth = math.degrees(math.atan2(sin_sum, cos_sum))
        
        if filtered_azimuth < 0:
            filtered_azimuth += 360
        
        # Simple mean cho elevation
        elevations = np.array([d['elevation'] for d in self.imu_buffer])
        filtered_elevation = float(elevations.mean())
        
        return (filtered_azimuth, filtered_elevation)
    
    def filter_range_distance(self, distance):
        """
        Lọc khoảng cách từ laser rangefinder với median filter
        """
        if distance <= 0 or distance > 10000:
            return None
        
        self.range_buffer.append(distance)
        
        if len(self.range_buffer) < 2:
            return distance
        
        # Numpy median
        distances = np.array(list(self.range_buffer))
        median = float(np.median(distances))
        
        # Outlier detection
        threshold = median * 0.1
        mask = np.abs(distances - median) <= threshold
        
        if not mask.any():
            return distance
        
        return float(distances[mask].mean())
    
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
        """Xử lý dữ liệu GPS từ NMEA"""
        gps_data = None
        
        if nmea_sentence.startswith(('$GPGGA', '$GNGGA')):
            gps_data = self.nmea_parser.parse_gga(nmea_sentence)
        elif nmea_sentence.startswith(('$GPRMC', '$GNRMC')):
            gps_data = self.nmea_parser.parse_rmc(nmea_sentence)
        
        if gps_data:
            # Áp dụng filter
            filtered_data = self.sensor_filter.filter_gps_position(gps_data)
            if filtered_data:
                self.last_valid_position = filtered_data
            return filtered_data
        
        return None
    
    def process_imu_data(self, azimuth_raw, elevation_raw):
        """Xử lý dữ liệu IMU/Compass"""
        # Validate input
        if not (0 <= azimuth_raw <= 360):
            azimuth_raw = azimuth_raw % 360
        
        elevation_raw = np.clip(elevation_raw, -90, 90)
        
        # Áp dụng filter
        filtered_angles = self.sensor_filter.filter_imu_angles(azimuth_raw, elevation_raw)
        self.last_valid_angles = filtered_angles
        
        return filtered_angles
    
    def process_range_data(self, distance_raw):
        """Xử lý dữ liệu laser rangefinder"""
        filtered_distance = self.sensor_filter.filter_range_distance(distance_raw)
        if filtered_distance:
            self.last_valid_range = filtered_distance
        
        return filtered_distance
    
    def get_fused_sensor_data(self):
        """Lấy dữ liệu cảm biến đã hợp nhất gần nhất"""
        if not all([self.last_valid_position, self.last_valid_angles, self.last_valid_range]):
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
            'data_quality': self._assess_data_quality()
        }
    
    def _assess_data_quality(self):
        """Đánh giá chất lượng dữ liệu cảm biến"""
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

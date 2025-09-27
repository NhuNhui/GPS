"""
target_calculator.py
Thuật toán chính tính toán tọa độ mục tiêu từ:
- Tọa độ GPS người quan sát
- Góc ngắm (azimuth, elevation) 
- Khoảng cách laser rangefinder

Chức năng chính:
- Chuyển đổi góc thành vector định hướng 3D
- Tính toán vị trí mục tiêu trong không gian
- Chuyển đổi về tọa độ địa lý (lat, lon, alt)

"""

import math
from coordinate_transforms import CoordinateTransforms

class DirectionVectors:
    """
    Lớp xử lý chuyển đổi góc azimuth/elevation thành vector định hướng 3D
    """
    
    def __init__(self, coordinate_system='ENU'):
        """
        Initialize với hệ tọa độ địa phương
        
        Input:
            coordinate_system: 'ENU' hoặc 'NED'
        """
        if coordinate_system not in ['ENU', 'NED']:
            raise ValueError("coordinate_system must be 'ENU' or 'NED'")
        self.coordinate_system = coordinate_system
    
    def angles_to_vector_enu(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc azimuth/elevation thành vector định hướng trong hệ ENU
        
        Input:
            azimuth_deg: Góc azimuth (độ), 0° = Bắc, 90° = Đông
            elevation_deg: Góc elevation (độ), 0° = ngang, +90° = thẳng đứng lên
            
        Output:
            tuple: (x, y, z) vector định hướng đơn vị trong ENU
        """
        # Chuyển đổi sang radian
        azimuth_rad = math.radians(azimuth_deg)
        elevation_rad = math.radians(elevation_deg)
        
        # Công thức chuyển đổi cho hệ ENU
        x_enu = math.cos(elevation_rad) * math.sin(azimuth_rad)   # East
        y_enu = math.cos(elevation_rad) * math.cos(azimuth_rad)   # North  
        z_enu = math.sin(elevation_rad)                           # Up
        
        return (x_enu, y_enu, z_enu)
    
    def angles_to_vector_ned(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc azimuth/elevation thành vector định hướng trong hệ NED
        
        Input:
            azimuth_deg: Góc azimuth (độ), 0° = Bắc, 90° = Đông
            elevation_deg: Góc elevation (độ), 0° = ngang, +90° = thẳng đứng lên
            
        Output:
            tuple: (x, y, z) vector định hướng đơn vị trong NED
        """
        azimuth_rad = math.radians(azimuth_deg)
        elevation_rad = math.radians(elevation_deg)
        
        # Công thức chuyển đổi cho hệ NED
        x_ned = math.cos(elevation_rad) * math.cos(azimuth_rad)   # North
        y_ned = math.cos(elevation_rad) * math.sin(azimuth_rad)   # East
        z_ned = -math.sin(elevation_rad)                          # Down (âm vì Down là âm)
        
        return (x_ned, y_ned, z_ned)
    
    def angles_to_vector(self, azimuth_deg, elevation_deg):
        """
        Chuyển đổi góc thành vector định hướng theo hệ tọa độ đã chọn
        
        Input:
            azimuth_deg: Góc azimuth (độ)
            elevation_deg: Góc elevation (độ)
            
        Output:
            tuple: Vector định hướng đơn vị
        """
        if self.coordinate_system == 'ENU':
            return self.angles_to_vector_enu(azimuth_deg, elevation_deg)
        else:
            return self.angles_to_vector_ned(azimuth_deg, elevation_deg)
    
    def vector_to_angles(self, direction_vector):
        """
        Chuyển đổi vector định hướng thành góc azimuth/elevation
        
        Input:
            direction_vector: tuple (x, y, z) vector định hướng
            
        Output:
            tuple: (azimuth_deg, elevation_deg)
        """
        x, y, z = direction_vector
        
        if self.coordinate_system == 'ENU':
            # ENU: x=East, y=North, z=Up
            azimuth_rad = math.atan2(x, y)  # atan2(East, North)
            elevation_rad = math.atan2(z, math.sqrt(x**2 + y**2))
        else:
            # NED: x=North, y=East, z=Down
            azimuth_rad = math.atan2(y, x)  # atan2(East, North)
            elevation_rad = math.atan2(-z, math.sqrt(x**2 + y**2))  # -z vì Down là âm
        
        # Chuyển về độ và đảm bảo azimuth trong [0, 360)
        azimuth_deg = math.degrees(azimuth_rad)
        if azimuth_deg < 0:
            azimuth_deg += 360
            
        elevation_deg = math.degrees(elevation_rad)
        
        return (azimuth_deg, elevation_deg)
    
    def normalize_vector(self, vector):
        """Chuẩn hóa vector về độ dài đơn vị"""
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude == 0:
            return vector
        return tuple(v / magnitude for v in vector)
    
class TargetCalculator:
    """
    Lớp chính tính toán tọa độ mục tiêu
    """
    
    def __init__(self, coordinate_system='ENU'):
        """
        Initialize target calculator
        
        Input:
            coordinate_system: 'ENU' hoặc 'NED'
        """
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
            dict: Thông tin mục tiêu bao gồm tọa độ trong nhiều hệ khác nhau
        """
        # Validate input
        if distance_m <= 0:
            raise ValueError("Distance must be positive")
        
        # 1. Chuyển đổi góc thành vector định hướng 3D
        direction_vector = self.direction_vectors.angles_to_vector(azimuth_deg, elevation_deg)
        
        # 2. Tính tọa độ mục tiêu trong hệ tọa độ địa phương (ENU hoặc NED)
        # Vị trí mục tiêu = vị trí observer + distance * direction_vector
        target_local = tuple(distance_m * v for v in direction_vector)
        
        # 3. Chuyển đổi từ hệ địa phương sang ECEF
        if self.coordinate_system == 'ENU':
            target_ecef = self.coord_transform.enu_to_ecef(target_local, observer_geodetic)
        else:
            target_ecef = self.coord_transform.ned_to_ecef(target_local, observer_geodetic)
        
        # 4. Chuyển đổi từ ECEF sang Geodetic (lat, lon, alt)
        target_geodetic = self.coord_transform.ecef_to_geodetic(*target_ecef)
        
        # 5. Tính khoảng cách 3D thực tế để verify
        observer_ecef = self.coord_transform.geodetic_to_ecef(*observer_geodetic)
        actual_distance = math.sqrt(sum((target_ecef[i] - observer_ecef[i])**2 for i in range(3)))
        
        # Tính bearing và range trong hệ địa phương để verify
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
                'X': target_ecef[0],
                'Y': target_ecef[1],
                'Z': target_ecef[2]
            },
            'target_local': {
                self.coordinate_system.lower(): target_local,
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
            'direction_vector': direction_vector
        }
    
    def calculate_multiple_targets(self, observer_geodetic, measurements):
        """
        Tính toán nhiều mục tiêu cùng lúc
        
        Input:
            observer_geodetic: tuple (lat_deg, lon_deg, alt_m)
            measurements: list of dict với keys: azimuth, elevation, distance
            
        Output:
            list: Danh sách kết quả cho từng mục tiêu
        """
        results = []
        for i, measurement in enumerate(measurements):
            try:
                result = self.calculate_target_position(
                    observer_geodetic,
                    measurement['azimuth'],
                    measurement['elevation'], 
                    measurement['distance']
                )
                result['target_id'] = i + 1
                results.append(result)
            except Exception as e:
                print(f"Error calculating target {i+1}: {e}")
                results.append(None)
        
        return results
    
    def calculate_bearing_distance(self, observer_geodetic, target_geodetic):
        """
        Tính toán góc ngắm và khoảng cách từ observer đến target (inverse problem)
        
        Input:
            observer_geodetic: tuple (lat_deg, lon_deg, alt_m)
            target_geodetic: tuple (lat_deg, lon_deg, alt_m)
            
        Output:
            dict: azimuth, elevation, distance
        """
        # Chuyển cả hai điểm sang ECEF
        observer_ecef = self.coord_transform.geodetic_to_ecef(*observer_geodetic)
        target_ecef = self.coord_transform.geodetic_to_ecef(*target_geodetic)
        
        # Chuyển target về hệ địa phương
        if self.coordinate_system == 'ENU':
            target_local = self.coord_transform.ecef_to_enu(target_ecef, observer_geodetic)
        else:
            target_local = self.coord_transform.ecef_to_ned(target_ecef, observer_geodetic)
        
        # Tính khoảng cách
        distance = math.sqrt(sum(v**2 for v in target_local))
        
        # Tính direction vector và chuyển về góc
        if distance > 0:
            direction_vector = tuple(v / distance for v in target_local)
            azimuth, elevation = self.direction_vectors.vector_to_angles(direction_vector)
        else:
            azimuth, elevation = 0, 90  # Điểm trùng nhau
        
        return {
            'azimuth': azimuth,
            'elevation': elevation,
            'distance': distance,
            'target_local': target_local,
            'direction_vector': direction_vector if distance > 0 else (0, 0, 1)
        }
    
def test_target_calculator():
    """Hàm test thuật toán tính toán mục tiêu"""
    
    print("=== TEST TARGET CALCULATOR ===")
    
    # Test với hệ ENU
    calculator = TargetCalculator('ENU')
    
    # Tọa độ người quan sát (Đại học Bách Khoa TP.HCM)
    observer = (10.762622, 106.660172, 10.0)  # lat, lon, alt
    
    print(f"Observer position: {observer[0]:.6f}°, {observer[1]:.6f}°, {observer[2]}m")
    
    # Test case 1: Mục tiêu hướng Đông Bắc, 45° elevation, 1000m
    print("\n--- Test Case 1: NE direction, 45° up, 1000m ---")
    azimuth = 45.0    # Đông Bắc
    elevation = 30.0  # 30° lên trên
    distance = 1000.0 # 1km
    
    result = calculator.calculate_target_position(observer, azimuth, elevation, distance)
    
    target_pos = result['target_geodetic']
    print(f"Target position: {target_pos['latitude']:.6f}°, {target_pos['longitude']:.6f}°, {target_pos['altitude']:.2f}m")
    print(f"Local coordinates (ENU): E={result['target_local']['enu'][0]:.2f}, N={result['target_local']['enu'][1]:.2f}, U={result['target_local']['enu'][2]:.2f}")
    print(f"Direction vector: {result['direction_vector']}")
    
    # Verification
    verification = result['verification']
    print(f"Verification - Distance error: {verification['distance_error']:.3f}m")
    print(f"Verification - Azimuth error: {verification['azimuth_error']:.3f}°")
    print(f"Verification - Elevation error: {verification['elevation_error']:.3f}°")
    
    # Test inverse calculation
    print("\n--- Inverse Calculation Test ---")
    target_geodetic = (target_pos['latitude'], target_pos['longitude'], target_pos['altitude'])
    inverse_result = calculator.calculate_bearing_distance(observer, target_geodetic)
    
    print(f"Calculated: Az={inverse_result['azimuth']:.2f}°, El={inverse_result['elevation']:.2f}°, Dist={inverse_result['distance']:.2f}m")
    print(f"Original:   Az={azimuth:.2f}°, El={elevation:.2f}°, Dist={distance:.2f}m")
    
    # Test multiple targets
    print("\n--- Multiple Targets Test ---")
    measurements = [
        {'azimuth': 0, 'elevation': 0, 'distance': 500},    # Bắc, ngang, 500m
        {'azimuth': 90, 'elevation': 10, 'distance': 800},  # Đông, 10° lên, 800m  
        {'azimuth': 180, 'elevation': -5, 'distance': 1200}, # Nam, 5° xuống, 1200m
        {'azimuth': 270, 'elevation': 20, 'distance': 600}  # Tây, 20° lên, 600m
    ]
    
    multi_results = calculator.calculate_multiple_targets(observer, measurements)
    
    for i, result in enumerate(multi_results):
        if result:
            target = result['target_geodetic']
            print(f"Target {i+1}: {target['latitude']:.6f}°, {target['longitude']:.6f}°, {target['altitude']:.1f}m")

def test_direction_vectors():
    """Test chuyển đổi góc và vector"""
    print("\n=== TEST DIRECTION VECTORS ===")
    
    # Test ENU
    dv_enu = DirectionVectors('ENU')
    
    # Test cases: cardinal directions
    test_cases = [
        (0, 0, "North, horizontal"),
        (90, 0, "East, horizontal"), 
        (180, 0, "South, horizontal"),
        (270, 0, "West, horizontal"),
        (0, 90, "North, straight up"),
        (45, 30, "Northeast, 30° up")
    ]
    
    print("ENU System:")
    for azimuth, elevation, description in test_cases:
        vector = dv_enu.angles_to_vector(azimuth, elevation)
        back_az, back_el = dv_enu.vector_to_angles(vector)
        print(f"{description}: Az={azimuth}° El={elevation}° -> Vector{vector} -> Az={back_az:.1f}° El={back_el:.1f}°")

if __name__ == "__main__":
    test_direction_vectors()
    test_target_calculator()
"""
test_calculations.py
Module kiểm thử các tính toán trong hệ thống

Chức năng:
- Kiểm thử chuyển đổi tọa độ
- Kiểm thử tính toán vector định hướng
- Kiểm thử tính toán tọa độ mục tiêu

"""

import unittest
import math
from core import CoordinateTransforms, DirectionVectors, GPSTargetSystem

class TestCoordinateTransforms(unittest.TestCase):
    """Kiểm thử chuyển đổi tọa độ"""
    
    def setUp(self):
        self.transforms = CoordinateTransforms()
        
    def test_geodetic_to_ecef(self):
        """Kiểm thử chuyển đổi Geodetic → ECEF"""
        # Test case: 0°N 0°E at sea level
        lat, lon, alt = 0, 0, 0
        x, y, z = self.transforms.geodetic_to_ecef(lat, lon, alt)
        
        self.assertAlmostEqual(x, 6378137.0, places=1)  # Bán kính xích đạo
        self.assertAlmostEqual(y, 0, places=1)
        self.assertAlmostEqual(z, 0, places=1)
        
    def test_ecef_to_geodetic(self):
        """Kiểm thử chuyển đổi ECEF → Geodetic"""
        # Test case: Điểm tại xích đạo, kinh tuyến gốc
        x, y, z = 6378137.0, 0, 0
        lat, lon, alt = self.transforms.ecef_to_geodetic(x, y, z)
        
        self.assertAlmostEqual(lat, 0, places=5)
        self.assertAlmostEqual(lon, 0, places=5)
        self.assertAlmostEqual(alt, 0, places=1)
        
class TestDirectionVectors(unittest.TestCase):
    """Kiểm thử tính toán vector định hướng"""
    
    def setUp(self):
        self.vectors = DirectionVectors()
        
    def test_angles_to_vector_enu(self):
        """Kiểm thử chuyển đổi góc → vector ENU"""
        # Test case: Hướng Bắc, ngang tầm
        azimuth, elevation = 0, 0
        x, y, z = self.vectors.angles_to_vector_enu(azimuth, elevation)
        
        self.assertAlmostEqual(x, 0, places=5)
        self.assertAlmostEqual(y, 1, places=5)
        self.assertAlmostEqual(z, 0, places=5)
        
    def test_vector_magnitude(self):
        """Kiểm thử độ dài vector định hướng = 1"""
        # Test nhiều góc khác nhau
        test_angles = [
            (0, 0),    # Bắc
            (90, 0),   # Đông
            (45, 45),  # Đông Bắc, hướng lên
        ]
        
        for azimuth, elevation in test_angles:
            vector = self.vectors.angles_to_vector(azimuth, elevation)
            magnitude = math.sqrt(sum(v*v for v in vector))
            self.assertAlmostEqual(magnitude, 1, places=5)

class TestGPSTargetSystem(unittest.TestCase):
    """Kiểm thử tính toán tọa độ mục tiêu"""
    
    def setUp(self):
        self.system = GPSTargetSystem()
        
    def test_calculate_target_north(self):
        """Kiểm thử mục tiêu ở hướng Bắc"""
        # Vị trí quan sát: 0°N 0°E
        # Mục tiêu cách 1km về phía Bắc
        observer_pos = (0, 0, 0)
        azimuth = 0      # Hướng Bắc
        elevation = 0    # Ngang tầm
        distance = 1000  # 1km
        
        target = self.system.calculate_target_position(
            observer_pos[0], observer_pos[1], observer_pos[2],
            azimuth, elevation, distance
        )
        
        # Mục tiêu phải ở vĩ độ dương, cùng kinh độ
        self.assertGreater(target[0], 0)  # Vĩ độ dương
        self.assertAlmostEqual(target[1], 0, places=5)  # Cùng kinh độ
        
    def test_input_validation(self):
        """Kiểm thử validate dữ liệu đầu vào"""
        invalid_inputs = [
            (91, 0, 0, 0, 0, 1000),    # Vĩ độ > 90
            (0, 181, 0, 0, 0, 1000),   # Kinh độ > 180
            (0, 0, 0, 360, 0, 1000),   # Azimuth >= 360
            (0, 0, 0, 0, 91, 1000),    # Elevation > 90
            (0, 0, 0, 0, 0, -1),       # Distance < 0
        ]
        
        for inputs in invalid_inputs:
            with self.assertRaises(ValueError):
                self.system.validate_input_data(*inputs)

if __name__ == '__main__':
    unittest.main()
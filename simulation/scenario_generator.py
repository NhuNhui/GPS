"""
scenario_generator.py
Module tạo các kịch bản mô phỏng cho hệ thống tính toán tọa độ mục tiêu

Chức năng:
- Tạo dữ liệu mô phỏng cho người quan sát (GPS position)
- Tạo mục tiêu với tọa độ ngẫu nhiên hoặc theo pattern
- Tạo dữ liệu cảm biến với nhiễu thực tế (GPS drift, IMU noise, laser error)
- Lưu/load kịch bản mô phỏng

"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

class ScenarioGenerator:
    """
    Lớp tạo kịch bản mô phỏng với các tham số có thể tùy chỉnh
    """
    
    def __init__(self, seed=None):
        """
        Initialize scenario generator
        
        Input:
            seed: Random seed để tái tạo kịch bản
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.scenarios = []
    
    def create_observer_position(self, location_name="HCMUT", 
                                 lat=10.762622, lon=106.660172, alt=10.0):
        """
        Tạo vị trí người quan sát
        
        Input:
            location_name: Tên địa điểm
            lat: Vĩ độ (độ)
            lon: Kinh độ (độ)
            alt: Độ cao (mét)
            
        Output:
            dict: Thông tin người quan sát
        """
        return {
            'location_name': location_name,
            'latitude': lat,
            'longitude': lon,
            'altitude': alt,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_random_target(self, observer_pos, 
                            distance_range=(500, 5000),
                            azimuth_range=(0, 360),
                            elevation_range=(-10, 45)):
        """
        Tạo mục tiêu ngẫu nhiên xung quanh người quan sát
        
        Input:
            observer_pos: dict vị trí người quan sát
            distance_range: tuple (min, max) khoảng cách (mét)
            azimuth_range: tuple (min, max) góc azimuth (độ)
            elevation_range: tuple (min, max) góc elevation (độ)
            
        Output:
            dict: Thông tin mục tiêu ground truth
        """
        distance = random.uniform(*distance_range)
        azimuth = random.uniform(*azimuth_range)
        elevation = random.uniform(*elevation_range)
        
        return {
            'target_id': f"T_{len(self.scenarios)+1:03d}",
            'true_azimuth': azimuth,
            'true_elevation': elevation,
            'true_distance': distance,
            'description': f"Random target at {distance:.1f}m, Az={azimuth:.1f}°, El={elevation:.1f}°"
        }
    
    def add_sensor_noise(self, true_values, noise_params=None):
        """
        Thêm nhiễu thực tế vào dữ liệu cảm biến
        
        Input:
            true_values: dict chứa giá trị thực
            noise_params: dict tham số nhiễu hoặc None để dùng mặc định
            
        Output:
            dict: Dữ liệu cảm biến có nhiễu
        """
        if noise_params is None:
            noise_params = {
                'gps_lat_std': 0.00001,      # ~1.1m standard deviation
                'gps_lon_std': 0.00001,
                'gps_alt_std': 2.0,          # 2m altitude error
                'azimuth_std': 1.5,          # 1.5° azimuth error
                'elevation_std': 1.0,        # 1.0° elevation error
                'distance_std': 5.0,         # 5m distance error
                'distance_bias': 0.5         # 0.5% systematic bias
            }
        
        # Nhiễu GPS
        gps_noisy = {
            'latitude': true_values['observer']['latitude'] + 
                       np.random.normal(0, noise_params['gps_lat_std']),
            'longitude': true_values['observer']['longitude'] + 
                        np.random.normal(0, noise_params['gps_lon_std']),
            'altitude': true_values['observer']['altitude'] + 
                       np.random.normal(0, noise_params['gps_alt_std']),
            'fix_quality': random.choice([1, 1, 1, 2]),  # Mostly GPS fix
            'num_satellites': random.randint(6, 12),
            'hdop': random.uniform(0.8, 2.5)
        }
        
        # Nhiễu IMU (azimuth, elevation)
        true_distance = true_values['target']['true_distance']
        distance_bias = true_distance * noise_params['distance_bias'] / 100
        
        imu_noisy = {
            'azimuth': true_values['target']['true_azimuth'] + 
                      np.random.normal(0, noise_params['azimuth_std']),
            'elevation': true_values['target']['true_elevation'] + 
                        np.random.normal(0, noise_params['elevation_std'])
        }
        
        # Chuẩn hóa azimuth về [0, 360)
        imu_noisy['azimuth'] = imu_noisy['azimuth'] % 360
        
        # Giới hạn elevation về [-90, 90]
        imu_noisy['elevation'] = np.clip(imu_noisy['elevation'], -90, 90)
        
        # Nhiễu Laser rangefinder
        range_noisy = {
            'distance': true_distance + distance_bias + 
                       np.random.normal(0, noise_params['distance_std'])
        }
        
        return {
            'gps': gps_noisy,
            'imu': imu_noisy,
            'range': range_noisy,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_scenario(self, observer_pos, num_targets=5, 
                       add_noise=True, noise_params=None):
        """
        Tạo kịch bản hoàn chỉnh với nhiều mục tiêu
        
        Input:
            observer_pos: dict vị trí người quan sát
            num_targets: Số lượng mục tiêu
            add_noise: Có thêm nhiễu hay không
            noise_params: Tham số nhiễu custom
            
        Output:
            dict: Kịch bản hoàn chỉnh
        """
        scenario = {
            'scenario_id': f"SCN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now().isoformat(),
            'observer': observer_pos,
            'targets': []
        }
        
        for i in range(num_targets):
            target = self.create_random_target(observer_pos)
            
            target_data = {
                'target_id': target['target_id'],
                'ground_truth': target,
                'measurements': []
            }
            
            # Tạo nhiều lần đo cho mỗi mục tiêu (giả lập đo lặp lại)
            num_measurements = random.randint(3, 8)
            for j in range(num_measurements):
                true_values = {
                    'observer': observer_pos,
                    'target': target
                }
                
                if add_noise:
                    measurement = self.add_sensor_noise(true_values, noise_params)
                else:
                    measurement = {
                        'gps': {
                            'latitude': observer_pos['latitude'],
                            'longitude': observer_pos['longitude'],
                            'altitude': observer_pos['altitude'],
                            'fix_quality': 2,
                            'num_satellites': 10,
                            'hdop': 1.0
                        },
                        'imu': {
                            'azimuth': target['true_azimuth'],
                            'elevation': target['true_elevation']
                        },
                        'range': {
                            'distance': target['true_distance']
                        },
                        'timestamp': (datetime.now() + timedelta(seconds=j)).isoformat()
                    }
                
                measurement['measurement_id'] = j + 1
                target_data['measurements'].append(measurement)
            
            scenario['targets'].append(target_data)
        
        self.scenarios.append(scenario)
        return scenario
    
    def create_pattern_scenario(self, observer_pos, pattern='grid'):
        """
        Tạo kịch bản theo pattern cụ thể (grid, circle, line)
        
        Input:
            observer_pos: dict vị trí người quan sát
            pattern: 'grid', 'circle', hoặc 'line'
            
        Output:
            dict: Kịch bản theo pattern
        """
        scenario = {
            'scenario_id': f"SCN_{pattern.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now().isoformat(),
            'observer': observer_pos,
            'pattern': pattern,
            'targets': []
        }
        
        if pattern == 'grid':
            # Tạo lưới mục tiêu 3x3
            distances = [1000, 2000, 3000]
            azimuths = [0, 45, 90, 135, 180, 225, 270, 315]
            elevation = 10.0
            
            for dist in distances:
                for az in azimuths:
                    target = {
                        'target_id': f"T_GRID_{len(scenario['targets'])+1:02d}",
                        'true_azimuth': az,
                        'true_elevation': elevation,
                        'true_distance': dist,
                        'description': f"Grid target: {dist}m, {az}°"
                    }
                    
                    target_data = {
                        'target_id': target['target_id'],
                        'ground_truth': target,
                        'measurements': [self.add_sensor_noise({
                            'observer': observer_pos,
                            'target': target
                        })]
                    }
                    
                    scenario['targets'].append(target_data)
        
        elif pattern == 'circle':
            # Mục tiêu theo vòng tròn
            num_targets = 12  # 12 mục tiêu mỗi 30°
            distance = 2000
            elevation = 15.0
            
            for i in range(num_targets):
                azimuth = i * 30
                target = {
                    'target_id': f"T_CIRCLE_{i+1:02d}",
                    'true_azimuth': azimuth,
                    'true_elevation': elevation,
                    'true_distance': distance,
                    'description': f"Circle target at {azimuth}°"
                }
                
                target_data = {
                    'target_id': target['target_id'],
                    'ground_truth': target,
                    'measurements': [self.add_sensor_noise({
                        'observer': observer_pos,
                        'target': target
                    })]
                }
                
                scenario['targets'].append(target_data)
        
        elif pattern == 'line':
            # Mục tiêu theo đường thẳng
            azimuth = 45  # Hướng Đông Bắc
            elevation = 0
            
            for i, dist in enumerate([500, 1000, 1500, 2000, 2500, 3000]):
                target = {
                    'target_id': f"T_LINE_{i+1:02d}",
                    'true_azimuth': azimuth,
                    'true_elevation': elevation,
                    'true_distance': dist,
                    'description': f"Line target at {dist}m"
                }
                
                target_data = {
                    'target_id': target['target_id'],
                    'ground_truth': target,
                    'measurements': [self.add_sensor_noise({
                        'observer': observer_pos,
                        'target': target
                    })]
                }
                
                scenario['targets'].append(target_data)
        
        self.scenarios.append(scenario)
        return scenario
    
    def save_scenario(self, scenario, filepath):
        """
        Lưu kịch bản ra file JSON
        
        Input:
            scenario: dict kịch bản
            filepath: Đường dẫn file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False)
        
        print(f"Đã lưu kịch bản vào: {filepath}")
    
    def load_scenario(self, filepath):
        """
        Load kịch bản từ file JSON
        
        Input:
            filepath: Đường dẫn file
            
        Output:
            dict: Kịch bản
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
        
        print(f"Đã load kịch bản: {scenario['scenario_id']}")
        return scenario


def test_scenario_generator():
    """Test tạo kịch bản mô phỏng"""
    print("=== TEST SCENARIO GENERATOR ===\n")
    
    generator = ScenarioGenerator(seed=42)
    
    # Tạo vị trí quan sát tại HCMUT
    observer = generator.create_observer_position()
    print(f"Observer: {observer['location_name']}")
    print(f"Position: {observer['latitude']:.6f}°, {observer['longitude']:.6f}°, {observer['altitude']}m\n")
    
    # Test 1: Random scenario
    print("--- Test 1: Random Scenario ---")
    scenario1 = generator.create_scenario(observer, num_targets=3, add_noise=True)
    print(f"Scenario ID: {scenario1['scenario_id']}")
    print(f"Number of targets: {len(scenario1['targets'])}")
    
    for target in scenario1['targets']:
        gt = target['ground_truth']
        print(f"\n{target['target_id']}: Az={gt['true_azimuth']:.1f}°, "
              f"El={gt['true_elevation']:.1f}°, Dist={gt['true_distance']:.1f}m")
        print(f"  Measurements: {len(target['measurements'])}")
    
    # Test 2: Grid pattern
    print("\n\n--- Test 2: Grid Pattern ---")
    scenario2 = generator.create_pattern_scenario(observer, pattern='grid')
    print(f"Scenario ID: {scenario2['scenario_id']}")
    print(f"Pattern: {scenario2['pattern']}")
    print(f"Number of targets: {len(scenario2['targets'])}")
    
    # Test 3: Save scenario
    print("\n\n--- Test 3: Save & Load ---")
    generator.save_scenario(scenario1, 'data/test_scenario.json')
    loaded = generator.load_scenario('data/test_scenario.json')
    print(f"Loaded scenario matches: {loaded['scenario_id'] == scenario1['scenario_id']}")


if __name__ == "__main__":
    test_scenario_generator()
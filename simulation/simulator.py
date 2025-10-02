"""
simulator.py
Engine mô phỏng chính - thực thi tính toán tọa độ mục tiêu từ kịch bản

Chức năng:
- Chạy kịch bản mô phỏng
- Sử dụng các module core để tính toán tọa độ
- Thu thập kết quả và so sánh với ground truth
- Tính toán sai số và thống kê hiệu suất
- Xuất báo cáo kết quả

"""

import sys
sys.path.append('..')

import numpy as np
import statistics
from datetime import datetime
from pathlib import Path
import json

# Import core modules
from core.coordinate_transforms import CoordinateTransforms
from core.sensor_fusion import SensorFusion
from core.target_calculator import TargetCalculator


class SimulationResult:
    """
    Lớp lưu trữ kết quả mô phỏng cho một mục tiêu
    """
    
    def __init__(self, target_id):
        self.target_id = target_id
        self.ground_truth = None
        self.calculated_position = None
        self.errors = {}
        self.measurements = []
        self.calculation_time = 0
    
    def calculate_errors(self):
        """
        Tính toán các loại sai số
        
        Output:
            dict: Các chỉ số sai số
        """
        if not self.ground_truth or not self.calculated_position:
            return None
        
        gt = self.ground_truth
        calc = self.calculated_position['target_geodetic']
        
        # Sai số vị trí (geodetic)
        lat_error = abs(calc['latitude'] - gt['true_latitude'])
        lon_error = abs(calc['longitude'] - gt['true_longitude'])
        alt_error = abs(calc['altitude'] - gt['true_altitude'])
        
        # Chuyển sang mét (xấp xỉ)
        # 1 độ vĩ độ ≈ 111km, 1 độ kinh độ ≈ 111km * cos(lat)
        lat_error_m = lat_error * 111000
        lon_error_m = lon_error * 111000 * np.cos(np.radians(gt['true_latitude']))
        
        # Sai số khoảng cách 2D và 3D
        horizontal_error = np.sqrt(lat_error_m**2 + lon_error_m**2)
        total_error_3d = np.sqrt(lat_error_m**2 + lon_error_m**2 + alt_error**2)
        
        self.errors = {
            'latitude_error_deg': lat_error,
            'longitude_error_deg': lon_error,
            'altitude_error_m': alt_error,
            'latitude_error_m': lat_error_m,
            'longitude_error_m': lon_error_m,
            'horizontal_error_m': horizontal_error,
            'total_error_3d_m': total_error_3d,
            'azimuth_error_deg': self.calculated_position['verification']['azimuth_error'],
            'elevation_error_deg': self.calculated_position['verification']['elevation_error'],
            'distance_error_m': self.calculated_position['verification']['distance_error']
        }
        
        return self.errors
    
    def to_dict(self):
        """Chuyển kết quả thành dictionary"""
        return {
            'target_id': self.target_id,
            'ground_truth': self.ground_truth,
            'calculated_position': self.calculated_position,
            'errors': self.errors,
            'calculation_time_ms': self.calculation_time * 1000,
            'num_measurements': len(self.measurements)
        }


class Simulator:
    """
    Engine mô phỏng chính
    """
    
    def __init__(self, coordinate_system='ENU'):
        """
        Initialize simulator
        
        Input:
            coordinate_system: 'ENU' hoặc 'NED'
        """
        self.coord_transform = CoordinateTransforms()
        self.sensor_fusion = SensorFusion()
        self.calculator = TargetCalculator(coordinate_system)
        self.results = []
        self.statistics = {}
    
    def run_scenario(self, scenario, use_sensor_fusion=True):
        """
        Chạy một kịch bản mô phỏng hoàn chỉnh
        
        Input:
            scenario: dict kịch bản từ ScenarioGenerator
            use_sensor_fusion: Có sử dụng sensor fusion hay không
            
        Output:
            list: Danh sách SimulationResult
        """
        print(f"\n{'='*60}")
        print(f"Running Scenario: {scenario['scenario_id']}")
        print(f"{'='*60}")
        
        observer_pos = scenario['observer']
        observer_geodetic = (
            observer_pos['latitude'],
            observer_pos['longitude'],
            observer_pos['altitude']
        )
        
        self.results = []
        
        # Xử lý từng mục tiêu
        for target_data in scenario['targets']:
            result = SimulationResult(target_data['target_id'])
            
            print(f"\nProcessing target: {target_data['target_id']}")
            
            # Ground truth
            gt = target_data['ground_truth']
            
            # Tính tọa độ ground truth từ góc và khoảng cách
            start_time = datetime.now()
            gt_position = self.calculator.calculate_target_position(
                observer_geodetic,
                gt['true_azimuth'],
                gt['true_elevation'],
                gt['true_distance']
            )
            
            result.ground_truth = {
                'true_azimuth': gt['true_azimuth'],
                'true_elevation': gt['true_elevation'],
                'true_distance': gt['true_distance'],
                'true_latitude': gt_position['target_geodetic']['latitude'],
                'true_longitude': gt_position['target_geodetic']['longitude'],
                'true_altitude': gt_position['target_geodetic']['altitude']
            }
            
            # Xử lý measurements
            measurements = target_data['measurements']
            result.measurements = measurements
            
            if use_sensor_fusion:
                # Sử dụng sensor fusion để lọc nhiễu
                filtered_measurements = []
                
                for measurement in measurements:
                    # Process GPS
                    gps_nmea = self._convert_to_nmea_gga(measurement['gps'])
                    self.sensor_fusion.process_gps_data(gps_nmea)
                    
                    # Process IMU
                    filtered_angles = self.sensor_fusion.process_imu_data(
                        measurement['imu']['azimuth'],
                        measurement['imu']['elevation']
                    )
                    
                    # Process Range
                    filtered_distance = self.sensor_fusion.process_range_data(
                        measurement['range']['distance']
                    )
                    
                    filtered_measurements.append({
                        'azimuth': filtered_angles[0],
                        'elevation': filtered_angles[1],
                        'distance': filtered_distance
                    })
                
                # Lấy measurement cuối cùng (đã được lọc tốt nhất)
                if filtered_measurements:
                    final_measurement = filtered_measurements[-1]
                    
                    # Lấy GPS đã lọc
                    fused_data = self.sensor_fusion.get_fused_sensor_data()
                    if fused_data:
                        observer_filtered = (
                            fused_data['gps']['latitude'],
                            fused_data['gps']['longitude'],
                            fused_data['gps']['altitude']
                        )
                    else:
                        observer_filtered = observer_geodetic
                else:
                    continue
            else:
                # Không dùng fusion - lấy measurement đầu tiên
                measurement = measurements[0]
                final_measurement = {
                    'azimuth': measurement['imu']['azimuth'],
                    'elevation': measurement['imu']['elevation'],
                    'distance': measurement['range']['distance']
                }
                observer_filtered = (
                    measurement['gps']['latitude'],
                    measurement['gps']['longitude'],
                    measurement['gps']['altitude']
                )
            
            # Tính toán vị trí mục tiêu
            calculated = self.calculator.calculate_target_position(
                observer_filtered,
                final_measurement['azimuth'],
                final_measurement['elevation'],
                final_measurement['distance']
            )
            
            end_time = datetime.now()
            result.calculation_time = (end_time - start_time).total_seconds()
            
            result.calculated_position = calculated
            result.calculate_errors()
            
            # In kết quả
            print(f"  Ground Truth: "
                  f"Lat={result.ground_truth['true_latitude']:.6f}°, "
                  f"Lon={result.ground_truth['true_longitude']:.6f}°, "
                  f"Alt={result.ground_truth['true_altitude']:.1f}m")
            
            print(f"  Calculated:   "
                  f"Lat={calculated['target_geodetic']['latitude']:.6f}°, "
                  f"Lon={calculated['target_geodetic']['longitude']:.6f}°, "
                  f"Alt={calculated['target_geodetic']['altitude']:.1f}m")
            
            print(f"  Horizontal Error: {result.errors['horizontal_error_m']:.2f}m")
            print(f"  3D Error: {result.errors['total_error_3d_m']:.2f}m")
            print(f"  Calculation time: {result.calculation_time*1000:.2f}ms")
            
            self.results.append(result)
        
        # Tính thống kê
        self._calculate_statistics()
        
        return self.results
    
    def _convert_to_nmea_gga(self, gps_data):
        """
        Chuyển GPS data thành NMEA GGA sentence
        
        Input:
            gps_data: dict GPS data
            
        Output:
            str: NMEA GGA sentence
        """
        lat = gps_data['latitude']
        lon = gps_data['longitude']
        
        # Convert to NMEA format
        lat_deg = int(abs(lat))
        lat_min = (abs(lat) - lat_deg) * 60
        lat_str = f"{lat_deg:02d}{lat_min:07.4f}"
        lat_dir = 'N' if lat >= 0 else 'S'
        
        lon_deg = int(abs(lon))
        lon_min = (abs(lon) - lon_deg) * 60
        lon_str = f"{lon_deg:03d}{lon_min:07.4f}"
        lon_dir = 'E' if lon >= 0 else 'W'
        
        nmea = (f"$GPGGA,123519,{lat_str},{lat_dir},{lon_str},{lon_dir},"
                f"{gps_data.get('fix_quality', 1)},"
                f"{gps_data.get('num_satellites', 8)},"
                f"{gps_data.get('hdop', 1.0):.1f},"
                f"{gps_data['altitude']:.1f},M,0.0,M,,*47")
        
        return nmea
    
    def _calculate_statistics(self):
        """Tính thống kê tổng hợp cho kịch bản"""
        if not self.results:
            return
        
        horizontal_errors = [r.errors['horizontal_error_m'] for r in self.results]
        error_3d = [r.errors['total_error_3d_m'] for r in self.results]
        calc_times = [r.calculation_time * 1000 for r in self.results]  # ms
        
        self.statistics = {
            'num_targets': len(self.results),
            'horizontal_error': {
                'mean': statistics.mean(horizontal_errors),
                'median': statistics.median(horizontal_errors),
                'std': statistics.stdev(horizontal_errors) if len(horizontal_errors) > 1 else 0,
                'min': min(horizontal_errors),
                'max': max(horizontal_errors)
            },
            '3d_error': {
                'mean': statistics.mean(error_3d),
                'median': statistics.median(error_3d),
                'std': statistics.stdev(error_3d) if len(error_3d) > 1 else 0,
                'min': min(error_3d),
                'max': max(error_3d)
            },
            'calculation_time_ms': {
                'mean': statistics.mean(calc_times),
                'median': statistics.median(calc_times),
                'min': min(calc_times),
                'max': max(calc_times)
            }
        }
    
    def print_statistics(self):
        """In thống kê kết quả"""
        if not self.statistics:
            print("No statistics available")
            return
        
        print(f"\n{'='*60}")
        print("SIMULATION STATISTICS")
        print(f"{'='*60}")
        print(f"Number of targets: {self.statistics['num_targets']}")
        
        print(f"\nHorizontal Error (m):")
        print(f"  Mean:   {self.statistics['horizontal_error']['mean']:.2f}")
        print(f"  Median: {self.statistics['horizontal_error']['median']:.2f}")
        print(f"  Std:    {self.statistics['horizontal_error']['std']:.2f}")
        print(f"  Range:  [{self.statistics['horizontal_error']['min']:.2f}, "
              f"{self.statistics['horizontal_error']['max']:.2f}]")
        
        print(f"\n3D Error (m):")
        print(f"  Mean:   {self.statistics['3d_error']['mean']:.2f}")
        print(f"  Median: {self.statistics['3d_error']['median']:.2f}")
        print(f"  Std:    {self.statistics['3d_error']['std']:.2f}")
        print(f"  Range:  [{self.statistics['3d_error']['min']:.2f}, "
              f"{self.statistics['3d_error']['max']:.2f}]")
        
        print(f"\nCalculation Time (ms):")
        print(f"  Mean:   {self.statistics['calculation_time_ms']['mean']:.2f}")
        print(f"  Median: {self.statistics['calculation_time_ms']['median']:.2f}")
        print(f"  Range:  [{self.statistics['calculation_time_ms']['min']:.2f}, "
              f"{self.statistics['calculation_time_ms']['max']:.2f}]")
    
    def export_results(self, filepath):
        """
        Xuất kết quả ra file JSON
        
        Input:
            filepath: Đường dẫn file output
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            'simulation_time': datetime.now().isoformat(),
            'statistics': self.statistics,
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults exported to: {filepath}")


def test_simulator():
    """Test simulator với kịch bản mẫu"""
    import sys
    sys.path.append('..')
    from simulation.scenario_generator import ScenarioGenerator
    
    print("=== TEST SIMULATOR ===\n")
    
    # Tạo kịch bản
    generator = ScenarioGenerator(seed=42)
    observer = generator.create_observer_position()
    scenario = generator.create_scenario(observer, num_targets=5, add_noise=True)
    
    # Chạy mô phỏng
    simulator = Simulator(coordinate_system='ENU')
    results = simulator.run_scenario(scenario, use_sensor_fusion=True)
    
    # In thống kê
    simulator.print_statistics()
    
    # Xuất kết quả
    simulator.export_results('data/simulation_results.json')
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    test_simulator()
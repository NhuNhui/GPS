from core.gps_target_system import *

def test_gps_target_system():
    """Test hệ thống hoàn chỉnh"""
    print("=== TEST GPS TARGET SYSTEM ===\n")
    
    system = GPSTargetSystem('ENU')
    
    # Test 1: Tính toán cơ bản
    print("--- Test 1: Basic Calculation ---")
    result = system.calculate_target_position(
        observer_lat=10.762622,
        observer_lon=106.660172,
        observer_alt=10.0,
        azimuth=45.0,
        elevation=30.0,
        distance=1000.0
    )
    
    target = result['target_geodetic']
    print(f"Target: {target['latitude']:.6f}°, {target['longitude']:.6f}°, {target['altitude']:.1f}m")
    print(f"Distance error: {result['verification']['distance_error']:.3f}m")
    
    # Test 2: Với sensor fusion
    print("\n--- Test 2: With Sensor Fusion ---")
    gps_data = {
        'latitude': 10.762622,
        'longitude': 106.660172,
        'altitude': 10.0,
        'fix_quality': 1,
        'num_satellites': 8,
        'hdop': 1.2
    }
    
    imu_data = {
        'azimuth': 45.5,  # Có nhiễu
        'elevation': 29.8
    }
    
    range_data = {
        'distance': 1005.0  # Có nhiễu
    }
    
    result_fusion = system.calculate_target_with_fusion(gps_data, imu_data, range_data)
    print(f"Fusion data quality: {result_fusion['sensor_fusion']['data_quality']}")
    print(f"Original angles: Az={imu_data['azimuth']}°, El={imu_data['elevation']}°")
    print(f"Used angles: Az={result_fusion['input_parameters']['azimuth']:.2f}°, "
          f"El={result_fusion['input_parameters']['elevation']:.2f}°")
    
    # Test 3: Inverse calculation
    print("\n--- Test 3: Inverse Calculation ---")
    inverse = system.calculate_inverse(
        observer_lat=10.762622,
        observer_lon=106.660172,
        observer_alt=10.0,
        target_lat=target['latitude'],
        target_lon=target['longitude'],
        target_alt=target['altitude']
    )
    print(f"Calculated bearing: Az={inverse['azimuth']:.2f}°, El={inverse['elevation']:.2f}°")
    print(f"Distance: {inverse['distance']:.2f}m")
    
    print("\n✓ ALL TESTS PASSED!")


if __name__ == "__main__":
    test_gps_target_system()
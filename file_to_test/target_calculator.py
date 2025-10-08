from core.target_calculator import *

def test_target_calculator():
    """Test thuật toán tính toán mục tiêu"""
    
    print("=== TEST TARGET CALCULATOR ===\n")
    
    calculator = TargetCalculator('ENU')
    
    # Observer tại HCMUT
    observer = (10.762622, 106.660172, 10.0)
    print(f"Observer: {observer[0]:.6f}°, {observer[1]:.6f}°, {observer[2]}m\n")
    
    # Test case: 45° Đông Bắc, 30° lên, 1000m
    print("\n--- Test Case 1: 45° NE direction, 30° up, 1000m ---")
    azimuth = 45.0    # Đông Bắc
    elevation = 30.0  # 30° lên trên
    distance = 1000.0 # 1km
    
    result = calculator.calculate_target_position(observer, azimuth, elevation, distance)
    
    target = result['target_geodetic']
    print(f"Target: {target['latitude']:.6f}°, {target['longitude']:.6f}°, {target['altitude']:.1f}m")
    
    # Verification
    ver = result['verification']
    print(f"\nVerification:")
    print(f"Distance error: {ver['distance_error']:.3f}m (should be < 0.01m)")
    print(f"Azimuth error: {ver['azimuth_error']:.3f}° (should be < 0.001°)")
    print(f"Elevation error: {ver['elevation_error']:.3f}° (should be < 0.001°)")

    # Assert để đảm bảo
    assert ver['distance_error'] < 0.01, "Distance error quá lớn!"
    assert ver['azimuth_error'] < 0.001, "Azimuth error quá lớn!"
    assert ver['elevation_error'] < 0.001, "Elevation error quá lớn!"
    
    # Test inverse
    print("\n--- Test Inverse Calculation ---")
    target_geo = (target['latitude'], target['longitude'], target['altitude'])
    inverse = calculator.calculate_bearing_distance(observer, target_geo)
    
    print(f"Calculated: Az={inverse['azimuth']:.2f}°, El={inverse['elevation']:.2f}°, Dist={inverse['distance']:.2f}m")
    print(f"Original:   Az={azimuth:.2f}°, El={elevation:.2f}°, Dist={distance:.2f}m")
    
    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_target_calculator()
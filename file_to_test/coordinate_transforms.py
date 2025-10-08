from core.coordinate_transforms import *

def test_coordinate_conversion():
    """Test chuyển đổi tọa độ với validation"""
    converter = CoordinateTransforms()
    
    # Tọa độ mẫu (khu vực TP.HCM)
    observer_lat = 10.762622 
    observer_lon = 106.660172
    observer_height = 10.0
    
    print("=== TEST CHUYỂN ĐỔI TỌA ĐỘ (FIXED) ===")
    print(f"Observer: {observer_lat:.6f}°, {observer_lon:.6f}°, {observer_height}m\n")
    
    # Test 1: Geodetic -> ECEF
    ecef = converter.geodetic_to_ecef(observer_lat, observer_lon, observer_height)
    print(f"ECEF: X={ecef[0]:.2f}, Y={ecef[1]:.2f}, Z={ecef[2]:.2f}")

    geodetic_verify = converter.ecef_to_geodetic(*ecef)

    lat_err = abs(geodetic_verify[0] - observer_lat) * 111000
    lon_err = abs(geodetic_verify[1] - observer_lon) * 111000 * math.cos(math.radians(observer_lat))
    alt_err = abs(geodetic_verify[2] - observer_height)

    print(f"Round-trip error: lat={lat_err:.6f}m, lon={lon_err:.6f}m, alt={alt_err:.6f}m")
    assert lat_err < 0.001 and lon_err < 0.001 and alt_err < 0.001, "Geodetic round-trip FAILED!"
    
    # Test 2: ECEF -> Geodetic (round-trip)
    target_enu = np.array([1000.0, 500.0, 0.0])  # 1km East, 500m North
    print(f"Target ENU: E={target_enu[0]}, N={target_enu[1]}, U={target_enu[2]}")

    target_ecef = converter.enu_to_ecef(target_enu, (observer_lat, observer_lon, observer_height))
    print(f"Target ECEF: X={target_ecef[0]:.2f}, Y={target_ecef[1]:.2f}, Z={target_ecef[2]:.2f}")

    verify_enu = converter.ecef_to_enu(target_ecef, (observer_lat, observer_lon, observer_height))

    enu_error = np.linalg.norm(verify_enu - target_enu)
    print(f"ENU round-trip error: {enu_error:.6f}m")
    assert enu_error < 0.001, "ENU round-trip FAILED!"
    
    # Test 3: Target geodetic
    target_geodetic = converter.ecef_to_geodetic(*target_ecef)
    print(f"\nTarget geodetic: {target_geodetic[0]:.6f}°, {target_geodetic[1]:.6f}°, {target_geodetic[2]:.2f}m")
    
    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_coordinate_conversion()
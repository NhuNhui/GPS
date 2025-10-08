from core.sensor_fusion import *

def test_sensor_fusion():
    """Test sensor fusion"""
    print("=== TEST SENSOR FUSION (OPTIMIZED) ===\n")
    fusion = SensorFusion()
    
    # Test NMEA parsing
    test_gga = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    gps_data = fusion.process_gps_data(test_gga)
    
    if gps_data:
        print(f"GPS: {gps_data['latitude']:.6f}°, {gps_data['longitude']:.6f}°")
    
    # Test IMU với nhiễu
    for i in range(5):
        azimuth = 45.0 + np.random.normal(0, 2)
        elevation = 10.0 + np.random.normal(0, 1)
        
        filtered = fusion.process_imu_data(azimuth, elevation)
        print(f"  {i+1}: Raw({azimuth:.2f}°, {elevation:.2f}°) → "
              f"Filtered({filtered[0]:.2f}°, {filtered[1]:.2f}°)")
    
    # Test Range
    print("\nRange filtering (5 samples):")
    for i in range(5):
        distance = 1000.0 + np.random.normal(0, 5)
        filtered = fusion.process_range_data(distance)
        print(f"  {i+1}: Raw({distance:.2f}m) → Filtered({filtered:.2f}m)")
    
    print("\nTEST COMPLETED!")

if __name__ == "__main__":
    test_sensor_fusion()
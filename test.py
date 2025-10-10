"""
test
Script kiểm thử đơn giản cho GIAI ĐOẠN 1

Chạy: python test.py
"""

from main import Phase1Calculator
import sys


def test_basic_calculation():
    """Test tính toán cơ bản"""
    print("Test 1: Tính toán cơ bản")
    print("-" * 50)
    
    calc = Phase1Calculator()
    
    # Test case
    observer_lat = 10.762622
    observer_lon = 106.660172
    azimuth = 45.0
    distance = 1000.0
    
    try:
        result = calc.calculate_2d_target(
            observer_lat, observer_lon, azimuth, distance
        )
        
        print(f"Input: ({observer_lat}, {observer_lon}), Az={azimuth}°, Dist={distance}m")
        print(f"Output: ({result['latitude']:.6f}, {result['longitude']:.6f})")
        print(f"Error: {result['error']:.6f}m")
        
        if result['error'] < 0.1:
            print("PASS: Độ chính xác xuất sắc\n")
            return True
        else:
            print("WARNING: Sai số hơi lớn\n")
            return False
            
    except Exception as e:
        print(f"FAIL: {e}\n")
        return False


def test_four_directions():
    """Test 4 hướng chính"""
    print("Test 2: 4 hướng chính (N, E, S, W)")
    print("-" * 50)
    
    calc = Phase1Calculator()
    observer_lat = 10.762622
    observer_lon = 106.660172
    distance = 1000.0
    
    directions = [
        (0, "Bắc (N)"),
        (90, "Đông (E)"),
        (180, "Nam (S)"),
        (270, "Tây (W)")
    ]
    
    all_pass = True
    
    for azimuth, name in directions:
        try:
            result = calc.calculate_2d_target(
                observer_lat, observer_lon, azimuth, distance
            )
            
            print(f"{name:12} → ({result['latitude']:.6f}°, {result['longitude']:.6f}°) | Error: {result['error']:.6f}m")
            
            if result['error'] > 0.1:
                all_pass = False
                
        except Exception as e:
            print(f"{name:12} → FAIL: {e}")
            all_pass = False
    
    if all_pass:
        print("PASS: Tất cả hướng đều chính xác\n")
    else:
        print("WARNING: Một số hướng có sai số lớn\n")
    
    return all_pass


def test_different_distances():
    """Test các khoảng cách khác nhau"""
    print("Test 3: Khoảng cách khác nhau")
    print("-" * 50)
    
    calc = Phase1Calculator()
    observer_lat = 10.762622
    observer_lon = 106.660172
    azimuth = 45.0
    
    distances = [500, 1000, 2000, 5000]
    all_pass = True
    
    for dist in distances:
        try:
            result = calc.calculate_2d_target(
                observer_lat, observer_lon, azimuth, dist
            )
            
            print(f"{dist:5}m → Error: {result['error']:.6f}m", end="")
            
            if result['error'] < 0.1:
                print("COMPLETED!")
            else:
                print("FAILED!")
                all_pass = False
                
        except Exception as e:
            print(f"{dist:5}m → FAIL: {e}")
            all_pass = False
    
    if all_pass:
        print("PASS: Tất cả khoảng cách đều OK\n")
    else:
        print("WARNING: Một số khoảng cách có sai số lớn\n")
    
    return all_pass


def test_imports():
    """Test imports"""
    print("Test 0: Kiểm tra imports")
    print("-" * 50)
    
    try:
        import numpy
        print(f"NumPy version: {numpy.__version__}")
    except ImportError:
        print("NumPy chưa cài đặt: pip install numpy")
        return False
    
    try:
        import matplotlib
        print(f"Matplotlib version: {matplotlib.__version__}")
    except ImportError:
        print("Matplotlib chưa cài đặt (optional): pip install matplotlib")
    
    try:
        from main import Phase1Calculator
        print("main.py import OK")
    except ImportError as e:
        print(f"Không import được main: {e}")
        return False
    
    try:
        from core.gps_target_system import GPSTargetSystem
        print("core modules import OK")
    except ImportError as e:
        print(f"Không import được core: {e}")
        return False
    
    print("PASS: Tất cả imports OK\n")
    return True


def main():
    """Chạy tất cả tests"""
    print("\n" + "=" * 60)
    print("KIỂM THỬ GIAI ĐOẠN 1")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test imports first
    results.append(("Imports", test_imports()))
    
    if not results[0][1]:
        print("\n" + "=" * 60)
        print("Imports thất bại. Fix trước khi tiếp tục.")
        print("=" * 60)
        sys.exit(1)
    
    # Run other tests
    results.append(("Basic Calculation", test_basic_calculation()))
    results.append(("Four Directions", test_four_directions()))
    results.append(("Different Distances", test_different_distances()))
    
    # Summary
    print("=" * 60)
    print("TÓM TẮT KẾT QUẢ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25} {status}")
    
    print("-" * 60)
    print(f"Kết quả: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TẤT CẢ TESTS ĐỀU PASS!")
        print("Hệ thống sẵn sàng cho Giai đoạn 1")
    else:
        print("\nMỘT SỐ TESTS FAIL")
        print("Xem chi tiết ở trên và fix lỗi")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
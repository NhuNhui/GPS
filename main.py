"""
main.py
Chương trình chính để demo tính năng của hệ thống

Chức năng:
- CLI tương tác
- Tính toán tọa độ mục tiêu
- Hiển thị kết quả trực quan trên bản đồ web
- Xuất kết quả dưới dạng GeoJSON

"""

from core.gps_target_system import GPSTargetSystem
from visualization.webmap_viewer import LeafletMapViewer
from pathlib import Path
import sys

class GPSTargetApp:
    """Application wrapper với error handling"""
    
    def __init__(self):
        self.system = GPSTargetSystem('ENU')
        self.viewer = LeafletMapViewer()
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def get_user_input(self):
        """Nhận input từ user với validation"""
        print("\n" + "="*60)
        print("GPS TARGET SYSTEM - CALCULATOR")
        print("="*60)
        
        try:
            print("\nOBSERVER POSITION (Vị trí quan sát)")
            print("-" * 60)
            obs_lat = float(input("  Vĩ độ (Latitude, độ):  "))
            obs_lon = float(input("  Kinh độ (Longitude, độ): "))
            obs_alt = float(input("  Độ cao (Altitude, mét):  "))
            
            print("\nTARGET INFORMATION (Thông tin ngắm mục tiêu)")
            print("-" * 60)
            azimuth = float(input("  Góc phương vị (Azimuth, 0-360°):   "))
            elevation = float(input("  Góc ngẩng (Elevation, -90 đến 90°): "))
            distance = float(input("  Khoảng cách (Distance, mét):      "))
            
            return obs_lat, obs_lon, obs_alt, azimuth, elevation, distance
        
        except ValueError as e:
            print(f"\nLỗi: Vui lòng nhập số hợp lệ!")
            return None
        except KeyboardInterrupt:
            print("\n\nĐã hủy!")
            sys.exit(0)
    
    def run_interactive(self):
        """Chạy chế độ interactive"""
        while True:
            # Get input
            inputs = self.get_user_input()
            if inputs is None:
                continue
            
            obs_lat, obs_lon, obs_alt, azimuth, elevation, distance = inputs
            
            # Validate
            try:
                self.system.validate_input_data(
                    obs_lat, obs_lon, obs_alt,
                    azimuth, elevation, distance
                )
            except ValueError as e:
                print(f"\nLỗi validation: {e}")
                continue
            
            # Calculate
            print("\nĐang tính toán...")
            try:
                result = self.system.calculate_target_position(
                    obs_lat, obs_lon, obs_alt,
                    azimuth, elevation, distance
                )
            except Exception as e:
                print(f"\nLỗi tính toán: {e}")
                continue
            
            # Display results
            self.display_results(result)
            
            # Create map
            observer_pos = (obs_lat, obs_lon, obs_alt)
            target = result['target_geodetic']
            target_pos = (target['latitude'], target['longitude'], target['altitude'])
            
            print("\nĐang tạo bản đồ...")
            map_path = self.viewer.create_interactive_map(
                observer_pos=observer_pos,
                target_pos=target_pos,
                title="GPS Target Calculation Result",
                save_path=self.output_dir / "result_map.html",
                auto_open=True
            )
            
            print(f"Bản đồ đã được lưu: {map_path}")
            
            # Ask to continue
            print("\n" + "="*60)
            choice = input("\nTiếp tục? (y/n): ").strip().lower()
            if choice != 'y':
                break
    
    def display_results(self, result):
        """Hiển thị kết quả đẹp"""
        print("\n" + "="*60)
        print("KẾT QUẢ TÍNH TOÁN")
        print("="*60)
        
        target = result['target_geodetic']
        verification = result['verification']
        
        print("\nTỌA ĐỘ MỤC TIÊU:")
        print(f"  Vĩ độ:   {target['latitude']:.6f}°")
        print(f"  Kinh độ: {target['longitude']:.6f}°")
        print(f"  Độ cao:  {target['altitude']:.1f}m")
        
        print("\nKIỂM TRA ĐỘ CHÍNH XÁC:")
        print(f"  Distance error:  {verification['distance_error']:.3f}m")
        print(f"  Azimuth error:   {verification['azimuth_error']:.4f}°")
        print(f"  Elevation error: {verification['elevation_error']:.4f}°")
        
        if verification['distance_error'] < 0.1:
            print("\nĐộ chính xác: EXCELLENT")
        elif verification['distance_error'] < 1.0:
            print("\nĐộ chính xác: GOOD")
        else:
            print("\nĐộ chính xác: ACCEPTABLE")

def run_demo():
    """Demo mode với dữ liệu mẫu"""
    print("\n" + "="*60)
    print("DEMO MODE - GPS TARGET SYSTEM")
    print("="*60)
    
    app = GPSTargetApp()
    
    # Demo data (HCMUT area)
    print("\nSử dụng dữ liệu demo:")
    observer_pos = (10.762622, 106.660172, 10.0)
    azimuth = 45.0
    elevation = 30.0
    distance = 1000.0
    
    print(f"  Observer: {observer_pos[0]:.6f}°, {observer_pos[1]:.6f}°, {observer_pos[2]}m")
    print(f"  Azimuth: {azimuth}°")
    print(f"  Elevation: {elevation}°")
    print(f"  Distance: {distance}m")
    
    # Calculate
    result = app.system.calculate_target_position(
        observer_pos[0], observer_pos[1], observer_pos[2],
        azimuth, elevation, distance
    )
    
    # Display
    app.display_results(result)
    
    # Create map
    target = result['target_geodetic']
    target_pos = (target['latitude'], target['longitude'], target['altitude'])
    
    print("\nĐang tạo bản đồ...")
    app.viewer.create_interactive_map(
        observer_pos=observer_pos,
        target_pos=target_pos,
        title="GPS Target System - Demo",
        save_path=app.output_dir / "demo_map.html",
        auto_open=True
    )
    
    print("\nDemo hoàn tất!")


def run_batch_mode():
    """Batch mode - tính nhiều targets"""
    print("\n" + "="*60)
    print("BATCH MODE - MULTIPLE TARGETS")
    print("="*60)
    
    app = GPSTargetApp()
    
    # Observer
    observer_pos = (10.762622, 106.660172, 10.0)
    print(f"\nObserver: {observer_pos[0]:.6f}°, {observer_pos[1]:.6f}°")
    
    # Multiple targets
    target_specs = [
        (0, 0, 1000, "North, 1km"),
        (45, 10, 1500, "NE, 1.5km, 10° up"),
        (90, 0, 2000, "East, 2km"),
        (180, -5, 1200, "South, 1.2km, 5° down"),
    ]
    
    print(f"\nCalculating {len(target_specs)} targets...")
    
    targets = []
    for i, (az, el, dist, desc) in enumerate(target_specs, 1):
        result = app.system.calculate_target_position(
            observer_pos[0], observer_pos[1], observer_pos[2],
            az, el, dist
        )
        
        target = result['target_geodetic']
        targets.append((
            target['latitude'],
            target['longitude'],
            target['altitude'],
            f"T{i}: {desc}"
        ))
        
        print(f"Target {i}: {target['latitude']:.6f}°, {target['longitude']:.6f}°")
    
    # Create multi-target map
    print("\nCreating multi-target map...")
    app.viewer.create_multi_target_map(
        observer_pos=observer_pos,
        targets=targets,
        title="Batch Mode - Multiple Targets",
        save_path=app.output_dir / "batch_map.html",
        auto_open=True
    )
    
    print("\nBatch processing complete!")

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print(" "*10 + "GPS TARGET SYSTEM")
    print(" "*5 + "Tính toán tọa độ mục tiêu từ GPS + góc ngắm + khoảng cách")
    print("="*60)
    
    print("\nChọn chế độ:")
    print("  1. Interactive Mode (Nhập tay)")
    print("  2. Demo Mode (Dữ liệu mẫu)")
    print("  3. Batch Mode (Nhiều mục tiêu)")
    print("  4. Exit")
    
    try:
        choice = input("\nLựa chọn (1-4): ").strip()
        
        if choice == '1':
            app = GPSTargetApp()
            app.run_interactive()
        elif choice == '2':
            run_demo()
        elif choice == '3':
            run_batch_mode()
        elif choice == '4':
            print("\nExit!")
        else:
            print("\nLựa chọn không hợp lệ!")
    
    except KeyboardInterrupt:
        print("\n\nĐã hủy!")
    except Exception as e:
        print(f"\nLỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
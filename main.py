"""
main.py - GIAI ĐOẠN 1 (ĐA KTMT)
Bài toán chỉ tập trung vào yêu cầu Giai đoạn 1:
- Tính toán 2D cơ bản (azimuth + distance)
- Bản đồ đơn giản với matplotlib

"""

from core.gps_target_system import GPSTargetSystem
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class Phase1Calculator:
    """
    Calculator đơn giản cho GIAI ĐOẠN 1
    Chỉ tính toán 2D, không dùng elevation angle
    """
    
    def __init__(self):
        self.system = GPSTargetSystem('ENU')
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def calculate_2d_target(self, observer_lat, observer_lon, 
                           azimuth, distance):
        """
        Tính toán 2D - KHÔNG dùng elevation angle
        
        Input:
            observer_lat: Vĩ độ người quan sát (độ)
            observer_lon: Kinh độ người quan sát (độ)
            azimuth: Góc phương vị (độ, 0-360)
            distance: Khoảng cách (mét)
            
        Output:
            dict: Tọa độ mục tiêu 2D
        """
        # GIAI ĐOẠN 1: Giả sử quan sát ngang (elevation = 0)
        # GIAI ĐOẠN 2: Sẽ thêm elevation angle thực
        
        observer_alt = 0.0  # Đơn giản hóa: không tính cao độ
        elevation = 0.0     # Ngang tầm
        
        # Sử dụng core system (đã fix)
        result = self.system.calculate_target_position(
            observer_lat, observer_lon, observer_alt,
            azimuth, elevation, distance
        )
        
        # Trả về chỉ tọa độ 2D (lat, lon)
        target = result['target_geodetic']
        
        return {
            'latitude': target['latitude'],
            'longitude': target['longitude'],
            'distance': distance,
            'azimuth': azimuth,
            'error': result['verification']['distance_error']
        }
    
    def plot_simple_map(self, observer_pos, target_pos, save_path=None):
        """
        Vẽ bản đồ 2D đơn giản với matplotlib (Giai đoạn 1)
        
        Input:
            observer_pos: tuple (lat, lon)
            target_pos: tuple (lat, lon)
            save_path: Đường dẫn lưu (optional)
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Chuyển sang offset (km) để dễ nhìn
        obs_lat, obs_lon = observer_pos
        tar_lat, tar_lon = target_pos
        
        # East-West offset (km)
        dx = (tar_lon - obs_lon) * 111 * np.cos(np.radians(obs_lat))
        # North-South offset (km)
        dy = (tar_lat - obs_lat) * 111
        
        # Plot observer
        ax.plot(0, 0, 'go', markersize=15, label='Người quan sát')
        ax.text(0, -0.05, 'Observer', ha='center', fontsize=10, fontweight='bold')
        
        # Plot target
        ax.plot(dx, dy, 'ro', markersize=15, label='Mục tiêu')
        ax.text(dx, dy + 0.05, 'Target', ha='center', fontsize=10, fontweight='bold')
        
        # Draw line
        ax.plot([0, dx], [0, dy], 'k--', linewidth=2, alpha=0.5)
        
        # Calculate distance
        distance = np.sqrt(dx**2 + dy**2)
        mid_x, mid_y = dx/2, dy/2
        ax.text(mid_x, mid_y, f'{distance:.2f} km', 
               fontsize=12, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
        
        # North arrow
        ax.arrow(0, 0, 0, 0.5, head_width=0.1, head_length=0.08, 
                fc='blue', ec='blue', linewidth=2)
        ax.text(0, 0.6, 'N', ha='center', fontsize=14, fontweight='bold', color='blue')
        
        # Styling
        ax.set_xlabel('East-West (km)', fontsize=12)
        ax.set_ylabel('North-South (km)', fontsize=12)
        ax.set_title('Bản đồ vị trí mục tiêu (2D)\nGIAI ĐOẠN 1 - ĐA KTMT', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axis('equal')
        ax.legend(loc='upper right', fontsize=10)
        
        # Add coordinates text
        info_text = f'Observer: ({obs_lat:.6f}°, {obs_lon:.6f}°)\n'
        info_text += f'Target: ({tar_lat:.6f}°, {tar_lon:.6f}°)'
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✓ Đã lưu bản đồ: {save_path}")
        
        return fig, ax


def run_phase1_demo():
    """Demo cho GIAI ĐOẠN 1"""
    print("\n" + "="*60)
    print("GIAI ĐOẠN 1 - ĐỒ ÁN KỸ THUẬT MÁY TÍNH")
    print("Tính toán tọa độ mục tiêu 2D")
    print("="*60)
    
    calc = Phase1Calculator()
    
    # Dữ liệu test
    print("\nDỮ LIỆU ĐẦU VÀO:")
    observer_lat = 10.762622   # HCMUT
    observer_lon = 106.660172
    azimuth = 45.0            # Đông Bắc
    distance = 1000.0         # 1km
    
    print(f"  Vị trí quan sát: {observer_lat:.6f}°, {observer_lon:.6f}°")
    print(f"  Góc phương vị: {azimuth}°")
    print(f"  Khoảng cách: {distance}m")
    
    # Tính toán
    print("\nĐang tính toán...")
    result = calc.calculate_2d_target(
        observer_lat, observer_lon, azimuth, distance
    )
    
    # Hiển thị kết quả
    print("\n" + "="*60)
    print("KẾT QUẢ TÍNH TOÁN")
    print("="*60)
    print(f"\nTỌA ĐỘ MỤC TIÊU (2D):")
    print(f"  Vĩ độ:  {result['latitude']:.6f}°")
    print(f"  Kinh độ: {result['longitude']:.6f}°")
    print(f"\nĐộ chính xác:")
    print(f"  Sai số: {result['error']:.3f}m")
    
    if result['error'] < 0.1:
        print("Độ chính xác: XUẤT SẮC")
    elif result['error'] < 1.0:
        print("Độ chính xác: TỐT")
    else:
        print("Độ chính xác: CHẤP NHẬN ĐƯỢC")
    
    # Vẽ bản đồ
    print("\nĐang tạo bản đồ 2D...")
    calc.plot_simple_map(
        observer_pos=(observer_lat, observer_lon),
        target_pos=(result['latitude'], result['longitude']),
        save_path="output/phase1_map.png"
    )
    
    plt.show()

    print("\nKết quả đã lưu:")
    print("  - Bản đồ 2D: output/phase1_map.png")


def run_phase1_interactive():
    """Chế độ nhập liệu cho Giai đoạn 1"""
    print("\n" + "="*60)
    print("GIAI ĐOẠN 1 - TÍNH TOÁN TỌA ĐỘ 2D")
    print("="*60)
    
    calc = Phase1Calculator()
    
    try:
        print("\nNHẬP VỊ TRÍ QUAN SÁT:")
        obs_lat = float(input("  Vĩ độ (độ): "))
        obs_lon = float(input("  Kinh độ (độ): "))
        
        print("\nNHẬP THÔNG TIN NGẮM:")
        azimuth = float(input("  Góc phương vị (0-360°): "))
        distance = float(input("  Khoảng cách (mét): "))
        
        # Validate
        if not (0 <= azimuth < 360):
            print("Góc phương vị phải trong khoảng [0, 360)")
            return
        
        if distance <= 0:
            print("Khoảng cách phải > 0")
            return
        
        # Calculate
        print("\nĐang tính toán...")
        result = calc.calculate_2d_target(obs_lat, obs_lon, azimuth, distance)
        
        # Display
        print("\n" + "="*60)
        print("KẾT QUẢ")
        print("="*60)
        print(f"\nTọa độ mục tiêu:")
        print(f"  Vĩ độ:  {result['latitude']:.6f}°")
        print(f"  Kinh độ: {result['longitude']:.6f}°")
        print(f"\nSai số: {result['error']:.3f}m")
        
        # Plot
        choice = input("\nVẽ bản đồ? (y/n): ").lower()
        if choice == 'y':
            calc.plot_simple_map(
                (obs_lat, obs_lon),
                (result['latitude'], result['longitude']),
                "output/phase1_custom.png"
            )
            plt.show()
    
    except ValueError:
        print("\nLỗi: Vui lòng nhập số hợp lệ!")
    except Exception as e:
        print(f"\nLỗi: {e}")


def main():
    """Main menu cho Giai đoạn 1"""
    print("\n" + "="*60)
    print("     GIAI ĐOẠN 1 - ĐỒ ÁN KỸ THUẬT MÁY TÍNH")
    print("     Tính toán tọa độ mục tiêu 2D")
    print("="*60)
    
    print("\nChọn chế độ:")
    print("  1. Demo (dữ liệu mẫu)")
    print("  2. Interactive (nhập liệu)")
    print("  3. Exit")
    
    choice = input("\nLựa chọn (1-3): ").strip()
    
    if choice == '1':
        run_phase1_demo()
    elif choice == '2':
        run_phase1_interactive()
    elif choice == '3':
        print("\nExit!")
    else:
        print("\nLựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
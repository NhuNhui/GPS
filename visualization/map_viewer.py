"""
map_viewer.py
Module hiển thị kết quả trên bản đồ 2D

Chức năng:
- Vẽ bản đồ với observer và targets
- Hiển thị sai số bằng màu sắc
- Vẽ vector hướng (azimuth)
- Xuất hình ảnh bản đồ
- Sử dụng matplotlib cho visualization 2D

"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Circle
import numpy as np
from pathlib import Path


class MapViewer:
    """
    Lớp hiển thị bản đồ 2D với matplotlib
    """
    
    def __init__(self, figsize=(12, 10)):
        """
        Initialize map viewer
        
        Args:
            figsize: Kích thước figure (width, height)
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None
    
    def plot_scenario_results(self, scenario, results, show_errors=True):
        """
        Vẽ kịch bản và kết quả mô phỏng
        
        Args:
            scenario: dict kịch bản
            results: list SimulationResult
            show_errors: Hiển thị sai số hay không
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        
        # Observer position
        observer = scenario['observer']
        obs_lat = observer['latitude']
        obs_lon = observer['longitude']
        
        # Chuyển đổi tọa độ sang offset (km) từ observer để dễ nhìn
        def geodetic_to_xy(lat, lon):
            """Chuyển lat/lon sang tọa độ XY (km) relative to observer"""
            # 1 degree lat ≈ 111 km
            # 1 degree lon ≈ 111 km * cos(lat)
            x = (lon - obs_lon) * 111 * np.cos(np.radians(obs_lat))
            y = (lat - obs_lat) * 111
            return x, y
        
        # Vẽ observer
        self.ax.plot(0, 0, 'bs', markersize=15, label='Observer', zorder=10)
        self.ax.text(0, -0.05, observer['location_name'], 
                    ha='center', va='top', fontsize=10, fontweight='bold')
        
        # Vẽ compass rose (hướng Bắc)
        arrow_length = 0.5
        self.ax.arrow(0, 0, 0, arrow_length, head_width=0.15, 
                     head_length=0.1, fc='blue', ec='blue', alpha=0.5)
        self.ax.text(0, arrow_length + 0.2, 'N', ha='center', 
                    fontsize=14, fontweight='bold', color='blue')
        
        # Vẽ từng target
        for result in results:
            gt = result.ground_truth
            calc = result.calculated_position['target_geodetic']
            
            # Ground truth position
            gt_x, gt_y = geodetic_to_xy(gt['true_latitude'], gt['true_longitude'])
            
            # Calculated position
            calc_x, calc_y = geodetic_to_xy(calc['latitude'], calc['longitude'])
            
            # Màu sắc dựa trên sai số
            error = result.errors['horizontal_error_m']
            if error < 10:
                color = 'green'
            elif error < 50:
                color = 'orange'
            else:
                color = 'red'
            
            # Vẽ ground truth (hình tròn)
            self.ax.plot(gt_x, gt_y, 'go', markersize=10, 
                        label='Ground Truth' if result == results[0] else '', 
                        zorder=8)
            
            # Vẽ calculated position (dấu x)
            self.ax.plot(calc_x, calc_y, marker='x', color=color, 
                        markersize=12, markeredgewidth=3,
                        label='Calculated' if result == results[0] else '', 
                        zorder=9)
            
            # Vẽ đường nối giữa ground truth và calculated
            if show_errors:
                self.ax.plot([gt_x, calc_x], [gt_y, calc_y], 
                           color=color, linestyle='--', linewidth=1.5, 
                           alpha=0.6, zorder=5)
            
            # Vẽ vector hướng từ observer đến ground truth
            arrow = FancyArrowPatch((0, 0), (gt_x, gt_y),
                                   arrowstyle='->', mutation_scale=20,
                                   linewidth=1, color='gray', alpha=0.4,
                                   zorder=3)
            self.ax.add_patch(arrow)
            
            # Label target
            self.ax.text(gt_x, gt_y + 0.1, result.target_id, 
                        ha='center', va='bottom', fontsize=8)
            
            # Hiển thị sai số
            if show_errors:
                self.ax.text(calc_x + 0.1, calc_y, 
                           f'{error:.1f}m', 
                           fontsize=8, color=color, 
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='white', alpha=0.7))
        
        # Vẽ vòng tròn khoảng cách
        distances = [1, 2, 3, 4, 5]  # km
        for dist in distances:
            circle = Circle((0, 0), dist, fill=False, 
                          edgecolor='lightgray', linestyle=':', 
                          linewidth=1, alpha=0.5, zorder=1)
            self.ax.add_patch(circle)
            self.ax.text(0, dist, f'{dist}km', 
                        ha='center', va='bottom', 
                        fontsize=8, color='gray', alpha=0.7)
        
        # Cài đặt axes
        self.ax.set_xlabel('East-West Distance (km)', fontsize=12)
        self.ax.set_ylabel('North-South Distance (km)', fontsize=12)
        self.ax.set_title(f'Target Positioning Simulation\n{scenario["scenario_id"]}', 
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.axis('equal')
        self.ax.legend(loc='upper right', fontsize=10)
        
        plt.tight_layout()
    
    def plot_error_distribution(self, results):
        """
        Vẽ phân bố sai số
        
        Args:
            results: list SimulationResult
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Thu thập dữ liệu
        horizontal_errors = [r.errors['horizontal_error_m'] for r in results]
        error_3d = [r.errors['total_error_3d_m'] for r in results]
        azimuth_errors = [r.errors['azimuth_error_deg'] for r in results]
        elevation_errors = [r.errors['elevation_error_deg'] for r in results]
        
        # Plot 1: Horizontal error histogram
        axes[0, 0].hist(horizontal_errors, bins=10, color='skyblue', 
                       edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(np.mean(horizontal_errors), color='red', 
                          linestyle='--', linewidth=2, label='Mean')
        axes[0, 0].axvline(np.median(horizontal_errors), color='green', 
                          linestyle='--', linewidth=2, label='Median')
        axes[0, 0].set_xlabel('Horizontal Error (m)', fontsize=11)
        axes[0, 0].set_ylabel('Frequency', fontsize=11)
        axes[0, 0].set_title('Horizontal Error Distribution', fontsize=12, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: 3D error histogram
        axes[0, 1].hist(error_3d, bins=10, color='lightcoral', 
                       edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(np.mean(error_3d), color='red', 
                          linestyle='--', linewidth=2, label='Mean')
        axes[0, 1].axvline(np.median(error_3d), color='green', 
                          linestyle='--', linewidth=2, label='Median')
        axes[0, 1].set_xlabel('3D Error (m)', fontsize=11)
        axes[0, 1].set_ylabel('Frequency', fontsize=11)
        axes[0, 1].set_title('3D Error Distribution', fontsize=12, fontweight='bold')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Azimuth error
        axes[1, 0].hist(azimuth_errors, bins=10, color='lightgreen', 
                       edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(np.mean(azimuth_errors), color='red', 
                          linestyle='--', linewidth=2, label='Mean')
        axes[1, 0].set_xlabel('Azimuth Error (°)', fontsize=11)
        axes[1, 0].set_ylabel('Frequency', fontsize=11)
        axes[1, 0].set_title('Azimuth Error Distribution', fontsize=12, fontweight='bold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Elevation error
        axes[1, 1].hist(elevation_errors, bins=10, color='lightyellow', 
                       edgecolor='black', alpha=0.7)
        axes[1, 1].axvline(np.mean(elevation_errors), color='red', 
                          linestyle='--', linewidth=2, label='Mean')
        axes[1, 1].set_xlabel('Elevation Error (°)', fontsize=11)
        axes[1, 1].set_ylabel('Frequency', fontsize=11)
        axes[1, 1].set_title('Elevation Error Distribution', fontsize=12, fontweight='bold')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.fig = fig
    
    def save_figure(self, filepath):
        """
        Lưu hình ảnh
        
        Args:
            filepath: Đường dẫn file output
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if self.fig:
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Figure saved to: {filepath}")
        else:
            print("No figure to save")
    
    def show(self):
        """Hiển thị figure"""
        plt.show()


def test_map_viewer():
    """Test map viewer"""
    import sys
    sys.path.append('..')
    from simulation.scenario_generator import ScenarioGenerator
    from simulation.simulator import Simulator
    
    print("=== TEST MAP VIEWER ===\n")
    
    # Tạo kịch bản
    generator = ScenarioGenerator(seed=42)
    observer = generator.create_observer_position()
    scenario = generator.create_scenario(observer, num_targets=8, add_noise=True)
    
    # Chạy mô phỏng
    simulator = Simulator(coordinate_system='ENU')
    results = simulator.run_scenario(scenario, use_sensor_fusion=True)
    
    # Vẽ bản đồ
    viewer = MapViewer()
    viewer.plot_scenario_results(scenario, results, show_errors=True)
    viewer.save_figure('data/scenario_map.png')
    
    # Vẽ phân bố sai số
    viewer.plot_error_distribution(results)
    viewer.save_figure('data/error_distribution.png')
    
    viewer.show()
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    test_map_viewer()
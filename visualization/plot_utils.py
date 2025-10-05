"""
plot_utils.py
Module hiển thị kết quả tính toán trên bản đồ và đồ thị

Chức năng:
- Vẽ bản đồ 2D với vị trí quan sát và mục tiêu
- Vẽ đường ngắm và vector định hướng
- Hiển thị thông tin tọa độ và khoảng cách

"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

class MapVisualizer:
    """
    Lớp hiển thị kết quả trên bản đồ
    """
    
    def __init__(self, figsize=(10, 8)):
        """
        Khởi tạo visualizer với kích thước figure
        
        Input:
            figsize: Tuple (width, height) kích thước figure
        """
        self.figsize = figsize
        
    def plot_target_scenario(self, observer_pos, target_pos, show_grid=True):
        """
        Vẽ kịch bản với vị trí quan sát và mục tiêu
        
        Input:
            observer_pos: tuple (lat, lon, alt) vị trí quan sát
            target_pos: tuple (lat, lon, alt) vị trí mục tiêu
            show_grid: bool - hiển thị lưới tọa độ
        """
        # Tạo figure với hệ tọa độ PlateCarree
        fig = plt.figure(figsize=self.figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Thêm các feature của bản đồ
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        if show_grid:
            ax.gridlines(draw_labels=True)
            
        # Plot vị trí quan sát
        ax.plot(observer_pos[1], observer_pos[0], 'go', 
                markersize=10, label='Observer')
                
        # Plot vị trí mục tiêu
        ax.plot(target_pos[1], target_pos[0], 'ro',
                markersize=10, label='Target')
                
        # Vẽ đường nối
        ax.plot([observer_pos[1], target_pos[1]],
                [observer_pos[0], target_pos[0]], 
                'k--', alpha=0.5)
                
        # Tính và hiển thị khoảng cách
        distance = self._calculate_distance(observer_pos, target_pos)
        midpoint = [(observer_pos[0] + target_pos[0])/2,
                   (observer_pos[1] + target_pos[1])/2]
        plt.annotate(f'{distance:.1f} km',
                    xy=(midpoint[1], midpoint[0]),
                    xytext=(5, 5), textcoords='offset points')
                    
        # Thêm chú thích
        ax.legend()
        
        # Điều chỉnh view để hiển thị cả hai điểm
        self._adjust_map_view(observer_pos, target_pos, ax)
        
        return fig, ax
        
    def _calculate_distance(self, pos1, pos2):
        """
        Tính khoảng cách giữa hai điểm (km)
        """
        # Đây là tính gần đúng, trong thực tế nên dùng công thức Haversine
        R = 6371  # Bán kính Trái Đất (km)
        lat1, lon1 = np.radians(pos1[0]), np.radians(pos1[1])
        lat2, lon2 = np.radians(pos2[0]), np.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
        
    def _adjust_map_view(self, pos1, pos2, ax, margin=0.1):
        """
        Điều chỉnh view của bản đồ để hiển thị cả hai điểm
        """
        min_lat = min(pos1[0], pos2[0])
        max_lat = max(pos1[0], pos2[0])
        min_lon = min(pos1[1], pos2[1])
        max_lon = max(pos1[1], pos2[1])
        
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        
        # Thêm margin
        min_lat -= lat_range * margin
        max_lat += lat_range * margin
        min_lon -= lon_range * margin
        max_lon += lon_range * margin
        
        # Set limits
        ax.set_extent([min_lon, max_lon, min_lat, max_lat])
        
    def plot_elevation_profile(self, observer_pos, target_pos):
        """
        Vẽ profile độ cao giữa quan sát viên và mục tiêu
        
        Input:
            observer_pos: tuple (lat, lon, alt) vị trí quan sát
            target_pos: tuple (lat, lon, alt) vị trí mục tiêu
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Tạo trục khoảng cách
        distance = self._calculate_distance(observer_pos, target_pos)
        x = np.linspace(0, distance, 100)
        
        # Tính độ cao tại mỗi điểm (đường thẳng)
        alt1, alt2 = observer_pos[2]/1000, target_pos[2]/1000  # chuyển sang km
        y = np.linspace(alt1, alt2, 100)
        
        # Vẽ profile
        ax.plot(x, y, 'b-')
        ax.plot([0], [alt1], 'go', label='Observer')
        ax.plot([distance], [alt2], 'ro', label='Target')
        
        # Trang trí đồ thị
        ax.set_xlabel('Distance (km)')
        ax.set_ylabel('Altitude (km)')
        ax.grid(True)
        ax.legend()
        
        return fig, ax
"""
webmap_viewer.py
Module hiển thị kết quả tính toán trên bản đồ web sử dụng Folium

Chức năng:
- Hiển thị vị trí quan sát và mục tiêu trên bản đồ web
- Vẽ đường ngắm và vector định hướng
- Export sang HTML để chia sẻ

"""

import folium
from folium import plugins
import math
import webbrowser
import os
from pathlib import Path

class WebMapViewer:
    """
    Lớp hiển thị kết quả trên bản đồ web
    """
    
    def __init__(self, tiles="OpenStreetMap"):
        """
        Khởi tạo viewer với loại bản đồ nền
        
        Input:
            tiles: Loại bản đồ nền, có thể là:
                - "OpenStreetMap"
                - "Stamen Terrain"
                - "CartoDB positron"
        """
        self.tiles = tiles
        self.maps = {}  # Lưu trữ các map object
        
    def create_map(self, center_lat, center_lon, zoom_start=13):
        """
        Tạo map mới với tâm và mức zoom cho trước
        
        Input:
            center_lat: Vĩ độ tâm bản đồ
            center_lon: Kinh độ tâm bản đồ
            zoom_start: Mức zoom ban đầu (1-18)
        """
        return folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles=self.tiles
        )
        
    def plot_target_scenario(self, observer_pos, target_pos, 
                           map_id="default", show=True, save_path=None):
        """
        Vẽ kịch bản với vị trí quan sát và mục tiêu
        
        Input:
            observer_pos: tuple (lat, lon, alt) vị trí quan sát
            target_pos: tuple (lat, lon, alt) vị trí mục tiêu
            map_id: ID của map để quản lý nhiều map
            show: Có mở trình duyệt để xem không
            save_path: Đường dẫn để lưu file HTML
            
        Return:
            folium.Map object
        """
        # Tính tâm bản đồ
        center_lat = (observer_pos[0] + target_pos[0]) / 2
        center_lon = (observer_pos[1] + target_pos[1]) / 2
        
        # Tạo map mới
        m = self.create_map(center_lat, center_lon)
        self.maps[map_id] = m
        
        # Tạo HTML cho popup người quan sát
        observer_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: green;">Observer Position</h4>
            <table>
                <tr><td><b>Latitude:</b></td><td>{observer_pos[0]:.6f}°</td></tr>
                <tr><td><b>Longitude:</b></td><td>{observer_pos[1]:.6f}°</td></tr>
                <tr><td><b>Altitude:</b></td><td>{observer_pos[2]:.1f} m</td></tr>
            </table>
        </div>
        """
        
        # Tạo HTML cho popup mục tiêu
        bearing = self._calculate_bearing(observer_pos, target_pos)
        distance = self._calculate_distance(observer_pos, target_pos)
        elevation = self._calculate_elevation_angle(observer_pos, target_pos)
        
        target_html = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: red;">Target Position</h4>
            <table>
                <tr><td><b>Latitude:</b></td><td>{target_pos[0]:.6f}°</td></tr>
                <tr><td><b>Longitude:</b></td><td>{target_pos[1]:.6f}°</td></tr>
                <tr><td><b>Altitude:</b></td><td>{target_pos[2]:.1f} m</td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td><b>Distance:</b></td><td>{distance:.1f} km</td></tr>
                <tr><td><b>Bearing:</b></td><td>{bearing:.1f}°</td></tr>
                <tr><td><b>Elevation:</b></td><td>{elevation:.1f}°</td></tr>
            </table>
        </div>
        """
        
        # Thêm marker cho người quan sát với popup đã cải tiến
        folium.Marker(
            location=[observer_pos[0], observer_pos[1]],
            popup=folium.Popup(observer_html, max_width=300),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        
        # Thêm marker cho mục tiêu với popup đã cải tiến
        folium.Marker(
            location=[target_pos[0], target_pos[1]],
            popup=folium.Popup(target_html, max_width=300),
            icon=folium.Icon(color='red', icon='crosshairs')
        ).add_to(m)
        
        # Vẽ đường nối
        folium.PolyLine(
            locations=[[observer_pos[0], observer_pos[1]], 
                      [target_pos[0], target_pos[1]]],
            weight=2,
            color='black',
            opacity=0.8,
            dash_array='5'
        ).add_to(m)
        
        # Tính và hiển thị khoảng cách
        distance = self._calculate_distance(observer_pos, target_pos)
        mid_point = [(observer_pos[0] + target_pos[0])/2,
                    (observer_pos[1] + target_pos[1])/2]
        folium.Popup(
            f"Distance: {distance:.1f} km",
            location=mid_point
        ).add_to(m)
        
        # Thêm mini map
        plugins.MiniMap().add_to(m)
        
        # Thêm layer control
        folium.LayerControl().add_to(m)
        
        # Lưu file nếu có yêu cầu
        if save_path:
            m.save(save_path)
            
        # Mở trình duyệt nếu có yêu cầu
        if show and save_path:
            webbrowser.open('file://' + os.path.abspath(save_path))
            
        return m
    
    def add_measurement_tools(self, map_id="default"):
        """Thêm công cụ đo đạc vào map"""
        if map_id in self.maps:
            plugins.MeasureControl(
                position='topright',
                primary_length_unit='kilometers',
                secondary_length_unit='miles',
                primary_area_unit='sqmeters',
                secondary_area_unit='acres'
            ).add_to(self.maps[map_id])
    
    def add_fullscreen_control(self, map_id="default"):
        """Thêm nút full screen vào map"""
        if map_id in self.maps:
            plugins.Fullscreen(
                position='topright'
            ).add_to(self.maps[map_id])
    
    def _calculate_distance(self, pos1, pos2):
        """
        Tính khoảng cách giữa hai điểm (km) using Haversine formula
        """
        R = 6371  # Bán kính Trái Đất (km)
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
        
    def _calculate_bearing(self, pos1, pos2):
        """
        Tính góc phương vị từ điểm 1 đến điểm 2 (độ)
        """
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.atan2(y, x)
        
        # Chuyển sang độ và chuẩn hóa
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
        
    def _calculate_elevation_angle(self, pos1, pos2):
        """
        Tính góc ngẩng từ điểm 1 đến điểm 2 (độ)
        """
        # Tính khoảng cách ngang
        dist_km = self._calculate_distance(pos1, pos2)
        dist_m = dist_km * 1000
        
        # Tính chênh lệch độ cao
        delta_h = pos2[2] - pos1[2]
        
        # Tính góc ngẩng
        elevation = math.degrees(math.atan2(delta_h, dist_m))
        
        return elevation
        
def test_webmap_viewer():
    """Test WebMapViewer với dữ liệu mẫu"""
    # Tạo thư mục output nếu chưa có
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Khởi tạo viewer
    viewer = WebMapViewer()
    
    # Dữ liệu test (khu vực TP.HCM)
    observer_pos = (10.762622, 106.660172, 10.0)  # Đại học Bách Khoa
    target_pos = (10.773456, 106.674512, 15.0)    # Công viên Tao Đàn
    
    # Tạo map và hiển thị
    viewer.plot_target_scenario(
        observer_pos=observer_pos,
        target_pos=target_pos,
        save_path="output/test_scenario.html"
    )
    
if __name__ == "__main__":
    test_webmap_viewer()
"""
webmap_viewer.py (NEW)
Web viewer sử dụng thuần Leaflet.js với giao diện responsive và interactive

Chức năng:
- Thiết kế responsive, có thể chạy trên mọi thiết bị
- Bản đồ tương tác với chức năng phóng to, thu nhỏ
- Tính toán khoảng cách/phương vị theo thời gian thực
- Giao diện người dùng đẹp mắt với các nút điều khiển

"""

import json
import math
import webbrowser
from pathlib import Path
from datetime import datetime


class LeafletMapViewer:
    """
    Web map viewer sử dụng Leaflet.js
    """
    
    def __init__(self):
        """Initialize viewer"""
        self.map_data = []
    
    def create_interactive_map(self, observer_pos, target_pos=None, 
                              title="GPS Target System", 
                              save_path="output/map.html",
                              auto_open=True):
        """
        Tạo bản đồ interactive với Leaflet.js
        
        Args:
            observer_pos: tuple (lat, lon, alt)
            target_pos: tuple (lat, lon, alt) hoặc None
            title: Tiêu đề bản đồ
            save_path: Đường dẫn lưu HTML
            auto_open: Tự động mở browser
        """
        # Tính toán dữ liệu
        if target_pos:
            distance = self._calculate_distance(observer_pos, target_pos)
            bearing = self._calculate_bearing(observer_pos, target_pos)
            elevation = self._calculate_elevation_angle(observer_pos, target_pos)
            center_lat = (observer_pos[0] + target_pos[0]) / 2
            center_lon = (observer_pos[1] + target_pos[1]) / 2
        else:
            distance = bearing = elevation = 0
            center_lat, center_lon = observer_pos[0], observer_pos[1]
        
        # Tạo HTML
        html = self._generate_html(
            observer_pos, target_pos, 
            center_lat, center_lon,
            distance, bearing, elevation,
            title
        )
        
        # Lưu file
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Map saved to: {save_path.absolute()}")
        
        # Mở browser
        if auto_open:
            webbrowser.open(f'file://{save_path.absolute()}')
        
        return str(save_path.absolute())
    
    def create_multi_target_map(self, observer_pos, targets, 
                               title="Multi-Target Scenario",
                               save_path="output/multi_target_map.html",
                               auto_open=True):
        """
        Tạo bản đồ với nhiều mục tiêu
        
        Args:
            observer_pos: tuple (lat, lon, alt)
            targets: list of tuples [(lat, lon, alt, name), ...]
            title: Tiêu đề
            save_path: Đường dẫn lưu
            auto_open: Tự động mở browser
        """
        html = self._generate_multi_target_html(
            observer_pos, targets, title
        )
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Multi-target map saved to: {save_path.absolute()}")
        
        if auto_open:
            webbrowser.open(f'file://{save_path.absolute()}')
        
        return str(save_path.absolute())
    
    def _generate_html(self, observer_pos, target_pos, 
                      center_lat, center_lon,
                      distance, bearing, elevation, title):
        """Generate HTML with embedded Leaflet.js"""
        
        observer_data = json.dumps({
            'lat': observer_pos[0],
            'lon': observer_pos[1],
            'alt': observer_pos[2]
        })
        
        target_data = json.dumps({
            'lat': target_pos[0] if target_pos else None,
            'lon': target_pos[1] if target_pos else None,
            'alt': target_pos[2] if target_pos else None
        }) if target_pos else 'null'
        
        html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        
        #map {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        
        .info-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
            z-index: 1000;
            min-width: 280px;
            max-width: 90%;
        }}
        
        .info-panel h2 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 18px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
        }}
        
        .info-item {{
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #34495e;
            margin-right: 10px;
        }}
        
        .info-value {{
            color: #7f8c8d;
            font-family: 'Courier New', monospace;
        }}
        
        .observer-badge {{
            background: #27ae60;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        
        .target-badge {{
            background: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        
        .metric-group {{
            background: #ecf0f1;
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        
        .metric-group h3 {{
            font-size: 14px;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        
        .timestamp {{
            text-align: center;
            color: #95a5a6;
            font-size: 11px;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #ecf0f1;
        }}
        
        @media (max-width: 768px) {{
            .info-panel {{
                top: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
                padding: 15px;
            }}
        }}
        
        /* Custom marker styles */
        .leaflet-popup-content-wrapper {{
            border-radius: 8px;
        }}
        
        .leaflet-popup-content {{
            margin: 15px;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h2>📍 Mission Data</h2>
        
        <div class="info-item">
            <span class="info-label">Observer:</span>
            <span class="observer-badge">ACTIVE</span>
        </div>
        <div class="info-item">
            <span class="info-label">Lat:</span>
            <span class="info-value">{observer_pos[0]:.6f}°</span>
        </div>
        <div class="info-item">
            <span class="info-label">Lon:</span>
            <span class="info-value">{observer_pos[1]:.6f}°</span>
        </div>
        <div class="info-item">
            <span class="info-label">Alt:</span>
            <span class="info-value">{observer_pos[2]:.1f}m</span>
        </div>
        
        {f'''
        <div class="metric-group">
            <h3>🎯 Target Information</h3>
            <div class="info-item">
                <span class="info-label">Distance:</span>
                <span class="info-value">{distance:.2f} km</span>
            </div>
            <div class="info-item">
                <span class="info-label">Bearing:</span>
                <span class="info-value">{bearing:.1f}°</span>
            </div>
            <div class="info-item">
                <span class="info-label">Elevation:</span>
                <span class="info-value">{elevation:.1f}°</span>
            </div>
        </div>
        ''' if target_pos else ''}
        
        <div class="timestamp">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <script>
        // Initialize map
        const map = L.map('map').setView([{center_lat}, {center_lon}], 13);
        
        // Add tile layer
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // Observer data
        const observer = {observer_data};
        
        // Observer marker
        const observerIcon = L.divIcon({{
            html: '<div style="background:#27ae60;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>',
            className: '',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        }});
        
        const observerMarker = L.marker([observer.lat, observer.lon], {{
            icon: observerIcon
        }}).addTo(map);
        
        observerMarker.bindPopup(`
            <div style="font-family:Arial;min-width:200px;">
                <h3 style="color:#27ae60;margin:0 0 10px 0;">👁️ Observer</h3>
                <table style="width:100%;font-size:12px;">
                    <tr><td><b>Latitude:</b></td><td>${{observer.lat.toFixed(6)}}°</td></tr>
                    <tr><td><b>Longitude:</b></td><td>${{observer.lon.toFixed(6)}}°</td></tr>
                    <tr><td><b>Altitude:</b></td><td>${{observer.alt.toFixed(1)}}m</td></tr>
                </table>
            </div>
        `);
        
        // Target marker (if exists)
        const target = {target_data};
        if (target) {{
            const targetIcon = L.divIcon({{
                html: '<div style="background:#e74c3c;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>',
                className: '',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            }});
            
            const targetMarker = L.marker([target.lat, target.lon], {{
                icon: targetIcon
            }}).addTo(map);
            
            targetMarker.bindPopup(`
                <div style="font-family:Arial;min-width:200px;">
                    <h3 style="color:#e74c3c;margin:0 0 10px 0;">🎯 Target</h3>
                    <table style="width:100%;font-size:12px;">
                        <tr><td><b>Latitude:</b></td><td>${{target.lat.toFixed(6)}}°</td></tr>
                        <tr><td><b>Longitude:</b></td><td>${{target.lon.toFixed(6)}}°</td></tr>
                        <tr><td><b>Altitude:</b></td><td>${{target.alt.toFixed(1)}}m</td></tr>
                        <tr><td colspan="2"><hr style="margin:5px 0;"></td></tr>
                        <tr><td><b>Distance:</b></td><td>{distance:.2f} km</td></tr>
                        <tr><td><b>Bearing:</b></td><td>{bearing:.1f}°</td></tr>
                        <tr><td><b>Elevation:</b></td><td>{elevation:.1f}°</td></tr>
                    </table>
                </div>
            `);
            
            // Draw line
            const line = L.polyline([
                [observer.lat, observer.lon],
                [target.lat, target.lon]
            ], {{
                color: '#3498db',
                weight: 2,
                opacity: 0.7,
                dashArray: '10, 5'
            }}).addTo(map);
            
            // Fit bounds
            map.fitBounds(line.getBounds(), {{padding: [50, 50]}});
        }}
        
        // Scale control
        L.control.scale({{imperial: false}}).addTo(map);
    </script>
</body>
</html>'''
        
        return html
    
    def _generate_multi_target_html(self, observer_pos, targets, title):
        """Generate HTML for multiple targets"""
        
        # Calculate center
        all_lats = [observer_pos[0]] + [t[0] for t in targets]
        all_lons = [observer_pos[1]] + [t[1] for t in targets]
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        # Prepare targets data
        targets_json = json.dumps([
            {
                'lat': t[0],
                'lon': t[1],
                'alt': t[2],
                'name': t[3] if len(t) > 3 else f'Target {i+1}',
                'distance': self._calculate_distance(observer_pos, t),
                'bearing': self._calculate_bearing(observer_pos, t),
                'elevation': self._calculate_elevation_angle(observer_pos, t)
            }
            for i, t in enumerate(targets)
        ])
        
        observer_json = json.dumps({
            'lat': observer_pos[0],
            'lon': observer_pos[1],
            'alt': observer_pos[2]
        })
        
        html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', sans-serif; overflow: hidden; }}
        #map {{ position: absolute; width: 100%; height: 100%; }}
        .info-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
            min-width: 280px;
        }}
        .info-panel h2 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 18px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
        }}
        .target-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .target-item:hover {{
            background: #e9ecef;
            transform: translateX(-2px);
        }}
        .target-name {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 5px;
        }}
        .target-stats {{
            font-size: 11px;
            color: #6c757d;
        }}
        @media (max-width: 768px) {{
            .info-panel {{
                top: 10px;
                right: 10px;
                left: 10px;
                max-height: 60vh;
            }}
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h2>📍 Multi-Target Mission</h2>
        <div style="margin-bottom:15px;font-size:12px;color:#7f8c8d;">
            Observer: {observer_pos[0]:.6f}°, {observer_pos[1]:.6f}°
        </div>
        <div id="targetList"></div>
    </div>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([{center_lat}, {center_lon}], 12);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);
        
        const observer = {observer_json};
        const targets = {targets_json};
        
        // Observer marker
        const observerIcon = L.divIcon({{
            html: '<div style="background:#27ae60;width:28px;height:28px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:14px;">O</div>',
            className: '',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        }});
        
        L.marker([observer.lat, observer.lon], {{icon: observerIcon}})
            .addTo(map)
            .bindPopup('<b>👁️ Observer</b><br>Base position');
        
        // Target markers
        const targetMarkers = [];
        const targetList = document.getElementById('targetList');
        
        targets.forEach((target, index) => {{
            const targetIcon = L.divIcon({{
                html: `<div style="background:#e74c3c;width:26px;height:26px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:11px;">${{index+1}}</div>`,
                className: '',
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            }});
            
            const marker = L.marker([target.lat, target.lon], {{icon: targetIcon}})
                .addTo(map)
                .bindPopup(`
                    <b>🎯 ${{target.name}}</b><br>
                    <small>
                    Lat: ${{target.lat.toFixed(6)}}°<br>
                    Lon: ${{target.lon.toFixed(6)}}°<br>
                    Alt: ${{target.alt.toFixed(1)}}m<br>
                    <hr style="margin:5px 0;">
                    Distance: ${{target.distance.toFixed(2)}} km<br>
                    Bearing: ${{target.bearing.toFixed(1)}}°<br>
                    Elevation: ${{target.elevation.toFixed(1)}}°
                    </small>
                `);
            
            targetMarkers.push(marker);
            
            // Line to target
            L.polyline([
                [observer.lat, observer.lon],
                [target.lat, target.lon]
            ], {{
                color: '#3498db',
                weight: 2,
                opacity: 0.5,
                dashArray: '5, 5'
            }}).addTo(map);
            
            // Add to list
            const item = document.createElement('div');
            item.className = 'target-item';
            item.innerHTML = `
                <div class="target-name">${{index+1}}. ${{target.name}}</div>
                <div class="target-stats">
                    📏 ${{target.distance.toFixed(2)}} km | 
                    🧭 ${{target.bearing.toFixed(1)}}° | 
                    📐 ${{target.elevation.toFixed(1)}}°
                </div>
            `;
            item.onclick = () => {{
                marker.openPopup();
                map.setView([target.lat, target.lon], 15);
            }};
            targetList.appendChild(item);
        }});
        
        // Fit all markers
        const group = L.featureGroup([
            L.marker([observer.lat, observer.lon]),
            ...targetMarkers
        ]);
        map.fitBounds(group.getBounds().pad(0.1));
        
        L.control.scale({{imperial: false}}).addTo(map);
    </script>
</body>
</html>'''
        
        return html
    
    def _calculate_distance(self, pos1, pos2):
        """Khoảng cách Haversine (km)"""
        R = 6371
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_bearing(self, pos1, pos2):
        """Calculate bearing (degrees)"""
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.atan2(y, x)
        
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _calculate_elevation_angle(self, pos1, pos2):
        """Calculate elevation angle (degrees)"""
        dist_km = self._calculate_distance(pos1, pos2)
        dist_m = dist_km * 1000
        
        delta_h = pos2[2] - pos1[2]
        
        if dist_m == 0:
            return 90 if delta_h > 0 else -90
        
        elevation = math.degrees(math.atan2(delta_h, dist_m))
        
        return elevation

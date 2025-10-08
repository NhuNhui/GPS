# GPS Target System - Hệ thống tính toán tọa độ mục tiêu

## Tổng quan

### Giới thiệu

Hệ thống GPS Target Calculator là một ứng dụng tính toán tọa độ mục tiêu dựa trên:
- **Vị trí người quan sát** từ GPS (vĩ độ, kinh độ, độ cao)
- **Góc ngắm** từ IMU/la bàn (azimuth - phương vị, elevation - ngẩng)
- **Khoảng cách** đến mục tiêu từ laser rangefinder

Hệ thống chuyển đổi các dữ liệu này thành **tọa độ địa lý chính xác** (latitude, longitude, altitude) của mục tiêu, có thể hiển thị trên bản đồ số.

### Điểm nổi bật

**Độ chính xác cao:** Error < 0.01m trong điều kiện lý tưởng  
**Hiệu suất tốt:** 2-5x nhanh hơn nhờ tối ưu với NumPy  
**Sensor Fusion:** Lọc nhiễu tự động từ GPS, IMU, Laser  
**Visualization:** Bản đồ web responsive, interactive với Leaflet.js  
**Đa hệ tọa độ:** Hỗ trợ ECEF, ENU, NED, Geodetic (WGS-84)  
**Export:** GeoJSON, JSON, HTML cho GIS tools

---

## Tính năng chính

### 1. Tính toán chính xác
- Chuyển đổi góc azimuth/elevation thành vector định hướng 3D
- Tính toán vị trí mục tiêu với độ chính xác cao
- Chuyển đổi giữa các hệ tọa độ: Geodetic ↔ ECEF ↔ ENU ↔ NED
- Hỗ trợ ellipsoid WGS-84 chuẩn quốc tế

### 2. Sensor Fusion (Lọc nhiễu)
- Lọc nhiễu GPS (moving average, weighted filter)
- Lọc nhiễu IMU (circular mean cho azimuth)
- Lọc nhiễu Laser (median filter, outlier detection)
- Đánh giá chất lượng dữ liệu tự động

### 3. Visualization
- **Bản đồ web interactive** (Leaflet.js):
   - Responsive design (mobile-friendly)
   - Click markers để xem thông tin
   - Zoom, pan, scale bar
   - Tự động tính distance/bearing/elevation

- **Matplotlib plots:**
   - Bản đồ 2D với observer và targets
   - Elevation profile
   - Error distribution charts

### 4. Multiple Modes
- **Interactive Mode:** Nhập dữ liệu từ bàn phím
- **Demo Mode:** Dữ liệu mẫu sẵn có
- **Batch Mode:** Xử lý nhiều targets cùng lúc

### 5. Export & Integration
- GeoJSON cho QGIS, ArcGIS
- HTML maps có thể share
- JSON results cho data analysis

## Yêu cầu hệ thống

### Python Environment
- Python 3.8 trở lên
- Các thư viện Python:
  ```
  numpy
  matplotlib
  ```

### Web Viewer (Leaflet.js)
- Trình duyệt web hiện đại (Chrome, Firefox, Safari, Edge)
- Kết nối internet (để tải tiles bản đồ OpenStreetMap)

## Hướng dẫn cài đặt

### Bước 1: Kiểm tra Python

```bash
python --version
```

Nếu chưa có Python, tải tại: https://www.python.org/downloads/

### Bước 2: Clone/Download project

**Option 1: Git clone**
```bash
git clone hhttps://github.com/NhuNhui/GPS.git
cd GPS
```

**Option 2: Download ZIP**
- Download file ZIP từ GitHub
- Giải nén vào thư mục bạn muốn

### Bước 3: Tạo Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 4: Cài đặt Dependencies

**Cài đặt cơ bản:**
```bash
pip install numpy
```

**Cài đặt đầy đủ (với visualization):**
```bash
pip install numpy matplotlib
```

**Hoặc dùng requirements.txt:**
```bash
pip install -r requirements.txt
```

---

## Hướng dẫn sử dụng

### Cách 1: Interactive Mode

#### Bước 1: Khởi chạy chương trình

```bash
python main.py
```

#### Bước 2: Chọn mode
```
         GPS TARGET SYSTEM
   Tính toán tọa độ mục tiêu từ GPS + góc ngắm + khoảng cách
============================================================

Chọn chế độ:
  1. Interactive Mode (Nhập tay)
  2. Demo Mode (Dữ liệu mẫu)
  3. Batch Mode (Nhiều mục tiêu)
  4. Exit

Lựa chọn (1-4): 1
```

#### Bước 3: Nhập dữ liệu Observer

```
📍 OBSERVER POSITION (Vị trí quan sát)
------------------------------------------------------------
  Vĩ độ (Latitude, độ):  10.762622
  Kinh độ (Longitude, độ): 106.660172
  Độ cao (Altitude, mét):  10
```

**Ghi chú:**
- Vĩ độ: -90 đến +90 (Bắc dương, Nam âm)
- Kinh độ: -180 đến +180 (Đông dương, Tây âm)
- Độ cao: tính từ mực nước biển (mét)

#### Bước 4: Nhập thông tin ngắm

```
🎯 TARGET INFORMATION (Thông tin ngắm mục tiêu)
------------------------------------------------------------
  Góc phương vị (Azimuth, 0-360°):   45
  Góc ngẩng (Elevation, -90 đến 90°): 30
  Khoảng cách (Distance, mét):      1000
```

**Ghi chú:**
- **Azimuth (Phương vị):**
  - 0° = Bắc (North)
  - 90° = Đông (East)
  - 180° = Nam (South)
  - 270° = Tây (West)
  
- **Elevation (Góc ngẩng):**
  - 0° = Ngang
  - +90° = Thẳng đứng lên
  - -90° = Thẳng đứng xuống
  
- **Distance:** Khoảng cách thẳng (line of sight) tính bằng mét

#### Bước 5: Xem kết quả

```
⏳ Đang tính toán...

============================================================
✅ KẾT QUẢ TÍNH TOÁN
============================================================

📍 TỌA ĐỘ MỤC TIÊU:
  Vĩ độ:   10.768123°
  Kinh độ: 106.665789°
  Độ cao:  510.0m

✓ KIỂM TRA ĐỘ CHÍNH XÁC:
  Distance error:  0.003m
  Azimuth error:   0.0001°
  Elevation error: 0.0001°
  
  ✅ Độ chính xác: EXCELLENT

🗺️  Đang tạo bản đồ...
✅ Bản đồ đã được lưu: output/result_map.html
```

#### Bước 6: Xem bản đồ

Browser sẽ tự động mở file `output/result_map.html` với:
- 🟢 Marker xanh: Vị trí quan sát
- 🔴 Marker đỏ: Mục tiêu
- ➖ Đường nét đứt: Line of sight
- 📊 Panel thông tin: Distance, bearing, elevation

**Tương tác với bản đồ:**
- Click markers để xem thông tin chi tiết
- Scroll để zoom in/out
- Drag để di chuyển bản đồ
- Scale bar hiển thị tỷ lệ

---

### Cách 2: Demo Mode (Nhanh nhất)

#### Chạy demo với dữ liệu mẫu:

```bash
python main.py
# Chọn: 2. Demo Mode
```

Demo sẽ tự động:
1. Sử dụng vị trí mặc định (HCMUT)
2. Tính toán mục tiêu mẫu
3. Hiển thị kết quả
4. Mở bản đồ web

**Dữ liệu demo:**
- Observer: Đại học Bách Khoa TP.HCM (10.762622°, 106.660172°)
- Azimuth: 45° (Đông Bắc)
- Elevation: 30° (Hướng lên)
- Distance: 1000m

---

### 📦 Cách 3: Batch Mode (Nhiều mục tiêu)

#### Xử lý nhiều targets cùng lúc:

```bash
python main.py
# Chọn: 3. Batch Mode
```

Batch mode sẽ:
1. Tính toán 4 targets ở các hướng khác nhau
2. Tạo bản đồ với tất cả targets
3. Hiển thị thông tin từng target

**Use case:** Khi cần survey nhiều điểm trong khu vực

---

### Cách 4: Chạy từng module riêng lẻ

**Test coordinate transforms:**
```bash
python file_to_test/coordinate_transforms.py
```

**Test sensor fusion:**
```bash
python file_to_test/sensor_fusion.py
```

**Test target calculator:**
```bash
python file_to_test/target_calculator.py
```

**Test webmap viewer:**
```bash
python file_to_test/webmap_viewer.py
```

---

### Module Descriptions

#### `core/` - Core Functionality

- **`coordinate_transforms.py`**: Chuyển đổi giữa các hệ tọa độ
  - Geodetic (lat, lon, alt) ↔ ECEF ↔ ENU ↔ NED
  - WGS-84 ellipsoid standard
  - Numpy optimized với matrix caching
  
- **`target_calculator.py`**: Thuật toán tính toán chính
  - Góc → Vector định hướng 3D
  - Tính vị trí mục tiêu
  - Verification & accuracy checking
  
- **`gps_target_system.py`**: API wrapper
  - Simplified interface
  - Input validation
  - Sensor fusion integration
  
- **`sensor_fusion.py`**: Xử lý dữ liệu cảm biến
  - NMEA parser cho GPS
  - Filtering algorithms (moving average, median, circular mean)
  - Data quality assessment

#### `visualization/` - Visualization Tools

- **`leaflet_map_viewer.py`**: Pure Leaflet.js web viewer - NEW
  - Responsive design
  - Interactive markers
  - Distance/bearing calculations
  
- **`map_viewer.py`**: Matplotlib 2D maps
- **`plot_utils.py`**: Plotting utilities
- **`export_utils.py`**: GeoJSON export

#### `simulation/` - Testing & Simulation

- **`scenario_generator.py`**: Tạo test scenarios
  - Random targets
  - Pattern-based (grid, circle, line)
  - Noise injection
  
- **`simulator.py`**: Simulation engine
  - Batch processing
  - Statistics calculation
  - Results export

---

## Kiểm thử

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_calculations.py

# With verbose output
python -m pytest tests/ -v
```

### Manual Testing

```python
# Test coordinate conversion
from core.coordinate_transforms import CoordinateTransforms

converter = CoordinateTransforms()

# Test point
lat, lon, alt = 10.762622, 106.660172, 10.0

# Geodetic → ECEF → Geodetic (round-trip)
ecef = converter.geodetic_to_ecef(lat, lon, alt)
lat2, lon2, alt2 = converter.ecef_to_geodetic(*ecef)

# Check error
import numpy as np
lat_err = abs(lat2 - lat) * 111000
lon_err = abs(lon2 - lon) * 111000 * np.cos(np.radians(lat))
alt_err = abs(alt2 - alt)

print(f"Errors: lat={lat_err:.6f}m, lon={lon_err:.6f}m, alt={alt_err:.6f}m")
# Should be < 0.001m
```

### Simulation Testing

```python
from simulation.scenario_generator import ScenarioGenerator
from simulation.simulator import Simulator

# Generate scenario
generator = ScenarioGenerator(seed=42)
observer = generator.create_observer_position()
scenario = generator.create_scenario(observer, num_targets=5, add_noise=True)

# Run simulation
simulator = Simulator(coordinate_system='ENU')
results = simulator.run_scenario(scenario, use_sensor_fusion=True)

# Print statistics
simulator.print_statistics()
```
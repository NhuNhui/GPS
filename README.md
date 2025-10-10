# GPS Target System - Hệ thống tính toán tọa độ mục tiêu

> **Đề tài:** Xây dựng thuật toán tính toán tọa độ mục tiêu từ dữ liệu GPS, góc ngắm và khoảng cách  
> **Giai đoạn:** 1 - Đồ án Kỹ thuật Máy tính  
> **HCMUT - 2024/2025**

---

## Tổng quan

### Giới thiệu

Hệ thống GPS Target Calculator là một ứng dụng tính toán tọa độ mục tiêu dựa trên:
- **Vị trí người quan sát** từ GPS (vĩ độ, kinh độ, độ cao)
- **Góc ngắm** từ IMU/la bàn (azimuth - phương vị, elevation - ngẩng)
- **Khoảng cách** đến mục tiêu từ laser rangefinder

Hệ thống chuyển đổi các dữ liệu này thành **tọa độ địa lý chính xác** (latitude, longitude, altitude) của mục tiêu, có thể hiển thị trên bản đồ số.

## Cài đặt nhanh

### Bước 1: Kiểm tra Python

```bash
python --version
# Cần Python 3.8+
```

Nếu chưa có Python hoặc phiên bản Python không phải từ 3.8, tải Python tại: https://www.python.org/downloads/

### Bước 2: Cài đặt thư viện

```bash
# Thư viện bắt buộc
pip install numpy

# Thư viện cho visualization (khuyến nghị)
pip install matplotlib

# Cài đặt đầy đủ thư viện
pip install numpy matplotlib

# Cài đặt với requirements.txt
pip install -r requirement.txt
```

### Bước 3: Chạy chương trình

```bash
python main.py
```

---

## Hướng dẫn cài đặt chi tiết

### Bước 1: Kiểm tra Python

```bash
python --version
```

Nếu chưa có Python hoặc phiên bản Python không phải từ 3.8, tải Python tại: https://www.python.org/downloads/

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

## 📖 Hướng dẫn sử dụng

### Cách 1: Demo Mode (Nhanh nhất)

```bash
python main.py
# Chọn: 1. Demo
```

**Kết quả:**
```
GIAI ĐOẠN 1 - ĐỒ ÁN KỸ THUẬT MÁY TÍNH
Tính toán tọa độ mục tiêu 2D
============================================================

📝 DỮ LIỆU ĐẦU VÀO:
  Vị trí quan sát: 10.762622°, 106.660172°
  Góc phương vị: 45°
  Khoảng cách: 1000m

⏳ Đang tính toán...

============================================================
✅ KẾT QUẢ TÍNH TOÁN
============================================================

TỌA ĐỘ MỤC TIÊU (2D):
  Vĩ độ:  10.768123°
  Kinh độ: 106.665789°

Độ chính xác:
  Sai số: 0.003m
  → Độ chính xác: XUẤT SẮC

Đang tạo bản đồ 2D...
Đã lưu bản đồ: output/phase1_map.png
```

### Cách 2: Interactive Mode

```bash
python main.py
# Chọn: 2. Interactive
```

Nhập dữ liệu của bạn:
```
📍 NHẬP VỊ TRÍ QUAN SÁT:
  Vĩ độ (độ): 10.762622
  Kinh độ (độ): 106.660172

🎯 NHẬP THÔNG TIN NGẮM:
  Góc phương vị (0-360°): 45
  Khoảng cách (mét): 1000
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

---

## 📚 Tài liệu tham khảo (Giai đoạn 1)

### Công thức toán học:

**[1]** Sinnott, R. W. (1984). *"Virtues of the Haversine"*. Sky and Telescope, 68(2), 159.
- Công thức tính khoảng cách trên mặt cầu

**[2]** National Geospatial-Intelligence Agency. *"World Geodetic System 1984 (WGS 84)"*.
- Hệ tọa độ chuẩn GPS

**[3]** Hofmann-Wellenhof, B. et al. (2012). *"Global Positioning System: Theory and Practice"*. Springer.
- Lý thuyết GPS và coordinate systems

### Thư viện sử dụng:

**[4]** Harris, C. R., et al. (2020). *"Array programming with NumPy"*. Nature, 585(7825), 357-362.
- NumPy cho tính toán vector và ma trận

**[5]** Hunter, J. D. (2007). *"Matplotlib: A 2D graphics environment"*. Computing in Science & Engineering.
- Matplotlib cho visualization 2D

---
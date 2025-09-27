# requirements.txt
**Core dependencies**
numpy
statistics
datetime

# Target Location Calculator
## Tổng quan
Dự án xây dựng thuật toán tính toán tọa độ mục tiêu từ dữ liệu GPS, góc ngắm (azimuth/elevation) và khoảng cách laser rangefinder. Ứng dụng trong các hệ thống chỉ huy-điều khiển hỏa lực, khảo sát địa hình, và robotics.

## Tính năng chính
**Core Algorithm**
* Chuyển đổi hệ tọa độ: Geodetic <-> ECEF <-> ENU/NED
* Xử lý vector định hướng: Azimuth/Elevation -> Vector 3D
* Tính toán mục tiêu: Observer + Direction + Distance -> Target coordinates
* Validation: Round-trip verification và error analysis

**Sensor Fusion**
* NMEA GPS parsing: GGA, RMC sentence processing
* IMU data filtering: Noise reduction cho azimuth/elevation
* Laser rangefinder: Distance measurement với outlier detection
* Data fusion: Kết hợp multi-sensor với temporal filtering
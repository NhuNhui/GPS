import math
import matplotlib.pyplot as plt

# =====================================
# 1️⃣ HÀM CHUYỂN ĐỔI TỌA ĐỘ
# =====================================

def latlon_to_ecef(lat, lon, h):
    """Chuyển từ tọa độ địa lý sang tọa độ ECEF (Ellipsoid)"""
    a = 6378137.0                # bán trục lớn (m)
    e2 = 6.69437999014e-3        # độ lệch tâm bình phương
    lat, lon = math.radians(lat), math.radians(lon)
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    x = (N + h) * math.cos(lat) * math.cos(lon)
    y = (N + h) * math.cos(lat) * math.sin(lon)
    z = ((1 - e2) * N + h) * math.sin(lat)
    return x, y, z

def ecef_to_latlon(x, y, z):
    """Chuyển từ ECEF về tọa độ địa lý (lat, lon, h)"""
    a = 6378137.0
    e2 = 6.69437999014e-3
    lon = math.atan2(y, x)
    p = math.sqrt(x**2 + y**2)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(5):  # lặp cải tiến
        N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
        h = p / math.cos(lat) - N
        lat = math.atan2(z, p * (1 - e2 * (N / (N + h))))
    return math.degrees(lat), math.degrees(lon), h

# =====================================
# 2️⃣ HÀM TÍNH TỌA ĐỘ MỤC TIÊU
# =====================================

def target_from_geo(lat0, lon0, h0, az, el, d):
    """Tính tọa độ mục tiêu theo mô hình Ellipsoid (chuẩn GPS)"""
    az, el = math.radians(az), math.radians(el)
    x0, y0, z0 = latlon_to_ecef(lat0, lon0, h0)

    # vector định hướng ENU
    e = math.cos(el) * math.sin(az)
    n = math.cos(el) * math.cos(az)
    u = math.sin(el)

    # chuyển ENU sang ECEF (xấp xỉ địa phương)
    lat0_r, lon0_r = math.radians(lat0), math.radians(lon0)
    dx = -math.sin(lon0_r)*e - math.sin(lat0_r)*math.cos(lon0_r)*n + math.cos(lat0_r)*math.cos(lon0_r)*u
    dy = math.cos(lon0_r)*e - math.sin(lat0_r)*math.sin(lon0_r)*n + math.cos(lat0_r)*math.sin(lon0_r)*u
    dz = math.cos(lat0_r)*n + math.sin(lat0_r)*u

    xt = x0 + d * dx
    yt = y0 + d * dy
    zt = z0 + d * dz

    return ecef_to_latlon(xt, yt, zt)

# =====================================
# 3️⃣ CHẠY SO SÁNH 2 MÔ HÌNH
# =====================================

lat0, lon0, h0 = 16.0741, 108.1502, 10  # ví dụ: Đà Nẵng
az, el = 45, 10                         # góc ngắm (độ)
distances = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000]

results = []

for d in distances:
    # --- Flat Earth ---
    d_n = d * math.cos(math.radians(el))
    d_u = d * math.sin(math.radians(el))
    d_e = d_n * math.sin(math.radians(az))
    d_north = d_n * math.cos(math.radians(az))

    R = 6378137.0
    lat_target_flat = lat0 + (d_north / R) * (180 / math.pi)
    lon_target_flat = lon0 + (d_e / (R * math.cos(math.radians(lat0)))) * (180 / math.pi)
    h_target_flat = h0 + d_u

    # --- Ellipsoid (chuẩn GPS) ---
    lat_target_geo, lon_target_geo, h_target_geo = target_from_geo(lat0, lon0, h0, az, el, d)

    # --- Sai số ---
    d_lat = (lat_target_flat - lat_target_geo) * (math.pi / 180) * R
    d_lon = (lon_target_flat - lon_target_geo) * (math.pi / 180) * R * math.cos(math.radians(lat0))
    d_h = h_target_flat - h_target_geo
    err = math.sqrt(d_lat**2 + d_lon**2 + d_h**2)

    results.append((d, err, abs(d_h)))

# =====================================
# 4️⃣ IN KẾT QUẢ DẠNG BẢNG
# =====================================

print("distance(m), mean_err(m), max_err(m)")
for d, mean_err, max_err in results:
    print(f"{d:8.0f}, {mean_err:8.4f}, {max_err:8.4f}")

# =====================================
# 5️⃣ VẼ BIỂU ĐỒ SAI SỐ
# =====================================

distances = [r[0] for r in results]
mean_errs = [r[1] for r in results]
max_errs = [r[2] for r in results]

plt.figure(figsize=(8,5))
plt.plot(distances, mean_errs, 'o-', label='Sai số tổng hợp')
plt.plot(distances, max_errs, 's--', label='Sai số độ cao (|Δh|)')

plt.xscale('log')
plt.xlabel('Khoảng cách tới mục tiêu (m)')
plt.ylabel('Sai số (m)')
plt.title('So sánh sai số mô hình Flat Earth vs Ellipsoid')
plt.legend()
plt.grid(True, which='both', ls='--', alpha=0.6)
plt.tight_layout()

# Lưu file ảnh biểu đồ (tùy chọn)
plt.savefig("error_plot.png", dpi=300)

plt.show()

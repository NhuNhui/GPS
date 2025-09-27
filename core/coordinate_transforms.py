"""
coordinate_systems.py
Mô-đun chuyển đổi giữa các hệ tọa độ khác nhau
Bao gồm: Geodetic (lat, lon, alt) ↔ ECEF ↔ ENU ↔ NED

Chức năng:
- Chuyển đổi từ tọa độ địa lý sang ECEF
- Chuyển đổi từ ECEF sang ENU (East-North-Up)
- Chuyển đổi từ ECEF sang NED (North-East-Down)
- Các phép chuyển đổi ngược

"""

import math

class WGS84Constants:
    """Hằng số WSG-84"""
    A = 6378137.0                   # Bán trục lớn (semi-major axis) (m)
    F = 1.0 / 298.257223563         # Độ dẹt (flattening)
    E = 0.0818191908426             # Độ lệch tâm (eccentricity)
    E_SQUARED = 0.00669437999013    # E^2
    B = 6356752.3142                # Bán trục nhỏ (semi-minor axis) (m)

class CoordinateTransforms:
    """
    Lớp thực hiện chuyển đổi giữa các hệ tọa độ:
    - Geodetic (lat, lon, height)
    - ECEF (Earth-Centered, Earth-Fixed)
    - ENU (East-North-Up)
    - NED (North-East-Down)
    """

    def __init__(self):
        self.wgs84 = WGS84Constants()

    def _validate_geodetic(self, lat_deg, lon_deg, alt_m=None):
        """Xác thực tọa độ trắc địa"""
        if not (-90 <= lat_deg <= 90):
            raise ValueError(f"Vĩ độ {lat_deg} phải nằm trong khoảng [-90, 90]")
        if not (-180 <= lon_deg <= 180):
            raise ValueError(f"Kinh độ {lon_deg} phải nằm trong khoảng [-180, 180]")
        if alt_m is not None and alt_m < -1000:
            print(f"Cảnh báo: Độ cao {alt_m}m có vẻ thấp bất thường")

    def geodetic_to_ecef(self, lat_deg, lon_deg, alt_m):
        """
        Chuyển đổi Geodetic (φ, λ, h) sang ECEF (X, Y, Z) trong hệ tọa độ không gian 3D

        Input:
            lat_deg: Vĩ độ (độ)
            lon_deg: Kinh độ (độ)
            alt_m: Cao độ (mét)

        Output:
            tuple: (X, Y, Z) tọa độ ECEF (mét)
        """
        self._validate_geodetic(lat_deg, lon_deg, alt_m)

        # Chuyển đổi sang radian
        phi = math.radians(lat_deg)
        lam = math.radians(lon_deg)

        # Tính N (bán kính cong đơn vị kinh tuyến chính)
        N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * math.sin(phi)**2)

        # Tính tọa độ ECEF theo công thức
        X = (N + alt_m) * math.cos(phi) * math.cos(lam)
        Y = (N + alt_m) * math.cos(phi) * math.sin(lam)
        Z = (N * (1 - self.wgs84.E_SQUARED) + alt_m) * math.sin(phi)

        # Trả về kết quả dưới dạng tuple
        return (X, Y, Z)
    
    def ecef_to_geodetic(self, X, Y, Z):
        """
        Chuyển đổi ECEF sang Geodetic (thuật toán iterative)
        
        Input:
            X, Y, Z: Tọa độ ECEF (mét)
            
        Output:
            tuple: (lat_deg, lon_deg, alt_m)
        """
        # Tính kinh độ
        lon_rad = math.atan2(Y, X)
        
        # Tính khoảng cách từ trục Z
        p = math.sqrt(X**2 + Y**2)
        
        # Iterative algorithm để tính vĩ độ và độ cao
        lat_rad = math.atan2(Z, p * (1 - self.wgs84.E_SQUARED))
        
        for _ in range(10):  # Tối đa 10 iterations
            N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * math.sin(lat_rad)**2)
            alt = p / math.cos(lat_rad) - N
            lat_rad_new = math.atan2(Z, p * (1 - self.wgs84.E_SQUARED * N / (N + alt)))
            
            if abs(lat_rad_new - lat_rad) < 1e-12:
                break
            lat_rad = lat_rad_new
        
        # Tính độ cao cuối cùng
        N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * math.sin(lat_rad)**2)
        alt = p / math.cos(lat_rad) - N
        
        return (math.degrees(lat_rad), math.degrees(lon_rad), alt)
    
    def ecef_to_enu(self, target_ecef, observer_geodetic):
        """
        Chuyển đổi từ ECEF sang ENU (East-North-Up)
        
        Input:
            target_ecef: tuple (X, Y, Z) tọa độ ECEF cần chuyển đổi
            observer_geodetic: tuple (lat_deg, lon_deg, height_m) tọa độ người quan sát
            
        Output:
            tuple: (E, N, U) tọa độ trong hệ ENU (mét)
        """
        observer_ecef = self.geodetic_to_ecef(*observer_geodetic)

        # Tìm vector sai khác
        dX = target_ecef[0] - observer_ecef[0]
        dY = target_ecef[1] - observer_ecef[1] 
        dZ = target_ecef[2] - observer_ecef[2]

        # Góc của người quan sát (radian)
        phi0 = math.radians(observer_geodetic[0])   # Vĩ độ
        lam0 = math.radians(observer_geodetic[1])   # Kinh độ

        # Ma trận quay từ ECEF sang ENU theo công thức
        # ENU = R * [dX, dY, dZ]^T
        E = -math.sin(lam0) * dX + math.cos(lam0) * dY
        N = (-math.sin(phi0) * math.cos(lam0) * dX + 
             -math.sin(phi0) * math.sin(lam0) * dY + 
             math.cos(phi0) * dZ)
        U = (math.cos(phi0) * math.cos(lam0) * dX + 
             math.cos(phi0) * math.sin(lam0) * dY + 
             math.sin(phi0) * dZ)
        
        # Trả về kết quả
        return (E, N, U)
    
    def enu_to_ecef(self, enu_coords, observer_geodetic):
        """
        Chuyển đổi từ ENU sang ECEF (đảo ngược của ecef_to_enu)

        Input:
            enu_coords: tuple (E, N, U) tọa độ trong hệ ENU
            observer_geodetic: tuple (lat_deg, lon_deg, height_m) tọa độ người quan sát

        Output:
            tuple: (X, Y, Z) tọa độ ECEF
        """
        E, N, U = enu_coords
        observer_ecef = self.geodetic_to_ecef(*observer_geodetic)

        # Góc của người quan sát
        phi0 = math.radians(observer_geodetic[0])
        lam0 = math.radians(observer_geodetic[1])

        # Ma trận quay nghịch đảo (chuyển vị của ma trận quay ENU -> ECEF)
        dX = (-math.sin(lam0) * E + 
              -math.sin(phi0) * math.cos(lam0) * N + 
              math.cos(phi0) * math.cos(lam0) * U)
        dY = (math.cos(lam0) * E + 
              -math.sin(phi0) * math.sin(lam0) * N + 
              math.cos(phi0) * math.sin(lam0) * U)
        dZ = (math.cos(phi0) * N + math.sin(phi0) * U)

        # Thêm vào tọa độ ECEF của người quan sát
        X = observer_ecef[0] + dX
        Y = observer_ecef[1] + dY
        Z = observer_ecef[2] + dZ

        # Trả về kết quả
        return (X, Y, Z)
    
    def enu_to_ned(self, enu_coords):
        """
        Chuyển đổi ENU sang NED

        Input:
            enu_coords: tuple (E, N, U)
            
        Output:
            tuple: (N, E, D) tọa độ NED
        """
        E, N, U = enu_coords
        return (N, E, -U)  # N, E, D
    
    def ned_to_enu(self, ned_coords):
        """
        Chuyển đổi NED sang ENU

        Input:
            ned_coords: tuple (N, E, D)
            
        Output:
            tuple: (E, N, U) tọa độ ENU
        """
        N, E, D = ned_coords
        return (E, N, -D)  # E, N, U
    
    def ecef_to_ned(self, target_ecef, observer_geodetic):
        """Chuyển đổi trực tiếp ECEF sang NED"""
        enu = self.ecef_to_enu(target_ecef, observer_geodetic)
        return self.enu_to_ned(enu)
    
    def ned_to_ecef(self, ned_coords, observer_geodetic):
        """Chuyển đổi trực tiếp NED sang ECEF"""
        enu = self.ned_to_enu(ned_coords)
        return self.enu_to_ecef(enu, observer_geodetic)
    
def test_coordinate_conversion():
    """Hàm test chuyển đổi tọa độ với validation"""
    converter = CoordinateTransforms()
    
    # Tọa độ mẫu (khu vực TP.HCM)
    observer_lat = 10.762622  # Vĩ độ Đại học Bách Khoa
    observer_lon = 106.660172  # Kinh độ Đại học Bách Khoa  
    observer_height = 10.0  # Độ cao 10m
    
    print("=== TEST CHUYỂN ĐỔI TỌA ĐỘ (FIXED) ===")
    print(f"Tọa độ người quan sát (Geodetic): {observer_lat:.6f}°, {observer_lon:.6f}°, {observer_height}m")
    
    # Test Geodetic -> ECEF
    ecef_coords = converter.geodetic_to_ecef(observer_lat, observer_lon, observer_height)
    print(f"Tọa độ ECEF: X={ecef_coords[0]:.2f}m, Y={ecef_coords[1]:.2f}m, Z={ecef_coords[2]:.2f}m")
    
    # Test ECEF -> Geodetic (round-trip)
    geodetic_verify = converter.ecef_to_geodetic(*ecef_coords)
    print(f"Verify Geodetic: {geodetic_verify[0]:.6f}°, {geodetic_verify[1]:.6f}°, {geodetic_verify[2]:.2f}m")
    print(f"Error: lat={abs(geodetic_verify[0] - observer_lat)*1e6:.2f}μ°, " +
          f"lon={abs(geodetic_verify[1] - observer_lon)*1e6:.2f}μ°, " +
          f"alt={abs(geodetic_verify[2] - observer_height):.3f}m")
    
    # Test với mục tiêu cách observer 1000m về phía đông, 500m về phía bắc
    target_enu = (1000.0, 500.0, 0.0)  # E, N, U
    print(f"\nMục tiêu trong hệ ENU: E={target_enu[0]}m, N={target_enu[1]}m, U={target_enu[2]}m")
    
    # Chuyển ENU -> ECEF -> ENU (round-trip test)
    target_ecef = converter.enu_to_ecef(target_enu, (observer_lat, observer_lon, observer_height))
    print(f"Mục tiêu ECEF: X={target_ecef[0]:.2f}m, Y={target_ecef[1]:.2f}m, Z={target_ecef[2]:.2f}m")
    
    verify_enu = converter.ecef_to_enu(target_ecef, (observer_lat, observer_lon, observer_height))
    print(f"Verify ENU: E={verify_enu[0]:.2f}m, N={verify_enu[1]:.2f}m, U={verify_enu[2]:.2f}m")
    print(f"ENU Error: E={abs(verify_enu[0] - target_enu[0]):.3f}m, " +
          f"N={abs(verify_enu[1] - target_enu[1]):.3f}m, " +
          f"U={abs(verify_enu[2] - target_enu[2]):.3f}m")
    
    # Test ENU <-> NED
    ned_coords = converter.enu_to_ned(target_enu)
    print(f"\nTọa độ NED: N={ned_coords[0]}m, E={ned_coords[1]}m, D={ned_coords[2]}m")
    
    # Chuyển mục tiêu thành geodetic coordinates
    target_geodetic = converter.ecef_to_geodetic(*target_ecef)
    print(f"Tọa độ mục tiêu (Geodetic): {target_geodetic[0]:.6f}°, {target_geodetic[1]:.6f}°, {target_geodetic[2]:.2f}m")

if __name__ == "__main__":
    test_coordinate_conversion()
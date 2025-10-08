"""
coordinate_transforms.py
Mô-đun chuyển đổi giữa các hệ tọa độ khác nhau
Bao gồm: Geodetic (lat, lon, alt) ↔ ECEF ↔ ENU ↔ NED

Chức năng:
- Chuyển đổi từ tọa độ địa lý sang ECEF
- Chuyển đổi từ ECEF sang ENU (East-North-Up)
- Chuyển đổi từ ECEF sang NED (North-East-Down)
- Các phép chuyển đổi ngược

"""

import math
import numpy as np

class WGS84Constants:
    """Hằng số WGS-84"""
    A = 6378137.0                   # Bán trục lớn (semi-major axis) (m)
    F = 1.0 / 298.257223563         # Độ dẹt (flattening)
    E = 0.0818191908426             # Độ lệch tâm (eccentricity)
    E_SQUARED = 0.00669437999013    # E^2
    B = 6356752.314245179           # Bán trục nhỏ (semi-minor axis) (m)

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
        self._cache = {}        # Cache sin/cos để tối ưu khi gọi lặp lại với cùng tọa độ

    def _validate_geodetic(self, lat_deg, lon_deg, alt_m=None):
        """Xác thực tọa độ trắc địa"""
        if not (-90 <= lat_deg <= 90):
            raise ValueError(f"Vĩ độ {lat_deg} phải nằm trong khoảng [-90, 90]")
        if not (-180 <= lon_deg <= 180):
            raise ValueError(f"Kinh độ {lon_deg} phải nằm trong khoảng [-180, 180]")
        if alt_m is not None and alt_m < -1000:
            print(f"Cảnh báo: Độ cao {alt_m}m thấp bất thường")

    def geodetic_to_ecef(self, lat_deg, lon_deg, alt_m):
        """
        Chuyển đổi Geodetic (φ, λ, h) sang ECEF (X, Y, Z)

        Input:
            lat_deg: Vĩ độ (độ)
            lon_deg: Kinh độ (độ)
            alt_m: Cao độ (mét)

        Output:
            np.ndarray: [X, Y, Z] tọa độ ECEF (mét)
        """
        self._validate_geodetic(lat_deg, lon_deg, alt_m)

        # Chuyển đổi sang radian
        phi = math.radians(lat_deg)
        lam = math.radians(lon_deg)

        # Tính N (bán kính cong kinh tuyến chính)
        sin_phi = math.sin(phi)
        N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * sin_phi**2)

        cos_phi = math.cos(phi)
        cos_lam = math.cos(lam)
        sin_lam = math.sin(lam)

        # Tính tọa độ ECEF theo công thức
        X = (N + alt_m) * cos_phi * cos_lam
        Y = (N + alt_m) * cos_phi * sin_lam
        Z = (N * (1 - self.wgs84.E_SQUARED) + alt_m) * sin_phi

        return np.array([X, Y, Z])
    
    def ecef_to_geodetic(self, X, Y, Z):
        """
        Chuyển đổi ECEF sang Geodetic (thuật toán Bowring)
        
        Input:
            X, Y, Z: Tọa độ ECEF (mét)
            
        Output:
            tuple: (lat_deg, lon_deg, alt_m)
        """
        # Tính kinh độ
        lon_rad = math.atan2(Y, X)
        
        # Tính khoảng cách từ trục Z
        p = math.sqrt(X**2 + Y**2)

        # Thuật toán lặp Bowring (hội tụ nhanh)
        lat_rad = math.atan2(Z, p * (1 - self.wgs84.E_SQUARED))
        
        # Lặp tối đa 5 lần (thường hội tụ sau 2-3 lần)
        for _ in range (5):
            sin_lat = math.sin(lat_rad)
            N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * sin_lat**2)

            alt = p / math.cos(lat_rad) - N

            lat_rad_new = math.atan2(Z, p * (1 - self.wgs84.E_SQUARED * N / (N + alt)))

            lat_rad_new = math.atan2(Z, p * (1 - self.wgs84.E_SQUARED * N / (N + alt)))
            
            
            if abs(lat_rad_new - lat_rad) < 1e-12:
                break
            lat_rad = lat_rad_new
        
        # Tính độ cao cuối cùng
        N = self.wgs84.A / math.sqrt(1 - self.wgs84.E_SQUARED * math.sin(lat_rad)**2)
        alt = p / math.cos(lat_rad) - N
        
        return (math.degrees(lat_rad), math.degrees(lon_rad), alt)
    
    def _get_rotation_matrix_enu_to_ecef(self, lat_deg, lon_deg):
        """
        Tính ma trận quay chuyển ECEF sang ENU (tối ưu hóa với cache)

        Input:
            lat_deg: Vĩ độ (độ)
            lon_deg: Kinh độ (độ)

        Output:
            np.ndarray: Ma trận quay 3x3
        """
        cache_key = (round(lat_deg, 8), round(lon_deg, 8))
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        phi = math.radians(lat_deg)
        lam = math.radians(lon_deg)
        
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        sin_lam = math.sin(lam)
        cos_lam = math.cos(lam)
        
        # Ma trận quay ECEF → ENU
        R = np.array([
            [-sin_lam,              cos_lam,           0        ],
            [-sin_phi * cos_lam,   -sin_phi * sin_lam, cos_phi  ],
            [ cos_phi * cos_lam,    cos_phi * sin_lam, sin_phi  ]
        ])
        
        self._cache[cache_key] = R
        return R
    
    def ecef_to_enu(self, target_ecef, observer_geodetic):
        """
        Chuyển đổi từ ECEF sang ENU (East-North-Up)
        
        Input:
            target_ecef: tuple array-like [X, Y, Z] hoặc tuple
            observer_geodetic: tuple (lat_deg, lon_deg, alt_m) tọa độ người quan sát
            
        Output:
            np.ndarray: (E, N, U) tọa độ trong hệ ENU (mét)
        """
        # Chuyển sang numpy array nếu cần
        if not isinstance(target_ecef, np.ndarray):
            target_ecef = np.array(target_ecef)

        observer_ecef = self.geodetic_to_ecef(*observer_geodetic)

        # Vector sai khác
        delta = target_ecef - observer_ecef

        # Ma trận quay
        R = self._get_rotation_matrix_enu_to_ecef(observer_geodetic[0], observer_geodetic[1])

        # Áp dụng phép quay
        enu = R @ delta
        
        return enu
    
    def enu_to_ecef(self, enu_coords, observer_geodetic):
        """
        Chuyển đổi từ ENU sang ECEF (đảo ngược của ecef_to_enu)

        Input:
            enu_coords: array-like [E, N, U] tọa độ trong hệ ENU
            observer_geodetic: tuple (lat_deg, lon_deg, height_m) tọa độ người quan sát

        Output:
            tuple: (X, Y, Z) tọa độ ECEF
        """
        # Chuyển sang numpy array nếu cần
        if not isinstance(enu_coords, np.ndarray):
            enu_coords = np.array(enu_coords)

        E, N, U = enu_coords
        observer_ecef = self.geodetic_to_ecef(*observer_geodetic)

        # Ma trận quay ENU → ECEF (transpose của ECEF → ENU)
        R = self._get_rotation_matrix_ecef_to_enu(observer_geodetic[0], observer_geodetic[1])
        R_inv = R.T  # Orthogonal matrix: R^-1 = R^T
        
        # Áp dụng phép quay nghịch
        delta_ecef = R_inv @ enu_coords

        # Cộng vào tọa độ người quan sát
        target_ecef = observer_ecef + delta_ecef

        # Trả về kết quả
        return target_ecef
    
    def enu_to_ned(self, enu_coords):
        """
        Chuyển đổi ENU sang NED
        """
        if not isinstance(enu_coords, np.ndarray):
            enu_coords = np.array(enu_coords)
        return np.array([enu_coords[1], enu_coords[0], -enu_coords[2]])  # N, E, D
    
    def ned_to_enu(self, ned_coords):
        """
        Chuyển đổi NED sang ENU
        """
        if not isinstance(ned_coords, np.ndarray):
            ned_coords = np.array(ned_coords)
        return np.array([ned_coords[1], ned_coords[0], -ned_coords[2]])  # E, N, U
    
    def ecef_to_ned(self, target_ecef, observer_geodetic):
        """Chuyển đổi trực tiếp ECEF sang NED"""
        enu = self.ecef_to_enu(target_ecef, observer_geodetic)
        return self.enu_to_ned(enu)
    
    def ned_to_ecef(self, ned_coords, observer_geodetic):
        """Chuyển đổi trực tiếp NED sang ECEF"""
        enu = self.ned_to_enu(ned_coords)
        return self.enu_to_ecef(enu, observer_geodetic)
    
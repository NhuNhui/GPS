from visualization.webmap_viewer import *

def test_leaflet_viewer():
    """Test Leaflet viewer"""
    print("=== TEST LEAFLET MAP VIEWER ===\n")
    
    viewer = LeafletMapViewer()
    
    # Test 1: Single target
    print("Test 1: Single target map")
    observer_pos = (10.762622, 106.660172, 10.0)
    target_pos = (10.773456, 106.674512, 50.0)
    
    viewer.create_interactive_map(
        observer_pos=observer_pos,
        target_pos=target_pos,
        title="GPS Target System - Single Target",
        save_path="output/leaflet_single.html",
        auto_open=False
    )
    
    # Test 2: Multiple targets
    print("\nTest 2: Multiple targets map")
    targets = [
        (10.773456, 106.674512, 50.0, "Target Alpha"),
        (10.780000, 106.690000, 30.0, "Target Bravo"),
        (10.750000, 106.650000, 20.0, "Target Charlie"),
        (10.770000, 106.655000, 40.0, "Target Delta"),
    ]
    
    viewer.create_multi_target_map(
        observer_pos=observer_pos,
        targets=targets,
        title="Multi-Target Mission",
        save_path="output/leaflet_multi.html",
        auto_open=True
    )
    
    print("\nMaps created successfully!")
    print("  - output/leaflet_single.html")
    print("  - output/leaflet_multi.html")


if __name__ == "__main__":
    test_leaflet_viewer()
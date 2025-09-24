import matplotlib.pyplot as plt
import math

# Board dimensions
BOARD_WIDTH = 50
BOARD_HEIGHT = 50

class Component:
    def __init__(self, name, width, height, rotation=0):
        self.name = name
        self.width = width
        self.height = height
        self.rotation = rotation
        self.x = None
        self.y = None

    def get_bounds(self):
        w, h = (self.width, self.height) if self.rotation == 0 else (self.height, self.width)
        return self.x, self.y, w, h

    def get_center(self):
        x, y, w, h = self.get_bounds()
        return (x + w / 2, y + h / 2)

    def set_position(self, x, y, rotation=0):
        self.x = x
        self.y = y
        self.rotation = rotation

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def check_overlap(c1, c2):
    x1, y1, w1, h1 = c1.get_bounds()
    x2, y2, w2, h2 = c2.get_bounds()
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

def is_within_board(c):
    x, y, w, h = c.get_bounds()
    return x >= 0 and y >= 0 and x + w <= BOARD_WIDTH and y + h <= BOARD_HEIGHT

def place_edge_component(comp, edge, y_hint=None):
    for y in range(0, BOARD_HEIGHT - comp.height + 1):
        if y_hint and abs(y - y_hint) > 5:
            continue
        if edge == 'left':
            comp.set_position(0, y)
        elif edge == 'right':
            comp.set_position(BOARD_WIDTH - comp.width, y)
        elif edge == 'bottom':
            comp.set_position(y, BOARD_HEIGHT - comp.height)
        if is_within_board(comp):
            return True
    return False

def place_microcontroller():
    uc = Component("μC", 5, 5)
    for x in range(24, 26):
        for y in range(24, 26):
            uc.set_position(x, y)
            if is_within_board(uc):
                return uc
    return None

def place_xtal_near_uc(uc, other_components):
    xtal = Component("XTAL", 5, 5)
    uc_center = uc.get_center()
    best_xtal = None
    best_score = float('inf')

    for dx in range(-10, 11):
        for dy in range(-10, 11):
            x = int(uc_center[0] + dx - xtal.width / 2)
            y = int(uc_center[1] + dy - xtal.height / 2)
            xtal.set_position(x, y)
            if not is_within_board(xtal):
                continue
            if distance(uc.get_center(), xtal.get_center()) > 10:
                continue
            if any(check_overlap(xtal, c) for c in other_components):
                continue
            temp_components = other_components + [xtal]
            _, _, keepout_ok, _, _, com_dist = validate_constraints(temp_components)
            if keepout_ok and com_dist < best_score:
                best_score = com_dist
                best_xtal = Component("XTAL", 5, 5)
                best_xtal.set_position(x, y)

    if best_xtal:
        return best_xtal

    # Fallback: place XTAL without center-of-mass constraint
    for dx in range(-10, 11):
        for dy in range(-10, 11):
            x = int(uc_center[0] + dx - xtal.width / 2)
            y = int(uc_center[1] + dy - xtal.height / 2)
            xtal.set_position(x, y)
            if not is_within_board(xtal):
                continue
            if distance(uc.get_center(), xtal.get_center()) > 10:
                continue
            if any(check_overlap(xtal, c) for c in other_components):
                continue
            temp_components = other_components + [xtal]
            _, _, keepout_ok, _, _, _ = validate_constraints(temp_components)
            if keepout_ok:
                return xtal

    return None

def validate_constraints(components):
    comp_dict = {c.name: c for c in components}
    uc = comp_dict["μC"]
    xtal = comp_dict["XTAL"]
    usb = comp_dict["USB"]

    dist = distance(uc.get_center(), xtal.get_center())
    proximity_ok = dist <= 10.0

    centers = [c.get_center() for c in components]
    avg_x = sum(p[0] for p in centers) / len(centers)
    avg_y = sum(p[1] for p in centers) / len(centers)
    com_dist = distance((25, 25), (avg_x, avg_y))
    com_ok = com_dist <= 2.0

    usb_center = usb.get_center()
    zone_x = usb_center[0] - 5
    zone_y = usb.y - 15
    zone_w = 10
    zone_h = 15

    xtal_center = xtal.get_center()
    uc_center = uc.get_center()

    def line_intersects_zone(p1, p2):
        min_x = min(p1[0], p2[0])
        max_x = max(p1[0], p2[0])
        min_y = min(p1[1], p2[1])
        max_y = max(p1[1], p2[1])
        return not (max_x < zone_x or min_x > zone_x + zone_w or
                    max_y < zone_y or min_y > zone_y + zone_h)

    keepout_ok = not line_intersects_zone(xtal_center, uc_center)

    overlap_ok = True
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            if check_overlap(components[i], components[j]):
                overlap_ok = False

    return proximity_ok, com_ok, keepout_ok, overlap_ok, dist, com_dist

def plot_components(components):
    fig, ax = plt.subplots(figsize=(6,6))
    ax.set_xlim(0, BOARD_WIDTH)
    ax.set_ylim(0, BOARD_HEIGHT)
    ax.set_aspect('equal')
    ax.set_title("PCB Component Placement Solution")

    for comp in components:
        x, y, w, h = comp.get_bounds()
        rect = plt.Rectangle((x, y), w, h, edgecolor='black', facecolor='lightblue')
        ax.add_patch(rect)
        cx, cy = comp.get_center()
        ax.text(cx, cy, comp.name, ha='center', va='center', fontsize=8)

    uc = next(c for c in components if c.name == "μC")
    circle = plt.Circle(uc.get_center(), 10, color='orange', fill=False, linestyle='--')
    ax.add_patch(circle)

    usb = next(c for c in components if c.name == "USB")
    usb_center = usb.get_center()
    zone_x = usb_center[0] - 5
    zone_y = usb.y - 15
    zone_rect = plt.Rectangle((zone_x, zone_y), 10, 15, color='red', alpha=0.3)
    ax.add_patch(zone_rect)

    plt.grid(True)
    plt.savefig("pcb_layout.png", dpi=300, bbox_inches='tight')  # ✅ Save before showing
    plt.show()

def main():
    max_attempts = 500
    for attempt in range(max_attempts):
        y_hint = 15 + (attempt % 10)  # Try y_hint from 15 to 24

        mb1 = Component("MB1", 5, 15)
        mb2 = Component("MB2", 5, 15)
        usb = Component("USB", 5, 5)

        if not place_edge_component(mb1, 'left', y_hint=y_hint):
            continue
        if not place_edge_component(mb2, 'right', y_hint=y_hint):
            continue

        usb_x = (BOARD_WIDTH - usb.width) // 2
        usb.set_position(usb_x, BOARD_HEIGHT - usb.height)
        if not is_within_board(usb):
            continue

        uc = place_microcontroller()
        if uc is None:
            continue

        xtal = place_xtal_near_uc(uc, [mb1, mb2, usb, uc])
        if xtal is None:
            continue

        components = [mb1, mb2, usb, uc, xtal]
        proximity_ok, com_ok, keepout_ok, overlap_ok, dist, com_dist = validate_constraints(components)

        if proximity_ok and com_ok and keepout_ok and overlap_ok:
            print("--- FINAL PLACEMENT VALIDATION ---")
            print(f"Proximity Constraint  : PASSED Distance: {dist:.2f}")
            print(f"Center of Mass        : PASSED Distance from center: {com_dist:.2f}")
            print(f"Keep-Out Zone         : PASSED")
            print(f"No Overlap            : PASSED")
            plot_components(components)
            return

    print("❌ Failed to find valid placement with center of mass ≤ 2.0 after multiple attempts.")
    

if __name__ == "__main__":
    main()
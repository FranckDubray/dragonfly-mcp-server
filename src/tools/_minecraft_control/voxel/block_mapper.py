"""
Block color palette and voxel-to-block mapping (extended for high-contrast image rendering).
"""
import logging
import math

logger = logging.getLogger(__name__)

# High-contrast palettes: include all 16 wools and all 16 concretes
# RGB are representative sRGB values for default textures
# NOTE: Gravity-affected blocks are intentionally excluded (e.g., sand, gravel, concrete_powder).
BLOCK_COLOR_PALETTE = {
    # --- Wool (16) ---
    "white_wool": (234, 236, 237),
    "orange_wool": (240, 118, 19),
    "magenta_wool": (189, 68, 179),
    "light_blue_wool": (58, 175, 217),
    "yellow_wool": (248, 198, 39),
    "lime_wool": (112, 185, 25),
    "pink_wool": (237, 141, 172),
    "gray_wool": (62, 68, 71),
    "light_gray_wool": (142, 142, 134),
    "cyan_wool": (22, 156, 156),
    "purple_wool": (123, 47, 190),
    "blue_wool": (41, 46, 152),
    "brown_wool": (97, 58, 33),
    "green_wool": (73, 91, 36),
    "red_wool": (161, 39, 34),
    "black_wool": (20, 21, 25),

    # --- Concrete (16) ---
    "white_concrete": (207, 213, 214),
    "orange_concrete": (224, 97, 0),
    "magenta_concrete": (169, 49, 161),
    "light_blue_concrete": (36, 137, 199),
    "yellow_concrete": (245, 205, 47),
    "lime_concrete": (94, 168, 24),
    "pink_concrete": (237, 141, 172),
    "gray_concrete": (54, 57, 61),
    "light_gray_concrete": (122, 122, 116),
    "cyan_concrete": (22, 156, 156),
    "purple_concrete": (123, 47, 190),
    "blue_concrete": (31, 46, 168),
    "brown_concrete": (98, 51, 11),
    "green_concrete": (73, 91, 36),
    "red_concrete": (143, 32, 32),
    "black_concrete": (15, 15, 15),

    # --- Select neutrals/blocks useful for shading (non-gravity) ---
    "stone": (125, 125, 125),
    "cobblestone": (127, 127, 127),
    "diorite": (180, 180, 183),
    "andesite": (130, 130, 130),
    "granite": (150, 100, 77),
    "gold_block": (252, 238, 75),
    "iron_block": (219, 219, 219),
    "diamond_block": (93, 236, 229),
    "emerald_block": (80, 218, 133),
    "oak_planks": (162, 130, 78),
    "spruce_planks": (114, 84, 48),
    "birch_planks": (192, 175, 121),
    "dirt": (134, 96, 67),
    "grass_block": (127, 178, 56),
    "glowstone": (255, 198, 73),
    "obsidian": (16, 11, 28),
    "snow_block": (249, 254, 254),
}


def map_voxels_to_blocks(voxel_grid: dict, mapping_mode: str = "auto") -> dict:
    """Map voxel grid to Minecraft blocks.

    Args:
        voxel_grid: Dict {(x,y,z): color_rgb_tuple}
        mapping_mode: "auto", "color", or "single"

    Returns:
        Dict {(x,y,z): "block_type"}
    """
    if mapping_mode == "single":
        # Single block type for all voxels
        return {pos: "stone" for pos in voxel_grid}

    # Color-based mapping (choose closest block color in palette)
    block_map = {}
    color_cache = {}  # Cache color matches

    for pos, color in voxel_grid.items():
        if color in color_cache:
            block_map[pos] = color_cache[color]
        else:
            block_type = find_closest_block(color)
            color_cache[color] = block_type
            block_map[pos] = block_type

    logger.info(f"Mapped {len(block_map)} voxels to {len(set(block_map.values()))} unique blocks")
    return block_map


def find_closest_block(rgb: tuple) -> str:
    """Find closest Minecraft block by RGB color.

    Args:
        rgb: (R, G, B) tuple

    Returns:
        Block type string
    """
    if not rgb or len(rgb) < 3:
        return "stone"

    r, g, b = rgb[0], rgb[1], rgb[2]

    min_distance = float('inf')
    closest_block = "stone"

    for block_type, (br, bg, bb) in BLOCK_COLOR_PALETTE.items():
        # Euclidean distance in RGB space
        distance = math.sqrt((r - br) ** 2 + (g - bg) ** 2 + (b - bb) ** 2)

        if distance < min_distance:
            min_distance = distance
            closest_block = block_type

    return closest_block

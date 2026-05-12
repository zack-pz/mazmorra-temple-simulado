import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


TILE_PARED = 0
TILE_PISO = 1
TILE_INICIO = 2
TILE_SALIDA = 3
TILE_TESORO = 4
TILE_BOSS = 5


ROOMS = {
    "entrada": {"x": 2, "y": 8, "w": 6, "h": 5, "center": (5, 10)},
    "pasillo_norte": {"x": 11, "y": 3, "w": 5, "h": 4, "center": (13, 5)},
    "sala_central": {"x": 10, "y": 8, "w": 8, "h": 6, "center": (14, 11)},
    "tesoro": {"x": 21, "y": 4, "w": 5, "h": 5, "center": (23, 6)},
    "boss": {"x": 22, "y": 11, "w": 7, "h": 7, "center": (25, 14)},
}


CONNECTIONS = [
    ("entrada", "sala_central"),
    ("sala_central", "pasillo_norte"),
    ("pasillo_norte", "tesoro"),
    ("sala_central", "boss"),
]


def create_grid(width=32, height=22):
    return np.full((height, width), TILE_PARED, dtype=int)


def carve_room(grid, room, tile=TILE_PISO):
    x, y, w, h = room["x"], room["y"], room["w"], room["h"]
    grid[y : y + h, x : x + w] = tile


def carve_corridor(grid, start, end):
    x1, y1 = start
    x2, y2 = end

    x_min, x_max = sorted((x1, x2))
    y_min, y_max = sorted((y1, y2))

    grid[y1, x_min : x_max + 1] = TILE_PISO
    grid[y_min : y_max + 1, x2] = TILE_PISO


def build_dungeon():
    grid = create_grid()

    for room_name in ROOMS:
        carve_room(grid, ROOMS[room_name])

    for source, target in CONNECTIONS:
        carve_corridor(grid, ROOMS[source]["center"], ROOMS[target]["center"])

    grid[ROOMS["entrada"]["center"][1], ROOMS["entrada"]["center"][0]] = TILE_INICIO
    grid[ROOMS["tesoro"]["center"][1], ROOMS["tesoro"]["center"][0]] = TILE_TESORO
    grid[ROOMS["boss"]["center"][1], ROOMS["boss"]["center"][0]] = TILE_BOSS
    grid[ROOMS["boss"]["center"][1], ROOMS["boss"]["center"][0] - 2] = TILE_SALIDA

    return grid


def draw_graph(ax):
    ax.set_title("Estructura lógica (grafo)")

    for source, target in CONNECTIONS:
        x1, y1 = ROOMS[source]["center"]
        x2, y2 = ROOMS[target]["center"]
        ax.plot([x1, x2], [y1, y2], color="#94a3b8", linewidth=2, zorder=1)

    room_colors = {
        "entrada": "#22c55e",
        "pasillo_norte": "#60a5fa",
        "sala_central": "#eab308",
        "tesoro": "#f59e0b",
        "boss": "#ef4444",
    }

    for room_name, room in ROOMS.items():
        x, y = room["center"]
        ax.scatter(x, y, s=800, color=room_colors[room_name], edgecolor="#0f172a", zorder=2)
        ax.text(x, y, room_name.replace("_", "\n"), ha="center", va="center", fontsize=8, weight="bold")

    ax.set_xlim(0, 31)
    ax.set_ylim(21, 0)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)


def draw_grid(ax, grid):
    cmap = ListedColormap(
        [
            "#111827",  # pared
            "#e5e7eb",  # piso
            "#22c55e",  # inicio
            "#3b82f6",  # salida
            "#f59e0b",  # tesoro
            "#ef4444",  # boss
        ]
    )

    ax.imshow(grid, cmap=cmap, interpolation="nearest", vmin=0, vmax=5)
    ax.set_title("Mapa espacial (grid)")
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="#cbd5e1", linewidth=0.4)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


def main():
    grid = build_dungeon()

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), constrained_layout=True)
    fig.suptitle("Prototipo estático de mazmorra híbrida: grafo + grid", fontsize=14, weight="bold")

    draw_graph(axes[0])
    draw_grid(axes[1], grid)

    output_path = "practica9/mazmorra-estatica.png"
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.show()

    print(f"Imagen guardada en: {output_path}")


if __name__ == "__main__":
    main()


from pathlib import Path
from awpy import Demo, plot


def create_position_map(demo_path, player_steam_id):

    demo = Demo(demo_path)
    demo.load("kills")

    player_steam_id = int(player_steam_id)
    map_name = demo.header["map_name"]

    kills = demo.kills

    # Убийства игрока
    player_kills = kills.filter(
        kills["attacker_steamid"] == player_steam_id
    )

    # Смерти игрока
    player_deaths = kills.filter(
        kills["victim_steamid"] == player_steam_id
    )

    # Создаём карту Mirage
    fig, ax = plot.radar(map_name)

    # Отмечаем убийства
    kill_count = 0

    for row in player_kills.iter_rows(named=True):
        x = row["attacker_x"]
        y = row["attacker_y"]

        if x is None or y is None:
            continue

        px, py = plot.world_to_pixel(map_name, (x, y))

        ax.scatter(px, py, marker="o", s=65, label="Kill" if kill_count == 0 else None)
        kill_count += 1

    # Отмечаем смерти
    death_count = 0

    for row in player_deaths.iter_rows(named=True):
        x = row["victim_x"]
        y = row["victim_y"]

        if x is None or y is None:
            continue

        px, py = plot.world_to_pixel(map_name, (x, y))

        ax.scatter(px, py, marker="x", s=65, label="Death" if death_count == 0 else None)
        death_count += 1

    ax.legend()

    # Сохраняем карту
    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "heatmaps"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "mirage_positions.png"

    fig.savefig(output_path, dpi=200, bbox_inches="tight")

    print("\nКарта с позициями сохранена:")
    print(output_path)

    print("Убийств отмечено:", kill_count)
    print("Смертей отмечено:", death_count)

    return output_path

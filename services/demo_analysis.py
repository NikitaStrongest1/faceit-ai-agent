
from pathlib import Path
from awpy import Demo, plot


def analyze_demo(demo_path, player_steam_id):

    print("\nЗагружаем демо для создания Heatmap...")

    demo = Demo(demo_path)
    demo.load("kills", "damages")

    player_steam_id = int(player_steam_id)
    map_name = demo.header["map_name"]

    # Создаём папку для изображений
    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "heatmaps"
    output_dir.mkdir(exist_ok=True)

    print("Карта:", map_name)

    # Получаем события убийств
    kills = demo.kills

    # Убийства игрока
    player_kills = kills.filter(
        kills["attacker_steamid"] == player_steam_id
    )

    # Смерти игрока
    player_deaths = kills.filter(
        kills["victim_steamid"] == player_steam_id
    )

    # Координаты убийств
    kill_points = (
        player_kills
        .select("attacker_x", "attacker_y")
        .drop_nulls()
        .rows()
    )

    # Координаты смертей
    death_points = (
        player_deaths
        .select("victim_x", "victim_y")
        .drop_nulls()
        .rows()
    )

    # 1. HEATMAP УБИЙСТВ
    if kill_points:
        fig, ax = plot.heatmap(
            map_name,
            kill_points,
            method="kde"
        )

        fig.savefig(
            output_dir / "kill_heatmap.png",
            dpi=200,
            bbox_inches="tight"
        )

        print("Kill Heatmap сохранена.")

    else:
        print("Нет координат убийств.")

    # 2. HEATMAP СМЕРТЕЙ
    if death_points:
        fig, ax = plot.heatmap(
            map_name,
            death_points,
            method="kde"
        )

        fig.savefig(
            output_dir / "death_heatmap.png",
            dpi=200,
            bbox_inches="tight"
        )

        print("Death Heatmap сохранена.")

    else:
        print("Нет координат смертей.")

    # 3. HEATMAP ПОЗИЦИЙ
    print("\nСобираем позиции игрока...")

    snapshots = demo.snapshots(seconds=2.0)

    print("Доступные столбцы:", snapshots.columns)

    if "steamid" in snapshots.columns:
        player_positions = snapshots.filter(
            snapshots["steamid"] == player_steam_id
        )

        if "x" in snapshots.columns and "y" in snapshots.columns:

            position_points = (
                player_positions
                .select("x", "y")
                .drop_nulls()
                .rows()
            )

            if position_points:
                fig, ax = plot.heatmap(
                    map_name,
                    position_points,
                    method="kde"
                )

                fig.savefig(
                    output_dir / "position_heatmap.png",
                    dpi=200,
                    bbox_inches="tight"
                )

                print("Position Heatmap сохранена.")

            else:
                print("Нет координат позиций игрока.")

    else:
        print("В snapshots не найден Steam ID игрока.")

    print("\nВсе доступные Heatmap сохранены в:")
    print(output_dir)

    return demo

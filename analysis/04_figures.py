"""Draft figures for the analysis report (static PNG, docs/figures/).

Run:  python -m analysis.04_figures
"""

import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "docs" / "figures"

# Colours: validated categorical slots 1-3 and one sequential blue ramp.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#256abf", "#0d366b"]
INK, SECONDARY, MUTED, GRID, AXIS, SURFACE, NO_DATA = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb", "#e9e8e3"
MIN_CHILDREN = 100
NEAR_M = 400

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 10,
    "axes.edgecolor": AXIS, "axes.labelcolor": SECONDARY, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": SECONDARY, "ytick.labelcolor": SECONDARY,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "savefig.dpi": 160,
})


def title(fig, headline: str, subtitle: str) -> None:
    fig.text(0.02, 0.975, headline, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.925, subtitle, fontsize=9.5, color=SECONDARY, va="top")


def save(fig, name: str, source: str) -> None:
    fig.text(0.02, 0.012, source, fontsize=7.5, color=MUTED, va="bottom")
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / name)
    plt.close(fig)


def percent(value: float) -> str:
    # The small offset keeps values such as 74.5 from being rounded down (round-half-even).
    return f"{value * 100 + 1e-6:.0f} %"


def distance_curves(homes: pd.DataFrame) -> None:
    distances = np.arange(0, 1001, 20)
    children = homes["children"].values
    series = [
        ("Luftlinie", "playground_air_m", BLUE, 1.02),
        ("Fußweg", "playground_net_m", ORANGE, 0.955),
        ("Fußweg ohne Querung\neiner Hauptstraße", "playground_no_main_road_m", AQUA, 0.86),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.11, right=0.78, top=0.83, bottom=0.14)
    for label, column, colour, label_y in series:
        shares = [children[homes[column].values <= d].sum() / children.sum() for d in distances]
        ax.plot(distances, shares, color=colour, linewidth=2)
        ax.text(1012, label_y, label, color=INK, fontsize=9, va="center")
        at_400 = shares[list(distances).index(NEAR_M)]
        ax.plot(NEAR_M, at_400, "o", color=colour, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(NEAR_M - 14, at_400 + 0.012, percent(at_400), color=INK, fontsize=9, ha="right", va="bottom")
    ax.axvline(NEAR_M, color=AXIS, linewidth=1, linestyle=(0, (3, 3)))
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f} %")
    ax.set_xlabel("Entfernung zum nächsten öffentlichen Spielplatz in Metern")
    ax.set_ylabel("Anteil der Kinder und Jugendlichen unter 18")
    title(fig, "Der Spielplatz um die Ecke ist oft weiter weg, als die Karte verspricht",
          "Anteil der unter 18-Jährigen, die höchstens die jeweilige Entfernung vom nächsten öffentlichen Spielplatz wohnen")
    save(fig, "01_luftlinie_vs_fussweg.png", "Daten: Grünanlagenbestand (SenMVKU), Einwohnerdichte 2025 (AfS), ALKIS-Gebäude, OpenStreetMap-Wegenetz. Eigene Berechnung.")


def reach_map(plr: pd.DataFrame) -> None:
    areas = gpd.read_file(ROOT / "data" / "raw" / "lor_plr.geojson").set_index("plr_id").join(plr[["children", "playground_share_400_net"]])
    bounds = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
    labels = ["unter 20 %", "20 bis unter 40 %", "40 bis unter 60 %", "60 bis unter 80 %", "80 % und mehr"]
    valid = areas["children"] >= MIN_CHILDREN
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.05)
    areas[~valid].plot(ax=ax, color=NO_DATA, edgecolor=SURFACE, linewidth=0.3, hatch="////")
    areas[valid].plot(ax=ax, column="playground_share_400_net", cmap=ListedColormap(SEQUENTIAL_BLUE), norm=BoundaryNorm(bounds, 5), edgecolor=SURFACE, linewidth=0.3)
    handles = [Patch(facecolor=c, edgecolor=AXIS, linewidth=0.5, label=l) for c, l in zip(SEQUENTIAL_BLUE, labels)]
    handles.append(Patch(facecolor=NO_DATA, edgecolor=MUTED, linewidth=0.5, hatch="////", label=f"weniger als {MIN_CHILDREN} Kinder"))
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=8.5, title="Anteil der Kinder mit Spielplatz\nin 400 m Fußweg", title_fontsize=8.5, alignment="left")
    ax.set_axis_off()
    title(fig, "Kurze Wege in der Innenstadt, lange am Stadtrand",
          "Anteil der unter 18-Jährigen mit einem öffentlichen Spielplatz in höchstens 400 m Fußweg, je Planungsraum")
    save(fig, "02_karte_spielplatz_400m.png", "Daten: Grünanlagenbestand (SenMVKU), Einwohnerdichte 2025 und LOR (AfS), ALKIS, OpenStreetMap. Eigene Berechnung.")


def social_status(findings: dict) -> None:
    groups = findings["by_social_status"]
    order = ["hoch", "mittel", "niedrig", "sehr niedrig"]
    panels = [
        ("Spielplatz in 400 m Fußweg", "share_playground_400_walking", percent, 1.0),
        ("Erreichbare Spielfläche je Kind\n(1000 m Fußweg)", "reachable_m2_per_child_1000", lambda v: f"{v:.1f} m²".replace(".", ","), 5.0),
        ("Jugendfreizeiteinrichtung in 1000 m\n(10- bis 17-Jährige)", "share_teens_youth_facility_1000", percent, 1.0),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10, 4.3), sharey=True)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.72, bottom=0.12, wspace=0.12)
    for ax, (label, key, fmt, limit) in zip(axes, panels):
        values = [groups[g][key] for g in order]
        ax.barh(order[::-1], values[::-1], color=BLUE, height=0.55)
        for position, value in zip(order[::-1], values[::-1]):
            ax.text(value + limit * 0.02, position, fmt(value), va="center", fontsize=9, color=INK)
        ax.set_xlim(0, limit * 1.22)
        ax.set_title(label, fontsize=9.5, color=INK, loc="left", pad=8)
        ax.set_xticks([])
        ax.grid(False)
        ax.spines["bottom"].set_visible(False)
    axes[0].set_ylabel("Sozialer Status des Planungsraums\n(Status-Index MSS 2025)")
    title(fig, "Kinder in Quartieren mit hohem Status wohnen am weitesten von öffentlichen Angeboten",
          "Nach Status-Index des Monitorings Soziale Stadtentwicklung 2025; Mittelwerte gewichtet mit der Zahl der Kinder")
    save(fig, "03_sozialer_status.png", "Daten: MSS 2025 (SenStadt), Grünanlagenbestand, Jugendfreizeiteinrichtungen (SenBJF), Einwohnerdichte 2025. Eigene Berechnung.")


def growth_scatter(plr: pd.DataFrame) -> None:
    valid = plr[(plr["children_2022"] >= MIN_CHILDREN) & (plr["children"] >= MIN_CHILDREN)]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.83, bottom=0.14)
    ax.scatter(valid["children_change_2022_2025"] * 100, valid["playground_share_400_net"] * 100, s=valid["children"] / 25, color=BLUE, alpha=0.45, edgecolor=SURFACE, linewidth=0.6)
    notable = valid[(valid["children_change_2022_2025"] >= 0.2) & (valid["playground_share_400_net"] < 0.45) & (valid["children"] >= 1000)].nlargest(4, "children")
    for _, row in notable.iterrows():
        ax.annotate(row["plr_name"], (row["children_change_2022_2025"] * 100, row["playground_share_400_net"] * 100), xytext=(6, 4), textcoords="offset points", fontsize=8.5, color=INK)
    ax.axvline(0, color=AXIS, linewidth=1)
    ax.set_xlim(-30, 60)
    ax.set_ylim(0, 102)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f} %")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f} %")
    ax.set_xlabel("Veränderung der Zahl der unter 18-Jährigen, Ende 2022 bis Ende 2025")
    ax.set_ylabel("Kinder mit Spielplatz in 400 m Fußweg")
    title(fig, "Wo die Zahl der Kinder wächst, sind die Wege zum Spielplatz länger",
          "Jeder Punkt ist ein Planungsraum; Punktgröße nach Zahl der Kinder. Nicht dargestellt: Werte außerhalb −30 % bis +60 %")
    save(fig, "04_wachstum_und_erreichbarkeit.png", "Daten: Einwohnerdichte 2022 und 2025 (AfS), Grünanlagenbestand (SenMVKU). Eigene Berechnung.")


def scenarios() -> None:
    green = pd.read_csv(PROCESSED / "scenario_new_playgrounds.csv")
    schools = pd.read_csv(PROCESSED / "scenario_schoolyards.csv")
    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.1, right=0.74, top=0.83, bottom=0.14)
    for table, label, colour in [(green, "Neuer Spielplatz in einer\nbestehenden Grünanlage", BLUE), (schools, "Geöffneter Schulhof einer\nöffentlichen Grundschule", ORANGE)]:
        ax.plot(table["step"], table["cumulative"], color=colour, linewidth=2, marker="o", markersize=4, markeredgecolor=SURFACE, markeredgewidth=0.8)
        ax.text(table["step"].iloc[-1] + 0.6, table["cumulative"].iloc[-1], f"{label}\n{table['cumulative'].iloc[-1]:,} Kinder".replace(",", "."), fontsize=9, color=INK, va="center")
    ax.set_xlim(0, 25.3)
    ax.set_ylim(0, 22000)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    ax.set_xlabel("Anzahl der Standorte (jeweils der wirksamste nächste)")
    ax.set_ylabel("Zusätzlich erreichte Kinder (kumuliert)")
    title(fig, "Modellrechnung: Wenige Standorte würden viele Kinder zusätzlich erreichen",
          "Kinder, die bisher keinen öffentlichen Spielplatz in 400 m Fußweg haben und ihn dann hätten. Hypothetisches Szenario.")
    save(fig, "05_szenarien.png", "Greedy-Maximum-Coverage ohne Doppelzählung. Machbarkeit, Eigentum und Kosten sind nicht geprüft. Eigene Berechnung.")


def housing_types(homes: pd.DataFrame) -> None:
    groups = homes.groupby("typklar").apply(
        lambda g: pd.Series({
            "children": g["children"].sum(),
            "official": g.loc[g["playground_net_m"] <= NEAR_M, "children"].sum() / max(g["children"].sum(), 1),
            "with_osm": g.loc[g["playground_incl_osm_net_m"] <= NEAR_M, "children"].sum() / max(g["children"].sum(), 1),
        }), include_groups=False)
    top = groups.nlargest(9, "children").sort_values("official")
    short = lambda name: name.split(" (")[0].split(",")[0][:48]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(left=0.40, right=0.95, top=0.76, bottom=0.12)
    rows = np.arange(len(top))
    ax.hlines(rows, top["official"], top["with_osm"], color=AXIS, linewidth=2)
    ax.scatter(top["official"], rows, s=70, color=BLUE, zorder=3, edgecolor=SURFACE, linewidth=1.5, label="nur öffentliche Spielplätze (amtlicher Bestand)")
    ax.scatter(top["with_osm"], rows, s=70, color=ORANGE, zorder=3, edgecolor=SURFACE, linewidth=1.5, label="zusätzlich weitere in OpenStreetMap erfasste Spielplätze")
    for row, (_, record) in zip(rows, top.iterrows()):
        ax.text(record["official"] - 0.02, row, percent(record["official"]), ha="right", va="center", fontsize=8.5, color=INK)
        ax.text(record["with_osm"] + 0.02, row, percent(record["with_osm"]), ha="left", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(rows, [f"{short(name)}\n{record['children']:,.0f} Kinder".replace(",", ".") for name, record in top.iterrows()], fontsize=8.5)
    ax.set_xlim(0, 1.1)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f} %")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.68, 1.01), frameon=False, fontsize=8.5, ncol=1)
    title(fig, "Großsiedlungen: Der amtliche Bestand zeigt nur einen Teil der Spielplätze",
          "Anteil der Kinder mit einem Spielplatz in 400 m Fußweg, nach Bebauungstyp des Wohnblocks (neun häufigste Typen)")
    save(fig, "06_bebauungstypen.png", "Daten: Stadtstrukturtypen und Einwohnerdichte 2025 (Umweltatlas/AfS), Grünanlagenbestand, OpenStreetMap. Eigene Berechnung.")


def main() -> None:
    homes = pd.read_csv(INTERIM / "homes_supply.csv", dtype={"block_id": str, "plr_id": str})
    plr = pd.read_csv(PROCESSED / "plr_indicators.csv", dtype={"plr_id": str}).set_index("plr_id")
    findings = json.loads((PROCESSED / "findings.json").read_text())
    distance_curves(homes)
    reach_map(plr)
    social_status(findings)
    growth_scatter(plr)
    scenarios()
    housing_types(homes)
    print(f"figures written to {FIGURES}")


if __name__ == "__main__":
    main()

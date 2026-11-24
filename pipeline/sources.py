"""Central registry of all raw data sources.

Every source used anywhere in the pipeline or analysis is listed here. The
downloader, docs/DATA_SOURCES.md and the "Daten und Methodik" page of the web
application are all generated from this one list.
"""

from dataclasses import dataclass

WFS_BASE = "https://gdi.berlin.de/services/wfs"
PORTAL_BASE = "https://daten.berlin.de/datensaetze"
ANALYSIS_CRS = "EPSG:25833"  # ETRS89 / UTM 33N: metric, official CRS of Berlin geodata


@dataclass(frozen=True)
class Source:
    key: str  # file name (stem) under data/raw/
    title: str  # official German title, shown to users
    provider: str
    license: str
    reference_date: str  # what point in time the data describes
    used_for: str  # German, shown to users
    dataset_page: str  # human-readable landing page (daten.berlin.de where available)
    attribution: str | None = None  # required attribution text, if the licence demands one


@dataclass(frozen=True)
class WfsSource(Source):
    service: str = ""
    layer: str = ""
    cql_filter: str | None = None  # server-side attribute filter
    properties: str | None = None  # comma-separated attribute subset (geometry is then omitted, bbox remains)

    @property
    def url(self) -> str:
        return f"{WFS_BASE}/{self.service}"

    @property
    def file_name(self) -> str:
        return f"{self.key}.geojson"


@dataclass(frozen=True)
class FileSource(Source):
    url: str = ""

    @property
    def file_name(self) -> str:
        return self.key


DL_ZERO = "Datenlizenz Deutschland – Zero – Version 2.0"
DL_BY = "Datenlizenz Deutschland – Namensnennung – Version 2.0"
CC_BY_DE = "CC BY 3.0 DE"
SEN_MVKU = "Senatsverwaltung für Mobilität, Verkehr, Klimaschutz und Umwelt Berlin"
SEN_SBW = "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin"
SEN_BJF = "Senatsverwaltung für Bildung, Jugend und Familie Berlin"
AFS = "Amt für Statistik Berlin-Brandenburg"
GREEN_PAGE = f"{PORTAL_BASE}/grunanlagenbestand-berlin-einschliesslich-der-offentlichen-spielplatze-wfs-737fd0a4"
GREEN_TITLE = "Grünanlagenbestand Berlin (einschließlich der öffentlichen Spielplätze)"
MSS_PAGE = f"{PORTAL_BASE}/monitoring-soziale-stadtentwicklung-mss-2025-wfs-67692212"
MSS_TITLE = "Monitoring Soziale Stadtentwicklung (MSS) 2025"

WFS_SOURCES = [
    WfsSource(
        "lor_plr", "Lebensweltlich orientierte Räume (LOR), Planungsräume, Stand 01.01.2021", AFS, CC_BY_DE, "2021",
        "Räumliche Bezugseinheit (542 Planungsräume)",
        f"{PORTAL_BASE}/lebensweltlich-orientierte-raume-lor-01-01-2021-wfs-34c86848",
        "Amt für Statistik Berlin-Brandenburg / Lebensweltlich orientierte Räume (LOR) (01.01.2021)",
        service="lor_2021", layer="a_lor_plr_2021",
    ),
    WfsSource(
        "blocks_population_2025", "Einwohnerdichte 2025 (Umweltatlas)", AFS, CC_BY_DE, "31.12.2025",
        "Einwohner nach Altersgruppen je Block, Bebauungstyp",
        f"{PORTAL_BASE}/einwohnerdichte-2025-umweltatlas-wfs-b2654f6b",
        "Amt für Statistik Berlin-Brandenburg / Einwohnerdichte 2025 (Umweltatlas)",
        service="ua_einwohnerdichte_2025", layer="ua_einwohnerdichte_2025",
    ),
    WfsSource(
        "blocks_population_2022", "Einwohnerdichte 2022 (Umweltatlas)", AFS, CC_BY_DE, "31.12.2022",
        "Vergleichsstand für die Veränderung der Kinderzahl (erstes Jahr mit Altersgruppen)",
        f"{PORTAL_BASE}/einwohnerdichte-2022-umweltatlas-wfs-8536f5b2",
        "Amt für Statistik Berlin-Brandenburg / Einwohnerdichte 2022 (Umweltatlas)",
        service="ua_einwohnerdichte_2022", layer="einwohnerdichte2022",
    ),
    # Attributes only: the location of each building is taken from its bounding box.
    # ALKIS function codes below 1300 are residential or mixed residential use.
    WfsSource(
        "residential_buildings", "ALKIS Berlin Gebäude", SEN_SBW, DL_ZERO, "11/2026",
        "Verteilung der Einwohner eines Blocks auf die Wohngebäude",
        f"{PORTAL_BASE}/alkis-berlin-gebaude-wfs-728b368a",
        service="alkis_gebaeude", layer="gebaeude", cql_filter="gfk<1300", properties="gfk,aog,shape_area",
    ),
    WfsSource(
        "playgrounds", f"{GREEN_TITLE} – Spielplätze", SEN_MVKU, DL_ZERO, "04/2026",
        "Öffentliche Spielplätze mit Netto-Spielfläche", GREEN_PAGE,
        service="gruenanlagen", layer="spielplaetze",
    ),
    WfsSource(
        "green_spaces", f"{GREEN_TITLE} – Grünanlagen", SEN_MVKU, DL_ZERO, "04/2026",
        "Erreichbarkeit von Grünanlagen, mögliche Standorte im Szenario", GREEN_PAGE,
        service="gruenanlagen", layer="gruenanlagen",
    ),
    WfsSource(
        "youth_facilities", "Jugendfreizeiteinrichtungen", SEN_BJF, DL_ZERO, "12/2025",
        "Angebote für Jugendliche mit Platzzahl",
        f"{PORTAL_BASE}/jugendfreizeiteinrichtungen-wfs-fc9dc3cf",
        service="jfe", layer="jfe",
    ),
    WfsSource(
        "daycare", "Kindertagesstätten", SEN_BJF, DL_ZERO, "12/2025",
        "Kita-Standorte mit genehmigten Plätzen",
        f"{PORTAL_BASE}/kindertagesstatten-wfs-d03b94d2",
        service="kita", layer="kita",
    ),
    WfsSource(
        "schools", "Schulen", SEN_SBW, DL_ZERO, "Schuljahr 2026/27",
        "Öffentliche Grundschulen: Schulweg, Schulhof-Szenario",
        f"{PORTAL_BASE}/schulen-wfs-ebc64e18",
        service="schulen", layer="schulen",
    ),
    WfsSource(
        "sports_sites", "Standorte öffentlicher Sportanlagen", "Senatsverwaltung für Inneres und Sport Berlin", DL_ZERO, "12/2025",
        "Erreichbarkeit von Sportanlagen",
        f"{PORTAL_BASE}/standorte-offentlicher-sportanlagen-wfs-a291318f",
        service="sportstandorte", layer="sportstandorte",
    ),
    WfsSource(
        "mss2025_index_indicators", f"{MSS_TITLE} – Index-Indikatoren", SEN_SBW, DL_ZERO, "31.12.2024",
        "Kinderarmut, Kinder in alleinerziehenden Haushalten", MSS_PAGE,
        service="mss_2025", layer="mss2025_indexind_542",
    ),
    WfsSource(
        "mss2025_context_indicators", f"{MSS_TITLE} – Kontext-Indikatoren", SEN_SBW, DL_ZERO, "31.12.2024",
        "Wohnfläche je Einwohner", MSS_PAGE,
        service="mss_2025", layer="mss2025_kontextind_542",
    ),
    WfsSource(
        "mss2025_indices", f"{MSS_TITLE} – Indizes", SEN_SBW, DL_ZERO, "31.12.2024",
        "Status-Index der Planungsräume", MSS_PAGE,
        service="mss_2025", layer="mss2025_indizes_542",
    ),
    WfsSource(
        "envjustice_multi", "Umweltgerechtigkeit 2023/2024 (Umweltatlas) – Integrierte Mehrfachbelastung", SEN_MVKU, DL_ZERO, "2023/2024",
        "Lärm, Luft, Hitze und Grünversorgung je Planungsraum",
        f"{PORTAL_BASE}/umweltgerechtigkeit-2023-2024-umweltatlas-wfs-2d02ba21",
        service="ua_umweltgerechtigkeit2023", layer="f_mehrfach4_2023",
    ),
]

UNFALLATLAS_YEARS = range(2018, 2025)  # Berlin is included in the Unfallatlas since 2018
OSM_ATTRIBUTION = "© OpenStreetMap-Mitwirkende"

FILE_SOURCES = [
    FileSource(
        "accidents_berlin_2025.csv", "Verkehrsunfallsituation Berlin 2025", "Polizei Berlin", "CC BY 4.0", "2025",
        "Beteiligte Kinder und Jugendliche (berlinweite Kontextzahl; ohne Koordinaten)",
        f"{PORTAL_BASE}/verkehrsunfallsituation-berlin", "Polizei Berlin",
        url="https://www.berlin.de/polizei/_assets/aufgaben/anlagen-verkehrssicherheit/verkehrsunfaelle-2025-csv.csv",
    ),
    *[
        FileSource(
            f"unfallatlas_{year}.zip", f"Unfallatlas – Unfallorte {year}", "Statistische Ämter des Bundes und der Länder", DL_BY, str(year),
            "Unfälle mit verletzten Fußgängern und Radfahrenden im Umfeld von Grundschulen",
            "https://unfallatlas.statistikportal.de/", "Statistische Ämter des Bundes und der Länder, Unfallatlas",
            url=f"https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte{year}_EPSG25832_CSV.zip",
        )
        for year in UNFALLATLAS_YEARS
    ],
    FileSource(
        "berlin.osm.pbf", "OpenStreetMap, Auszug Berlin (Geofabrik)", "OpenStreetMap-Mitwirkende", "ODbL 1.0", "11/2026",
        "Fußwegenetz, Querungen, weitere Spielplätze, Bibliotheken, Bahn- und Gewässerbarrieren",
        "https://download.geofabrik.de/europe/germany/berlin.html", OSM_ATTRIBUTION,
        url="https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf",
    ),
]

ALL_SOURCES: list[Source] = [*WFS_SOURCES, *FILE_SOURCES]

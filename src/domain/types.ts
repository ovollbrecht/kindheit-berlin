/** Shapes of the static data files under public/data (written by pipeline/export_frontend.py). */

export type ReachVariant = 'walking' | 'straight' | 'withOsm'

/** Share of children with a playground within each threshold of `IndicatorData.reachThresholdsM`. */
export type ReachByThreshold = Record<ReachVariant, number[]>

/** Indicators that exist for a planning area and for Berlin as a whole. */
export interface AreaValues {
  residents: number
  children: number
  age0to5: number
  age6to9: number
  age10to17: number
  childShare: number | null
  childrenChange: number | null
  densityPerHa: number | null
  playM2PerResidentInside: number | null
  playgroundMedianM: number | null
  playM2PerChild: number | null
  shareNoMainRoad400: number | null
  smallChildren200: number | null
  youthShare1000: number | null
  youthMedianM: number | null
  youthPlacesPer100: number | null
  daycareMedianM: number | null
  daycarePlacesPerChild: number | null
  primarySchoolMedianM: number | null
  greenShare400: number | null
  sportsMedianM: number | null
  libraryMedianM: number | null
  childPoverty: number | null
  singleParent: number | null
  livingSpace: number | null
  reach: ReachByThreshold | null
}

export interface PlanningArea extends AreaValues {
  id: string
  name: string
  /** Bezirksregion */
  region: string
  /** Bezirk */
  district: string
  /** "Innere Stadt" or "Äußere Stadt" */
  zone: string
  /** False if the area has too few children for stable child-weighted values. */
  enoughChildren: boolean
  playgroundsInside: number | null
  accidentsSchoolRun: number | null
  statusIndex: string | null
  envBurdens: string | null
  envNoise: string | null
  envAir: string | null
  envHeat: string | null
  envGreen: string | null
}

export interface IndicatorData {
  generated: string
  populationReferenceDate: string
  reachThresholdsM: number[]
  minChildrenForShares: number
  city: AreaValues
  areas: PlanningArea[]
}

export interface DistanceCurves {
  distancesM: number[]
  series: Record<'straight' | 'walking' | 'securedCrossings' | 'noMainRoad' | 'withOsm', number[]>
}

export interface HousingType {
  name: string
  fullName: string
  children: number
  hasGardens: boolean
  shareOfficial: number
  shareWithOsm: number
}

export interface GroupSummary {
  planning_areas: number
  children: number
  share_playground_400_walking: number
  reachable_m2_per_child_1000: number
  share_teens_youth_facility_1000: number
  youth_places_per_100_teens: number
  children_change_2022_2025: number
}

/** Subset of data/processed/findings.json that the story reads. Keys are the Python names. */
export interface Findings {
  reference: { residents: number; children_under_18: number; home_locations: number }
  straight_line_versus_walking: {
    children_within_400_straight_but_not_walking: number
    children_needing_main_road_crossing_for_400: number
    children_needing_unsecured_main_road_crossing_for_400: number
    walking_distance_quantiles_m: { p50: number }
    straight_distance_quantiles_m: { p50: number }
  }
  barriers: {
    share_by_barrier_on_straight_line: {
      railway: number
      motorway: number
      water: number
      no_linear_barrier: number
    }
  }
  supply_per_child: {
    city_m2_per_child: number
    city_m2_per_resident: number
    net_play_area_ha: number
  }
  by_social_status: Record<string, GroupSummary>
  by_city_zone: Record<string, GroupSummary>
  growth_2022_2025: {
    city_change: number
    planning_areas_growing_10pct: number
    children_added_in_growing_areas: number
    share_400_walking_growing: number
    share_400_walking_shrinking: number
    by_city_zone: Record<string, number>
  }
  age_groups: {
    share_0_5_playground_within_200: number
    share_0_5_daycare_within_400: number
    share_10_17_youth_facility_within_1000: number
    teens_without_youth_facility_within_1000: number
  }
  osm_robustness: {
    osm_playgrounds_in_berlin: number
    official_public_playgrounds: number
    osm_playgrounds_with_wheelchair_tag: number
    share_children_400_walking_official_only: number
    share_children_400_walking_official_plus_osm: number
    share_children_large_estates_400_official_only: number
    share_children_large_estates_400_official_plus_osm: number
  }
  data_gaps: {
    playgrounds: number
    playgrounds_without_construction_year: number
    playgrounds_without_renovation_year: number
  }
}

export interface StoryData {
  distanceCurves: DistanceCurves
  housingTypes: HousingType[]
  findings: Findings
}

export type ScenarioKey = 'greenSpace' | 'schoolyard'
/** "official": children without a public playground count as not yet served.
 *  "withOsm": only children without any known playground (official or OSM) count. */
export type ScenarioVariant = 'official' | 'withOsm'

export interface ScenarioStep {
  step: number
  id: string
  name: string
  district: string
  lon: number
  lat: number
  childrenReached: number
  cumulative: number
  areaM2?: number
}

export interface ScenarioData {
  scenarios: Record<
    ScenarioKey,
    {
      summary: Record<
        ScenarioVariant,
        {
          children_without_playground_400: number
          /** Number of sites the selection could choose from (one of the two is present). */
          candidate_green_spaces?: number
          public_primary_schools?: number
        }
      >
      variants: Record<ScenarioVariant, ScenarioStep[]>
    }
  >
}

export interface DataSource {
  key: string
  title: string
  provider: string
  license: string
  reference_date: string
  used_for: string
  dataset_page: string
  attribution: string | null
  retrieved: string | null
}

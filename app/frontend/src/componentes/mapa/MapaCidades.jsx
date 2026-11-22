import { MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { formatNumber, normalizeText } from "../../utils/format.js";
import { publicAssetUrl } from "../../utils/publicAssetUrl.js";
import "leaflet/dist/leaflet.css";
import "./MapaCidades.css";

const MUNICIPAL_ZOOM = 8;
// Paleta categórica de territórios — fita do Governo da Bahia em tons
// legíveis (>= 3:1 contra o fundo do mapa). Valores literais porque o
// Leaflet aplica cores como atributos SVG, onde var() não resolve.
const territoryColors = {
  1: "#044b8d", 2: "#0f8f93", 3: "#6f9a12", 4: "#a86f00", 5: "#c05a00",
  6: "#c01574", 7: "#c21f16", 8: "#0f5f96", 9: "#127a7e", 10: "#557512",
  11: "#8a5a10", 12: "#9a4a06", 13: "#a80d5d", 14: "#b3261e", 15: "#034179",
  16: "#0d7b7e", 17: "#5f840f", 18: "#905f00", 19: "#a54d00", 20: "#a51264",
  21: "#a71b13", 22: "#0d5281", 23: "#0f696c", 24: "#49650f", 25: "#774d0e",
  26: "#844005", 27: "#900b50",
};
const nameAliases = new Map([
  ["muquem do sao francisco", "muquem de sao francisco"],
  ["santa terezinha", "santa teresinha"],
]);
const normalize = (value) => {
  const normalized = normalizeText(value || "").trim().replace(/\s+/g, " ");
  return nameAliases.get(normalized) || normalized;
};
const colorForTerritory = (id) => territoryColors[String(id)] || "#bfc8cc";

/** Dá nome acessível ao container do Leaflet (o mapa não é operável só com o mouse). */
function MapAccessible({ label, describedBy }) {
  const map = useMap();
  useEffect(() => {
    const container = map.getContainer();
    container.setAttribute("role", "region");
    container.setAttribute("aria-label", label);
    if (describedBy) container.setAttribute("aria-describedby", describedBy);
  }, [map, label, describedBy]);
  return null;
}

function getTerritoryBorders(geoJson) {
  const segments = new Map();
  geoJson.features.forEach((feature) => {
    const polygons = feature.geometry.type === "Polygon"
      ? [feature.geometry.coordinates]
      : feature.geometry.coordinates;
    polygons.forEach((polygon) => polygon.forEach((ring) => {
      for (let index = 1; index < ring.length; index += 1) {
        const start = ring[index - 1];
        const end = ring[index];
        const startKey = start.join(",");
        const endKey = end.join(",");
        const key = startKey < endKey ? `${startKey}|${endKey}` : `${endKey}|${startKey}`;
        const territoryId = String(feature.properties.territorio_id);
        const segment = segments.get(key);
        if (segment) {
          segment.count += 1;
          segment.territoryIds.add(territoryId);
        } else {
          segments.set(key, { line: [start, end], count: 1, territoryIds: new Set([territoryId]) });
        }
      }
    }));
  });

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "MultiLineString",
      coordinates: Array.from(segments.values())
        .filter((segment) => segment.count === 1 || segment.territoryIds.size > 1)
        .map((segment) => segment.line),
    },
  };
}

function FitBahia({ geoJson }) {
  const map = useMap();
  useEffect(() => {
    const bounds = L.geoJSON(geoJson).getBounds();
    if (!bounds.isValid()) return;
    map.fitBounds(bounds, { padding: [18, 18], maxZoom: 7 });
    map.setMaxBounds(bounds.pad(0.04));
    map.options.maxBoundsViscosity = 1;
  }, [geoJson, map]);
  return null;
}

function ZoomLevel({ onChange }) {
  useMapEvents({ zoomend: (event) => onChange(event.target.getZoom()) });
  return null;
}

export default function MapaCidades({
  cidades = [],
  bolsasPorCidade = [],
  onSynchronizeTerritories,
  syncingTerritories = false,
  syncResult = "",
}) {
  const [geoJson, setGeoJson] = useState(null);
  const [mapError, setMapError] = useState("");
  const [zoom, setZoom] = useState(7);
  const [selection, setSelection] = useState(null);
  const detailed = zoom >= MUNICIPAL_ZOOM;

  useEffect(() => setSelection(null), [detailed]);

  useEffect(() => {
    const controller = new AbortController();
    fetch(publicAssetUrl("mapas/territorio_cidades_relacionados.json"), { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Não foi possível carregar os limites da Bahia.");
        return response.json();
      })
      .then((data) => setGeoJson(data))
      .catch((error) => { if (error.name !== "AbortError") setMapError(error.message); });
    return () => controller.abort();
  }, []);

  const cityIndex = useMemo(
    () => new Map(cidades.map((city) => [normalize(city.cidade), city])),
    [cidades],
  );
  const scholarshipsIndex = useMemo(
    () => new Map(bolsasPorCidade.map((city) => [normalize(city.cidade), city])),
    [bolsasPorCidade],
  );

  const territories = useMemo(() => {
    if (!geoJson) return [];
    const groups = new Map();
    for (const feature of geoJson.features) {
      const properties = feature.properties;
      const id = String(properties.territorio_id);
      if (!groups.has(id)) {
        groups.set(id, {
          id,
          name: properties.territorio_identidade,
          cities: [],
          population: 0,
          scholarships: 0,
        });
      }
      const group = groups.get(id);
      const city = cityIndex.get(normalize(properties.name));
      const scholarship = scholarshipsIndex.get(normalize(properties.name));
      const cityPopulation = Number(city?.populacao_estimada) || 0;
      const cityScholarships = Number(scholarship?.total) || 0;
      group.cities.push({
        name: properties.name,
        population: cityPopulation,
        scholarships: cityScholarships,
      });
      group.population += cityPopulation;
      group.scholarships += cityScholarships;
    }
    return [...groups.values()].sort((a, b) => Number(a.id) - Number(b.id));
  }, [geoJson, cityIndex, scholarshipsIndex]);

  const territoryById = useMemo(
    () => new Map(territories.map((territory) => [territory.id, territory])),
    [territories],
  );
  const territoryBorders = useMemo(() => geoJson ? getTerritoryBorders(geoJson) : null, [geoJson]);
  const selectedTerritory = selection?.type === "territory" ? territoryById.get(selection.id) : null;
  const selectedCity = selection?.type === "city" ? cityIndex.get(selection.key) : null;
  const selectedCityScholarships = selectedCity
    ? Number(scholarshipsIndex.get(normalize(selectedCity.cidade))?.total) || 0
    : 0;

  // Resumo textual: a mesma informação do mapa, legível por qualquer meio.
  const mapSummary = useMemo(() => {
    if (!territories.length) return null;
    const totalCities = territories.reduce((sum, territory) => sum + territory.cities.length, 0);
    const totalPopulation = territories.reduce((sum, territory) => sum + (territory.population || 0), 0);
    const totalScholarships = territories.reduce((sum, territory) => sum + (territory.scholarships || 0), 0);
    const top = [...territories].sort((a, b) => b.scholarships - a.scholarships)[0];
    return {
      totalCities,
      totalPopulation,
      totalScholarships,
      topName: top?.name,
      topScholarships: top?.scholarships || 0,
    };
  }, [territories]);

  const featureStyle = (feature) => ({
    color: detailed ? "#ffffff" : "transparent",
    weight: detailed ? 0.55 : 0,
    fillColor: colorForTerritory(feature?.properties?.territorio_id),
    fillOpacity: 0.9,
  });

  const bindFeatureEvents = (feature, layer) => {
    const properties = feature.properties;
    const city = cityIndex.get(normalize(properties.name));
    const tip = document.createElement("div");
    tip.textContent = detailed
      ? `${properties.name} · ${properties.territorio_identidade}`
      : properties.territorio_identidade;
    layer.bindTooltip(tip, { sticky: true });
    layer.on({
      click: () => setSelection(detailed
        ? { type: "city", key: normalize(properties.name) }
        : { type: "territory", id: String(properties.territorio_id) }),
      mouseover: () => { if (detailed) layer.setStyle({ weight: 1.8, color: "#044b8d" }); },
      mouseout: () => { if (detailed) layer.setStyle(featureStyle(feature)); },
    });
    if (!city) layer.setStyle({ fillOpacity: 0.65 });
  };

  return (
    <section className="panel city-map-panel">
      <div className="panel-header">
        <div>
          <h3>Territórios de identidade da Bahia</h3>
          <p>{detailed ? "Visualização municipal: selecione uma cidade para ver os detalhes." : "Visão territorial: selecione um território para consultar população e municípios."}</p>
        </div>
        <div className="map-header-actions">
          <span className="map-city-count">{detailed ? `${formatNumber(cidades.length)} municípios` : `${territories.length} territórios`}</span>
          <a className="map-table-link" href="#tabela-territorios">Ver em tabela</a>
          <button type="button" className="territory-sync-button" onClick={onSynchronizeTerritories} disabled={syncingTerritories}>
            {syncingTerritories ? "Sincronizando…" : "Atualizar territórios dos pesquisadores"}
          </button>
        </div>
      </div>
      <div className="city-map-layout">
        {geoJson ? <MapContainer
          className="bahia-map"
          center={[-12.7, -41.7]}
          zoom={7}
          minZoom={6}
          maxZoom={11}
          maxBoundsViscosity={1}
          scrollWheelZoom
          zoomControl
          keyboard
          style={{ backgroundColor: "#f3f4f6" }}
        >
          <MapAccessible label={detailed ? "Mapa dos municípios da Bahia. Use as setas do teclado para mover a visão." : `Mapa dos ${territories.length} territórios de identidade da Bahia. Use as setas do teclado para mover a visão.`} describedBy="mapa-resumo" />
          <FitBahia geoJson={geoJson} />
          <ZoomLevel onChange={setZoom} />
          <GeoJSON
            key={`${detailed}-${cidades.length}`}
            data={geoJson}
            style={featureStyle}
            onEachFeature={bindFeatureEvents}
          />
          {!detailed && territoryBorders && <GeoJSON
            data={territoryBorders}
            interactive={false}
            style={{ color: "#3f484c", weight: 1.35, opacity: 0.95 }}
          />}
        </MapContainer> : <div className="bahia-map map-loading" role={mapError ? "alert" : "status"}>{mapError || "Carregando mapa da Bahia…"}</div>}
        <aside className="city-map-aside">
          {selectedTerritory ? (
            <div className="selected-city-card" aria-live="polite">
              <span className="selected-city-kicker">TERRITÓRIO DE IDENTIDADE</span>
              <h4>{selectedTerritory.name}</h4>
              <dl>
                <div><dt>População estimada</dt><dd>{formatNumber(selectedTerritory.population)} habitantes</dd></div>
                <div><dt>Cidades envolvidas</dt><dd>{formatNumber(selectedTerritory.cities.length)} municípios</dd></div>
                <div><dt>Registros de bolsistas no recorte atual</dt><dd>{formatNumber(selectedTerritory.scholarships)}</dd></div>
              </dl>
              <div className="territory-city-list" aria-label={`Municípios de ${selectedTerritory.name}`}>
                {selectedTerritory.cities.slice().sort((a, b) => a.name.localeCompare(b.name, "pt-BR")).map((city) => (
                  <div key={city.name}>
                    <span>{city.name}</span><small>{formatNumber(city.population)} hab.</small>
                  </div>
                ))}
              </div>
              <button type="button" onClick={() => setSelection(null)}>Limpar seleção</button>
            </div>
          ) : selectedCity ? (
            <div className="selected-city-card" aria-live="polite">
              <span className="selected-city-kicker">MUNICÍPIO SELECIONADO</span>
              <h4>{selectedCity.cidade}</h4>
              <dl>
                <div><dt>Território de identidade</dt><dd>{selectedCity.territorio_identidade || "Não identificado"}</dd></div>
                <div><dt>População estimada</dt><dd>{formatNumber(selectedCity.populacao_estimada)} habitantes</dd></div>
                <div><dt>Registros de bolsistas no recorte atual</dt><dd>{formatNumber(selectedCityScholarships)}</dd></div>
              </dl>
              <button type="button" onClick={() => setSelection(null)}>Limpar seleção</button>
            </div>
          ) : (
            <div className="map-selection-hint"><span aria-hidden="true"><MapPin size={16} /></span><strong>{detailed ? "Explore os municípios" : "Explore os territórios"}</strong><p>{detailed ? "Clique em uma cidade no mapa para consultar seus dados." : "Clique em uma área colorida para ver a população e a lista de municípios."}</p></div>
          )}
          <div className="territory-map-legend">
            <strong>Territórios de identidade</strong>
            <div>{territories.map((territory) => <button key={territory.id} type="button" onClick={() => setSelection({ type: "territory", id: territory.id })}>
              <i style={{ backgroundColor: colorForTerritory(territory.id) }} />
              <span>{territory.name}</span>
              <small>{territory.cities.length}</small>
            </button>)}</div>
          </div>
        </aside>
      </div>
      {syncResult && <p className="territory-sync-result" role="status">{syncResult}</p>}
      {mapSummary && <p className="map-summary" id="mapa-resumo">
        <strong>Resumo dos territórios:</strong> {territories.length} territórios de identidade · {formatNumber(mapSummary.totalCities)} municípios · {formatNumber(mapSummary.totalPopulation)} habitantes estimados · {formatNumber(mapSummary.totalScholarships)} registros de bolsistas no recorte atual. O território com mais registros é {mapSummary.topName} ({formatNumber(mapSummary.topScholarships)}).
      </p>}
      <p className="map-data-note">População estimada conforme a base municipal incluída no projeto. O detalhe muda de território para município ao aproximar o zoom.</p>
    </section>
  );
}

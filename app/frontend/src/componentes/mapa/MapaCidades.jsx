import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { formatNumber, normalizeText } from "../../utils/format.js";
import "leaflet/dist/leaflet.css";
import "./MapaCidades.css";

const MUNICIPAL_ZOOM = 8;
const territoryColors = {
  1: "#ead091", 2: "#bbda92", 3: "#c9c0ed", 4: "#cfe195", 5: "#eaca7f",
  6: "#daac69", 7: "#c1dd94", 8: "#cec3ab", 9: "#c5dc92", 10: "#f2aed2",
  11: "#e9c67d", 12: "#f6acd2", 13: "#ead493", 14: "#ebd798", 15: "#f3aac5",
  16: "#e7db8d", 17: "#e8ce8c", 18: "#ecc17c", 19: "#ecdcb0", 20: "#e6d789",
  21: "#b0cae5", 22: "#e8b2cd", 23: "#f5aac4", 24: "#e8df91", 25: "#b8c5d3",
  26: "#e9bb78", 27: "#c7bdec",
};
const nameAliases = new Map([
  ["muquem do sao francisco", "muquem de sao francisco"],
  ["santa terezinha", "santa teresinha"],
]);
const normalize = (value) => {
  const normalized = normalizeText(value || "").trim().replace(/\s+/g, " ");
  return nameAliases.get(normalized) || normalized;
};
const colorForTerritory = (id) => territoryColors[String(id)] || "#d6ddd9";

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
    fetch("/mapas/territorio_cidades_relacionados.json", { signal: controller.signal })
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
      mouseover: () => { if (detailed) layer.setStyle({ weight: 1.8, color: "#263c36" }); },
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
          <span className="map-city-count">{detailed ? "Municípios" : "27 territórios"}</span>
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
          style={{ backgroundColor: "#f1f5f9" }}
        >
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
            style={{ color: "#53635e", weight: 1.35, opacity: 0.95 }}
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
                <div><dt>Bolsas no recorte atual</dt><dd>{formatNumber(selectedTerritory.scholarships)}</dd></div>
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
                <div><dt>Bolsas no recorte atual</dt><dd>{formatNumber(selectedCityScholarships)}</dd></div>
              </dl>
              <button type="button" onClick={() => setSelection(null)}>Limpar seleção</button>
            </div>
          ) : (
            <div className="map-selection-hint"><span>⌖</span><strong>{detailed ? "Explore os municípios" : "Explore os territórios"}</strong><p>{detailed ? "Clique em uma cidade no mapa para consultar seus dados." : "Clique em uma área colorida para ver a população e a lista de municípios."}</p></div>
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
      <p className="map-data-note">População estimada conforme a base municipal incluída no projeto. O detalhe muda de território para município ao aproximar o zoom.</p>
    </section>
  );
}

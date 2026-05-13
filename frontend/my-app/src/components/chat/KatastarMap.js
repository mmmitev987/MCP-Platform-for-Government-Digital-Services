import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet default marker icon paths broken by webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
});

/**
 * Mini Leaflet map shown in the chat when a katastar__search_property
 * response contains geometry data.
 *
 * Uses plain Leaflet (not react-leaflet) to avoid v5 tile-rendering quirks.
 *
 * Props:
 *   geometry: { centroid: [lat, lon], polygon: [[lat, lon], ...] }
 */
export default function KatastarMap({ geometry }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!geometry?.centroid || !el) return;

    // Clean up any existing Leaflet instance on this element.
    // React 18 StrictMode runs effects twice, so this guard is essential.
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }
    // Belt-and-suspenders: clear Leaflet's internal id flag on the container
    // so re-initialization doesn't throw "Map container is already initialized".
    if (el._leaflet_id) {
      el._leaflet_id = null;
    }

    const map = L.map(el, {
      center: geometry.centroid,
      zoom: 17,
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);

    const { polygon, centroid } = geometry;

    if (polygon && polygon.length > 0) {
      const poly = L.polygon(polygon, {
        color: "#6366f1",
        fillColor: "#6366f1",
        fillOpacity: 0.2,
        weight: 2,
      }).addTo(map);

      map.fitBounds(poly.getBounds(), { padding: [24, 24] });
    }

    // Always show a centroid marker
    L.marker(centroid).addTo(map);

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [geometry]);

  if (!geometry?.centroid) return null;

  return (
    <div
      ref={containerRef}
      style={{
        marginTop: "12px",
        borderRadius: "12px",
        overflow: "hidden",
        border: "1px solid #e0e7ff",
        height: "260px",
        width: "100%",
      }}
    />
  );
}

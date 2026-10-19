'use client';

import { useEffect, useState } from 'react';
import { DealerSummary } from '@/lib/types';
import 'leaflet/dist/leaflet.css';

type ReactLeafletModule = typeof import('react-leaflet');
type LeafletModule = typeof import('leaflet');
interface MapComponentState {
  MapContainer: ReactLeafletModule['MapContainer']; TileLayer: ReactLeafletModule['TileLayer'];
  Marker: ReactLeafletModule['Marker']; Popup: ReactLeafletModule['Popup']; L: LeafletModule;
}

interface DealerMapProps {
  dealers: DealerSummary[];
  onDealerClick: (dealerId: number) => void;
  isDark?: boolean;
}

export function DealerMap({ dealers, onDealerClick, isDark = false }: DealerMapProps) {
  const [MapComponents, setMapComponents] = useState<MapComponentState | null>(null);

  useEffect(() => {
    // Dynamically import Leaflet components (client-side only)
    import('react-leaflet').then((mod) => {
      import('leaflet').then((L) => {
        // Fix default marker icons
        const markerPrototype = L.Icon.Default.prototype as L.Icon.Default & { _getIconUrl?: unknown };
        delete markerPrototype._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
          iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        });
        setMapComponents({
          MapContainer: mod.MapContainer,
          TileLayer: mod.TileLayer,
          Marker: mod.Marker,
          Popup: mod.Popup,
          L,
        });
      });
    });
  }, []);

  if (!MapComponents) {
    return (
      <div className={`flex h-[500px] items-center justify-center rounded-3xl ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}>
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
          <p className={`mt-3 text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading map...</p>
        </div>
      </div>
    );
  }

  const { MapContainer, TileLayer, Marker, Popup, L } = MapComponents;

  // Center on Jordan
  const jordanCenter: [number, number] = [31.5, 36.5];

  // Custom marker icon
  const createCustomIcon = (index: number) => {
    return L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
          border: 3px solid white;
        ">
          <span style="
            transform: rotate(45deg);
            color: white;
            font-weight: bold;
            font-size: 14px;
          ">${index + 1}</span>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 36],
      popupAnchor: [0, -36],
    });
  };

  return (
    <div className="relative overflow-hidden rounded-3xl">
      <MapContainer
        center={jordanCenter}
        zoom={8}
        style={{ height: '500px', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isDark 
            ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
            : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
          }
        />
        {dealers.map((dealer, index) => {
          const location = dealer.location;
          if (!location?.lat || !location?.lng) return null;
          
          return (
            <Marker
              key={dealer.id}
              position={[location.lat, location.lng]}
              icon={createCustomIcon(index)}
            >
              <Popup>
                <div className="min-w-[200px] p-2">
                  <h3 className="text-lg font-bold text-slate-900">{dealer.name}</h3>
                  <p className="text-sm text-slate-600">{location.address || location.city}</p>
                  <div className="mt-2 flex items-center gap-2 text-sm text-slate-500">
                    <span>🚗 {dealer.total_listings} listings</span>
                  </div>
                  {dealer.top_makes?.length > 0 && (
                    <p className="mt-1 text-xs text-slate-400">
                      Top brands: {dealer.top_makes.map(m => m.make).join(', ')}
                    </p>
                  )}
                  <button
                    onClick={() => onDealerClick(dealer.id)}
                    className="mt-3 w-full rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-600"
                  >
                    View Showroom
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

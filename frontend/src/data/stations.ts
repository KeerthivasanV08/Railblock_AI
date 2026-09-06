import type { Station } from "@/types";

/** Real-world Chennai Egmore – Thoothukudi corridor derived from OpenStreetMap (69 stations). */
export const STATIONS: Station[] = [
  { station_code: "MS", name: "Chennai Egmore", km: 0.0, lat: 13.0777, lng: 80.2613, major: true },
  { station_code: "MBM", name: "Mambalam", km: 6.2, lat: 13.0381, lng: 80.2278, major: true },
  { station_code: "GDY", name: "Guindy", km: 10.0, lat: 13.0087, lng: 80.2126, major: true },
  { station_code: "STM", name: "St. Thomas Mount", km: 12.2, lat: 12.9948, lng: 80.1994, major: false },
  { station_code: "PZA", name: "Palavanthangal", km: 14.8, lat: 12.9906, lng: 80.1879, major: false },
  { station_code: "MN", name: "Meenambakkam", km: 16.3, lat: 12.9847, lng: 80.1751, major: false },
  { station_code: "TLM", name: "Tirusulam", km: 17.5, lat: 12.9805, lng: 80.1658, major: false },
  { station_code: "PV", name: "Pallavaram", km: 19.5, lat: 12.9676, lng: 80.1521, major: false },
  { station_code: "CMP", name: "Chromepet", km: 21.6, lat: 12.9522, lng: 80.1412, major: false },
  { station_code: "TBMS", name: "Tambaram Sanatorium", km: 23.7, lat: 12.937, lng: 80.1307, major: false },
  { station_code: "TBM", name: "Tambaram", km: 25.6, lat: 12.9258, lng: 80.1179, major: true },
  { station_code: "PRGL", name: "Perungalattur", km: 29.0, lat: 12.9052, lng: 80.095, major: false },
  { station_code: "VDR", name: "Vandalur", km: 30.9, lat: 12.8916, lng: 80.085, major: false },
  { station_code: "UPM", name: "Urappakkam", km: 33.9, lat: 12.8674, lng: 80.072, major: false },
  { station_code: "GI", name: "Guduvancheri", km: 36.9, lat: 12.8452, lng: 80.0576, major: false },
  { station_code: "CTM", name: "Kattangulathur", km: 42.4, lat: 12.8056, lng: 80.0266, major: false },
  { station_code: "SKL", name: "Singaperumal Koil", km: 48.1, lat: 12.7619, lng: 80.0008, major: false },
  { station_code: "CGL", name: "Chengalpattu Junction", km: 56.4, lat: 12.6935, lng: 79.9805, major: true },
  { station_code: "OV", name: "Ottivakkam", km: 64.8, lat: 12.6227, lng: 79.9753, major: false },
  { station_code: "KGZ", name: "Karunguzhi", km: 77.2, lat: 12.5321, lng: 79.9115, major: false },
  { station_code: "MMK", name: "Madurantakam", km: 80.9, lat: 12.5047, lng: 79.8933, major: true },
  { station_code: "MLMR", name: "Melmaruvattur", km: 91.8, lat: 12.4287, lng: 79.8329, major: true },
  { station_code: "TZD", name: "Tozhuppedu", km: 100.4, lat: 12.3689, lng: 79.7847, major: false },
  { station_code: "KSGL", name: "Karasangal", km: 105.7, lat: 12.3348, lng: 79.7505, major: false },
  { station_code: "OLA", name: "Olakur", km: 110.4, lat: 12.3049, lng: 79.7209, major: false },
  { station_code: "TMV", name: "Tindivanam", km: 121.9, lat: 12.2292, lng: 79.6515, major: true },
  { station_code: "MTL", name: "Mailam", km: 131.3, lat: 12.1603, lng: 79.6021, major: false },
  { station_code: "PEI", name: "Perani", km: 140.0, lat: 12.1029, lng: 79.5522, major: false },
  { station_code: "VVN", name: "Vikravandi", km: 146.5, lat: 12.0455, lng: 79.5427, major: false },
  { station_code: "MYP", name: "Mundiyampakkam", km: 153.1, lat: 11.9952, lng: 79.5116, major: false },
  { station_code: "VM", name: "Viluppuram Junction", km: 162.8, lat: 11.9417, lng: 79.4991, major: true },
  { station_code: "KDMD", name: "Kandambakkam", km: 171.3, lat: 11.8983, lng: 79.4555, major: false },
  { station_code: "TVNL", name: "Tiruvennainallur Road", km: 179.6, lat: 11.8413, lng: 79.4131, major: false },
  { station_code: "PVN", name: "Pavunur", km: 208.6, lat: 11.6009, lng: 79.3157, major: false },
  { station_code: "VRI", name: "Vriddhachalam Junction", km: 222.4, lat: 11.5333, lng: 79.3165, major: true },
  { station_code: "TLNR", name: "Talanallur", km: 231.2, lat: 11.4697, lng: 79.2693, major: false },
  { station_code: "PNDM", name: "Pennadam", km: 241.1, lat: 11.3984, lng: 79.221, major: false },
  { station_code: "ICG", name: "Ichchangadu", km: 244.3, lat: 11.3706, lng: 79.2194, major: false },
  { station_code: "MTUR", name: "Mathur", km: 250.4, lat: 11.3185, lng: 79.2062, major: false },
  { station_code: "SNDI", name: "Sendurai", km: 258.9, lat: 11.2553, lng: 79.1676, major: false },
  { station_code: "OTK", name: "Ottakovil", km: 267.3, lat: 11.2163, lng: 79.1011, major: false },
  { station_code: "ALU", name: "Ariyalur", km: 275.9, lat: 11.1489, lng: 79.0686, major: true },
  { station_code: "SLTH", name: "Sillakkudi", km: 282.8, lat: 11.0967, lng: 79.0372, major: false },
  { station_code: "KLGM", name: "Kallagam", km: 291.7, lat: 11.0252, lng: 79.005, major: false },
  { station_code: "KKPM", name: "Kallakkudi Palanganatham", km: 300.6, lat: 10.9665, lng: 78.9497, major: false },
  { station_code: "PMB", name: "Pullampadi", km: 305.3, lat: 10.9397, lng: 78.9171, major: false },
  { station_code: "KTTR", name: "Kattur", km: 313.8, lat: 10.8961, lng: 78.8555, major: false },
  { station_code: "LLI", name: "Lalgudi", km: 318.9, lat: 10.8754, lng: 78.8153, major: true },
  { station_code: "VLDE", name: "Valadi", km: 325.2, lat: 10.8726, lng: 78.758, major: false },
  { station_code: "SRGM", name: "Srirangam", km: 332.9, lat: 10.8577, lng: 78.696, major: true },
  { station_code: "TPTN", name: "Tiruchchirappalli Town", km: 336.3, lat: 10.8293, lng: 78.703, major: false },
  { station_code: "TP", name: "Tiruchchirapalli Fort", km: 341.3, lat: 10.8257, lng: 78.6891, major: false },
  { station_code: "TPE", name: "Tiruchchirappalli Palakarai", km: 343.4, lat: 10.8078, lng: 78.6942, major: false },
  { station_code: "TPJ", name: "Tiruchchirappalli Junction", km: 347.3, lat: 10.7943, lng: 78.6853, major: true },
  { station_code: "PUG", name: "Punggudi", km: 358.2, lat: 10.7473, lng: 78.6189, major: false },
  { station_code: "KLS", name: "Kolatur", km: 367.7, lat: 10.7005, lng: 78.5472, major: false },
  { station_code: "MPA", name: "Manapparai", km: 385.5, lat: 10.6073, lng: 78.4181, major: true },
  { station_code: "CII", name: "Chettiyapatti", km: 392.8, lat: 10.5726, lng: 78.3627, major: false },
  { station_code: "VPJ", name: "Vaiyampatti", km: 399.6, lat: 10.5434, lng: 78.3086, major: false },
  { station_code: "KFC", name: "Kalpattichatram", km: 407.8, lat: 10.5197, lng: 78.2383, major: false },
  { station_code: "AYR", name: "Ayyalur", km: 419.7, lat: 10.4864, lng: 78.1593, major: false },
  { station_code: "VDM", name: "Vadamadurai", km: 428.1, lat: 10.4368, lng: 78.1026, major: true },
  { station_code: "KON", name: "Kudalnagar", km: 482.5, lat: 9.9467, lng: 78.1052, major: false },
  { station_code: "MDU", name: "Madurai Junction", km: 486.2, lat: 9.9195, lng: 78.1102, major: true },
  { station_code: "TDN", name: "Tiruparankundram", km: 510.8, lat: 9.8791, lng: 78.0652, major: false },
  { station_code: "APK", name: "Aruppukkottai", km: 550.7, lat: 9.5246, lng: 78.1029, major: true },
  { station_code: "TIP", name: "Tattapparai", km: 628.6, lat: 8.8278, lng: 78.0232, major: true },
  { station_code: "MVN", name: "Milavittan", km: 640.7, lat: 8.8116, lng: 78.0877, major: true },
  { station_code: "TN", name: "Tuticorin", km: 648.2, lat: 8.806, lng: 78.1552, major: true },
];

export const stationByCode = (code: string) => STATIONS.find((s) => s.station_code === code);

export const CORRIDOR_START_KM = STATIONS[0].km;
export const CORRIDOR_END_KM = STATIONS[STATIONS.length - 1].km;

/** Interpolate a lat/lng along the corridor for an arbitrary chainage. */
export function kmToLatLng(km: number): { lat: number; lng: number } {
  const clamped = Math.min(Math.max(km, CORRIDOR_START_KM), CORRIDOR_END_KM);
  for (let i = 0; i < STATIONS.length - 1; i++) {
    const a = STATIONS[i];
    const b = STATIONS[i + 1];
    if (clamped >= a.km && clamped <= b.km) {
      const t = (clamped - a.km) / (b.km - a.km || 1);
      return { lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t };
    }
  }
  const last = STATIONS[STATIONS.length - 1];
  return { lat: last.lat, lng: last.lng };
}

export function kmToStationLabel(km: number): string {
  let nearest = STATIONS[0];
  for (const s of STATIONS) if (Math.abs(s.km - km) < Math.abs(nearest.km - km)) nearest = s;
  return nearest.station_code;
}

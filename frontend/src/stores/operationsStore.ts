import { create } from "zustand";
import type { DisruptionEvent, Train } from "@/types";
import { generateTrains } from "@/data/trains";
import { sectionForKm } from "@/data/sections";
import { liveTrainSocket, liveApi, type LiveTrainPosition } from "@/api";
import { useNotificationStore } from "./notificationStore";
import { useDisruptionStore } from "./disruptionStore";

export type SimSpeed = 0.5 | 1 | 2;

let evtSeq = 9100;
let isSocketSubscribed = false;

interface OperationsState {
  trains: Train[];
  playing: boolean;
  speed: SimSpeed;
  selectedTrainNumber: string | null;
  lastTick: number;
  play: () => void;
  pause: () => void;
  setSpeed: (s: SimSpeed) => void;
  select: (train_number: string | null) => void;
  tick: () => void;
  initLiveStream: () => void;
}

export const useOperationsStore = create<OperationsState>((set, get) => ({
  trains: generateTrains(),
  playing: true,
  speed: 1,
  selectedTrainNumber: null,
  lastTick: 0,

  play: () => set({ playing: true }),
  pause: () => set({ playing: false }),
  setSpeed: (speed) => set({ speed }),
  select: (selectedTrainNumber) => set({ selectedTrainNumber }),

  initLiveStream: () => {
    if (isSocketSubscribed || typeof window === "undefined") return;
    isSocketSubscribed = true;

    // Initial fetch of train positions from backend provider
    liveApi
      .getTrainPositions()
      .then((res) => {
        if (res?.items?.length) {
          const liveMap = new Map<string, LiveTrainPosition>(
            res.items.map((i) => [i.train_id || i.train_number || "", i]),
          );
          set((s) => ({
            trains: s.trains.map((t) => {
              const live = liveMap.get(t.train_number);
              if (live) {
                return {
                  ...t,
                  km: live.current_km ?? t.km,
                  speed_kmph: live.speed_kmph ?? t.speed_kmph,
                  delay_min: live.delay_minutes ?? t.delay_min,
                };
              }
              return t;
            }),
          }));
        }
      })
      .catch(() => {});

    // Subscribe to live telemetry WebSocket
    liveTrainSocket.subscribe((msg) => {
      if (msg?.event_type === "TRAIN_POSITION_UPDATED" && Array.isArray(msg.data)) {
        const liveItems = msg.data as LiveTrainPosition[];
        const liveMap = new Map<string, LiveTrainPosition>(
          liveItems.map((i) => [i.train_id || i.train_number || "", i]),
        );
        set((s) => ({
          trains: s.trains.map((t) => {
            const live = liveMap.get(t.train_number);
            if (live) {
              return {
                ...t,
                km: live.current_km ?? t.km,
                speed_kmph: live.speed_kmph ?? t.speed_kmph,
                delay_min: live.delay_minutes ?? t.delay_min,
              };
            }
            return t;
          }),
        }));
      }
    });
  },

  tick: () => {
    const { speed } = get();
    set((s) => ({
      lastTick: s.lastTick + 1,
      trains: s.trains.map((t) => {
        const step = (t.speed_kmph / 3600) * 6 * speed; // ~6s of simulated movement per tick
        let km = t.direction === "UP" ? t.km - step : t.km + step;
        let direction = t.direction;
        if (km > 440) {
          km = 440 - (km - 440);
          direction = "UP";
        } else if (km < 0) {
          km = -km;
          direction = "DOWN";
        }
        return { ...t, km, direction, section_id: sectionForKm(km).section_id };
      }),
    }));

    // Occasionally simulate a new delay event on a random train if in standalone simulation.
    if (get().lastTick > 10 && get().lastTick % 50 === 0) {
      const trains = get().trains;
      const idx = Math.floor(Math.random() * trains.length);
      const t = trains[idx];
      if (t && t.delay_min < 10) {
        const newDelay = t.delay_min + 15 + Math.round(Math.random() * 30);
        set((s) => ({
          trains: s.trains.map((tr) =>
            tr.train_number === t.train_number ? { ...tr, delay_min: newDelay } : tr,
          ),
        }));
        useNotificationStore.getState().push({
          type: "Train Delay",
          title: `${t.category} ${t.train_number} running ${newDelay} min late`,
          body: `Delay detected near Km ${t.km.toFixed(1)} on ${t.section_id}.`,
          href: "/live",
          severity: newDelay > 30 ? "Critical" : "Warning",
        });
        if (newDelay > 30) {
          const event: DisruptionEvent = {
            event_id: `EVT-${++evtSeq}`,
            type: "Train Delay",
            detected_at: new Date().toTimeString().slice(0, 5),
            train_number: t.train_number,
            delay_min: newDelay,
            section_id: t.section_id,
            location: t.section_id,
            affected_block_id: null,
            original_window: "—",
            available_window: "Reduced by delay",
            status: "Open",
            severity: "Warning",
          };
          useDisruptionStore.getState().injectDisruption(event);
        }
      }
    }
  },
}));

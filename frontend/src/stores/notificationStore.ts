import { create } from "zustand";
import type { AppNotification, AuditEvent } from "@/types";
import { generateAudit, generateNotifications } from "@/data/operations";
import { clockNow } from "@/utils/dateUtils";
import { useSettingsStore } from "./settingsStore";

let seq = 0;
const nextId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${seq++}`;

interface NotificationState {
  notifications: AppNotification[];
  audit: AuditEvent[];
  push: (n: Omit<AppNotification, "id" | "at" | "read">) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clearAll: () => void;
  logAudit: (
    action: string,
    entity: string,
    result?: AuditEvent["result"],
    detail?: string,
  ) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: generateNotifications(),
  audit: generateAudit(),
  push: (n) =>
    set((s) => ({
      notifications: [
        { ...n, id: nextId("N"), at: clockNow(), read: false },
        ...s.notifications,
      ].slice(0, 60),
    })),
  markRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)),
    })),
  markAllRead: () =>
    set((s) => ({ notifications: s.notifications.map((n) => ({ ...n, read: true })) })),
  clearAll: () => set({ notifications: [] }),
  logAudit: (action, entity, result = "Success", detail) =>
    set((s) => ({
      audit: [
        {
          id: nextId("A"),
          at: clockNow(),
          role: useSettingsStore.getState().role,
          action,
          entity,
          result,
          detail,
        },
        ...s.audit,
      ].slice(0, 200),
    })),
}));

export const unreadCount = (n: AppNotification[]) => n.filter((x) => !x.read).length;

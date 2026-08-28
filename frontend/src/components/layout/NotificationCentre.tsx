import { useNavigate } from "@tanstack/react-router";
import { AlertTriangle, Bell, CheckCheck, CircleDot, Info, Trash2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { unreadCount, useNotificationStore } from "@/stores/notificationStore";
import type { AppNotification } from "@/types";

const SEVERITY_ICON: Record<AppNotification["severity"], typeof Info> = {
  Critical: XCircle,
  Warning: AlertTriangle,
  Info: Info,
};

const SEVERITY_CLASS: Record<AppNotification["severity"], string> = {
  Critical: "text-crit",
  Warning: "text-warn",
  Info: "text-info",
};

export function NotificationCentre() {
  const notifications = useNotificationStore((s) => s.notifications);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const clearAll = useNotificationStore((s) => s.clearAll);
  const navigate = useNavigate();
  const unread = unreadCount(notifications);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Bell className="size-4" aria-hidden />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-crit text-[9px] font-bold text-crit-foreground">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between border-b border-border px-3 py-2">
          <p className="text-sm font-semibold text-foreground">Notifications</p>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-xs"
              onClick={markAllRead}
            >
              <CheckCheck className="size-3.5" aria-hidden /> Mark all read
            </Button>
            <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs" onClick={clearAll}>
              <Trash2 className="size-3.5" aria-hidden /> Clear
            </Button>
          </div>
        </div>
        <ScrollArea className="h-96">
          {notifications.length === 0 ? (
            <p className="px-3 py-8 text-center text-xs text-muted-foreground">No notifications.</p>
          ) : (
            notifications.map((n, i) => {
              const Icon = SEVERITY_ICON[n.severity];
              return (
                <div key={n.id}>
                  {i > 0 && <Separator />}
                  <button
                    onClick={() => {
                      markRead(n.id);
                      navigate({ to: n.href });
                    }}
                    className={cn(
                      "flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition-colors hover:bg-accent",
                      !n.read && "bg-accent/40",
                    )}
                  >
                    <Icon
                      className={cn("mt-0.5 size-3.5 shrink-0", SEVERITY_CLASS[n.severity])}
                      aria-hidden
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-xs font-medium text-foreground">{n.title}</p>
                        {!n.read && (
                          <CircleDot className="size-2.5 shrink-0 text-primary" aria-hidden />
                        )}
                      </div>
                      <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">
                        {n.body}
                      </p>
                      <p className="mt-1 text-[10px] text-muted-foreground">
                        {n.type} · {n.at}
                      </p>
                    </div>
                  </button>
                </div>
              );
            })
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

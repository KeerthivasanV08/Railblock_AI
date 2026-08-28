import type { LucideIcon } from "lucide-react";
import { AlertOctagon, Inbox, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  className,
}: {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: { label: string; onClick: () => void };
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border py-14 text-center",
        className,
      )}
    >
      <Icon className="size-6 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="max-w-sm text-xs text-muted-foreground">{description}</p>}
      {action && (
        <Button size="sm" variant="outline" className="mt-2" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function LoadingState({
  label = "Loading operational data…",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-2 py-14 text-center", className)}
    >
      <Loader2 className="size-5 animate-spin text-primary" aria-hidden />
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

export function ErrorState({
  title = "Unable to load data",
  description = "This is simulated frontend data — try refreshing the view.",
  onRetry,
  className,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-md border border-crit/30 bg-crit/5 py-14 text-center",
        className,
      )}
    >
      <AlertOctagon className="size-6 text-crit" aria-hidden />
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="max-w-sm text-xs text-muted-foreground">{description}</p>
      {onRetry && (
        <Button size="sm" variant="outline" className="mt-2" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

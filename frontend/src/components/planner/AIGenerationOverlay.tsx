import { Check, Loader2, Sparkles } from "lucide-react";
import { AI_STAGES } from "@/services/mock/aiService";
import { cn } from "@/lib/utils";

export function AIGenerationOverlay({ stage }: { stage: number }) {
  return (
    <div className="absolute inset-0 z-30 flex items-center justify-center bg-background/85 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-md border border-ai/30 bg-surface p-5 shadow-lg">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-ai" aria-hidden />
          <p className="text-sm font-semibold text-foreground">AI Simulation — generating plan</p>
        </div>
        <div className="mt-4 space-y-2.5">
          {AI_STAGES.map((label, i) => {
            const done = i < stage;
            const active = i === stage;
            return (
              <div key={label} className="flex items-center gap-2.5">
                <span
                  className={cn(
                    "flex size-4 shrink-0 items-center justify-center rounded-full border text-[9px]",
                    done && "border-ok bg-ok/20 text-ok",
                    active && "border-primary bg-primary/20 text-primary",
                    !done && !active && "border-border text-muted-foreground",
                  )}
                >
                  {done ? (
                    <Check className="size-2.5" aria-hidden />
                  ) : active ? (
                    <Loader2 className="size-2.5 animate-spin" aria-hidden />
                  ) : null}
                </span>
                <span
                  className={cn(
                    "text-xs",
                    done
                      ? "text-foreground"
                      : active
                        ? "font-medium text-foreground"
                        : "text-muted-foreground",
                  )}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

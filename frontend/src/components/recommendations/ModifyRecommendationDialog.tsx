import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toHHMM } from "@/utils/dateUtils";
import type { AIRecommendation } from "@/types";

const schema = z.object({
  newTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "Use 24-hour HH:MM format"),
  newDuration: z.coerce.number().min(15, "Minimum 15 minutes").max(600, "Maximum 600 minutes"),
  reason: z.string().min(5, "Provide a short justification (min 5 characters)"),
});
type FormValues = z.infer<typeof schema>;

export function ModifyRecommendationDialog({
  open,
  onOpenChange,
  rec,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rec: AIRecommendation;
  onSubmit: (patch: { start_min: number; duration_min: number; reason: string }) => void;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: { newTime: toHHMM(rec.start_min), newDuration: rec.duration_min, reason: "" },
  });

  const submit = (values: FormValues) => {
    const [h_raw, m_raw] = values.newTime.split(":").map(Number);
    const h = h_raw ?? 0;
    const m = m_raw ?? 0;
    onSubmit({ start_min: h * 60 + m, duration_min: values.newDuration, reason: values.reason });
    toast.success(`Recommendation ${rec.recommendation_id} modified.`);
    onOpenChange(false);
    form.reset();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Modify recommendation {rec.recommendation_id}</DialogTitle>
          <DialogDescription>
            Propose a new time window before approving this AI recommendation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(submit)} className="space-y-3">
          <div>
            <Label htmlFor="newTime2">New start time</Label>
            <Input id="newTime2" type="time" {...form.register("newTime")} className="mt-1" />
            {form.formState.errors.newTime && (
              <p className="mt-1 text-xs text-crit">{form.formState.errors.newTime.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="newDuration2">New duration (minutes)</Label>
            <Input
              id="newDuration2"
              type="number"
              step={15}
              {...form.register("newDuration")}
              className="mt-1"
            />
            {form.formState.errors.newDuration && (
              <p className="mt-1 text-xs text-crit">{form.formState.errors.newDuration.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="reason2">Reason</Label>
            <Textarea id="reason2" rows={3} {...form.register("reason")} className="mt-1" />
            {form.formState.errors.reason && (
              <p className="mt-1 text-xs text-crit">{form.formState.errors.reason.message}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Save changes</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

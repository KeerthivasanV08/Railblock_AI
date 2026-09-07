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
import type { BlockPlan } from "@/types";

const schema = z.object({
  newTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "Use 24-hour HH:MM format"),
  newDuration: z.coerce.number().min(15, "Minimum 15 minutes").max(600, "Maximum 600 minutes"),
  reason: z.string().min(5, "Provide a short justification (min 5 characters)"),
});

type FormValues = z.infer<typeof schema>;

interface ModifyBlockDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  block: Pick<BlockPlan, "block_id" | "start_min" | "duration_min">;
  onSubmit: (patch: { start_min: number; duration_min: number; reason: string }) => void;
}

export function ModifyBlockDialog({ open, onOpenChange, block, onSubmit }: ModifyBlockDialogProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: {
      newTime: toHHMM(block.start_min),
      newDuration: block.duration_min,
      reason: "",
    },
  });

  const submit = (values: FormValues) => {
    const [h_raw, m_raw] = values.newTime.split(":").map(Number);
    const h = h_raw ?? 0;
    const m = m_raw ?? 0;
    onSubmit({ start_min: h * 60 + m, duration_min: values.newDuration, reason: values.reason });
    toast.success(`Block ${block.block_id} modified successfully.`);
    onOpenChange(false);
    form.reset();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Modify block {block.block_id}</DialogTitle>
          <DialogDescription>
            Propose a new time window and justification for this block.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(submit)} className="space-y-3">
          <div>
            <Label htmlFor="newTime">New start time</Label>
            <Input id="newTime" type="time" {...form.register("newTime")} className="mt-1" />
            {form.formState.errors.newTime && (
              <p className="mt-1 text-xs text-crit">{form.formState.errors.newTime.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="newDuration">New duration (minutes)</Label>
            <Input
              id="newDuration"
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
            <Label htmlFor="reason">Reason</Label>
            <Textarea
              id="reason"
              rows={3}
              placeholder="e.g. Traffic window shifted after path re-timing"
              {...form.register("reason")}
              className="mt-1"
            />
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

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { blocksApi, type ManualBlockCreateRequest, type ManualBlockCreateResponse } from "@/api/blocksApi";
import { SECTIONS } from "@/data/sections";
import { PlusCircle, Loader2, AlertTriangle, ShieldCheck, CheckCircle2 } from "lucide-react";

interface CreateBlockModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultWeek?: number;
  onBlockCreated?: (res: ManualBlockCreateResponse) => void;
}

export function CreateBlockModal({
  open,
  onOpenChange,
  defaultWeek = 17,
  onBlockCreated,
}: CreateBlockModalProps) {
  const [weekNumber, setWeekNumber] = useState<number>(defaultWeek);
  const [department, setDepartment] = useState<string>("Engineering");
  const [sectionId, setSectionId] = useState<string>(SECTIONS[0]?.section_id || "SEC_001");
  const [startDate, setStartDate] = useState<string>("2026-12-22");
  const [endDate, setEndDate] = useState<string>("2026-12-22");
  const [startTime, setStartTime] = useState<string>("02:00");
  const [endTime, setEndTime] = useState<string>("05:00");
  const [durationMinutes, setDurationMinutes] = useState<number>(180);
  const [taskIds, setTaskIds] = useState<string>("");
  const [resources, setResources] = useState<string>("BCM 02, Ballast Tamper");
  const [remarks, setRemarks] = useState<string>("Urgent controller-requested track possession for deep screening");

  const [loading, setLoading] = useState(false);
  const [errorMessages, setErrorMessages] = useState<string[]>([]);
  const [successInfo, setSuccessInfo] = useState<ManualBlockCreateResponse | null>(null);

  // Auto-calculate suggested dates when week number changes
  useEffect(() => {
    const base = new Date("2026-09-01T00:00:00");
    const offsetDays = (weekNumber - 1) * 7;
    const wStart = new Date(base.getTime() + offsetDays * 86400000);
    const dateStr = wStart.toISOString().slice(0, 10);
    setStartDate(dateStr);
    setEndDate(dateStr);
  }, [weekNumber]);

  // Recalculate duration in minutes when start or end time changes
  useEffect(() => {
    try {
      const parts = startTime.split(":").map(Number);
      const eParts = endTime.split(":").map(Number);
      const sh = parts[0] ?? 0;
      const sm = parts[1] ?? 0;
      const eh = eParts[0] ?? 0;
      const em = eParts[1] ?? 0;
      if (!isNaN(sh) && !isNaN(sm) && !isNaN(eh) && !isNaN(em)) {
        let diff = (eh * 60 + em) - (sh * 60 + sm);
        if (diff < 0) diff += 24 * 60; // crossed midnight
        if (diff > 0) setDurationMinutes(diff);
      }
    } catch {
      // Keep manual
    }
  }, [startTime, endTime]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessages([]);
    setSuccessInfo(null);

    const parsedTasks = taskIds
      .split(/[;,]/)
      .map((t) => t.trim())
      .filter(Boolean);

    const parsedResources = resources
      .split(/[;,]/)
      .map((r) => r.trim())
      .filter(Boolean);

    const payload: ManualBlockCreateRequest = {
      week_number: Number(weekNumber),
      department,
      section_id: sectionId,
      start_date: startDate,
      end_date: endDate,
      start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
      end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
      duration_minutes: Number(durationMinutes),
      ...(parsedTasks.length ? { task_ids: parsedTasks } : {}),
      ...(parsedResources.length ? { resources: parsedResources } : {}),
      remarks,
    };

    try {
      const res = await blocksApi.createManualBlock(payload);
      if (res.success) {
        setSuccessInfo(res);
        toast.success(`Block Created: ${res.block_id}`, {
          description: res.message || "Passed Weather, MDPS & Timetable constraint gates.",
        });
        if (onBlockCreated) onBlockCreated(res);
        setTimeout(() => {
          onOpenChange(false);
          setSuccessInfo(null);
        }, 1200);
      } else {
        const errs = res.errors && res.errors.length > 0 ? res.errors : [res.message || "Failed to create block."];
        setErrorMessages(errs);
        toast.error("Block Creation Rejected", {
          description: errs[0],
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Backend service error during block evaluation.";
      setErrorMessages([msg]);
      toast.error("Submission Error", { description: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <PlusCircle className="size-5 text-primary" aria-hidden />
            <DialogTitle>Create Operational Maintenance Block</DialogTitle>
          </div>
          <DialogDescription>
            Manual Controller Allocation · Evaluated in real-time through the AI pipeline (Weather SRS Hard Safety Exclusion, MDPS Priority, Shadow Clustering & Timetable Clash Constraints).
          </DialogDescription>
        </DialogHeader>

        {errorMessages.length > 0 && (
          <div className="rounded-md border border-crit/40 bg-crit/10 p-3 text-xs text-crit space-y-1">
            <div className="flex items-center gap-1.5 font-semibold">
              <AlertTriangle className="size-4 shrink-0" />
              Safety / Constraint Gate Rejection:
            </div>
            <ul className="list-disc pl-5 space-y-0.5">
              {errorMessages.map((msg, i) => (
                <li key={i}>{msg}</li>
              ))}
            </ul>
          </div>
        )}

        {successInfo && (
          <div className="rounded-md border border-ok/40 bg-ok/10 p-3 text-xs text-ok flex items-center gap-2">
            <CheckCircle2 className="size-4 shrink-0" />
            <div>
              <p className="font-semibold">Block {successInfo.block_id} Successfully Created & Queued!</p>
              <p className="text-[11px] opacity-90">{successInfo.message}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Week Number */}
            <div>
              <Label className="text-xs">Rolling Week (1–26)</Label>
              <Input
                type="number"
                min={1}
                max={26}
                value={weekNumber}
                onChange={(e) => setWeekNumber(Number(e.target.value))}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>

            {/* Department */}
            <div>
              <Label className="text-xs">Department</Label>
              <Select value={department} onValueChange={setDepartment}>
                <SelectTrigger className="h-8 text-xs mt-1">
                  <SelectValue placeholder="Select Department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Engineering">Engineering (P-Way)</SelectItem>
                  <SelectItem value="TRD">TRD (Overhead Traction)</SelectItem>
                  <SelectItem value="S&T">S&T (Signals & Telecom)</SelectItem>
                  <SelectItem value="Engineering;TRD">Engineering + TRD (Joint)</SelectItem>
                  <SelectItem value="Engineering;TRD;S&T">Integrated (All Disciplines)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Section ID */}
            <div>
              <Label className="text-xs">Corridor Section</Label>
              <Select value={sectionId} onValueChange={setSectionId}>
                <SelectTrigger className="h-8 text-xs mt-1 font-mono">
                  <SelectValue placeholder="Select Section" />
                </SelectTrigger>
                <SelectContent className="max-h-56">
                  {SECTIONS.slice(0, 30).map((sec) => (
                    <SelectItem key={sec.section_id} value={sec.section_id} className="font-mono text-xs">
                      {sec.section_id} ({sec.from_station}–{sec.to_station})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Start Date */}
            <div>
              <Label className="text-xs">Start Date (YYYY-MM-DD)</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>

            {/* End Date */}
            <div>
              <Label className="text-xs">End Date (YYYY-MM-DD)</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Start Time */}
            <div>
              <Label className="text-xs">Start Time (HH:MM)</Label>
              <Input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>

            {/* End Time */}
            <div>
              <Label className="text-xs">End Time (HH:MM)</Label>
              <Input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>

            {/* Duration Minutes */}
            <div>
              <Label className="text-xs">Possession Duration (min)</Label>
              <Input
                type="number"
                min={30}
                max={720}
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(Number(e.target.value))}
                required
                className="h-8 text-xs font-mono mt-1"
              />
            </div>
          </div>

          {/* Task IDs */}
          <div>
            <Label className="text-xs">Maintenance Task IDs (Optional, comma-separated)</Label>
            <Input
              type="text"
              value={taskIds}
              onChange={(e) => setTaskIds(e.target.value)}
              placeholder="e.g. TSK_001, TSK_042"
              className="h-8 text-xs font-mono mt-1"
            />
          </div>

          {/* Resources */}
          <div>
            <Label className="text-xs">Required Machines / Gangs</Label>
            <Input
              type="text"
              value={resources}
              onChange={(e) => setResources(e.target.value)}
              placeholder="e.g. BCM 02, Ballast Tamper, OHE Wiring Gang"
              className="h-8 text-xs mt-1"
            />
          </div>

          {/* Remarks */}
          <div>
            <Label className="text-xs">Operational Justification & Controller Remarks</Label>
            <Textarea
              rows={2}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Detail reasons for possession window request..."
              className="text-xs mt-1"
            />
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={loading}
              className="gap-1.5 bg-primary text-primary-foreground font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" aria-hidden />
                  Evaluating AI Gates…
                </>
              ) : (
                <>
                  <ShieldCheck className="size-3.5" aria-hidden />
                  Validate & Create Block
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { RollingPlanPage } from "@/components/planner/RollingPlanPage";

export const Route = createFileRoute("/_app/rolling-plan")({
  component: RollingPlanPage,
});

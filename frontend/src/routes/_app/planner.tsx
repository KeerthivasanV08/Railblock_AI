import { createFileRoute } from "@tanstack/react-router";
import { PlannerPage } from "@/components/planner/PlannerPage";

export const Route = createFileRoute("/_app/planner")({
  component: PlannerPage,
});

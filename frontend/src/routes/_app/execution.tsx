import { createFileRoute } from "@tanstack/react-router";
import { ExecutionMonitorPage } from "@/components/execution/ExecutionMonitorPage";

export const Route = createFileRoute("/_app/execution")({
  component: ExecutionMonitorPage,
});

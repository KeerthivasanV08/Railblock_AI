import { createFileRoute } from "@tanstack/react-router";
import { LiveCorridorPage } from "@/components/dashboard/LiveCorridorPage";

export const Route = createFileRoute("/_app/live")({
  component: LiveCorridorPage,
});

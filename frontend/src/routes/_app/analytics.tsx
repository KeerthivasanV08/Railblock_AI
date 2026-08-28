import { createFileRoute } from "@tanstack/react-router";
import { AnalyticsPage } from "@/components/analytics/AnalyticsPage";

export const Route = createFileRoute("/_app/analytics")({
  component: AnalyticsPage,
});

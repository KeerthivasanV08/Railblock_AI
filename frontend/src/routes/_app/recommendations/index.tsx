import { createFileRoute } from "@tanstack/react-router";
import { RecommendationsPage } from "@/components/recommendations/RecommendationsPage";

export const Route = createFileRoute("/_app/recommendations/")({
  component: RecommendationsPage,
});

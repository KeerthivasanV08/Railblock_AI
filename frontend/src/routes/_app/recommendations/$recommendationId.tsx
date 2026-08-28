import { createFileRoute } from "@tanstack/react-router";
import { RecommendationDetailPage } from "@/components/recommendations/RecommendationDetailPage";

function RecommendationRouteComponent() {
  const { recommendationId } = Route.useParams();
  return <RecommendationDetailPage recommendationId={recommendationId} />;
}

export const Route = createFileRoute("/_app/recommendations/$recommendationId")({
  component: RecommendationRouteComponent,
});

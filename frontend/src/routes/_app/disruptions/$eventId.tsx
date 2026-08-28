import { createFileRoute } from "@tanstack/react-router";
import { DisruptionDetailPage } from "@/components/disruptions/DisruptionDetailPage";

function DisruptionRouteComponent() {
  const { eventId } = Route.useParams();
  return <DisruptionDetailPage eventId={eventId} />;
}

export const Route = createFileRoute("/_app/disruptions/$eventId")({
  component: DisruptionRouteComponent,
});

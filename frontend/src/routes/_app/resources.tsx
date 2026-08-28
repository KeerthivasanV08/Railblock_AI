import { createFileRoute } from "@tanstack/react-router";
import { ResourcesPage } from "@/components/resources/ResourcesPage";

export const Route = createFileRoute("/_app/resources")({
  component: ResourcesPage,
});

import { createFileRoute } from "@tanstack/react-router";
import { DisruptionsPage } from "@/components/disruptions/DisruptionsPage";

export const Route = createFileRoute("/_app/disruptions/")({
  component: DisruptionsPage,
});

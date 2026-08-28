import { createFileRoute } from "@tanstack/react-router";
import { TaskDetailPage } from "@/components/tasks/TaskDetailPage";

function TaskDetailRouteComponent() {
  const { taskId } = Route.useParams();
  return <TaskDetailPage taskId={taskId} />;
}

export const Route = createFileRoute("/_app/tasks/$taskId")({
  component: TaskDetailRouteComponent,
});

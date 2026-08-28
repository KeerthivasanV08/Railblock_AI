import { Link, useRouterState } from "@tanstack/react-router";
import {
  AlertTriangle,
  BarChart3,
  ClipboardList,
  FileText,
  LayoutDashboard,
  Radio,
  Settings2,
  Sparkles,
  TrainFront,
  Wrench,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useDisruptionStore } from "@/stores/disruptionStore";
import { useRecommendationStore } from "@/stores/recommendationStore";
import { useTaskStore } from "@/stores/taskStore";

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  badge?: number;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

function useNavGroups(): NavGroup[] {
  const openDisruptions = useDisruptionStore(
    (s) => s.disruptions.filter((d) => d.status === "Open").length,
  );
  const pendingRecs = useRecommendationStore(
    (s) => s.recommendations.filter((r) => r.status === "Pending").length,
  );
  const criticalTasks = useTaskStore(
    (s) =>
      s.tasks.filter((t) => t.severity === "A" && t.overdue_days > 0 && t.status !== "Completed")
        .length,
  );

  return [
    {
      label: "Command",
      items: [
        { label: "Command Dashboard", to: "/dashboard", icon: LayoutDashboard },
        { label: "Live Corridor", to: "/live", icon: Radio },
      ],
    },
    {
      label: "Planning",
      items: [
        { label: "AI Block Planner", to: "/planner", icon: TrainFront },
        { label: "Maintenance Tasks", to: "/tasks", icon: ClipboardList, badge: criticalTasks },
        { label: "Resources", to: "/resources", icon: Wrench },
      ],
    },
    {
      label: "Intelligence",
      items: [
        { label: "AI Recommendations", to: "/recommendations", icon: Sparkles, badge: pendingRecs },
        { label: "Analytics", to: "/analytics", icon: BarChart3 },
      ],
    },
    {
      label: "Disruption",
      items: [
        {
          label: "Self-Healing Console",
          to: "/disruptions",
          icon: AlertTriangle,
          badge: openDisruptions,
        },
      ],
    },
    {
      label: "Governance",
      items: [
        { label: "Reports", to: "/reports", icon: FileText },
        { label: "Administration", to: "/admin", icon: Settings2 },
      ],
    },
  ];
}

export function AppSidebar() {
  const groups = useNavGroups();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <Sidebar collapsible="icon" className="border-r border-border">
      <SidebarHeader className="border-b border-border px-3 py-3">
        <Link to="/dashboard" className="flex items-center gap-2 px-1">
          <span className="flex size-7 shrink-0 items-center justify-center rounded bg-primary/15 text-primary">
            <TrainFront className="size-4" aria-hidden />
          </span>
          <span className="flex flex-col leading-none group-data-[collapsible=icon]:hidden">
            <span className="text-sm font-bold tracking-tight text-foreground">RailBlock AI</span>
            <span className="text-[10px] text-muted-foreground">Ops Command Centre</span>
          </span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {groups.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
                  return (
                    <SidebarMenuItem key={item.to}>
                      <SidebarMenuButton asChild isActive={active} tooltip={item.label}>
                        <Link to={item.to}>
                          <item.icon />
                          <span>{item.label}</span>
                        </Link>
                      </SidebarMenuButton>
                      {!!item.badge && <SidebarMenuBadge>{item.badge}</SidebarMenuBadge>}
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter className="border-t border-border px-3 py-2.5">
        <p className="text-[10px] leading-snug text-muted-foreground group-data-[collapsible=icon]:hidden">
          Synthetic Demo Data · New Delhi–Kanpur Corridor. Not connected to live Indian Railways
          systems.
        </p>
      </SidebarFooter>
    </Sidebar>
  );
}

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState } from "@/components/common/States";
import { useRecommendationStore } from "@/stores/recommendationStore";
import { RecommendationCard } from "./RecommendationCard";
import { ModifyRecommendationDialog } from "./ModifyRecommendationDialog";
import type { AIRecommendation } from "@/types";

export function RecommendationsPage() {
  const { recommendations, approve, reject, modify, fetchRecommendations, loading } = useRecommendationStore();
  const [modifyTarget, setModifyTarget] = useState<AIRecommendation | null>(null);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const simulate = (rec: AIRecommendation) => {
    toast.success("AI rescheduling simulation completed.", {
      description: `Block ${rec.block_id} — ${rec.confidence}% confidence, ${rec.train_impact.toLowerCase()} train impact.`,
    });
  };

  return (
    <div className="flex h-full flex-col overflow-auto">
      <PageHeader
        title="AI Recommendations"
        description="Central AI decision-support workspace — explainable block recommendations validated against railway operational constraints"
        crumbs={[{ label: "Intelligence" }, { label: "AI Recommendations" }]}
      />
      <div className="flex-1 p-4">
        {recommendations.length === 0 ? (
          <EmptyState
            title="No AI recommendations yet"
            description="Generate an AI plan from the Block Planner to see recommendations here."
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
            {recommendations.map((rec) => (
              <RecommendationCard
                key={rec.recommendation_id}
                rec={rec}
                onApprove={() => {
                  approve(rec.recommendation_id);
                  toast.success(`Block ${rec.block_id} approved successfully.`);
                }}
                onReject={() => {
                  reject(rec.recommendation_id, "Rejected from XAI console review");
                  toast.error("Recommendation rejected.");
                }}
                onModify={() => setModifyTarget(rec)}
                onSimulate={() => simulate(rec)}
              />
            ))}
          </div>
        )}
      </div>
      {modifyTarget && (
        <ModifyRecommendationDialog
          open={!!modifyTarget}
          onOpenChange={(open) => !open && setModifyTarget(null)}
          rec={modifyTarget}
          onSubmit={(patch) => modify(modifyTarget.recommendation_id, patch)}
        />
      )}
    </div>
  );
}

import { AlertTriangle, CheckCircle, AlertCircle, CircleHelp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type StatusType = "compliant" | "warning" | "overdue" | "neutral";

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
  showIcon?: boolean;
}

const statusConfig = {
  compliant: {
    label: "Compliant",
    className: "bg-[var(--status-compliant)] hover:bg-[var(--status-compliant)]/90 text-white",
    Icon: CheckCircle,
  },
  warning: {
    label: "Warning",
    className: "bg-[var(--status-warning)] hover:bg-[var(--status-warning)]/90 text-black",
    Icon: AlertCircle,
  },
  overdue: {
    label: "Overdue",
    className: "bg-[var(--status-overdue)] hover:bg-[var(--status-overdue)]/90 text-white",
    Icon: AlertTriangle,
  },
  neutral: {
    label: "Unknown",
    className: "border border-border bg-muted text-muted-foreground hover:bg-muted",
    Icon: CircleHelp,
  },
};

export function StatusBadge({ status, label, className, showIcon = true }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.Icon;

  return (
    <Badge className={cn("text-sm px-3 py-1 font-medium", config.className, className)}>
      {showIcon && <Icon className="h-4 w-4 mr-1.5" />}
      {label || config.label}
    </Badge>
  );
}

export function getStatusFromAdStatus(adStatus: string): StatusType {
  const normalized = adStatus.trim().toLowerCase().replace(/[\s-]+/g, "_");

  if (
    normalized.includes("overdue") ||
    normalized.includes("noncompliant") ||
    normalized.includes("non_compliant")
  ) {
    return "overdue";
  }
  if (
    normalized.includes("needs_review") ||
    normalized.includes("warning") ||
    normalized.includes("due_soon")
  ) {
    return "warning";
  }
  if (normalized.includes("compliant") || normalized === "current" || normalized === "clear") {
    return "compliant";
  }
  return "neutral";
}

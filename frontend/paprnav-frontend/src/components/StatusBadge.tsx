import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusType = "compliant" | "warning" | "overdue";

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
  if (adStatus.toLowerCase().includes("overdue")) {
    return "overdue";
  }
  if (adStatus.toLowerCase().includes("warning") || adStatus.includes("1")) {
    return "warning";
  }
  return "compliant";
}

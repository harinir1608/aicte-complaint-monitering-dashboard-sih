import React from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowUpRight, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface KPICardProps {
  title: string;
  value: number | string;
  icon: React.ElementType;
  description?: string;
  colorClass?: string;
  href?: string;
  isLoading?: boolean;
  trend?: {
    value: number;
    label?: string;
    direction?: "up" | "down" | "neutral";
  };
  onClick?: () => void;
}

export function KPICard({
  title,
  value,
  icon: Icon,
  description,
  colorClass = "text-indigo-600 bg-indigo-50",
  href,
  isLoading,
  trend,
  onClick,
}: KPICardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) onClick();
    else if (href) navigate(href);
  };

  const isClickable = !!(href || onClick);

  return (
    <Card
      className={cn(
        "transition-shadow",
        isClickable && "cursor-pointer hover:shadow-md hover:border-indigo-200"
      )}
      onClick={isClickable ? handleClick : undefined}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-500 font-medium truncate">{title}</p>
            {isLoading ? (
              <Skeleton className="mt-2 h-8 w-20" />
            ) : (
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {typeof value === "number" ? value.toLocaleString() : value}
              </p>
            )}
            {description && !isLoading && (
              <p className="mt-1 text-xs text-gray-400">{description}</p>
            )}
            {trend && !isLoading && (
              <div
                className={cn(
                  "mt-1.5 flex items-center gap-1 text-xs font-medium",
                  trend.direction === "up" ? "text-green-600" :
                  trend.direction === "down" ? "text-red-600" :
                  "text-gray-500"
                )}
              >
                {trend.direction === "up" && <TrendingUp className="h-3 w-3" />}
                {trend.direction === "down" && <TrendingDown className="h-3 w-3" />}
                <span>{trend.value > 0 ? "+" : ""}{trend.value}%</span>
                {trend.label && <span className="text-gray-400">{trend.label}</span>}
              </div>
            )}
          </div>
          <div className={cn("rounded-lg p-2.5 shrink-0 ml-3", colorClass)}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
        {isClickable && !isLoading && (
          <div className="mt-3 flex items-center gap-1 text-xs text-indigo-600 font-medium">
            View all <ArrowUpRight className="h-3 w-3" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default KPICard;

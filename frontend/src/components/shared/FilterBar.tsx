import { SearchInput } from "./SearchInput";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SlidersHorizontal, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: "search" | "select" | "date";
  options?: FilterOption[];
  placeholder?: string;
}

interface FilterBarProps {
  filters: FilterConfig[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onReset?: () => void;
  className?: string;
}

export function FilterBar({
  filters,
  values,
  onChange,
  onReset,
  className,
}: FilterBarProps) {
  const hasActiveFilters = Object.values(values).some((v) => v !== "" && v !== undefined);

  return (
    <div className={cn("flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4", className)}>
      <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-0.5">
        <SlidersHorizontal className="h-4 w-4" />
        <span>Filters</span>
      </div>

      {filters.map((filter) => (
        <div key={filter.key} className="flex flex-col gap-1 min-w-[160px]">
          <Label className="text-xs">{filter.label}</Label>

          {filter.type === "search" && (
            <SearchInput
              value={values[filter.key] ?? ""}
              onChange={(val) => onChange(filter.key, val)}
              placeholder={filter.placeholder ?? `Search ${filter.label.toLowerCase()}...`}
              className="w-48"
            />
          )}

          {filter.type === "select" && (
            <Select
              value={values[filter.key] ?? ""}
              onValueChange={(val) => onChange(filter.key, val === "__all__" ? "" : val)}
            >
              <SelectTrigger className="h-10 w-48">
                <SelectValue placeholder={filter.placeholder ?? `All ${filter.label}`} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">All {filter.label}</SelectItem>
                {filter.options?.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {filter.type === "date" && (
            <Input
              type="date"
              value={values[filter.key] ?? ""}
              onChange={(e) => onChange(filter.key, e.target.value)}
              className="h-10 w-44"
            />
          )}
        </div>
      ))}

      {hasActiveFilters && onReset && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="text-gray-500 hover:text-gray-700 self-end"
        >
          <X className="mr-1 h-3.5 w-3.5" />
          Clear filters
        </Button>
      )}
    </div>
  );
}

export default FilterBar;

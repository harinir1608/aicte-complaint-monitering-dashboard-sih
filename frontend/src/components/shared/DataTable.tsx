import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown, ChevronsUpDown, Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ColumnDef<T> {
  key: string;
  header: string;
  cell: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
  headerClassName?: string;
}

export interface SortState {
  key: string;
  direction: "asc" | "desc";
}

export interface PaginationState {
  page: number;
  size?: number;        // optional — some APIs return page_size instead
  total: number;
  pages: number;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  pagination?: PaginationState;
  onPageChange?: (page: number) => void;
  onSort?: (sort: SortState) => void;
  sortState?: SortState;
  isLoading?: boolean;
  emptyMessage?: string;
  rowKey?: (row: T) => string;
}

// ── Component ─────────────────────────────────────────────────────────────────

function SortIcon({ columnKey, sortState }: { columnKey: string; sortState?: SortState }) {
  if (!sortState || sortState.key !== columnKey) {
    return <ChevronsUpDown className="ml-1 h-3 w-3 text-gray-400 inline" />;
  }
  return sortState.direction === "asc" ? (
    <ChevronUp className="ml-1 h-3 w-3 text-indigo-600 inline" />
  ) : (
    <ChevronDown className="ml-1 h-3 w-3 text-indigo-600 inline" />
  );
}

export function DataTable<T>({
  columns,
  data,
  pagination,
  onPageChange,
  onSort,
  sortState,
  isLoading = false,
  emptyMessage = "No records found.",
  rowKey,
}: DataTableProps<T>) {
  const handleSort = (col: ColumnDef<T>) => {
    if (!col.sortable || !onSort) return;
    const direction =
      sortState?.key === col.key && sortState.direction === "asc"
        ? "desc"
        : "asc";
    onSort({ key: col.key, direction });
  };

  const skeletonRows = 5;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 hover:bg-gray-50">
              {columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    col.sortable && "cursor-pointer select-none",
                    col.headerClassName
                  )}
                  onClick={() => handleSort(col)}
                >
                  {col.header}
                  {col.sortable && (
                    <SortIcon columnKey={col.key} sortState={sortState} />
                  )}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: skeletonRows }).map((_, i) => (
                <TableRow key={i}>
                  {columns.map((col) => (
                    <TableCell key={col.key}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center"
                >
                  <div className="flex flex-col items-center justify-center gap-2 text-gray-400">
                    <Inbox className="h-8 w-8" />
                    <span className="text-sm">{emptyMessage}</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, i) => (
                <TableRow key={rowKey ? rowKey(row) : i}>
                  {columns.map((col) => (
                    <TableCell key={col.key} className={col.className}>
                      {col.cell(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <div className="flex items-center justify-between px-1">
          <p className="text-sm text-gray-500">
            Showing {Math.min((pagination.page - 1) * (pagination.size ?? 20) + 1, pagination.total)}–
            {Math.min(pagination.page * (pagination.size ?? 20), pagination.total)} of{" "}
            {pagination.total} records
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page <= 1 || isLoading}
              onClick={() => onPageChange?.(pagination.page - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm text-gray-600">
              Page {pagination.page} of {pagination.pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page >= pagination.pages || isLoading}
              onClick={() => onPageChange?.(pagination.page + 1)}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;

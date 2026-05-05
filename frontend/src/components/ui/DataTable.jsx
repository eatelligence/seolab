import { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Skeleton } from './Skeleton';

/**
 * Lightweight data table with sortable columns, search, and pagination.
 * columns: [{ key, header, render?, align?, sortable?, width? }]
 */
export function DataTable({
  columns,
  rows = [],
  keyField = 'id',
  loading = false,
  searchable = true,
  pageSize = 25,
  searchKeys,
  emptyState,
  rowAction,
  density = 'comfortable',
  className,
}) {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    if (!search) return rows;
    const keys = searchKeys || columns.filter((c) => c.searchable !== false).map((c) => c.key);
    const q = search.toLowerCase();
    return rows.filter((r) => keys.some((k) => String(r[k] ?? '').toLowerCase().includes(q)));
  }, [rows, search, searchKeys, columns]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const arr = [...filtered];
    arr.sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey];
      if (va === vb) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      const cmp = typeof va === 'number' && typeof vb === 'number'
        ? va - vb
        : String(va).localeCompare(String(vb), undefined, { numeric: true });
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageRows = sorted.slice((safePage - 1) * pageSize, safePage * pageSize);

  const onSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const cellPad = density === 'compact' ? 'px-3 py-2' : 'px-4 py-3';

  return (
    <div className={cn('panel', className)}>
      {searchable && (
        <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-line">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-dim" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="filter..."
              className="w-full h-8 pl-9 pr-3 bg-transparent border border-line text-bone text-xs font-mono placeholder:text-dim focus:border-signal/60 focus-ring"
            />
          </div>
          <div className="font-mono text-2xs uppercase tracking-widest2 text-dim">
            {sorted.length} <span className="text-dim/60">rows</span>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-dim">
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{ width: col.width }}
                  className={cn(
                    cellPad,
                    'text-left font-mono text-2xs uppercase tracking-widest2 font-normal whitespace-nowrap',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.sortable !== false && 'cursor-pointer select-none hover:text-bone',
                  )}
                  onClick={() => col.sortable !== false && onSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1.5">
                    {col.header}
                    {sortKey === col.key && (
                      sortDir === 'asc' ? <ArrowUp className="w-3 h-3 text-signal" /> : <ArrowDown className="w-3 h-3 text-signal" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="border-b border-line/60">
                  {columns.map((c) => (
                    <td key={c.key} className={cellPad}><Skeleton className="h-4" /></td>
                  ))}
                </tr>
              ))
            ) : pageRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-16 text-center">
                  {emptyState || <span className="text-dim text-xs font-mono uppercase tracking-widest2">No matching rows</span>}
                </td>
              </tr>
            ) : (
              pageRows.map((row) => (
                <tr
                  key={row[keyField] ?? JSON.stringify(row)}
                  className={cn(
                    'border-b border-line/60 hover:bg-ink-100 transition-colors',
                    rowAction && 'cursor-pointer',
                  )}
                  onClick={() => rowAction?.(row)}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        cellPad,
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center',
                      )}
                    >
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-line font-mono text-2xs uppercase tracking-widest2 text-dim">
          <span>
            page <span className="text-bone num-mono">{String(safePage).padStart(2, '0')}</span>
            <span className="mx-1">/</span>
            <span className="num-mono">{String(totalPages).padStart(2, '0')}</span>
          </span>
          <div className="flex gap-2">
            <button
              disabled={safePage <= 1}
              onClick={() => setPage(safePage - 1)}
              className="h-7 px-3 border border-line hover:border-line2 disabled:opacity-30 transition-colors"
            >
              ← prev
            </button>
            <button
              disabled={safePage >= totalPages}
              onClick={() => setPage(safePage + 1)}
              className="h-7 px-3 border border-line hover:border-line2 disabled:opacity-30 transition-colors"
            >
              next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

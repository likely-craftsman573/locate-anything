import { useNavigate } from "react-router-dom";

import { resolveUrl } from "../api/client";
import { useDeleteHistory, useHistory } from "../api/hooks";

export default function HistoryPage() {
  const { data, isLoading } = useHistory();
  const del = useDeleteHistory();
  const navigate = useNavigate();

  if (isLoading) {
    return <p className="label-kicker">loading log…</p>;
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="ticks panel mx-auto flex max-w-md flex-col items-center gap-2 py-16 text-center">
        <span className="font-mono text-3xl text-edge">≡</span>
        <p className="font-display text-lg text-bone">No searches yet</p>
        <p className="font-mono text-xs text-ash">Your past detections will appear here.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex items-baseline justify-between">
        <h1 className="font-display text-xl font-bold tracking-tight text-bone">Search Log</h1>
        <span className="label-kicker">{data.total} entries</span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {data.items.map((item) => {
          const n = item.box_count + item.point_count;
          return (
            <div key={item.id} className="group panel overflow-hidden">
              <button
                onClick={() => navigate(`/?load=${item.id}`)}
                className="block w-full text-left"
              >
                <div className="relative aspect-square overflow-hidden bg-black/40">
                  <img
                    src={resolveUrl(item.image_url)}
                    alt={item.prompt}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <span className="absolute left-1.5 top-1.5 bg-lime px-1.5 py-0.5 font-mono text-[10px] font-semibold text-ink">
                    {n}
                  </span>
                </div>
                <div className="p-2.5">
                  <p className="label-kicker mb-1 truncate">{item.task}</p>
                  <p className="truncate font-mono text-xs text-bone">
                    {item.prompt || "—"}
                  </p>
                </div>
              </button>
              <button
                onClick={() => del.mutate(item.id)}
                className="w-full border-t border-edge py-1.5 font-mono text-[10px] uppercase tracking-wider text-ash transition-colors hover:bg-rose/10 hover:text-rose"
              >
                delete
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

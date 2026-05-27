import { useState } from "react";

import { getApiBase, setApiBase } from "../api/client";
import { useDevices, useHealth, useSwitchDevice } from "../api/hooks";

function Row({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex items-center justify-between border-b border-edge/60 py-2.5">
      <span className="label-kicker">{label}</span>
      <span className={`font-mono text-sm ${tone ?? "text-bone"}`}>{value}</span>
    </div>
  );
}

function GpuPicker() {
  const { data } = useDevices();
  const switchDevice = useSwitchDevice();

  if (!data || data.devices.length === 0) {
    return <p className="font-mono text-xs text-ash">No selectable GPUs (mock mode or no CUDA).</p>;
  }

  return (
    <div className="space-y-2">
      {data.devices.map((d) => {
        const active = d.index === data.current;
        const vram =
          d.vram_free_gb != null && d.vram_gb != null
            ? `${d.vram_free_gb} / ${d.vram_gb} GB free`
            : d.vram_gb != null
              ? `${d.vram_gb} GB`
              : "—";
        const disabled = active || !d.compatible || switchDevice.isPending;
        return (
          <button
            key={d.index}
            disabled={disabled}
            onClick={() => switchDevice.mutate(d.index)}
            className={`flex w-full items-center justify-between rounded-md border px-3 py-2.5 text-left transition-colors ${
              active
                ? "border-lime/70 bg-lime/10"
                : d.compatible
                  ? "border-edge hover:border-ash/60"
                  : "border-edge opacity-50"
            } ${switchDevice.isPending && !active ? "opacity-50" : ""}`}
          >
            <span className="min-w-0">
              <span className="block truncate font-mono text-sm text-bone">
                <span className="text-ash">[{d.index}]</span> {d.name}
              </span>
              <span className="font-mono text-[11px] text-ash">
                {vram}
                {!d.compatible && " · unsupported"}
              </span>
            </span>
            <span className="ml-3 shrink-0 font-mono text-[10px] uppercase tracking-wider">
              {active ? (
                <span className="text-lime">● active</span>
              ) : switchDevice.isPending ? (
                <span className="text-amber">…</span>
              ) : d.compatible ? (
                <span className="text-ash">select</span>
              ) : (
                <span className="text-rose">n/a</span>
              )}
            </span>
          </button>
        );
      })}
      {switchDevice.isError && (
        <p className="font-mono text-xs text-rose">{(switchDevice.error as Error).message}</p>
      )}
    </div>
  );
}

export default function SystemPage() {
  const { data, isError, refetch } = useHealth();
  const [base, setBase] = useState(getApiBase());

  function saveBase() {
    setApiBase(base);
    refetch();
  }

  const statusLabel =
    data?.status === "loading"
      ? "loading model…"
      : data?.status === "error"
        ? "error"
        : data?.mock
          ? "mock mode"
          : "live";

  const compatTone =
    data?.status === "error" || data?.compatible === false
      ? "text-rose"
      : data?.status === "loading" || data?.mock
        ? "text-amber"
        : "text-lime";

  return (
    <div className="mx-auto max-w-xl space-y-8">
      <div>
        <h1 className="font-display text-xl font-bold tracking-tight text-bone">System</h1>
        <p className="label-kicker mt-1">runtime + backend status</p>
      </div>

      <section className="panel p-5">
        <p className="label-kicker mb-3">backend</p>
        {isError ? (
          <p className="font-mono text-sm text-rose">Cannot reach backend.</p>
        ) : data ? (
          <div>
            <Row label="status" value={statusLabel} tone={compatTone} />
            <Row label="model" value={data.model_path} />
            <Row label="loaded" value={data.model_loaded ? "yes" : "no"} />
            <Row label="device" value={data.device ?? "—"} />
            <Row label="gpu" value={data.gpu_name ?? "—"} />
            <Row label="vram" value={data.vram_gb ? `${data.vram_gb} GB` : "—"} />
            <Row
              label="compatible"
              value={data.compatible == null ? "—" : data.compatible ? "yes" : "no"}
              tone={compatTone}
            />
            {data.note && <p className="mt-3 font-mono text-xs text-amber">{data.note}</p>}
          </div>
        ) : (
          <p className="label-kicker">checking…</p>
        )}
      </section>

      <section className="panel p-5">
        <p className="label-kicker mb-1">gpu</p>
        <p className="mb-3 font-mono text-[11px] text-ash">
          Pick which GPU runs the model. Switching moves the model and takes a few seconds.
        </p>
        <GpuPicker />
      </section>

      <section className="panel p-5">
        <p className="label-kicker mb-1">backend url</p>
        <p className="mb-3 font-mono text-[11px] text-ash">
          Leave blank for same origin. Set this to use a backend running on a remote GPU box.
        </p>
        <div className="flex gap-2">
          <input
            value={base}
            onChange={(e) => setBase(e.target.value)}
            placeholder="https://my-gpu-box:8000"
            className="min-w-0 flex-1 rounded-md border border-edge bg-ink/60 px-3 py-2 font-mono text-sm text-bone placeholder:text-ash/50 focus:border-lime/60 focus:outline-none"
          />
          <button
            onClick={saveBase}
            className="rounded-md border border-lime/70 bg-lime/10 px-4 font-mono text-xs uppercase tracking-wider text-lime"
          >
            save
          </button>
        </div>
      </section>

      <p className="font-mono text-[11px] leading-relaxed text-ash">
        Powered by NVIDIA LocateAnything-3B, used under its{" "}
        <a
          href="https://huggingface.co/nvidia/LocateAnything-3B"
          target="_blank"
          rel="noreferrer"
          className="text-amber underline"
        >
          non-commercial license
        </a>{" "}
        (academic / research use only). This UI is Apache-2.0 and is not affiliated with NVIDIA.
      </p>
    </div>
  );
}

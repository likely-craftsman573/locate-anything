import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { resolveUrl } from "../api/client";
import { useHealth, useHistoryItem, useLocate, useTasks } from "../api/hooks";
import type { GenerationMode, LocateResult, TaskInfo } from "../api/types";
import InfoTip from "../components/InfoTip";
import Scope from "../components/Scope";
import UploadDropzone from "../components/UploadDropzone";

const MODES: GenerationMode[] = ["fast", "hybrid", "slow"];
const DECODE_HELP =
  "Speed vs. quality of box decoding. fast = predict all boxes in parallel, best for simple " +
  "scenes. hybrid (default) = parallel first, falls back to careful decoding when unsure. " +
  "slow = fully sequential, most accurate for dense or ambiguous scenes.";

async function urlToFile(url: string, name: string): Promise<File> {
  const res = await fetch(url);
  const blob = await res.blob();
  return new File([blob], name, { type: blob.type || "image/jpeg" });
}

export default function SearchPage() {
  const { data: tasks } = useTasks();
  const { data: health } = useHealth();
  const locate = useLocate();

  const [params, setParams] = useSearchParams();
  const loadId = params.get("load");
  const { data: loaded } = useHistoryItem(loadId);
  const appliedRef = useRef<string | null>(null);

  const [task, setTask] = useState("ground_multi");
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<GenerationMode>("hybrid");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<LocateResult | null>(null);

  const spec: TaskInfo | undefined = useMemo(
    () => tasks?.find((t) => t.name === task) ?? tasks?.[0],
    [tasks, task],
  );

  // Hydrate from a history entry when arriving via /?load=<id>.
  useEffect(() => {
    if (!loaded || appliedRef.current === loaded.id) return;
    appliedRef.current = loaded.id;
    setTask(loaded.task);
    setPrompt(loaded.prompt);
    setMode(loaded.generation_mode);
    setResult(loaded);
    setPreviewUrl(null);
    urlToFile(resolveUrl(loaded.image_url), `${loaded.id}.jpg`).then(setFile).catch(() => {});
  }, [loaded]);

  function chooseFile(f: File) {
    setFile(f);
    setResult(null);
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(f);
    });
    if (loadId) setParams({}, { replace: true });
    appliedRef.current = null;
  }

  function run() {
    if (!file || !spec) return;
    const form = new FormData();
    form.append("image", file);
    form.append("task", task);
    form.append("prompt", prompt);
    form.append("generation_mode", mode);
    locate.mutate(form, { onSuccess: setResult });
  }

  const modelLoading = health?.status === "loading";
  const modelError = health?.status === "error";
  const promptRequired = spec ? spec.input_kind !== "none" : true;
  const canRun =
    !!file &&
    (!promptRequired || prompt.trim().length > 0) &&
    !locate.isPending &&
    !modelLoading &&
    !modelError;
  const scopeSrc = result ? resolveUrl(result.image_url) : previewUrl;

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[360px_1fr]">
      {/* Console */}
      <section className="space-y-5">
        <div>
          <p className="label-kicker mb-2">target image</p>
          <UploadDropzone onFile={chooseFile} fileName={file?.name ?? (result ? "from log" : null)} />
        </div>

        <div>
          <p className="label-kicker mb-2">task</p>
          <div className="grid grid-cols-2 gap-2">
            {tasks?.map((t) => (
              <div key={t.name} className="relative flex">
                <button
                  onClick={() => setTask(t.name)}
                  className={`chip flex-1 pr-7 ${task === t.name ? "chip-on" : "chip-off"}`}
                >
                  {t.label}
                </button>
                <span className="absolute right-1.5 top-1/2 -translate-y-1/2">
                  <InfoTip text={t.description} align="right" label={`About ${t.label}`} />
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="label-kicker mb-2">{spec?.input_kind === "categories" ? "categories" : "prompt"}</p>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={!promptRequired}
            rows={2}
            placeholder={spec?.placeholder ?? ""}
            className="w-full resize-none rounded-md border border-edge bg-ink/60 px-3 py-2 font-mono text-sm text-bone placeholder:text-ash/50 focus:border-lime/60 focus:outline-none disabled:opacity-40"
          />
        </div>

        <div>
          <div className="mb-2 flex items-center gap-2">
            <p className="label-kicker">decode mode</p>
            <InfoTip text={DECODE_HELP} label="About decode modes" />
          </div>
          <div className="flex overflow-hidden rounded-md border border-edge">
            {MODES.map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 font-mono text-[11px] uppercase tracking-wider transition-colors ${
                  mode === m ? "bg-lime/15 text-lime" : "text-ash hover:text-bone"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={run}
          disabled={!canRun}
          className="ticks w-full rounded-md bg-lime py-3 font-display text-sm font-bold uppercase tracking-widest text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-25"
        >
          {locate.isPending ? "scanning…" : modelLoading ? "loading model…" : "▸ locate"}
        </button>

        {modelLoading && (
          <p className="font-mono text-xs text-amber">
            Model is loading — this can take a minute on first run.
          </p>
        )}
        {modelError && (
          <p className="font-mono text-xs text-rose">Model failed to load. Check the System page.</p>
        )}
        {locate.isError && (
          <p className="font-mono text-xs text-rose">{(locate.error as Error).message}</p>
        )}
      </section>

      {/* Viewport */}
      <section className="space-y-4">
        <Scope
          src={scopeSrc}
          boxes={result?.boxes ?? []}
          points={result?.points ?? []}
          scanning={locate.isPending}
        />
        {result && <ResultMeta result={result} />}
      </section>
    </div>
  );
}

function ResultMeta({ result }: { result: LocateResult }) {
  const [open, setOpen] = useState(false);
  const n = result.boxes.length + result.points.length;
  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-xs text-ash">
        <span>
          <span className="text-lime">{n}</span> hit{n === 1 ? "" : "s"}
        </span>
        <span>
          mode <span className="text-bone">{result.generation_mode}</span>
        </span>
        <span>
          <span className="text-bone">{result.timing_ms.toFixed(0)}</span> ms
        </span>
        <span>
          {result.image_width}×{result.image_height}
        </span>
        <button onClick={() => setOpen((o) => !o)} className="ml-auto text-ash hover:text-bone">
          {open ? "hide raw ▴" : "raw ▾"}
        </button>
      </div>
      {open && (
        <pre className="mt-3 max-h-40 overflow-auto rounded bg-ink/60 p-3 font-mono text-[11px] leading-relaxed text-ash">
          {result.raw || "(empty)"}
        </pre>
      )}
    </div>
  );
}

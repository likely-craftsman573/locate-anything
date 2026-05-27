import { useRef, useState } from "react";

interface Props {
  onFile: (file: File) => void;
  fileName?: string | null;
}

export default function UploadDropzone({ onFile, fileName }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  function pick(files: FileList | null) {
    const f = files?.[0];
    if (f && f.type.startsWith("image/")) onFile(f);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          pick(e.dataTransfer.files);
        }}
        className={`group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-4 py-7 text-center transition-colors ${
          drag ? "border-lime bg-lime/10" : "border-edge hover:border-ash/60"
        }`}
      >
        <span className="font-mono text-2xl text-lime">[ + ]</span>
        <span className="font-mono text-[11px] uppercase tracking-wider text-ash">
          {fileName ? (
            <span className="text-bone">{fileName}</span>
          ) : (
            <>
              drop image · <span className="text-bone underline-offset-2 group-hover:underline">browse</span>
            </>
          )}
        </span>
      </div>

      <button
        type="button"
        onClick={() => cameraRef.current?.click()}
        className="mt-2 w-full rounded-md border border-edge py-2 font-mono text-[11px] uppercase tracking-wider text-ash transition-colors hover:border-ash/60 hover:text-bone sm:hidden"
      >
        ⊙ use camera
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => pick(e.target.files)}
      />
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(e) => pick(e.target.files)}
      />
    </div>
  );
}

import { useHealth } from "../api/hooks";

export default function HealthBadge() {
  const { data, isError } = useHealth();

  let dot = "bg-ash";
  let text = "connecting";
  let pulse = !data && !isError;

  if (isError) {
    dot = "bg-rose";
    text = "offline";
  } else if (data) {
    if (data.status === "loading") {
      dot = "bg-amber";
      text = "loading model…";
      pulse = true;
    } else if (data.status === "error") {
      dot = "bg-rose";
      text = "model error";
    } else if (data.mock) {
      dot = "bg-amber";
      text = "mock mode";
    } else if (data.compatible) {
      dot = "bg-lime";
      text = data.gpu_name ? data.gpu_name.replace(/NVIDIA\s*/i, "") : "gpu ready";
    } else {
      dot = "bg-rose";
      text = "gpu incompatible";
    }
  }

  return (
    <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-ash">
      <span className={`h-2 w-2 rounded-full ${dot} ${pulse ? "animate-blink" : ""}`} />
      <span className="max-w-[40vw] truncate sm:max-w-none">{text}</span>
    </div>
  );
}

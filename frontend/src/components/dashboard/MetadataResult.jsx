import toast from "react-hot-toast";

import Button from "../ui/Button";
import Card from "../ui/Card";

const metadataConfig = [
  { key: "title", label: "Title Suggestions" },
  { key: "description", label: "Description" },
  { key: "tags", label: "Tags" },
  { key: "keywords", label: "Keywords" },
  { key: "summary", label: "Summary" },
  { key: "thumbnail_ideas", label: "Thumbnail Ideas" },
];

function MetadataResult({ metadata, onGenerate, loading }) {
  const copy = async (value) => {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    toast.success("Copied");
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">Metadata Output</h2>
        <Button onClick={onGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Metadata"}
        </Button>
      </div>

      {loading ? (
        <div className="panel-card flex items-center gap-3 p-5 text-slate-600">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
          AI is generating optimized metadata...
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {metadataConfig.map((item) => (
          <Card
            key={item.key}
            title={item.label}
            action={
              <Button
                variant="ghost"
                className="px-2 py-1 text-xs"
                onClick={() => copy(metadata?.[item.key])}
              >
                Copy
              </Button>
            }
          >
            <p className="whitespace-pre-wrap text-sm text-slate-600">
              {metadata?.[item.key] || "No content yet"}
            </p>
          </Card>
        ))}
      </div>

      {metadata?.playback_url ? (
        <Card title="Video Preview">
          <video controls src={metadata.playback_url} className="w-full rounded-xl" />
        </Card>
      ) : null}
    </div>
  );
}

export default MetadataResult;

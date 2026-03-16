import { useRef, useState } from "react";
import toast from "react-hot-toast";

import Button from "../ui/Button";
import Card from "../ui/Card";
import { uploadVideo } from "../../services/api";

function UploadVideo({ onUploaded, onGenerating, loading }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);

  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
    }
  };

  const upload = async () => {
    if (!file) {
      toast.error("Select a video file first");
      return;
    }
    try {
      onGenerating(true);
      const result = await uploadVideo(file);
      onUploaded(result);
      toast.success("Video uploaded and transcribed");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Upload failed");
    } finally {
      onGenerating(false);
    }
  };

  return (
    <Card title="Upload Video">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragging
            ? "border-brand-500 bg-brand-50"
            : "border-slate-300 bg-slate-50"
        }`}
      >
        <p className="text-sm text-slate-500">Drag and drop your video here</p>
        <p className="my-2 font-semibold text-slate-700">or</p>
        <Button
          variant="secondary"
          onClick={() => inputRef.current?.click()}
          type="button"
        >
          Choose File
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </div>

      {file ? (
        <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          Selected: <span className="font-semibold">{file.name}</span>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button onClick={upload} disabled={loading}>
          {loading ? "Processing..." : "Upload"}
        </Button>
      </div>
    </Card>
  );
}

export default UploadVideo;

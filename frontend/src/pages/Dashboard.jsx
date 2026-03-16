import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import HistoryList from "../components/dashboard/HistoryList";
import MetadataResult from "../components/dashboard/MetadataResult";
import UploadVideo from "../components/dashboard/UploadVideo";
import Navbar from "../components/layout/Navbar";
import { generateMetadata, getHistory, getVideoDetail } from "../services/api";

function Dashboard() {
  const [history, setHistory] = useState([]);
  const [selectedVideoId, setSelectedVideoId] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingGenerate, setLoadingGenerate] = useState(false);

  const loadHistory = async () => {
    try {
      const list = await getHistory();
      setHistory(list);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load history");
    }
  };

  const loadVideo = async (videoId) => {
    try {
      const item = await getVideoDetail(videoId);
      setSelectedVideoId(videoId);
      setMetadata(item);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load video detail");
    }
  };

  const onUploaded = (result) => {
    setSelectedVideoId(result.video_id);
    setMetadata({
      summary: "Video processed. Click Generate Metadata.",
      keywords: result.raw_tags?.join(", "),
      playback_url: result.video_url,
    });
    loadHistory();
  };

  const onGenerate = async () => {
    if (!selectedVideoId) {
      toast.error("Upload or select a video first");
      return;
    }

    setLoadingGenerate(true);
    try {
      const generated = await generateMetadata(selectedVideoId);
      const detail = await getVideoDetail(selectedVideoId);
      setMetadata({ ...detail, ...generated });
      toast.success("Metadata generated");
      loadHistory();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Generation failed");
    } finally {
      setLoadingGenerate(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="min-h-screen">
      <Navbar authenticated />
      <main className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-5 px-4 py-6 lg:grid-cols-[280px_1fr] md:px-8">
        <HistoryList
          items={history}
          selectedId={selectedVideoId}
          onSelect={(id) => loadVideo(id)}
        />

        <section className="space-y-5">
          <UploadVideo
            onUploaded={onUploaded}
            loading={loadingUpload}
            onGenerating={setLoadingUpload}
          />
          <MetadataResult
            metadata={metadata}
            onGenerate={onGenerate}
            loading={loadingGenerate}
          />
        </section>
      </main>
    </div>
  );
}

export default Dashboard;

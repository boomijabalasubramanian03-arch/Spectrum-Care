import { useEffect, useRef, useState } from "react";

export default function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const [snapshot, setSnapshot] = useState(null);
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        setError(
          "Camera access requires http://localhost or HTTPS. Open this app at http://localhost:8000 and allow camera permission."
        );
        return;
      }

      try {
        let stream;
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: "environment" },
              width: { ideal: 1280 },
              height: { ideal: 720 },
            },
            audio: false,
          });
        } catch (firstError) {
          if (["NotAllowedError", "SecurityError"].includes(firstError.name)) {
            throw firstError;
          }
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;
        const video = videoRef.current;
        if (!video) return;

        video.srcObject = stream;
        await new Promise((resolve) => {
          if (video.readyState >= 2 && video.videoWidth > 0) {
            resolve();
            return;
          }
          const timer = window.setTimeout(resolve, 4000);
          video.onloadeddata = () => {
            window.clearTimeout(timer);
            resolve();
          };
        });

        await video.play();

        if (!cancelled && video.videoWidth > 0 && video.videoHeight > 0) {
          setReady(true);
        } else if (!cancelled) {
          setError("The camera opened, but no video frames were received. Try again.");
        }
      } catch (err) {
        if (err.name === "NotAllowedError" || err.name === "SecurityError") {
          setError("Camera permission was denied. Allow camera access for localhost and try again.");
        } else if (err.name === "NotReadableError") {
          setError("The camera is already being used by another application.");
        } else if (err.name === "NotFoundError" || err.name === "OverconstrainedError") {
          setError("No compatible camera was found. You can use an image from the gallery instead.");
        } else {
          setError(`Could not start the camera: ${err.message || "unknown error"}`);
        }
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      const video = videoRef.current;
      if (video) video.srcObject = null;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  function takePhoto() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !ready) return;

    if (!video.videoWidth || !video.videoHeight) {
      setError("The camera is not ready yet. Wait a moment and try again.");
      return;
    }

    setCapturing(true);
    const MAX = 1600;
    const scale = Math.min(1, MAX / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);

    const ctx = canvas.getContext("2d", { alpha: false });
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    setSnapshot(canvas.toDataURL("image/jpeg", 0.9));
    setCapturing(false);
  }

  function retake() {
    setSnapshot(null);
    setError("");
  }

  function usePhoto() {
    const canvas = canvasRef.current;
    if (!canvas || !canvas.width || !canvas.height) return;

    canvas.toBlob((blob) => {
      if (!blob) {
        setError("Could not create the photo. Please retake it.");
        return;
      }
      const file = new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" });
      onCapture(file);
    }, "image/jpeg", 0.9);
  }

  return (
    <div className="camera-overlay" role="dialog" aria-modal="true" aria-label="Camera capture">
      <div className="camera-panel">
        <div className="camera-panel__head">
          <span>Camera capture</span>
          <button type="button" className="camera-close" onClick={onClose} aria-label="Close camera">
            ✕
          </button>
        </div>

        {error && (
          <div className="alert" role="alert">
            <span className="alert__icon" aria-hidden="true">⚠</span>
            <span>{error}</span>
          </div>
        )}

        <div className="camera-viewport">
          <video
            ref={videoRef}
            playsInline
            muted
            autoPlay
            style={{ display: !snapshot ? "block" : "none" }}
          />
          {snapshot && <img src={snapshot} alt="Captured preview" />}
          {!ready && !error && <p className="camera-loading">Requesting camera permission…</p>}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />

        <div className="camera-actions">
          {!snapshot ? (
            <button className="btn-primary" type="button" onClick={takePhoto} disabled={!ready || capturing}>
              {capturing ? "Capturing…" : "Take photo"}
            </button>
          ) : (
            <>
              <button className="btn-ghost" type="button" onClick={retake}>Retake</button>
              <button className="btn-primary" type="button" onClick={usePhoto}>Use this photo</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

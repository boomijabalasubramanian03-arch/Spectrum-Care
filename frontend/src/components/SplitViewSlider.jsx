import { useState, useRef, useCallback } from "react";

export default function SplitViewSlider({ originalUrl, cvdUrl, cvdType = "Deuteranopia" }) {
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handleMove = useCallback((clientX) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const x = clientX - rect.left;
    const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(pct);
  }, []);

  const onMouseDown = () => setIsDragging(true);
  const onMouseUp = () => setIsDragging(false);

  const onMouseMove = (e) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  const onTouchMove = (e) => {
    if (e.touches && e.touches[0]) {
      handleMove(e.touches[0].clientX);
    }
  };

  return (
    <div className="split-slider-wrapper">
      <div className="split-slider-header">
        <span className="split-slider-badge split-slider-badge--left">
          ◀ Original Scene ({Math.round(sliderPos)}%)
        </span>
        <span className="split-slider-badge split-slider-badge--right">
          As seen with {cvdType} ({Math.round(100 - sliderPos)}%) ▶
        </span>
      </div>

      <div
        ref={containerRef}
        className="split-slider-container"
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onTouchMove={onTouchMove}
      >
        {/* Right side: CVD Simulated */}
        <img
          src={cvdUrl || originalUrl}
          alt={`Scene seen with ${cvdType}`}
          className="split-slider-img split-slider-img--sim"
        />

        {/* Left side: Original Scene (clipped by slider) */}
        <div
          className="split-slider-clipped"
          style={{ width: `${sliderPos}%` }}
        >
          <img
            src={originalUrl}
            alt="Original Scene"
            className="split-slider-img split-slider-img--orig"
            style={{
              width: containerRef.current ? `${containerRef.current.clientWidth}px` : "100%",
              maxWidth: "none"
            }}
          />
        </div>

        {/* The sliding vertical bar */}
        <div
          className="split-slider-handle"
          style={{ left: `${sliderPos}%` }}
          onMouseDown={onMouseDown}
          onTouchStart={() => setIsDragging(true)}
        >
          <div className="split-slider-knob">
            <span>◀▶</span>
          </div>
        </div>
      </div>
      <p className="split-slider-hint">
        ↔ Drag the slider left or right to seamlessly compare true colors vs. simulated vision.
      </p>
    </div>
  );
}

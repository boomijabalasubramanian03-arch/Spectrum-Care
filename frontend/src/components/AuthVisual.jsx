// The signature element: shapes standing in for everyday objects, each
// gaining a contextual colour+object tag one at a time — the exact
// "Red Apple" / "Blue Shirt" transformation the product performs on
// every image it processes (see SRS 3.7 Context Analysis Module).
const TAGS = [
  { label: "Red Apple", dot: "#c4553b", top: "18%", left: "12%", delay: "0.1s" },
  { label: "Blue Shirt", dot: "#3b82c4", top: "58%", left: "6%", delay: "0.5s" },
  { label: "Green Tree", dot: "#2c6e71", top: "10%", left: "58%", delay: "0.9s" },
  { label: "Yellow Bus", dot: "#e8a33d", top: "70%", left: "56%", delay: "1.3s" },
];

const BLOBS = [
  { size: 130, top: "14%", left: "10%", bg: "#c4553b" },
  { size: 100, top: "54%", left: "4%", bg: "#3b82c4" },
  { size: 150, top: "6%", left: "54%", bg: "#2c6e71" },
  { size: 110, top: "66%", left: "52%", bg: "#e8a33d" },
];

export default function AuthVisual() {
  return (
    <aside className="auth-visual" aria-hidden="true">
      <div className="auth-visual__brand">
        <span className="auth-visual__brand-mark" />
        Chroma Context
      </div>

      <div className="auth-visual__stage">
        {BLOBS.map((b, i) => (
          <span
            key={i}
            className="auth-visual__blob"
            style={{
              width: b.size,
              height: b.size,
              top: b.top,
              left: b.left,
              background: b.bg,
              opacity: 0.22,
            }}
          />
        ))}
        {TAGS.map((t, i) => (
          <span
            key={i}
            className="auth-visual__tag"
            style={{ top: t.top, left: t.left, animationDelay: t.delay }}
          >
            <span className="auth-visual__tag-dot" style={{ background: t.dot }} />
            {t.label}
          </span>
        ))}
      </div>

      <div>
        <p className="auth-visual__caption">
          Not just <span>&ldquo;red.&rdquo;</span> The object it belongs to — spoken aloud,
          the instant you upload.
        </p>
        <p className="auth-visual__footnote">
          YOLO object detection · OpenCV colour extraction · Amazon Polly voice guidance
        </p>
      </div>
    </aside>
  );
}

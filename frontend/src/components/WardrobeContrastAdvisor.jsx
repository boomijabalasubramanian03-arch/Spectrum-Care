import { useMemo } from "react";

// Color pairs that are notoriously confusable under CVD
const CONFUSIONS = {
  Deuteranopia: [
    ["Red", "Green"], ["Red", "Brown"], ["Green", "Brown"], ["Teal", "Gray"], ["Pink", "Gray"]
  ],
  Protanopia: [
    ["Red", "Black"], ["Red", "Dark Gray"], ["Red", "Brown"], ["Green", "Yellow"], ["Blue", "Purple"]
  ],
  Tritanopia: [
    ["Blue", "Green"], ["Yellow", "Pink"], ["Purple", "Black"], ["Orange", "Red"]
  ]
};

export default function WardrobeContrastAdvisor({ detections = [], cvdType = "Deuteranopia" }) {
  const analysis = useMemo(() => {
    if (!detections || detections.length === 0) return null;

    // Only check wearable / wardrobe items
    const WARDROBE_LABELS = new Set([
      "tie", "shirt", "suit", "jacket", "coat", "pants", "dress", "hat", "backpack", "handbag", "suitcase"
    ]);

    const relevant = detections.filter(d => WARDROBE_LABELS.has(d.label.toLowerCase()));

    // If there are fewer than 2 wardrobe items, do not render this advisor!
    if (relevant.length < 2) return null;

    const items = relevant;
    const confusablePairs = CONFUSIONS[cvdType] || CONFUSIONS.Deuteranopia;

    const pairs = [];
    let conflictsCount = 0;

    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        const a = items[i];
        const b = items[j];
        if (a.color === b.color) continue;

        const isConfusable = confusablePairs.some(
          ([c1, c2]) =>
            (a.color.includes(c1) && b.color.includes(c2)) ||
            (a.color.includes(c2) && b.color.includes(c1))
        );

        if (isConfusable) {
          conflictsCount++;
          pairs.push({
            itemA: `${a.color} ${a.label}`,
            itemB: `${b.color} ${b.label}`,
            status: "conflict",
            message: `⚠️ High confusion risk under ${cvdType}. Both items may look almost identical. Rely on labels or separate them.`,
            badge: "Confusable Pair"
          });
        } else {
          pairs.push({
            itemA: `${a.color} ${a.label}`,
            itemB: `${b.color} ${b.label}`,
            status: "safe",
            message: `✅ Distinct contrast under ${cvdType}. Easy to differentiate at a glance.`,
            badge: "Safe Pairing"
          });
        }
      }
    }

    return { pairs: pairs.slice(0, 4), conflictsCount };
  }, [detections, cvdType]);

  if (!analysis || analysis.pairs.length === 0) return null;

  return (
    <div className="advisor-card animate-fade-in">
      <div className="advisor-card__head">
        <div>
          <h4 className="advisor-card__title">👔 Wardrobe &amp; Item Contrast Advisor</h4>
          <span className="advisor-card__subtitle">
            Everyday color harmony &amp; distinctiveness check tailored for {cvdType}
          </span>
        </div>
        <span className={`advisor-pill advisor-pill--${analysis.conflictsCount > 0 ? "warning" : "good"}`}>
          {analysis.conflictsCount > 0 ? `${analysis.conflictsCount} Confusion Warning` : "All Safe Pairings"}
        </span>
      </div>

      <div className="advisor-list">
        {analysis.pairs.map((p, idx) => (
          <div key={idx} className={`advisor-item advisor-item--${p.status}`}>
            <div className="advisor-item__header">
              <span className="advisor-item__combo">
                <strong>{p.itemA}</strong> <span className="text-secondary">&amp;</span> <strong>{p.itemB}</strong>
              </span>
              <span className={`advisor-tag advisor-tag--${p.status}`}>{p.badge}</span>
            </div>
            <p className="advisor-item__msg">{p.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

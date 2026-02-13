// extension/src/content/overlay.ts
// Purpose: Inject floating "Optymalizuj" button on product pages
// NOT for: Popup UI or data extraction

import type { ProductData } from "@shared/types";
import { MSG } from "@shared/messages";

const OVERLAY_ID = "ns-overlay-btn";

export function injectOverlay(product: ProductData) {
  // Don't inject twice
  if (document.getElementById(OVERLAY_ID)) return;

  const container = document.createElement("div");
  container.id = OVERLAY_ID;
  container.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 2147483647;
    display: flex;
    align-items: center;
    gap: 8px;
    background: #1A1A1A;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 10px 16px;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    color: #fff;
    transition: transform 0.15s, box-shadow 0.15s;
    user-select: none;
  `;

  // Icon (simple chart/optimize icon via SVG)
  const icon = document.createElement("span");
  icon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>`;
  icon.style.display = "flex";

  // Label
  const label = document.createElement("span");
  label.textContent = "Optymalizuj";
  label.style.fontWeight = "600";

  // Close button
  const closeBtn = document.createElement("span");
  closeBtn.textContent = "×";
  closeBtn.style.cssText = `
    margin-left: 4px;
    font-size: 18px;
    color: #666;
    cursor: pointer;
    line-height: 1;
    padding: 0 2px;
  `;
  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    container.remove();
  });

  container.appendChild(icon);
  container.appendChild(label);
  container.appendChild(closeBtn);

  // Hover effect
  container.addEventListener("mouseenter", () => {
    container.style.transform = "scale(1.05)";
    container.style.boxShadow = "0 6px 24px rgba(0,0,0,0.6)";
  });
  container.addEventListener("mouseleave", () => {
    container.style.transform = "scale(1)";
    container.style.boxShadow = "0 4px 20px rgba(0,0,0,0.5)";
  });

  // Click → open popup (MV3 can't programmatically open popup, so send message)
  container.addEventListener("click", () => {
    chrome.runtime.sendMessage({
      type: MSG.OPEN_POPUP,
      payload: product,
    });
  });

  document.body.appendChild(container);
}

// FourenStudio: drifting wave dividers and preset audio players.
(function () {
  "use strict";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- drifting waves: parallel lines whose depth and speed wander, like DRiFT's scope ----
  const svgNS = "http://www.w3.org/2000/svg";
  document.querySelectorAll(".waves-svg").forEach(function (svg, index) {
    const lines = 6;
    const gradId = "wave-grad-" + index;
    svg.innerHTML =
      '<defs><linearGradient id="' + gradId + '" x1="0" x2="1" y1="0" y2="0">' +
      '<stop offset="0" stop-color="#86ffcf"/><stop offset="0.55" stop-color="#e8dfc8"/><stop offset="1" stop-color="#f2c48d"/>' +
      "</linearGradient></defs>";
    const paths = [];
    for (let i = 0; i < lines; i++) {
      const p = document.createElementNS(svgNS, "path");
      p.setAttribute("fill", "none");
      p.setAttribute("stroke", "url(#" + gradId + ")");
      p.setAttribute("stroke-width", "3");
      p.setAttribute("opacity", String(1 - i * 0.15));
      p.setAttribute("vector-effect", "non-scaling-stroke");
      svg.appendChild(p);
      paths.push(p);
    }

    // slow random walks for depth and speed, so the motion never settles into a loop
    let depth = 0.5, depthTarget = 0.6, speed = 1, speedTarget = 1, phase = 0, last = 0;
    function draw(t) {
      const w = svg.clientWidth || 1000, h = svg.clientHeight || 160;
      const dt = Math.min(0.05, (t - last) / 1000 || 0.016);
      last = t;
      if (Math.random() < dt * 0.4) depthTarget = 0.25 + Math.random() * 0.75;
      if (Math.random() < dt * 0.3) speedTarget = 0.4 + Math.random() * 1.4;
      depth += (depthTarget - depth) * dt * 0.8;
      speed += (speedTarget - speed) * dt * 0.6;
      phase += dt * speed * 1.6;

      const amp = h * 0.16 * depth, period = Math.max(120, w / 7);
      paths.forEach(function (p, i) {
        const base = h * 0.22 + i * h * 0.11;
        let d = "";
        for (let x = 0; x <= w; x += 8) {
          const y = base + amp * Math.sin((x / period) * Math.PI * 2 + phase + i * 0.35);
          d += (x === 0 ? "M" : "L") + x + " " + y.toFixed(1);
        }
        p.setAttribute("d", d);
      });
      if (!reduceMotion) requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
  });

  // ---- preset players: one plays at a time ----
  let current = null; // { button, audio }
  function stop() {
    if (!current) return;
    current.audio.pause();
    current.button.classList.remove("playing");
    current.button.setAttribute("aria-label", current.button.getAttribute("aria-label").replace(/^Pause/, "Play"));
    current = null;
  }
  document.querySelectorAll(".play").forEach(function (button) {
    const bar = button.parentElement.querySelector(".track-bar span");
    let audio = null;
    button.addEventListener("click", function () {
      if (current && current.button === button) { stop(); return; }
      stop();
      if (!audio) {
        audio = new Audio(button.dataset.src);
        audio.addEventListener("timeupdate", function () {
          if (audio.duration) bar.style.width = (100 * audio.currentTime / audio.duration) + "%";
        });
        audio.addEventListener("ended", function () { stop(); bar.style.width = "0"; });
      }
      audio.currentTime = 0;
      audio.play();
      button.classList.add("playing");
      button.setAttribute("aria-label", button.getAttribute("aria-label").replace(/^Play/, "Pause"));
      current = { button: button, audio: audio };
    });
  });

})();

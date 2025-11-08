// js/pages/support.js
// Renders general helplines for EN countries,
// and adds VETERAN-ONLY helplines when Firestore user.isVeteran === true.
// Also respects ?veteran=1 for quick manual testing.

(function () {
  const $ = (sel) => document.querySelector(sel);
  const helplineRoot = $("#helpline-content");
  const langSelect = $("#language-selector");

  // ----- Country detection (very lightweight & safe) -----
  const CC_MAP = {
    US: "United States",
    GB: "United Kingdom",
    CA: "Canada",
    AU: "Australia",
    NZ: "New Zealand",
    IE: "Ireland",
  };

  function detectCountryCode() {
    // Try navigator.language -> region (e.g., en-GB)
    const nav = (navigator.language || "en-GB").toUpperCase();
    const m = nav.match(/-([A-Z]{2})$/);
    const cc = m ? m[1] : "GB";
    return CC_MAP[cc] ? cc : "GB";
  }

  // ----- Data: GENERAL helplines (shown to everyone) -----
  const GENERAL = {
    US: [
      { name: "988 Suicide & Crisis Lifeline", detail: "Dial 988 (24/7)", tel: "988", url: "https://988lifeline.org" },
      { name: "Crisis Text Line", detail: 'Text HOME to 741741', url: "https://www.crisistextline.org" },
      { name: "National Domestic Violence Hotline", detail: "1-800-799-SAFE (7233)", tel: "+18007997233", url: "https://www.thehotline.org" },
    ],
    GB: [
      { name: "Samaritans", detail: "116 123 (free, 24/7)", tel: "116123", url: "https://www.samaritans.org" },
      { name: "Mind (Info line)", detail: "0300 123 3393", tel: "+443001233393", url: "https://www.mind.org.uk" },
      { name: "National Domestic Abuse Helpline", detail: "0808 2000 247 (24/7)", tel: "+448082000247", url: "https://www.nationaldahelpline.org.uk" },
    ],
    CA: [
      { name: "988 Suicide Crisis Helpline", detail: "Dial or text 988 (24/7)", tel: "988", url: "https://988.ca" },
      { name: "Kids Help Phone", detail: "1-800-668-6868 / Text CONNECT to 686868", tel: "+18006686868", url: "https://kidshelpphone.ca" },
      { name: "Hope for Wellness (Indigenous)", detail: "1-855-242-3310", tel: "+18552423310", url: "https://www.hopeforwellness.ca" },
    ],
    AU: [
      { name: "Lifeline", detail: "13 11 14 (24/7)", tel: "131114", url: "https://www.lifeline.org.au" },
      { name: "Beyond Blue", detail: "1300 22 4636", tel: "1300224636", url: "https://www.beyondblue.org.au" },
      { name: "Kids Helpline", detail: "1800 55 1800", tel: "1800551800", url: "https://kidshelpline.com.au" },
    ],
    NZ: [
      { name: "Need to Talk?", detail: "Call or text 1737 (24/7)", tel: "1737", url: "https://1737.org.nz" },
      { name: "Lifeline New Zealand", detail: "0800 543 354", tel: "+64800543354", url: "https://www.lifeline.org.nz" },
      { name: "Youthline", detail: "0800 376 633 / Free text 234", tel: "+64800376633", url: "https://www.youthline.co.nz" },
    ],
    IE: [
      { name: "Samaritans Ireland", detail: "116 123 (24/7)", tel: "116123", url: "https://www.samaritans.org/ireland" },
      { name: "Women’s Aid", detail: "1800 341 900 (24/7)", tel: "+3531800341900", url: "https://www.womensaid.ie" },
      { name: "Pieta (suicide & self-harm)", detail: "1800 247 247 / Text HELP to 51444", tel: "+3531800247247", url: "https://www.pieta.ie" },
    ],
  };

  // ----- Data: VETERAN-ONLY helplines (shown only if isVeteran === true) -----
  const VETERAN = {
    US: [
      { name: "Veterans Crisis Line", detail: "Dial 988 then press 1 (24/7)", tel: "988", url: "https://www.veteranscrisisline.net" },
      { name: "Vet Center Call Center (WAR-VETS)", detail: "1-877-927-8387", tel: "+18779278387", url: "https://www.vetcenter.va.gov" },
      { name: "VA Caregiver Support Line", detail: "1-855-260-3274", tel: "+18552603274", url: "https://www.caregiver.va.gov" },
    ],
    GB: [
      { name: "Combat Stress (24/7 Helpline)", detail: "0800 138 1619", tel: "+448001381619", url: "https://combatstress.org.uk" },
      { name: "Veterans’ Gateway", detail: "0808 802 1212", tel: "+448088021212", url: "https://www.veteransgateway.org.uk" },
      { name: "SSAFA Forcesline", detail: "0800 260 6767", tel: "+448002606767", url: "https://www.ssafa.org.uk/get-help/forcesline" },
      { name: "NHS Op COURAGE", detail: "Mental health service for veterans", url: "https://www.nhs.uk/opcourage" },
    ],
    CA: [
      { name: "VAC Assistance Service", detail: "1-800-268-7708 (24/7)", tel: "+18002687708", url: "https://www.veterans.gc.ca/eng/contact" },
      { name: "OSISS (Operational Stress Injury Social Support)", detail: "1-800-883-6094", tel: "+18008836094", url: "https://www.osiss.ca" },
    ],
    AU: [
      { name: "Open Arms — Veterans & Families Counselling", detail: "1800 011 046 (24/7)", tel: "1800011046", url: "https://www.openarms.gov.au" },
      { name: "Defence Family Helpline", detail: "1800 624 608", tel: "1800624608", url: "https://www.defence.gov.au/members-families/support" },
    ],
    NZ: [
      { name: "Veterans’ Affairs New Zealand", detail: "0800 483 8372 (0800 4 VETERAN)", tel: "+648004838372", url: "https://www.veteransaffairs.mil.nz" },
      { name: "RSA (Returned & Services’ Association)", detail: "Local support & services", url: "https://www.rsa.org.nz" },
    ],
    IE: [
      { name: "ONE — Organisation of National Ex-Service Personnel", detail: "01 485 4000", tel: "+35314854000", url: "https://one-veterans.org" },
      { name: "IUNVA — Irish UN Veterans Association", detail: "01 671 2716", tel: "+35316712716", url: "https://www.iunva.ie" },
    ],
  };

  // ----- Render helpers -----
  function telHref(t) {
    if (!t) return null;
    // Keep digits and plus
    const cleaned = t.replace(/[^\d+]/g, "");
    return cleaned ? `tel:${cleaned}` : null;
  }

  function liFor(service) {
    const li = document.createElement("li");
    const name = document.createElement("strong");
    name.textContent = service.name;

    const span = document.createElement("span");
    span.className = "service-detail";
    span.textContent = `: ${service.detail || ""}`;

    const parts = document.createElement("div");
    parts.className = "service-row";

    const left = document.createElement("div");
    left.appendChild(name);
    left.appendChild(span);

    const right = document.createElement("div");
    right.className = "service-actions";

    const tel = service.tel || telHref(service.detail);
    if (tel) {
      const aTel = document.createElement("a");
      aTel.href = tel.startsWith("tel:") ? tel : `tel:${tel}`;
      aTel.className = "chip";
      aTel.textContent = "Call";
      right.appendChild(aTel);
    }
    if (service.url) {
      const aWeb = document.createElement("a");
      aWeb.href = service.url;
      aWeb.target = "_blank";
      aWeb.rel = "noopener";
      aWeb.className = "chip";
      aWeb.textContent = "Website";
      right.appendChild(aWeb);
    }

    parts.appendChild(left);
    parts.appendChild(right);
    li.appendChild(parts);
    return li;
  }

  function block(title, list, opts = {}) {
    const section = document.createElement("section");
    section.className = `helpline-block ${opts.variant || ""}`;

    const h2 = document.createElement("h2");
    h2.innerHTML = `${title} ${opts.badge ? `<span class="badge">${opts.badge}</span>` : ""}`;
    section.appendChild(h2);

    const ul = document.createElement("ul");
    list.forEach((svc) => ul.appendChild(liFor(svc)));
    section.appendChild(ul);

    return section;
  }

  function renderAll({ cc, isVeteran }) {
    helplineRoot.innerHTML = "";

    // Emergency banner
    const emergency = document.createElement("div");
    emergency.className = "emergency-banner";
    emergency.innerHTML =
      '<strong>If you or someone else is in immediate danger:</strong> call your local emergency number (e.g., <em>999</em>, <em>911</em>, <em>112</em>).';
    helplineRoot.appendChild(emergency);

    // Language selector (simple list of EN countries)
    if (langSelect) {
      langSelect.innerHTML = "";
      Object.entries(CC_MAP).forEach(([code, label]) => {
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = label;
        if (code === cc) opt.selected = true;
        langSelect.appendChild(opt);
      });
      langSelect.addEventListener("change", () => {
        renderAll({ cc: langSelect.value, isVeteran });
      });
    }

    // Main general block (selected country)
    const countryName = CC_MAP[cc];
    const generalList = GENERAL[cc] || [];
    helplineRoot.appendChild(
      block(`${countryName} — General Support`, generalList)
    );

    // Veteran-only (if flagged)
    if (isVeteran) {
      const vets = VETERAN[cc] || [];
      if (vets.length) {
        helplineRoot.appendChild(
          block(`${countryName} — Veterans & Families`, vets, {
            variant: "veteran",
            badge: "Veterans only",
          })
        );
      }

      // Small note if travelling
      const tip = document.createElement("p");
      tip.className = "tip";
      tip.textContent =
        "Travelling or posted abroad? Your domestic veteran services can still advise and signpost you.";
      helplineRoot.appendChild(tip);
    }

    // Optional: “More countries” accordion
    const other = Object.keys(CC_MAP).filter((k) => k !== cc);
    const details = document.createElement("details");
    details.className = "other-countries";
    const sum = document.createElement("summary");
    sum.textContent = "Show resources for other English-speaking countries";
    details.appendChild(sum);

    other.forEach((code) => {
      const name = CC_MAP[code];
      details.appendChild(block(`${name} — General Support`, GENERAL[code]));
      if (isVeteran && VETERAN[code]?.length) {
        details.appendChild(
          block(`${name} — Veterans & Families`, VETERAN[code], {
            variant: "veteran",
            badge: "Veterans only",
          })
        );
      }
    });

    helplineRoot.appendChild(details);
  }

  // ----- Bootstrap: figure out veteran flag -----
  async function getVeteranFlag() {
    // URL override for testing
    const p = new URLSearchParams(location.search);
    if (p.get("veteran") === "1" || p.get("v") === "1") return true;

    // If Firebase is available and user is signed in, read Firestore
    try {
      if (window.firebase?.auth) {
        const user = firebase.auth().currentUser;
        if (user) {
          const doc = await firebase.firestore().collection("users").doc(user.uid).get();
          if (doc.exists) {
            const d = doc.data() || {};
            return Boolean(
              d.isVeteran ||
              d.profile?.isVeteran ||
              d.ai_preferences?.isVeteran ||
              d.onboarding_data?.isVeteran
            );
          }
        } else {
          // Wait briefly for onAuthStateChanged if auth is still starting up
          await new Promise((r) => setTimeout(r, 300));
          return Boolean(firebase.auth().currentUser && (await getVeteranFlag()));
        }
      }
    } catch (e) {
      console.warn("Veteran flag fetch failed; defaulting to false", e);
    }
    return false;
  }

  // Kickoff
  (async function init() {
    const cc = detectCountryCode();
    const isVeteran = await getVeteranFlag();
    renderAll({ cc, isVeteran });
  })();
})();

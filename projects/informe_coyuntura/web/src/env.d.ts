/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  /** Measurement ID de GA4 (G-XXXXXXXXXX). Sin esta variable el sitio no carga gtag.js. */
  readonly PUBLIC_GA_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

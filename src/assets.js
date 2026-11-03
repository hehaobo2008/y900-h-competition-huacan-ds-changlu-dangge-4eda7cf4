// Resolve runtime assets. The online build reads /assets; the single-file
// offline build installs window.__ASSET_MAP with data URLs before boot.
export const ASSET = (p) => (typeof window !== 'undefined' && window.__ASSET_MAP && window.__ASSET_MAP[p]) || new URL('.' + p, document.baseURI).href;

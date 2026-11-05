const APP_BASE_URL = import.meta.env.BASE_URL;

export function publicAssetUrl(path) {
  return `${APP_BASE_URL}${path.replace(/^\/+/, "")}`;
}

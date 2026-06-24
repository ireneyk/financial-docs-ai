/** Validated client environment — read env vars only here. */

function requireEnv(name: string): string {
  const value = import.meta.env[name];
  if (!value || value.trim() === "") {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value.trim();
}

export const env = {
  apiBaseUrl: requireEnv("VITE_API_BASE_URL").replace(/\/$/, ""),
  supabaseUrl: requireEnv("VITE_SUPABASE_URL"),
  supabaseAnonKey: requireEnv("VITE_SUPABASE_ANON_KEY"),
};

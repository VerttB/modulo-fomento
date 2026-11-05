import tailwindcss from "@tailwindcss/vite";
 export default defineConfig({
   envDir: "../..",
   plugins: [react(), tailwindcss()],
  base: '/fomento/',
   server: {
     allowedHosts: [
      'observatoriocti.secti.ba.gov.br'],
     host: "0.0.0.0",
     port: 5173,
   hmr: {
      host: 'observatoriocti.secti.ba.gov.br',
      protocol: 'wss',
      clientPort: 443,

    },
   proxy: {
      '/fomento/api': {
        target: 'http://api:8000', // Porta onde o container da API escuta
        changeOrigin: true,
      rewrite: (path) => path.replace(/^\/fomento\/api/, '/api'),
     },
    },
   },
 });
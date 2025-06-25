import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    __BUILD_DATE__: JSON.stringify(new Date().toLocaleDateString('en-GB')), // Format: DD-MM-YYYY
  },
  server: {
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'activetigger.eschultz.fr',
      'activetigger2.eschultz.fr',
    ],
  },
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  if (command === 'serve') {
    return {
      plugins: [react()],
      server: {
        port: 3000,
        proxy: {
          '/api': {
            target: 'http://0.0.0.0:7860',
            changeOrigin: true,
          },
        },
      },
    };
  } else {
    return {
      plugins: [react()],
      build: {
        outDir: './build',
      },
    };
  }
});

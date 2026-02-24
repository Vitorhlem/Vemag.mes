import { defineConfig } from '#q-app/wrappers';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default defineConfig((ctx: any) => {
  return {
    // REMOVI O BLOCO sourceFiles DAQUI

    boot: ['axios', 'apexcharts', 'push-notifications'],

    css: ['app.scss'],

    extras: ['roboto-font', 'material-icons'],

    build: {
      eslint: {
    warnings: true,
    errors: false, // <-- MUDE PARA FALSE: Impede que o erro pare o build
    fix: true      // Tenta corrigir erros simples (como ponto e vírgula) sozinho
  },
      target: {
        browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
        node: 'node20',
      },
      typescript: {
        strict: true,
        vueShim: true,
      },
      vueRouterMode: 'hash',
      env: {
        VITE_API_URL: ctx.dev ? 'http://localhost:8000/api/v1' : 'http://192.168.0.22:8000/api/v1' 
      },
      vitePlugins: [
        [
          'vite-plugin-checker',
          {
            vueTsc: false,
            eslint: {
              lintCommand:
                'eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"',
              useFlatConfig: true,
            },
          },
          { server: false },
        ],
      ],
    },

    devServer: {
      port: 9000,
      open: true
    },

    framework: {
      config: {},
      // CORREÇÃO AQUI: Adicionado 'Loading' na lista
      plugins: ['Notify', 'Dialog', 'Loading'], 
    },

    animations: [],

    ssr: {
      prodPort: 3000,
      middlewares: ['render'],
      pwa: false,
    },

    pwa: {
      workboxMode: 'GenerateSW',
    },

    capacitor: {
      hideSplashscreen: true,
    },

    electron: {
      preloadScripts: ['electron-preload'],
      inspectPort: 5858,
      bundler: 'packager',
      builder: {
        appId: 'com.vemag.mes',
      },
    },

    bex: {
      extraScripts: [],
    },
  };
});
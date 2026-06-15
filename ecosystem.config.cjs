const path = require('path');

const root = __dirname;

module.exports = {
  apps: [
    {
      name: 'core',
      script: path.join(root, 'scripts/start-core.sh'),
      cwd: root,
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '128M',
      env: {
        CORE_HOST: '127.0.0.1',
        CORE_PORT: '3040',
        CORE_DB_PATH: path.join(root, 'data/conversations.db'),
      },
      error_file: './logs/core-error.log',
      out_file: './logs/core-out.log',
      log_file: './logs/core-combined.log',
      time: true,
    },
  ],
};

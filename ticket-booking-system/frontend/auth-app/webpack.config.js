const {
  shareAll,
  withModuleFederationPlugin,
} = require('@angular-architects/module-federation/webpack');

module.exports = withModuleFederationPlugin({
  name: 'auth',

  exposes: {
    './LoginComponent': './src/app/login/login.ts',
  },

  shared: {
    ...shareAll({ singleton: true, strictVersion: true, requiredVersion: 'auto' }),
  },
});
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    entry: './src/scripts/main.js',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'js/[name].[contenthash].js',
      publicPath: isProduction ? '/sensylate-static/' : '/',
      clean: true,
    },
    module: {
      rules: [
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            'postcss-loader',
          ],
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html',
      }),
      isProduction &&
        new MiniCssExtractPlugin({
          filename: 'css/[name].[contenthash].css',
        }),
    ].filter(Boolean),
    devServer: {
      static: [
        {
          directory: path.join(__dirname, 'dist'),
        },
        {
          directory: path.join(__dirname, 'src'),
          publicPath: '/',
        },
      ],
      port: 3000,
      hot: true,
      proxy: [
        {
          context: ['/api'],
          target: 'http://localhost:8000',
        },
      ],
    },
  };
};

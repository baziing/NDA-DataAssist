module.exports = {
  title: 'Vue Element Admin',

  /**
   * @type {boolean} true | false
   * @description Whether show the settings right-panel
   */
  showSettings: true,

  /**
   * @type {boolean} true | false
   * @description Whether need tagsView
   */
  tagsView: true,

  /**
   * @type {boolean} true | false
   * @description Whether fix the header
   */
  fixedHeader: false,

  /**
   * @type {boolean} true | false
   * @description Whether show the logo in sidebar
   */
  sidebarLogo: false,

  /**
   * @type {string | array} 'production' | ['production', 'development']
   * @description Need show err logs component.
   * The default is only used in the production env
   * If you want to also use it in dev, you can pass ['production', 'development']
   */
  errorLog: 'production',

  /**
   * @type {string[]}
   * @description Modules to hide in sidebar. Use route names.
   */
  hiddenModules: ['Permission', 'Icons', 'ComponentDemo', 'Charts', 'Nested', 'Table', 'Example', 'Tab', 'ErrorPages', 'ErrorLog', 'Excel', 'Zip', 'PDF', 'Theme', 'ClipboardDemo', 'external-link', 'Guide', 'Documentation'],

  /**
   * @type {string}
   * @description The address of the backend server.
   *  - For local development, use 'localhost'.
   *  - For network access, use the server's IP address or hostname (e.g., '192.168.1.100' or 'my-server.example.com').
   */
  serverAddress: process.env.VUE_APP_SERVER_ADDRESS || 'localhost'
}

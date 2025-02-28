module.exports = {
  title: 'Vue Element Admin',

  /**
   * @type {boolean} true | false
   * @description Whether show the settings right-panel
   */
  showSettings: false,

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

  // ['Permission', 'Icons', 'ComponentDemo', 'Charts', 'Nested', 'Table', 'Example', 'Tab', 'ErrorPages', 'ErrorLog', 'Excel', 'Zip', 'PDF', 'Theme', 'ClipboardDemo', 'external-link', 'Guide', 'Documentation']

  /**
   * @type {string}
   * @description The address of the backend server.
   *  - For local development, use 'localhost'.
   *  - For network access, use the server's IP address or hostname (e.g., '192.168.1.100' or 'my-server.example.com').
   */
  serverAddress: process.env.VUE_APP_SERVER_ADDRESS || 'localhost',

  gameCategories: [
    { label: '无归类', value: '无归类' },
    { label: '风之大陆', value: '风之大陆' },
    { label: '战神遗迹', value: '战神遗迹' },
    { label: '云上城之歌', value: '云上城之歌' },
    { label: '闪烁之光', value: '闪烁之光' },
    { label: '有杀气童话2', value: '有杀气童话2' },
    { label: '矩阵临界', value: '矩阵临界' },
    { label: '不朽觉醒', value: '不朽觉醒' },
    { label: '最后的原始人', value: '最后的原始人' },
    { label: 'Kemono Friends', value: 'Kemono Friends' },
    { label: 'Order Daybreak', value: 'Order Daybreak' },
    { label: 'The Dragon Odyssey', value: 'The Dragon Odyssey' },
    { label: '白荆回廊', value: '白荆回廊' }
  ]
}

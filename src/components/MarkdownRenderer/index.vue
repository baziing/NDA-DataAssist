<template>
  <vue-markdown :source="content" />
</template>

<script>
import VueMarkdown from 'vue-markdown'

export default {
  name: 'MarkdownRenderer',
  components: { VueMarkdown },
  props: {
    content: {
      type: String,
      required: true
    }
  }
}
</script>

<style scoped>
/* 使用深度选择器覆盖 vue-markdown 内部样式 */
::v-deep pre {
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
    color: #000;
}

::v-deep code {
  border: 1px solid #eee;
  /* 可以根据需要调整内边距 */
  /* padding: 2px 4px; */
   background-color: #f9f9f9;
    color: #000
}

::v-deep pre code {
  border: none; /* 移除 pre code 的边框 */
  padding: 0; /* 移除 pre code 的内边距 */
  background-color: transparent; /* 移除 pre code 的背景色 */
  display: block;
  font-family: Consolas, Menlo, 'Courier New', monospace; /* 设置字体为 Consolas */
}
  ::v-deep h1, ::v-deep h2, ::v-deep h3, ::v-deep h4, ::v-deep h5, ::v-deep h6 {
    font-weight: bold;
    margin-bottom: 0.5em;
    color: #000;
  }

  ::v-deep h1 {
    font-size: 1.8em;
    border-bottom: 1px solid #ccc;
  }

  ::v-deep h2 {
    font-size: 1.5em;
  }

  ::v-deep h3 {
    font-size: 1.3em;
  }

    ::v-deep h4 {
     font-size: 1.2em;
  }

  ::v-deep p {
    margin-bottom: 1em;
    color: #000;
  }

  ::v-deep ul, ::v-deep ol {
    margin-bottom: 1em;
    padding-left: 2em;
    color: #000;
  }

  ::v-deep li {
    margin-bottom: 0.5em;
  }

  ::v-deep blockquote {
    border-left: 4px solid #ccc;
    padding-left: 1em;
    margin-left: 0;
    margin-bottom: 1em;
    color: #666;
  }

  ::v-deep a {
    color: #007acc;
    text-decoration: none;
  }

  ::v-deep a:hover {
    text-decoration: underline;
  }

    ::v-deep strong {
    font-weight: bold;
     color: #000
  }

  ::v-deep em {
    font-style: italic;
     color: #000
  }
</style>

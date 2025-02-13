<template>
  <div class="app-container">
    <vue-markdown :source="markdownContent" />
  </div>
</template>

<script>
import VueMarkdown from 'vue-markdown'

export default {
  components: { VueMarkdown },
  data() {
    return {
      markdownContent: ''
    }
  },
  mounted() {
    this.getMarkdown()
  },
  methods: {
    async getMarkdown() {
      try {
        this.markdownContent = require('./index.md')
      } catch (error) {
        console.error('Error fetching markdown:', error)
      }
    }
  }
}
</script>

<style>
div.app-container pre {
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
}

code {
  border: 1px solid #eee;
  /* 可以根据需要调整内边距 */
  /* padding: 2px 4px; */
  /* background-color: #f9f9f9; */
}

pre code {
  border: none; /* 移除 pre code 的边框 */
  padding: 0; /* 移除 pre code 的内边距 */
  background-color: transparent; /* 移除 pre code 的背景色 */
  display: block;
  font-family: Consolas; /* 设置字体为 Consolas */
}
</style>

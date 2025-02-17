<template>
  <div class="dashboard-container">
    <MarkdownRenderer :content="markdownContent" />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import MarkdownRenderer from '@/components/MarkdownRenderer/index.vue'

export default {
  name: 'Dashboard',
  components: { MarkdownRenderer },
  data() {
    return {
      markdownContent: require('./index.md')
    }
  },
  computed: {
    ...mapGetters([
      'roles'
    ])
  }
}
</script>

<style>
div.dashboard-container {
  padding: 20px;
}
div.dashboard-container pre {
  border: 1px solid #ccc;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
  box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
}

div.dashboard-container code {
  border: 1px solid #eee;
  /* 可以根据需要调整内边距 */
  /* padding: 2px 4px; */
  /* background-color: #f9f9f9; */
}

div.dashboard-container pre code {
  border: none; /* 移除 pre code 的边框 */
  padding: 0; /* 移除 pre code 的内边距 */
  background-color: transparent; /* 移除 pre code 的背景色 */
  display: block;
  font-family: Consolas; /* 设置字体为 Consolas */
}
</style>

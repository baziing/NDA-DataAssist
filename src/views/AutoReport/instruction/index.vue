<template>
  <div class="app-container">
    <MarkdownRenderer :content="markdownContent" />
  </div>
</template>

<script>
import MarkdownRenderer from '@/components/MarkdownRenderer'

export default {
  components: { MarkdownRenderer },
  data() {
    return {
      markdownContent: require('./index.md')
    }
  }
}
</script>

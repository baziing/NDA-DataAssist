<template>
  <el-dialog
    title="提示"
    :visible="visible"
    width="30%"
    :before-close="handleCancel"
  >
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
      <i class="el-icon-warning" style="color: #fa982f; font-size: 24px; margin-right: 10px;" />
      <span>{{ message }}</span>
    </div>
    <span slot="footer" class="dialog-footer" style="text-align: right;">
      <el-button @click="handleCancel">取 消</el-button>
      <el-button type="primary" :loading="loading" @click="handleConfirm">确 定</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: 'DeleteConfirmationDialog',
  props: {
    visible: {
      type: Boolean,
      required: true
    },
    message: {
      type: String,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    handleConfirm() {
      this.$emit('confirm')
    },
    handleCancel() {
      this.$emit('cancel')
    }
  }
}
</script>

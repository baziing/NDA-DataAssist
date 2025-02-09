<template>
  <div class="manual-report-container">
    <h1>手动生成报表</h1>

    <div class="progress-group">
      <div class="progress-item">
        <el-upload
          action="#"
          :show-file-list="false"
          :on-change="handleFileUpload"
          :auto-upload="false"
        >
          <el-button type="primary" :disabled="uploadButtonDisabled">导入文件</el-button>
        </el-upload>
        <el-progress :percentage="uploadProgress" :status="uploadStatus" class="progress-bar" />
      </div>

      <div class="progress-item">
        <el-button type="primary" :disabled="startButtonDisabled" @click="handleStart">开始执行</el-button>
        <el-progress :percentage="executionProgress" :status="executionStatus" class="progress-bar" />
      </div>

      <div class="progress-item">
        <el-button type="primary" :disabled="downloadButtonDisabled" @click="handleDownload">下载文件</el-button>
        <el-progress :percentage="downloadProgress" :status="downloadStatus" class="progress-bar" />
      </div>

      <div class="progress-item">
        <el-button type="warning" @click="handleReset">重置任务</el-button>
        <div class="progress-bar" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Manual',
  data() {
    return {
      uploadProgress: 0,
      executionProgress: 0,
      downloadProgress: 0,
      uploadStatus: null, // 进度条状态
      executionStatus: null,
      downloadStatus: null,
      file: null,
      uploadButtonDisabled: false,
      startButtonDisabled: true,
      downloadButtonDisabled: true,
      isExecuting: false // 标记是否正在执行
    }
  },
  methods: {
    handleFileUpload(file) {
      // this.file = file; // 移除这行代码
      this.uploadProgress = 0 // 先重置为 0
      this.$forceUpdate() // 强制更新
      // this.uploadProgress = 100; // 假数据，仅为视觉效果
      this.uploadStatus = 'success'
      this.startButtonDisabled = false
      this.downloadButtonDisabled = true
      this.executionProgress = 0 // 重置进度
      this.executionStatus = null
      // 如果正在执行，则重置执行状态
      if (this.isExecuting) {
        this.isExecuting = false
        this.uploadProgress = 0
        this.uploadStatus = null
        // this.startButtonDisabled = false; //这里不需要，因为导入文件后，开始执行按钮总是可用的
      }
      console.log('文件已选择:', file)

      // 使用 fetch API 调用后端 /upload 接口
      const formData = new FormData()
      formData.append('file', file.raw) // 使用 file.raw
      console.log(formData) // 检查 FormData 对象

      fetch('http://localhost:5000/upload', { // 修改 URL
        method: 'POST',
        body: formData
        // headers: { // 通常不需要手动设置 Content-Type
        //   'Content-Type': 'multipart/form-data'
        // }
      })
        .then(response => {
          if (response.ok) {
            this.uploadProgress = 100
            this.uploadStatus = 'success'
            return response.json()
          } else {
            throw new Error('文件上传失败')
          }
        })
        .then(data => {
          console.log(data.message)
        // TODO: 处理上传成功的响应
        })
        .catch(error => {
          console.error('Error:', error)
          this.uploadStatus = 'exception' // or 'error'
        // TODO: 处理上传失败的情况
        })
    },
    handleStart() {
      console.log('开始执行')
      this.startButtonDisabled = true
      this.isExecuting = true
      // TODO: 调用后端 API 开始执行任务
      // 模拟执行过程
      let progress = 0
      const interval = setInterval(() => {
        progress += 10
        this.executionProgress = progress
        if (progress >= 100) {
          this.executionProgress = 100
          this.executionStatus = 'success'
          this.downloadButtonDisabled = false
          this.uploadButtonDisabled = true
          this.isExecuting = false
          clearInterval(interval)
        }
      }, 200)
    },
    handleDownload() {
      console.log('下载文件')
      // TODO: 调用后端 API 下载文件
      // 模拟下载过程
      this.downloadProgress = 0
      this.downloadStatus = null
      let progress = 0
      const interval = setInterval(() => {
        progress += 10
        this.downloadProgress = progress
        if (progress >= 100) {
          this.downloadProgress = 100
          this.downloadStatus = 'success'
          clearInterval(interval)
        }
      }, 200)
    },
    handleReset() {
      this.uploadProgress = 0
      this.executionProgress = 0
      this.downloadProgress = 0
      this.uploadStatus = null
      this.executionStatus = null
      this.downloadStatus = null
      this.file = null
      this.uploadButtonDisabled = false
      this.startButtonDisabled = true
      this.downloadButtonDisabled = true
      this.isExecuting = false
    }
  }
}
</script>

<style scoped>
.manual-report-container {
  padding: 20px;
}

.progress-group {
  display: flex;
  flex-direction: column;
  gap: 20px; /* 增加间距 */
}

.progress-item {
  display: flex;
  align-items: center;
}

.progress-item .el-button {
  margin-right: 20px; /* 增加按钮和进度条之间的间距 */
  width: 100px; /* 固定按钮宽度 */
}
.progress-bar{
    flex: 1;
}
</style>

<template>
  <div class="manual-report-container">
    <h1>手动生成报表</h1>

    <el-collapse v-model="activeNames" @change="handleCollapseChange">
      <el-collapse-item title="新建" name="1">
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
      </el-collapse-item>
      <el-collapse-item title="基本信息" name="2">
        <div>提交时间：{{ submitTime }}</div>
        <div>文件名：{{ uploadedFilename }}</div>
        <div>文件大小：{{ fileSize }}</div>
      </el-collapse-item>
      <el-collapse-item title="执行" name="3">
        <el-button type="primary" :disabled="startButtonDisabled" @click="handleStart">开始执行</el-button>
        <el-progress :percentage="executionProgress" :status="executionStatus" class="progress-bar" />
        <div class="log-container">
          <pre>{{ executionLog }}</pre>
        </div>
      </el-collapse-item>
      <el-collapse-item title="下载" name="4">
        <el-button type="primary" :disabled="downloadButtonDisabled" @click="handleDownload">导出文件</el-button>
        <div>文件名：{{ outputFile }}</div>
        <div>文件大小：{{ outputFileSize }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
export default {
  name: 'Manual',
  data() {
    return {
      activeNames: ['1'], // 默认展开的面板
      uploadProgress: 0,
      executionProgress: 0,
      downloadProgress: 0,
      uploadStatus: null,
      executionStatus: null,
      downloadStatus: null,
      file: null,
      uploadedFilename: null,
      outputFile: null,
      uploadButtonDisabled: false,
      startButtonDisabled: true,
      downloadButtonDisabled: true,
      isExecuting: false,
      submitTime: null, // 提交时间
      fileSize: null, // 文件大小
      outputFileSize: null, // 输出文件大小
      executionLog: '' // 执行日志
    }
  },
  methods: {
    handleFileUpload(file) {
      this.uploadProgress = 0
      this.$forceUpdate()
      this.uploadStatus = 'success'
      this.startButtonDisabled = false
      this.downloadButtonDisabled = true
      this.executionProgress = 0
      this.executionStatus = null
      if (this.isExecuting) {
        this.isExecuting = false
        this.uploadProgress = 0
        this.uploadStatus = null
      }
      console.log('文件已选择:', file)

      const formData = new FormData()
      formData.append('file', file.raw)
      console.log(formData)

      fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('文件上传失败')
          }
        })
        .then(data => {
          this.uploadProgress = 100
          this.uploadStatus = 'success'
          console.log(data.message)
          this.uploadedFilename = data.filename
          this.submitTime = new Date().toLocaleString() // 获取当前时间
          this.fileSize = (file.raw.size / 1024).toFixed(2) + ' KB' // 文件大小，转换为 KB
          this.activeNames = ['1', '2'] // 展开“基本信息”面板
        })
        .catch(error => {
          console.error('Error:', error)
          this.uploadStatus = 'exception'
        })
    },
    handleStart() {
      console.log('开始执行')
      this.startButtonDisabled = true
      this.isExecuting = true
      this.executionLog = '' // 清空日志
      this.activeNames = ['1', '2', '3'] // 展开“执行”面板

      // 模拟日志输出
      this.executionLog += '开始执行...\n'
      setTimeout(() => {
        this.executionLog += '正在连接数据库...\n'
        this.executionProgress = 20
        this.$forceUpdate()
      }, 1000)
      setTimeout(() => {
        this.executionLog += '正在执行 SQL 查询...\n'
        this.executionProgress = 50
        this.$forceUpdate()
      }, 2000)
      setTimeout(() => {
        this.executionLog += '正在生成报表...\n'
        this.executionProgress = 80
        this.$forceUpdate()
      }, 3000)

      // 调用后端 /generate 接口
      fetch('http://localhost:5000/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: this.uploadedFilename })
      })
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('报表生成失败')
          }
        })
        .then(data => {
          console.log(data.message)
          this.outputFile = data.output_file
          // 获取输出文件大小（假设后端返回的文件名包含扩展名）
          this.outputFileSize = '未知' // 暂时设置为未知，后续需要后端提供
          this.executionProgress = 100
          this.executionStatus = 'success'
          this.downloadButtonDisabled = false
          this.uploadButtonDisabled = true
          this.isExecuting = false
          this.executionLog += '报表生成成功！\n'
          this.activeNames = ['1', '2', '3', '4'] // 展开“下载”面板
        })
        .catch(error => {
          console.error('Error:', error)
          this.executionStatus = 'exception'
          this.startButtonDisabled = false
          this.isExecuting = false
          this.executionLog += '报表生成失败！\n'
        })
    },
    handleDownload() {
      if (!this.outputFile) {
        alert('请先生成报表')
        return
      }
      const downloadUrl = `http://localhost:5000/download/${this.outputFile}`
      const link = document.createElement('a')
      link.href = downloadUrl
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      this.downloadProgress = 100
      this.downloadStatus = 'success'
    },
    handleReset() {
      this.uploadProgress = 0
      this.executionProgress = 0
      this.downloadProgress = 0
      this.uploadStatus = null
      this.executionStatus = null
      this.downloadStatus = null
      this.file = null
      this.uploadedFilename = null
      this.outputFile = null
      this.uploadButtonDisabled = false
      this.startButtonDisabled = true
      this.downloadButtonDisabled = true
      this.isExecuting = false
      this.submitTime = null
      this.fileSize = null
      this.outputFileSize = null
      this.executionLog = ''
      this.activeNames = ['1'] // 重置折叠面板
    },
    handleCollapseChange(activeNames) {
      console.log(activeNames)
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
  gap: 20px;
}

.progress-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px; /* 增加间距 */
}

.progress-item .el-button {
  margin-right: 20px;
  width: 100px;
}

.progress-bar {
  flex: 1;
}

.log-container {
  margin-top: 10px;
  border: 1px solid #ccc;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  background-color: #f8f8f8;
}
</style>

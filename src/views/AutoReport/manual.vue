<template>
  <div class="manual-report-container">
    <div class="header-container">
      <h1>手动生成报表</h1>
      <i class="el-icon-refresh reset-icon" title="重置任务" @click="handleResetTask" />
    </div>
    <el-collapse v-model="activeNames" @change="handleCollapseChange">
      <el-collapse-item title="新建" name="1">
        <div class="progress-item">
          <el-upload
            action="#"
            :show-file-list="false"
            :on-change="handleFileUpload"
            :auto-upload="false"
          >
            <el-button type="primary" :disabled="uploadButtonDisabled">导入模板</el-button>
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
        <div>文件名：{{ outputFileName }}</div>
        <div>文件大小：{{ outputFileSize }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import { MessageBox } from 'element-ui'
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
      executionLog: '', // 执行日志
      outputFileName: null // 添加这一行
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

      fetch(`http://localhost:${process.env.VUE_APP_API_PORT}/upload`, {
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
          this.uploadProgress = 100
          this.uploadStatus = 'success'
          console.log(data.message)
          this.uploadedFilename = data.original_filename
          this.submitTime = new Date().toLocaleString()
          this.fileSize = (file.raw.size / 1024).toFixed(2) + ' KB'
          this.file = file // 将 file 对象赋值给 this.file
          this.filename = data.filename // 保存上传后返回的filename
          this.activeNames = ['1', '2', '3']
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
      this.executionLog = ''
      this.executionLog += '开始执行...\n'

      // 调用后端 /generate 接口
      fetch(`http://localhost:${process.env.VUE_APP_API_PORT}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ filename: this.filename, original_filename: this.uploadedFilename })
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
          this.taskId = data.task_id // 保存 task_id

          // 使用 setInterval 定期获取进度
          const intervalId = setInterval(() => {
            fetch(`http://localhost:${process.env.VUE_APP_API_PORT}/progress/${this.taskId}`)
              .then(response => {
                if (response.ok) {
                  return response.json()
                } else {
                  throw new Error('获取进度失败')
                }
              })
              .then(progressData => {
                this.executionProgress = progressData.progress
                this.executionStatus = progressData.status
                this.executionLog = progressData.logs.join('\n') // 将日志数组连接成字符串

                if (progressData.status === 'success') {
                  this.outputFile = progressData.output_file
                  this.outputFileName = progressData.output_filename
                  this.outputFileSize = (progressData.output_file_size / 1024).toFixed(2) + ' KB' // 后续需要后端提供
                  this.downloadButtonDisabled = false
                  this.uploadButtonDisabled = true
                  this.isExecuting = false
                  this.activeNames = ['1', '2', '3', '4'] // 展开“下载”面板
                  clearInterval(intervalId) // 成功后清除 interval
                } else if (progressData.status === 'failed') {
                  this.executionStatus = 'exception'
                  this.startButtonDisabled = false
                  this.isExecuting = false
                  clearInterval(intervalId) // 失败后清除 interval
                }
              })
              .catch(error => {
                console.error('Error:', error)
                this.executionStatus = 'exception'
                this.startButtonDisabled = false
                this.isExecuting = false
                this.executionLog += '获取进度失败！\n'
                clearInterval(intervalId) // 出错时清除 interval
              })
          }, 1000) // 每秒获取一次进度
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

      if (!this.outputFile) {
        alert('请先生成报表')
        return
      }

      // 构造下载链接
      const downloadUrl = `http://localhost:${process.env.VUE_APP_API_PORT}/download/${this.outputFile}`

      // 创建一个隐藏的 <a> 元素
      const link = document.createElement('a')
      link.href = downloadUrl
      link.style.display = 'none'
      document.body.appendChild(link)

      // 模拟点击，触发下载
      link.click()

      // 移除 <a> 元素
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
      this.outputFileName = null
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
    // 添加确认对话框
    async handleResetTask() {
      try {
        await MessageBox.confirm('确定要重置任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        if (this.isExecuting) {
        // 调用后端 API 终止任务
          fetch(`http://localhost:${process.env.VUE_APP_API_PORT}/reset/${this.taskId}`, {
            method: 'POST'
          })
            .then(response => {
              if (response.ok) {
                this.$message({
                  message: '任务已重置',
                  type: 'success'
                })
              } else {
                this.$message.error('重置任务失败')
              }
            })
            .catch(error => {
              console.error('Error:', error)
              this.$message.error('重置任务失败')
            })
          clearInterval(this.intervalId) // 清除定时器
        }
        // 重置前端状态
        this.handleReset()
      } catch (error) {
        // 取消重置
      }
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
  position: relative;
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
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.reset-icon {
    font-size: 20px;
    cursor: pointer;
    color: #f56c6c;
    margin-left: auto;
    margin-top: 55px; /* 向下偏移 */
}
</style>

<template>
  <div class="manual-report-container">
    <div class="header-container">
      <h1 />
      <i class="el-icon-refresh reset-icon" title="重置任务" @click="handleResetTask" />
    </div>
    <el-collapse v-model="activeNames" @change="handleCollapseChange">
      <el-collapse-item title="新建任务" name="1">
        <div class="progress-item">
          <el-upload
            action="#"
            :show-file-list="false"
            :on-change="handleFileUpload"
            :auto-upload="false"
          >
            <el-button type="primary" :disabled="uploadButtonDisabled">导入模板</el-button>
          </el-upload>
          <el-progress :percentage="uploadProgress" :status="uploadStatus" class="progress-bar" style="margin-left: 10px;" />
        </div>
      </el-collapse-item>
      <el-collapse-item title="模板信息" name="2">
        <div>提交时间：{{ submitTime }}</div>
        <div>文件名：{{ uploadedFilename }}</div>
        <div>文件大小：{{ fileSize }}</div>
      </el-collapse-item>
      <el-collapse-item title="导入变量" name="5">
        <div class="progress-item">
          <el-button :style="{ width: '40px' }" type="danger" size="medium" :disabled="skipButtonDisabled" @click="handleSkipVariables">SKIP</el-button>
          <el-upload
            action="#"
            :show-file-list="false"
            :on-change="handleVarFileUpload"
            :on-progress="handleVarUploadProgress"
            :auto-upload="false"
            style="margin-left: 0px;"
          >
            <el-button :style="{ width: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }" type="primary" :disabled="skipButtonDisabled">上传</el-button>
          </el-upload>
          <el-progress :percentage="uploadVarProgress" :status="uploadVarStatus" class="progress-bar" style="margin-left: 10px;" />
        </div>
      </el-collapse-item>
      <el-collapse-item title="变量内容" name="6">
        <div v-if="!showVariables || (showVariables && (!variables || variables.length === 0))">
          没有导入变量
        </div>
        <div v-else>
          <div class="log-container">
            <table>
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="variable in variables" :key="variable.key">
                  <td>{{ variable.key }}</td>
                  <td>{{ variable.value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </el-collapse-item>
      <el-collapse-item title="执行任务" name="3">
        <div class="progress-item">
          <el-button type="primary" :disabled="startButtonDisabled" style="display: flex; align-items: center; justify-content: center;" @click="handleStart">开始执行</el-button>
          <el-progress :percentage="executionProgress" :status="executionStatus" class="progress-bar" style="margin-left: 10px;" />
        </div>
        <div class="log-container">
          <pre>{{ executionLog }}</pre>
        </div>
      </el-collapse-item>
      <el-collapse-item title="下载结果" name="4">
        <el-button type="primary" :disabled="downloadButtonDisabled" style="margin-bottom: 10px; display: flex; align-items: center; justify-content: center;" @click="handleDownload">导出文件</el-button>
        <div>文件名：{{ outputFileName }}</div>
        <div>文件大小：{{ outputFileSize }}</div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import { MessageBox } from 'element-ui'
import settings from '@/settings'

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
      uploadButtonDisabled: false, // 初始时启用上传模板按钮
      skipButtonDisabled: true, // 初始禁用“SKIP”和“上传”
      startButtonDisabled: true, // 初始时禁用开始按钮
      downloadButtonDisabled: true, // 初始时禁用下载按钮
      isExecuting: false,
      submitTime: null, // 提交时间
      fileSize: null, // 文件大小
      outputFileSize: null, // 输出文件大小
      executionLog: '', // 执行日志
      outputFileName: null,
      downloadFilename: null, // 用于下载的文件名
      variables_filename: null, // 存储变量文件名
      variables: [], // 存储变量
      showVariables: false, // 控制变量内容显示
      uploadVarProgress: 0,
      uploadVarStatus: null
    }
  },
  methods: {
    handleFileUpload(file) {
      this.uploadProgress = 0
      this.$forceUpdate()
      this.uploadStatus = null // 初始状态应为 null
      this.startButtonDisabled = true // 上传模板后禁用开始按钮
      this.downloadButtonDisabled = true
      this.executionProgress = 0
      this.executionStatus = null
      this.executionLog = '' // 清空执行日志
      if (this.isExecuting) {
        this.isExecuting = false
        this.uploadProgress = 0
        this.uploadStatus = null
      }
      console.log('文件已选择:', file)

      // 检查文件类型
      if (!file.raw.name.endsWith('.xlsx')) {
        this.uploadStatus = 'exception'
        this.$message.error('请上传 .xlsx 格式的模板文件')
        return // 提前返回，阻止后续操作
      }

      const formData = new FormData()
      formData.append('file', file.raw)

      // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/upload`, {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            return response.json().then(data => {
              throw new Error(data.error || '模板文件上传失败')
            })
          }
        })
        .then(data => {
          this.uploadProgress = 100
          this.uploadStatus = 'success'
          console.log(data.message)
          this.uploadedFilename = data.original_filename
          this.submitTime = new Date().toLocaleString()
          this.fileSize = (file.raw.size / 1024).toFixed(2) + ' KB'
          this.file = file // 将 file 对象赋值给 this.file
          this.filename = data.filename // 保存上传后返回的filename
          this.activeNames = ['1', '2', '5'] // 展开“模板信息”和“导入变量”
          this.skipButtonDisabled = false // 启用“SKIP”和“上传”按钮
          this.executionLog = '' // 清空执行日志
        })
        .catch(error => {
          console.error('Error:', error)
          this.uploadStatus = 'exception'
          this.$message.error(error.message)
          this.uploadProgress = 0 // 重置进度条
          this.skipButtonDisabled = true // 禁用“SKIP”
          this.executionLog = '' // 清空执行日志
        })
    },
    // 新增处理变量文件上传
    handleVarFileUpload(file) {
      this.uploadVarProgress = 0
      this.$forceUpdate()
      this.startButtonDisabled = false // 上传变量后启用开始按钮
      this.activeNames = ['1', '2', '5', '6', '3'] // 展开“变量内容”和“执行任务”
      console.log('变量文件已选择:', file)

      const formData = new FormData()
      formData.append('file', file.raw)

      // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/upload_vars`, {
        method: 'POST',
        body: formData
      })
        .then((response) => {
          if (response.ok) {
            return response.json()
          } else {
            // 处理 HTTP 错误
            return response.json().then((data) => {
              throw new Error(data.error || '变量文件上传失败')
            })
          }
        })
        .then((data) => {
          this.variables = data.variables
          this.showVariables = true
          this.variables_filename = data.filename
          console.log('变量文件上传成功:', data)
          this.uploadVarProgress = 100
          this.uploadVarStatus = 'success'
        })
        .catch((error) => {
          console.error('Error:', error)
          this.uploadVarStatus = 'exception'
          this.$message.error(error.message) // 显示错误信息
          this.startButtonDisabled = true // 禁用“执行任务”
          this.variables = [] // 清空变量
        })
    },
    handleVarUploadProgress(event, file, fileList) {
      this.uploadVarProgress = Math.floor((event.loaded / event.total) * 100)
      this.uploadVarStatus = this.uploadVarProgress === 100 ? 'success' : 'uploading'
    },
    handleSkipVariables() {
      this.showVariables = false
      this.uploadVarProgress = 0
      this.uploadVarStatus = null
      this.startButtonDisabled = false // 点击“SKIP”后启用开始按钮
      this.activeNames = ['1', '2', '5', '6', '3'] // 展开“变量内容”和“执行任务”
      this.variables_filename = null
      this.variables = []
    },
    handleStart() {
      console.log('开始执行')
      this.startButtonDisabled = true
      this.isExecuting = true
      this.executionLog = ''
      this.executionLog += '开始执行...\n'
      this.activeNames = ['1', '2', '5', '3', '6']
      // 调用后端 /generate 接口
      // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: this.filename,
          original_filename: this.uploadedFilename,
          variables_filename: this.variables_filename
        })
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
          this.downloadFilename = data.original_filename // 保存原始文件名

          // 使用 setInterval 定期获取进度
          const intervalId = setInterval(() => {
            // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
            fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/progress/${this.taskId}`)
              .then(response => {
                if (response.ok) {
                  return response.json()
                } else {
                  throw new Error('获取进度失败')
                }
              })
              .then(progressData => {
                this.executionProgress = progressData.progress
                this.executionStatus = progressData.status['status']
                this.executionLog = progressData.logs.join('\n') // 将日志数组连接成字符串

                if (progressData.status['status'] === 'success') {
                  this.outputFile = progressData.output_file
                  this.outputFileName = progressData.output_filename
                  this.outputFileSize = (progressData.output_file_size / 1024).toFixed(2) + ' KB'
                  this.downloadButtonDisabled = false // 启用下载按钮
                  this.uploadButtonDisabled = true
                  this.skipButtonDisabled = true
                  this.isExecuting = false
                  this.activeNames = ['1', '2', '5', '6', '3', '4'] // 展开“下载结果”
                  clearInterval(intervalId) // 成功后清除 interval
                } else if (progressData.status['status'] === 'failed') {
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

      // 获取当前时间戳
      const now = new Date()
      const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`

      // 构造下载链接
      // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
      const downloadUrl = `http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/download/${this.outputFile.replace('output/', '')}`

      // 创建一个隐藏的 <a> 元素
      const link = document.createElement('a')
      link.href = downloadUrl
      link.style.display = 'none'
      link.download = `${this.downloadFilename.replace('.xlsx', '')}_${timestamp}.xlsx` // 设置下载文件名
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
      this.downloadFilename = null // 重置下载文件名
      this.uploadButtonDisabled = false
      this.startButtonDisabled = true
      this.downloadButtonDisabled = true
      this.isExecuting = false
      this.submitTime = null
      this.fileSize = null
      this.outputFileSize = null
      this.executionLog = ''
      this.activeNames = ['1'] // 重置折叠面板
      this.variables = []
      this.showVariables = false
      this.variables_filename = null
      this.uploadVarProgress = 0
      this.uploadVarStatus = null
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
          // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
          fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/reset/${this.taskId}`, {
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
  padding: 10px 20px 20px 20px;
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
    display: flex;
    align-items: center;
    justify-content: center;
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

.log-container table {
  border-collapse: collapse;
  width: 100%;
}

.log-container th,
.log-container td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}
.reset-icon {
    font-size: 20px;
    cursor: pointer;
    color: #f56c6c;
    margin-left: auto;
    margin-top: 5px; /* 向下偏移 */
}
</style>

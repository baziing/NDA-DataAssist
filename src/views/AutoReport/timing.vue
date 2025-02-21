<template>
  <div class="timing-container">
    <h2>定时报表任务创建</h2>

    <el-form ref="taskForm" :model="task" label-width="120px">
      <el-form-item label="上传文件">
        <div class="progress-item">
          <div style="display: flex; align-items: center;">
            <el-upload
              class="upload-demo"
              action="#"
              :multiple="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :auto-upload="false"
              :file-list="fileList"
              :show-file-list="false"
              accept=".xlsx"
            >
              <el-button type="primary">上传文件</el-button>
            </el-upload>
            <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : undefined" style="margin-left: 10px;" />
            <span v-if="task.filename" style="margin-left: 10px;">{{ task.filename }}</span>
            <i v-if="task.filename" class="el-icon-delete" style="margin-left: 10px;" @click="handleFileRemove(null, [])" />
            <span v-else style="margin-left: 10px;">尚未上传文件</span>
          </div>
        </div>
      </el-form-item>

      <el-form-item label="游戏分类">
        <el-select v-model="task.gameType" placeholder="请选择游戏分类">
          <el-option label="无归类" value="无归类" />
          <el-option label="风之大陆" value="风之大陆" />
          <el-option label="战神遗迹" value="战神遗迹" />
          <el-option label="云上城之歌" value="云上城之歌" />
          <el-option label="闪烁之光" value="闪烁之光" />
          <el-option label="有杀气童话2" value="有杀气童话2" />
          <el-option label="矩阵临界" value="矩阵临界" />
          <el-option label="不朽觉醒" value="不朽觉醒" />
          <el-option label="Kemono Friends" value="Kemono Friends" />
          <el-option label="最后的原始人" value="最后的原始人" />
          <el-option label="Order Daybreak" value="Order Daybreak" />
          <el-option label="The Dragon Odyssey" value="The Dragon Odyssey" />
          <el-option label="白荆回廊" value="白荆回廊" />
        </el-select>
      </el-form-item>

      <el-form-item label="任务名称">
        <el-input v-model="task.taskName" placeholder="请输入任务名称" />
        <div class="input-tip">每个游戏分类下，任务名称不能重名，不支持空格输入</div>
      </el-form-item>

      <el-form-item label="定时设置">
        <el-select v-model="task.frequency" placeholder="请先选择频率" style="margin-right: 10px;">
          <el-option label="每月" value="month" />
          <el-option label="每周" value="week" />
          <el-option label="每日" value="day" />
        </el-select>

        <el-select v-if="task.frequency === 'month'" v-model="task.dayOfMonth" placeholder="请选择日期" style="margin-right: 10px;">
          <el-option v-for="day in 31" :key="day" :label="day + '日'" :value="day" />
        </el-select>

        <el-select v-if="task.frequency === 'week'" v-model="task.dayOfWeek" placeholder="请选择星期" style="margin-right: 10px;">
          <el-option label="周一" value="1" />
          <el-option label="周二" value="2" />
          <el-option label="周三" value="3" />
          <el-option label="周四" value="4" />
          <el-option label="周五" value="5" />
          <el-option label="周六" value="6" />
          <el-option label="周日" value="7" />
        </el-select>

        <el-select v-if="!task.frequency" v-model="task.daySetting" placeholder="请选择" style="margin-right: 10px;" disabled />
        <el-select v-else-if="task.frequency === 'day'" v-model="task.daySetting" placeholder="无需选择" style="margin-right: 10px;" disabled>
          <el-option label="无需选择" value="none" />
        </el-select>

        <el-time-picker
          v-model="task.time"
          placeholder="选择时间"
          format="HH:mm"
          value-format="HH:mm"
          style="margin-right: 10px;"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="danger" @click="clearForm">清空配置</el-button>
        <el-button type="primary" @click="createTask">创建任务</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import settings from '@/settings'
export default {
  name: 'Timing',
  data() {
    const now = new Date()
    return {
      task: {
        filename: '',
        gameType: '',
        taskName: '',
        frequency: '',
        dayOfMonth: '',
        dayOfWeek: '',
        time: `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
      },
      fileList: [],
      uploadProgress: 0,
      uploadStatus: null
    }
  },
  methods: {
    handleFileChange(file, fileList) {
      this.uploadProgress = 0
      this.uploadStatus = null
      this.fileList = fileList
      console.log('file:', file)
      console.log('fileList:', fileList)
      // 检查文件类型
      if (file && !file.raw.name.endsWith('.xlsx')) {
        this.uploadStatus = 'exception'
        this.$message.error('请上传 .xlsx 格式的模板文件')
        return // 提前返回，阻止后续操作
      }

      if (!file) {
        this.task.filename = ''
        return
      }

      const formData = new FormData()
      formData.append('file', file.raw)

      console.log('formData:', formData)
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
          this.task.filename = data.original_filename // 更新文件名
          console.log('uploadProgress:', this.uploadProgress)
          console.log('task.filename:', this.task.filename)
        })
        .catch(error => {
          console.error('Error:', error)
          this.uploadStatus = 'exception'
          this.$message.error(error.message)
          this.uploadProgress = 0 // 重置进度条
        })
    },
    handleFileRemove(file, fileList) {
      console.log('handleFileRemove - file:', file)
      console.log('handleFileRemove - fileList:', fileList)
      this.task.filename = ''
      this.fileList = []
      this.uploadProgress = 0
      console.log('handleFileRemove - task.filename:', this.task.filename)
    },
    clearForm() {
      // this.$refs.taskForm.resetFields(); // This line was causing the issue
      this.task.filename = ''
      this.task.gameType = ''
      this.task.taskName = ''
      this.task.frequency = ''
      this.task.dayOfMonth = ''
      this.task.dayOfWeek = ''
      this.task.daySetting = ''
      this.task.time = ''
      this.fileList = []
      this.uploadProgress = 0
    },
    createTask() {
      // 模拟创建任务
      // 检查必填项
      if (!this.task.filename || !this.task.gameType || !this.task.taskName || !this.task.frequency || !this.task.time) {
        this.$message.error('请填写所有必填项！')
        return
      }
      // 检查任务名称是否包含空格
      if (this.task.taskName.includes(' ')) {
        this.$message.error('任务名称不能包含空格！')
        return
      }

      // 检查月/周/日选项
      if (this.task.frequency === 'month' && !this.task.dayOfMonth) {
        this.$message.error('请选择月份中的具体日期！')
        return
      }
      if (this.task.frequency === 'week' && !this.task.dayOfWeek) {
        this.$message.error('请选择星期几！')
        return
      }

      this.$message.success('任务创建成功！')
    }
  }
}
</script>

<style scoped>
.timing-container {
  padding: 20px;
}

.input-tip{
  font-size: 12px;
}
</style>

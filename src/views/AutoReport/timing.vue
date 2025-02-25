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
            <el-progress :percentage="uploadProgress" :status="uploadStatus" style="margin-left: 10px;" />
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
        <div style="display: flex;  width: 100%;">
          <el-select v-model="task.frequency" placeholder="请先选择频率" style="flex: 1; max-width: 200px; margin-right: 10px;">
            <el-option label="每月" value="month" />
            <el-option label="每周" value="week" />
            <el-option label="每日" value="day" />
          </el-select>

          <el-select v-if="task.frequency === 'month'" v-model="task.dayOfMonth" placeholder="请选择日期" style="flex: 1; max-width: 200px; margin-right: 10px;">
            <el-option v-for="day in 31" :key="day" :label="day + '日'" :value="day" />
          </el-select>

          <el-select v-if="task.frequency === 'week'" v-model="task.dayOfWeek" placeholder="请选择星期" style="flex: 1; max-width: 200px; margin-right: 10px;">
            <el-option label="周一" value="1" />
            <el-option label="周二" value="2" />
            <el-option label="周三" value="3" />
            <el-option label="周四" value="4" />
            <el-option label="周五" value="5" />
            <el-option label="周六" value="6" />
            <el-option label="周日" value="7" />
          </el-select>

          <el-select v-if="!task.frequency" v-model="task.daySetting" placeholder="请选择" style="flex: 1; max-width: 200px; margin-right: 10px;" disabled />
          <el-select v-else-if="task.frequency === 'day'" v-model="task.daySetting" placeholder="无需选择" style="flex: 1; max-width: 200px; margin-right: 10px;" disabled>
            <el-option label="无需选择" value="none" />
          </el-select>

          <el-time-picker
            v-model="task.time"
            placeholder="选择时间"
            format="HH:mm"
            value-format="HH:mm"
            style="flex: 1; max-width: 200px;"
          />
        </div>
      </el-form-item>

      <el-form-item>
        <el-button type="danger" @click="clearForm">清空配置</el-button>
        <el-button type="primary" @click="createTask">创建任务</el-button>
      </el-form-item>

      <el-form-item label="任务进度">
        <el-input
          v-model="taskProgress"
          type="textarea"
          :rows="8"
          placeholder="任务进度信息"
          readonly
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import settings from '@/settings'
const { serverAddress } = settings
export default {
  name: 'Timing',
  data() {
    const now = new Date()
    return {
      task: {
        filename: '',
        uuidFileName: '', // 用于存储后端返回的 UUID 文件名
        gameType: '',
        taskName: '',
        frequency: '',
        dayOfMonth: '',
        dayOfWeek: '',
        time: `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
      },
      fileList: [],
      uploadProgress: 0,
      uploadStatus: null,
      taskProgress: ''
    }
  },
  methods: {
    getFormattedTimestamp() {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')

      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    handleFileChange(file, fileList) {
      this.uploadProgress = 0
      this.uploadStatus = null
      this.fileList = fileList
      console.log('file:', file)
      console.log('fileList:', fileList)

      // 检查文件类型
      if (file && !file.raw.name.endsWith('.xlsx')) {
        this.$message.error('请上传 .xlsx 格式的模板文件')
        this.task.filename = ''
        return // 提前返回，阻止后续操作
      }

      // 如果file为空
      if (!file) {
        this.task.filename = ''
        this.taskProgress = ''
        return
      }

      // 使用 FormData 对象上传文件
      const formData = new FormData()
      formData.append('file', file.raw)

      fetch(`http://${serverAddress}:${process.env.VUE_APP_API_PORT}/upload`, {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            return response.json().then(data => {
              throw new Error(data.message || '文件上传失败')
            })
          }
        })
        .then(data => {
          this.$message.success(data.message || '文件上传成功！')
          this.task.filename = data.original_filename // 使用原始文件名
          this.task.uuidFileName = data.filename // 保存后端返回的 UUID 文件名
          this.uploadProgress = 100
          this.uploadStatus = 'success'
          this.taskProgress += `${this.getFormattedTimestamp()} - 文件上传成功\n`
        })
        .catch(error => {
          this.$message.error(error.message)
          this.taskProgress = `${this.getFormattedTimestamp()} - 文件上传失败: ${error.message}\n`
          this.uploadStatus = 'exception'
          this.uploadProgress = 0 // 重置进度条
          this.task.filename = ''
        })
    },
    handleFileRemove(file, fileList) {
      console.log('handleFileRemove - file:', file)
      console.log('handleFileRemove - fileList:', fileList)
      this.taskProgress = ''
      this.task.filename = ''
      this.fileList = []
      this.uploadProgress = 0
      this.uploadStatus = null
      console.log('handleFileRemove - task.filename:', this.task.filename)
    },
    clearForm() {
      // this.$refs.taskForm.resetFields(); // This line was causing the issue
      this.task.filename = ''
      this.task.uuidFileName = ''
      this.task.gameType = ''
      this.task.taskName = ''
      this.task.frequency = ''
      this.task.dayOfMonth = ''
      this.task.dayOfWeek = ''
      this.task.daySetting = ''
      this.task.time = ''
      this.fileList = []
      this.uploadProgress = 0
      this.uploadStatus = null
      // this.taskProgress = ''
    },
    createTask() {
      // 模拟创建任务
      this.taskProgress += `${this.getFormattedTimestamp()} - 正在检测是否有未填写内容……\n`
      // 检查必填项
      if (!this.task.filename || !this.task.gameType || !this.task.taskName || !this.task.frequency || !this.task.time) {
        this.$message.error('请填写所有必填项！')
        this.taskProgress += `${this.getFormattedTimestamp()} - 请填写所有必填项！\n`
        return
      }
      // 检查任务名称是否包含空格
      if (this.task.taskName.includes(' ')) {
        this.$message.error('任务名称不能包含空格！')
        this.taskProgress += `${this.getFormattedTimestamp()} - 任务名称不能包含空格！\n`
        return
      }

      // 检查月/周/日选项
      if (this.task.frequency === 'month' && !this.task.dayOfMonth) {
        this.$message.error('请选择月份中的具体日期！')
        this.taskProgress += `${this.getFormattedTimestamp()} - 请选择月份中的具体日期！\n`
        return
      }
      if (this.task.frequency === 'week' && !this.task.dayOfWeek) {
        this.$message.error('请选择星期几！')
        this.taskProgress += `${this.getFormattedTimestamp()} - 请填写所有必填项！\n`
        return
      }

      // 检查任务名称是否重名
      this.taskProgress += `${this.getFormattedTimestamp()} - 正在检测任务名称是否有重名……\n`
      // 重要提示：如果您希望从同一网络中的其他计算机访问此服务，请将 "localhost" 替换为运行此服务的计算机的 IP 地址或主机名。
      fetch(`http://${serverAddress}:${process.env.VUE_APP_API_PORT}/check_task_name`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          gameType: this.task.gameType,
          taskName: this.task.taskName
        })
      })
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            return response.json().then(data => {
              throw new Error(data.message || '任务名称校验失败')
            })
          }
        })
        .then(data => {
          if (!data.is_valid) {
            this.$message.error(data.message)
            this.taskProgress += `${this.getFormattedTimestamp()} - 任务名称校验失败: ${data.message}\n`
            return // 显式返回，阻止后续的 .then() 执行
          }

          // 在这里添加 SQL 校验逻辑
          this.taskProgress += `${this.getFormattedTimestamp()} - 正在校验sql……\n`
          // 调用后端 API 校验 SQL
          return fetch(`http://${serverAddress}:${process.env.VUE_APP_API_PORT}/check_sql`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              filename: this.task.uuidFileName // 使用后端返回的 UUID 文件名
            })
          })
            .then(response => {
              if (response.ok) {
                return response.json()
              } else {
                return response.json().then(data => {
                  throw new Error(data.message || 'SQL 校验失败')
                })
              }
            })
            .then(data => {
              if (!data.is_valid) {
                this.$message.error(data.message)
                this.taskProgress += `${this.getFormattedTimestamp()} - SQL 校验失败: ${data.message}\n`
                throw new Error(data.message || 'SQL 校验失败') // 抛出异常，阻止后续的 .then() 执行
              }

              // 正在创建任务
              this.taskProgress += `${this.getFormattedTimestamp()} - 正在创建任务……\n`
              // TODO: 调用后端 API 创建任务
              return fetch(`http://${serverAddress}:${process.env.VUE_APP_API_PORT}/create_task`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.task)
              })
            })
            .then(response => {
              if (response.ok) {
                return response.json()
              } else {
                return response.json().then(data => {
                  throw new Error(data.message || '创建任务失败')
                })
              }
            })
            .then(data => {
              this.$message.success(data.message || '任务创建成功！')
              this.taskProgress += `${this.getFormattedTimestamp()} - 创建成功。\n`
              // 清空表单
              this.clearForm()
            })
            .catch(error => {
              this.$message.error(error.message)
              this.taskProgress += `${this.getFormattedTimestamp()} - ${error.message}\n`
              this.taskProgress += `${this.getFormattedTimestamp()} - 任务终止。\n`
            })
        })
        .catch(error => {
          this.$message.error(error.message)
          this.taskProgress += `${this.getFormattedTimestamp()} - 任务名称校验失败: ${error.message}\n`
          this.taskProgress += `${this.getFormattedTimestamp()} - 任务终止。\n`
        })
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

<template>
  <div class="timing-container">

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
          <el-option
            v-for="item in gameCategories"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="任务名称">
        <el-input v-model="task.taskName" placeholder="请输入任务名称" @blur="updateOutputExample" />
        <div class="form-tip">每个游戏分类下，任务名称不能重名，不支持空格输入；<br>
          支持日期命名，以达到[25M02月度报告.xlsx]效果。具体请见 格式说明-文件名格式化；</div>
      </el-form-item>

      <el-form-item label="输出示例">
        <span v-if="outputExample">{{ outputExample }}</span>
        <span v-else>请在上方输入任务名称</span>
      </el-form-item>

      <el-row>
        <el-col :span="24">
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
        </el-col>
      </el-row>

      <!-- 新增邮件地址选择 -->
      <el-form-item label="邮件地址">
        <el-select
          v-model="task.recipients"
          multiple
          filterable
          placeholder="请选择收件人"
          style="width: 100%;"
          @tag-close="handleTagClose"
        >
          <template slot="prefix">
            <i class="el-icon-message" style="color: #909399;" />
          </template>
          <el-option-group label="邮件组">
            <el-option
              v-for="group in emailGroups"
              :key="'group-' + group.id"
              :label="group.group_name"
              :value="'group-' + group.id"
              class="email-group-option"
            >
              <span style="float: left">{{ group.group_name }}</span>
              <span style="float: right; color: #409EFF; font-size: 13px">邮件组</span>
            </el-option>
          </el-option-group>
          <el-option-group label="邮件地址">
            <el-option
              v-for="email in emails"
              :key="'email-' + email.id"
              :label="email.name ? email.name + ' <' + email.email + '>' : email.email"
              :value="'email-' + email.id"
              class="email-address-option"
            >
              <span style="float: left">{{ email.email }}</span>
              <span style="float: right; color: #67C23A; font-size: 13px">个人</span>
            </el-option>
          </el-option-group>
        </el-select>
        <div class="form-tip">可以选择多个邮件组或邮件地址作为收件人</div>
      </el-form-item>
      <!-- 邮件地址选择结束 -->

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

export default {
  name: 'Timing',
  data() {
    const now = new Date()
    return {
      gameCategories: settings.gameCategories,
      task: {
        filename: '',
        uuidFileName: '', // 用于存储后端返回的 UUID 文件名
        gameType: '',
        taskName: '',
        frequency: '',
        dayOfMonth: '',
        dayOfWeek: '',
        time: `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`,
        recipients: [] // 新增收件人字段
      },
      fileList: [],
      uploadProgress: 0,
      uploadStatus: null,
      taskProgress: '',
      tasks: [], // 假设任务列表存储在这个变量中
      outputExample: '',
      emails: [], // 存储邮件地址列表
      emailGroups: [] // 存储邮件组列表
    }
  },
  watch: {
    // 监听收件人变化，应用样式
    'task.recipients': {
      handler() {
        this.$nextTick(() => {
          this.applyTagStyles()
        })
      },
      deep: true
    }
  },
  created() {
    // 获取任务列表
    fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/get_tasks`)
      .then(response => {
        if (response.ok) {
          return response.json()
        } else {
          throw new Error('获取任务列表失败')
        }
      })
      .then(data => {
        console.log('任务列表:', data)
        // this.tasks = data; // 假设任务列表存储在 this.tasks 中
      })
      .catch(error => {
        console.error('Error:', error)
      })

    // 获取邮件地址列表
    this.fetchEmails()

    // 获取邮件组列表
    this.fetchEmailGroups()

    // 添加事件监听器，在组件挂载后应用样式
    this.$nextTick(() => {
      this.applyTagStyles()
    })
  },
  mounted() {
    // 组件挂载后应用样式
    this.applyTagStyles()

    // 添加全局点击事件监听器，确保在选择器展开/收起时应用样式
    document.addEventListener('click', this.handleGlobalClick)
  },
  beforeDestroy() {
    // 组件销毁前移除事件监听器
    document.removeEventListener('click', this.handleGlobalClick)
  },
  methods: {
    // 获取邮件地址列表
    fetchEmails() {
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/emails`)
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('获取邮件地址列表失败')
          }
        })
        .then(data => {
          console.log('邮件地址列表:', data)
          this.emails = data.items || []
          // 在数据加载后应用标签样式
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
        .catch(error => {
          console.error('获取邮件地址失败:', error)
          this.$message.error('获取邮件地址列表失败')
        })
    },

    // 获取邮件组列表
    fetchEmailGroups() {
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/email-groups`)
        .then(response => {
          if (response.ok) {
            return response.json()
          } else {
            throw new Error('获取邮件组列表失败')
          }
        })
        .then(data => {
          console.log('邮件组列表:', data)
          this.emailGroups = data
          // 在数据加载后应用标签样式
          this.$nextTick(() => {
            this.applyTagStyles()
          })
        })
        .catch(error => {
          console.error('获取邮件组失败:', error)
          this.$message.error('获取邮件组列表失败')
        })
    },
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
    updateOutputExample() {
      if (this.task.taskName) {
        fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/format_filename`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ taskName: this.task.taskName })
        })
          .then(response => response.json())
          .then(data => {
            this.outputExample = data.formatted_filename
          })
          .catch(error => {
            console.error('Error:', error)
            this.outputExample = '生成示例失败'
          })
      } else {
        this.outputExample = ''
      }
    },
    handleFileChange(file, fileList) {
      this.taskProgress = '' // 清空任务进度信息
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

      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/upload`, {
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
      this.task.recipients = [] // 清空收件人
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
      fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/check_task_name`, {
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
          return fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/check_sql`, {
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
              return fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/create_task`, {
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
              // 获取 task_id 和 next_run_at
              this.$message.success(data.message || '任务创建成功！')
              this.taskProgress += `${this.getFormattedTimestamp()} - 创建成功。\n`

              // 获取 task_id 和 next_run_at
              const nextRunAt = data.next_run_at

              // 显式地将 next_run_at 赋值给一个变量并打印
              const nextRunAtValue = data.next_run_at
              console.log('Next run at value:', nextRunAtValue)

              // 在控制台输出 next_run_at 的值
              console.log('Next run at:', nextRunAt)

              // 清空表单
              this.clearForm()
              // 触发事件
              this.$bus.$emit('task-created')
              // 重新获取任务列表
              fetch(`http://${settings.serverAddress}:${process.env.VUE_APP_API_PORT}/get_tasks`)
                .then(response => {
                  if (response.ok) {
                    return response.json()
                  } else {
                    throw new Error('获取任务列表失败')
                  }
                })
                .then(data => {
                  console.log('更新后的任务列表:', data)
                  // this.tasks = data; // 假设任务列表存储在 this.tasks 中
                })
                .catch(error => {
                  console.error('Error:', error)
                })
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
    },
    handleTagClose(tag) {
      console.log('Tag closed:', tag)
      // 在下一个DOM更新周期应用样式
      this.$nextTick(() => {
        this.applyTagStyles()
      })
    },
    applyTagStyles() {
      // 获取所有标签
      const tags = document.querySelectorAll('.el-select__tags .el-tag')

      // 遍历标签并应用样式
      tags.forEach(tag => {
        const value = tag.textContent || ''

        // 检查标签内容，根据内容判断类型
        if (this.emailGroups.some(group => group.group_name === value.trim())) {
          // 邮件组样式
          tag.style.backgroundColor = '#f0f9eb'
          tag.style.borderColor = '#e1f3d8'
          tag.style.color = '#67c23a'
          // 添加自定义类名
          tag.classList.add('email-group-tag')
          tag.classList.remove('email-address-tag')
        } else {
          // 个人邮件样式
          tag.style.backgroundColor = '#ecf5ff'
          tag.style.borderColor = '#d9ecff'
          tag.style.color = '#409eff'
          // 添加自定义类名
          tag.classList.add('email-address-tag')
          tag.classList.remove('email-group-tag')
        }
      })
    },
    // 处理全局点击事件
    handleGlobalClick() {
      // 延迟执行，确保DOM已更新
      setTimeout(() => {
        this.applyTagStyles()
      }, 100)
    }
  }
}
</script>

<style scoped>
.timing-container {
  padding: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  padding-top: 4px;
}

/* 自定义邮件标签样式 */
::v-deep .el-tag {
  margin-right: 4px;
}

/* 邮件组样式 - 使用属性选择器 */
::v-deep .el-tag[data-path*="group-"] {
  background-color: #ecf5ff !important;
  border-color: #d9ecff !important;
  color: #409eff !important;
}

/* 邮件地址样式 - 使用属性选择器 */
::v-deep .el-tag[data-path*="email-"] {
  background-color: #f0f9eb !important;
  border-color: #e1f3d8 !important;
  color: #67c23a !important;
}
</style>
